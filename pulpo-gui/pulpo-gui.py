# pulpo-gui/app.py
import os
import re

import io
import pandas as pd

import streamlit as st
import bw2data as bd
from pulpo import pulpo
from pulpo.utils.saver import extract_results
from pathlib import Path
from PIL import Image

# Compute the folder where this script lives:
HERE = Path(__file__).parent

# Build the absolute path to your PNG:
logo_path = HERE / "data" / "Pulpo.ico"
logo = Image.open(logo_path)
LOGO_PATH = HERE / "data" / "Pulpo-Logo_INKSCAPE_small.png"
logo_img = Image.open(LOGO_PATH)


@st.cache_data(show_spinner=False)
def get_dynamic_lists(project_name):
    """Retrieve processes, methods, and flows from Brightway data."""
    bd.projects.set_current(project_name)
    # All non-biosphere processes
    processes = sorted({
        f"{a['reference product']} {a['name']} {a['location']} [{db}] [key: {a.key}]"
        for db in bd.databases
        if db != "biosphere3"
        for a in bd.Database(db)
    })
    # LCIA methods
    methods = [str(m) for m in bd.methods] if bd.methods else []
    # Biosphere flows
    flows = sorted({
        f"{f['name']}  [key: {f.key}]"
        for f in bd.Database("biosphere3")
    }) if "biosphere3" in bd.databases else []
    return processes, methods, flows

def extract_key(item_str):
    """Pull the key out of “[key: …]” or return the raw string."""
    m = re.search(r"\[key:\s*([^\]]+)\]", item_str)
    return m.group(1) if m else item_str

def optimize(functional_unit, process_sets, objectives, constraints):
    """Run Pulpo optimization based on GUI inputs."""
    cwd = os.getcwd()
    project = st.session_state.bw_project.name
    dbs = [db for db in bd.databases if db != "biosphere3"]
    database = dbs[0] if dbs else None

    # Convert objectives to dict
    method_weights = {method: weight for method, weight in objectives}
    worker = pulpo.PulpoOptimizer(project, database, method_weights, cwd)
    worker.get_lci_data()

    # Build demand
    fu_map = {extract_key(s): q for s, q in functional_unit}
    fu_acts = worker.retrieve_processes(keys=list(fu_map))
    demand = {act: fu_map[str(act.key)] for act in fu_acts}

    # Build choice sets
    choices = {}
    for cfg in process_sets:
        bounds = {extract_key(p): ub for p, ub in cfg.get("bounds", {}).items()}
        acts = worker.retrieve_processes(keys=list(bounds))
        choices[cfg.get("label", "")] = {act: bounds.get(str(act.key)) for act in acts}

    # Process-level limits
    proc_limits = {
        extract_key(c["process"]): (c["lower"], c["upper"])
        for c in constraints.get("processes", [])
    }
    proc_acts = worker.retrieve_processes(keys=list(proc_limits))
    lower_limit = {
        a: proc_limits[str(a.key)][0]
        for a in proc_acts
        if proc_limits[str(a.key)][0] is not None
    }
    upper_limit = {
        a: proc_limits[str(a.key)][1]
        for a in proc_acts
        if proc_limits[str(a.key)][1] is not None
    }

    # Impact-method limits
    upper_imp_limit = {c["method"]: c["upper"] for c in constraints.get("methods", [])}

    # Flow-level limits
    flow_bounds = {
        extract_key(c["flow"]): c["upper"]
        for c in constraints.get("flows", [])
    }
    flow_acts = worker.retrieve_envflows(keys=list(flow_bounds))
    upper_elem_limit = {
        f: flow_bounds[str(f.key)]
        for f in flow_acts
    }

    # Instantiate & solve
    worker.instantiate(
        choices=choices,
        demand=demand,
        upper_limit=upper_limit,
        lower_limit=lower_limit,
        upper_elem_limit=upper_elem_limit,
        upper_imp_limit=upper_imp_limit,
    )

    worker.solve()
    results = extract_results(worker)

    return results

def change_project():
    bd.projects.set_current(st.session_state.bw_project.name)

def remove_entry(entry_id):
    """Remove any session items containing this entry_id."""
    # 1) Remove from its “_ids” list
    for list_key in [
        "fu_ids", "set_ids", "obj_ids",
        "proc_constr_ids", "method_constr_ids", "flow_constr_ids"
    ]:
        lst = st.session_state.get(list_key, [])
        if entry_id in lst:
            lst.remove(entry_id)
            break
    # 2) Drop any session_state keys that mention this id
    for key in list(st.session_state.keys()):
        if entry_id in key:
            st.session_state.pop(key, None)

