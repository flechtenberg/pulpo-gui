import sys, os
from streamlit.web import cli as stcli

if __name__ == "__main__":
    # Where pyinstaller unpacks everything at runtime:
    MEIPASS = getattr(sys, "_MEIPASS", os.path.dirname(__file__))

    # We copy pulpo-gui.py into the root of MEIPASS so we can point Streamlit at it
    script_path = os.path.join(MEIPASS, "pulpo-gui.py")

    # Build the fake CLI args for "streamlit run"
    sys.argv = [
        "streamlit",
        "run",
        script_path,
        "--server.port",            "8501",
        "--global.developmentMode", "false",
        "--server.headless",        "false",
    ]

    sys.exit(stcli.main())
