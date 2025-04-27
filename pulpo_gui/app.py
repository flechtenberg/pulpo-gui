import streamlit as st
from pulpo import optimize

def main():
    st.title("PULPO Life Cycle Optimization")

    functional_unit = st.text_input("Functional Unit", value="1 kg product")
    st.header("Process Choices (DOFs)")
    all_processes = ["process_a", "process_b", "process_c"]  # replace later
    dofs = st.multiselect("Select processes", options=all_processes, default=all_processes[:1])

    st.header("Objective Function")
    obj_options = ["minimize_co2", "minimize_cost"]
    objective = st.selectbox("Choose objective", options=obj_options)

    st.header("Constraints (Upper Bounds)")
    bounds = {}
    for p in dofs:
        bounds[p] = st.number_input(f"Upper bound for {p}", min_value=0.0, value=1.0, step=0.1)

    if st.button("Run Optimization"):
        with st.spinner("Solving..."):
            try:
                result = optimize(
                    functional_unit=functional_unit,
                    dofs=dofs,
                    objective=objective,
                    bounds=bounds
                )
                st.success("Optimization complete!")
                st.write(result)
            except Exception as e:
                st.error(f"Error: {e}")

if __name__ == "__main__":
    main()