def main():

    st.set_page_config(
        page_title="PULPO LCO 🐙",
        page_icon=logo,  # ← path to your logo file
    )

    st.image(
        logo_img,
        width=300,
    )

    st.title("Life Cycle Optimization")

    # --- Project selector ---
    projects = list(bd.projects)
    if "bw_project" not in st.session_state:
        st.session_state.bw_project = projects[0] if projects else None

    st.selectbox(
        "🔍 Brightway Project",
        projects,
        key="bw_project",
        format_func=lambda x: x.name,
        on_change=change_project,
        help="Select which Brightway2 project you want to use ⚙️"
    )

    # Load dynamic lists
    all_processes, obj_methods, all_flows = get_dynamic_lists(
        st.session_state.bw_project.name
    )

    # --- 1️⃣ Functional Unit Processes ---
    st.header("1️⃣ Functional Unit Processes")
    if "fu_ids" not in st.session_state:
        st.session_state.fu_ids = []
    if st.button("➕ Add Functional Unit Process", help="Add a new process to your functional unit"):
        st.session_state.fu_ids.append(f"fu_{len(st.session_state.fu_ids)+1}")

    fu_inputs = []
    for eid in st.session_state.fu_ids:
        c1, c2, c3 = st.columns([4, 4, 2])
        with c1:
            proc = st.selectbox(
                "🛠️ Select FU process",
                all_processes,
                key=f"fu_process_{eid}",
                help="Choose a process to include in the functional unit"
            )
        with c2:
            qty = st.number_input(
                "🔢 Quantity",
                min_value=0.0,
                value=1.0,
                step=0.1,
                key=f"fu_qty_{eid}",
                help="Set the amount of the selected process"
            )
        with c3:
            st.button(
                "🗑️ Remove",
                key=f"rm_fu_{eid}",
                on_click=remove_entry,
                args=(eid,),
                help="Remove this FU entry"
            )
        fu_inputs.append((proc, qty))

    # --- 2️⃣ Process Choice Sets ---
    st.header("2️⃣ Process Choice Sets")
    if "set_ids" not in st.session_state:
        st.session_state.set_ids = []
    if st.button("➕ Add Process Set", help="Define a group of alternative processes"):
        st.session_state.set_ids.append(f"set_{len(st.session_state.set_ids)+1}")

    set_configs = []
    for eid in st.session_state.set_ids:
        with st.expander(f"🗂️ Process Set {eid}"):
            st.button(
                "🗑️ Remove",
                key=f"rm_set_{eid}",
                on_click=remove_entry,
                args=(eid,),
                help="Remove this process set"
            )
            label = st.text_input(
                "🏷️ Label",
                key=f"set_label_{eid}",
                help="Give this choice set a descriptive name"
            )
            procs = st.multiselect(
                "🔍 Select processes",
                all_processes,
                key=f"set_procs_{eid}",
                help="Pick which processes belong to this set"
            )
            bounds = {
                p: st.number_input(
                    f"🔢 Upper bound for “{p}”",
                    min_value=0.0,
                    value=1e20,
                    step=1e19,
                    key=f"set_bound_{eid}_{p}",
                    help="Max amount allowed for this process"
                )
                for p in procs
            }
            set_configs.append({"label": label, "bounds": bounds})

    # --- 3️⃣ Objective Function Methods ---
    st.header("3️⃣ Objective Function Methods")
    if "obj_ids" not in st.session_state:
        st.session_state.obj_ids = []
    if st.button("➕ Add Objective Method", help="Add an LCIA method to the objective function"):
        st.session_state.obj_ids.append(f"obj_{len(st.session_state.obj_ids)+1}")

    obj_inputs = []
    for eid in st.session_state.obj_ids:
        c1, c2, c3 = st.columns([4, 4, 2])
        with c1:
            method = st.selectbox(
                "🎯 Select objective method",
                obj_methods,
                key=f"obj_method_{eid}",
                help="Choose an impact assessment method"
            )
        with c2:
            weight = st.number_input(
                "⚖️ Weight",
                min_value=0.0,
                value=1.0,
                step=0.1,
                key=f"obj_weight_{eid}",
                help="Set the relative importance of this method"
            )
        with c3:
            st.button(
                "🗑️ Remove",
                key=f"rm_obj_{eid}",
                on_click=remove_entry,
                args=(eid,),
                help="Remove this objective method"
            )
        obj_inputs.append((method, weight))

    # --- 4️⃣ Additional Constraints ---
    st.header("4️⃣ Additional Constraints")

    # 4a. Process Constraints
    st.subheader("Process Constraints")
    proc_tooltip = (
        "🔧 If lower = upper, a supply problem is solved and slack variables\n"
        "are activated for the demand."
    )
    if "proc_constr_ids" not in st.session_state:
        st.session_state.proc_constr_ids = []
    if st.button("➕ Add Process Constraint", help=proc_tooltip):
        st.session_state.proc_constr_ids.append(f"pc_{len(st.session_state.proc_constr_ids)+1}")

    proc_constraints = []
    for eid in st.session_state.proc_constr_ids:
        c1, c2, c3, c4 = st.columns([3, 3, 3, 2])
        with c1:
            proc = st.selectbox(
                "🛠️ Process",
                all_processes,
                key=f"proc_constr_proc_{eid}",
                help="Choose a process to constrain"
            )
        with c2:
            lb = st.number_input(
                "🔽 Lower bound",
                min_value=0.0,
                value=0.0,
                step=0.1,
                key=f"proc_constr_lb_{eid}",
                help="Minimum amount allowed"
            )
        with c3:
            ub = st.number_input(
                "🔼 Upper bound",
                min_value=0.0,
                value=1.0,
                step=0.1,
                key=f"proc_constr_ub_{eid}",
                help="Maximum amount allowed"
            )
        with c4:
            st.button(
                "🗑️ Remove",
                key=f"rm_pc_{eid}",
                on_click=remove_entry,
                args=(eid,),
                help="Remove this process constraint"
            )
        proc_constraints.append({"process": proc, "lower": lb, "upper": ub})

    # 4b. Method Constraints
    st.subheader("Method Constraints")
    if "method_constr_ids" not in st.session_state:
        st.session_state.method_constr_ids = []
    if st.button("➕ Add Method Constraint", help="Add an upper‐bound on an LCIA method"):
        st.session_state.method_constr_ids.append(f"mc_{len(st.session_state.method_constr_ids)+1}")

    method_constraints = []
    for eid in st.session_state.method_constr_ids:
        c1, c2, c3 = st.columns([4, 3, 2])
        with c1:
            m = st.selectbox(
                "🎯 Method",
                obj_methods,
                key=f"method_constr_{eid}",
                help="Select which method to constrain"
            )
        with c2:
            ub = st.number_input(
                "🔼 Upper bound",
                min_value=0.0,
                value=1.0,
                step=0.1,
                key=f"method_constr_val_{eid}",
                help="Maximum total impact allowed"
            )
        with c3:
            st.button(
                "🗑️ Remove",
                key=f"rm_mc_{eid}",
                on_click=remove_entry,
                args=(eid,),
                help="Remove this method constraint"
            )
        method_constraints.append({"method": m, "upper": ub})

    # 4c. Flow Constraints
    st.subheader("Flow Constraints")
    if "flow_constr_ids" not in st.session_state:
        st.session_state.flow_constr_ids = []
    if st.button("➕ Add Flow Constraint", help="Add an upper‐bound on an environmental flow"):
        st.session_state.flow_constr_ids.append(f"fc_{len(st.session_state.flow_constr_ids)+1}")

    flow_constraints = []
    for eid in st.session_state.flow_constr_ids:
        c1, c2, c3 = st.columns([4, 3, 2])
        with c1:
            f = st.selectbox(
                "Flow",
                all_flows,
                key=f"flow_constr_{eid}",
                help="Select which biosphere flow to constrain"
            )
        with c2:
            ub = st.number_input(
                "🔼 Upper bound",
                min_value=0.0,
                value=1.0,
                step=0.1,
                key=f"flow_constr_val_{eid}",
                help="Maximum total emission or uptake allowed"
            )
        with c3:
            st.button(
                "🗑️ Remove",
                key=f"rm_fc_{eid}",
                on_click=remove_entry,
                args=(eid,),
                help="Remove this flow constraint"
            )
        flow_constraints.append({"flow": f, "upper": ub})

    # --- 🚀 Run Optimization ---
    st.header("🚀 Run Optimization")
    if st.button("🏁 Run Optimization", help="Start solving the linear program"):
        with st.spinner("🕑 Solving..."):
            try:
                results = optimize(
                    functional_unit=fu_inputs,
                    process_sets=set_configs,
                    objectives=obj_inputs,
                    constraints={
                        "processes": proc_constraints,
                        "methods":   method_constraints,
                        "flows":     flow_constraints,
                    }
                )
                st.success("✅ Optimization complete!")

                # Display results
                for sheet_name, df in results.items():
                    title = sheet_name.replace("_", " ").capitalize()
                    icon = "📐" if sheet_name != "Choices" else "🔀"
                    st.subheader(f"{icon} {title}")
                    if sheet_name == "Choices":
                        for choice_name, choice_df in df.items():
                            st.markdown(f"**{choice_name}**")
                            st.dataframe(choice_df)
                    else:
                        st.dataframe(df)

                # Download as Excel
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
                    choices = results.pop("Choices", {})
                    combined = []
                    for name, cdf in choices.items():
                        header = pd.DataFrame([[name] + [None]*(len(cdf.columns)-1)],
                                              columns=cdf.columns)
                        combined.append(header)
                        tmp = cdf.reset_index()
                        tmp.insert(0, "Original Index", cdf.index)
                        combined.append(tmp)
                    if combined:
                        pd.concat(combined, ignore_index=True) \
                          .to_excel(writer, sheet_name="Choices", index=False)
                    for name, df in results.items():
                        if not df.empty:
                            df.to_excel(writer, sheet_name=name, index=True)
                buffer.seek(0)
                st.download_button(
                    label="💾 Download full results as Excel",
                    data=buffer,
                    file_name="pulpo_results.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    help="Export all result sheets to an Excel file"
                )

            except Exception as e:
                st.error(f"❌ Error during optimization: {e}")


if __name__ == "__main__":
    main()


