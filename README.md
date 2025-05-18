# Pulpo GUI

A desktop‐packaged Streamlit application for Life Cycle Optimization using [Pulpo](https://github.com/flechtenberg/pulpo).

## 📦 Download & Run the Executable

If you just want to use the application without installing anything else:

1. Download the latest `pulpo-gui.exe` from the [Release Page](https://github.com/flechtenberg/pulpo-gui/releases/tag/v0.1.1)
2. Double‐click `pulpo-gui.exe`.
3. Your default browser will automatically open to `http://localhost:8501` where the GUI is available.

> **Note:** Make sure port 8501 is free on your machine. If it’s in use, restart the app or stop the service occupying that port.

---

## 🔧 Local Setup & Development

Follow these steps to clone the repository, create a Python environment, and run the app locally.

### 1. Clone the Repository

```bash
git clone https://github.com/flechtenberg/pulpo-gui.git
cd pulpo-gui
```

### 2. Create & Activate a Virtual Environment

```bash
python -m venv .venv
# Windows
.\.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate
```

### 3. Install Dependencies

Install core requirements:

```bash
pip install -r requirements.txt
```

* `requirements.txt` includes Streamlit, Pyomo, bw2data, and other core libs.
* `pulpo-dev[bw2]` installs `pulpo` plus Brightway2 integration.
* `highspy` is required for the HiGHS solver backend.

### 4. Run the App Locally

You have two options:

1. **Via the launcher script** (recommended):

   ```bash
   python pulpo-gui/launcher.py
   ```
2. **Directly with Streamlit**:

   ```bash
   streamlit run pulpo-gui/pulpo-gui.py --server.headless false
   ```

Your browser should open at `http://localhost:8501` with the Pulpo GUI.

---

## ⚙️ Building Your Own Executable

If you need to repackage the app (e.g., after code changes), use PyInstaller (`pip install` it!) with all required data and dependencies bundled.

Run this command from the project root:

```bash
pyinstaller --onefile --icon=pulpo-gui/data/Pulpo.ico --add-data "pulpo-gui/data;data" --add-data "pulpo-gui/pulpo-gui.py;." --collect-all streamlit --collect-all pyomo --collect-all bw2data --collect-all pulpo --collect-all highspy pulpo-gui/launcher.py
```

* **`--onefile`**: packages everything into a single `exe`.
* **`--add-data`**: includes your icon and static data.
* **`--collect-all`**: ensures Streamlit, Pyomo, Brightway2, Pulpo, and Highspy assets/plugins are included. In case you introduce new dependencies add them also via ``collect-all``.
* The resulting standalone executable appears in `dist/launcher.exe` (you may rename it to `pulpo-gui.exe`).

---

## 🤝 Contributing & Development

Pulpo GUI is open source and welcomes contributions!

### How to Contribute

1. Fork the repository and create a feature branch:

   ```bash
   git checkout -b feature/awesome-change
   ```
2. Implement your feature or bug fix.
3. Update or add tests if applicable.
4. Commit and push your branch:

   ```bash
   git add .
   git commit -m "Add awesome change"
   git push origin feature/awesome-change
   ```
5. Open a Pull Request against `main` and describe your changes.

### Issues & Support

* For general questions, open a discussion or ask on the repository’s Discussions page.

---

## 📄 License

This project is licensed under the BSD 3-Clause License. See [LICENSE](LICENSE) for details.
