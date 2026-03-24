import os
import sys

# Set global.developmentMode to false when running as compiled executable
# to avoid conflict with server.port setting and ensure it runs in production mode
# This must be set BEFORE importing streamlit
if getattr(sys, 'frozen', False):
    # Try to disable development mode via environment variable
    os.environ["STREAMLIT_GLOBAL_DEVELOPMENTMODE"] = "false"

from streamlit.web import cli as stcli


def main() -> None:
    """Launch the Streamlit Log Viewer app via the Streamlit CLI.

    This mimics running `streamlit run app.py` so behavior matches the
    command that already works correctly in your environment.
    """
    
    # When running as a PyInstaller bundle, sys._MEIPASS contains the path to the bundle
    # Otherwise, use the current directory
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        base_path = sys._MEIPASS
    else:
        # Running as script
        base_path = os.path.dirname(__file__)
    
    script_path = os.path.join(base_path, "app.py")
    
    # Call stcli.main directly with the arguments
    # For compiled executables, we need to explicitly disable development mode
    # and specify the port
    if getattr(sys, 'frozen', False):
        # When frozen, explicitly disable development mode and specify port 8501
        sys.argv = ["streamlit", "run", "--global.developmentMode", "false", "--server.port", "8501", script_path]
    else:
        # When running as script, specify port 8501 explicitly to avoid confusion
        sys.argv = ["streamlit", "run", "--server.port", "8501", script_path]
    
    # Delegate to Streamlit's CLI entry point
    sys.exit(stcli.main())


if __name__ == "__main__":
    main()
