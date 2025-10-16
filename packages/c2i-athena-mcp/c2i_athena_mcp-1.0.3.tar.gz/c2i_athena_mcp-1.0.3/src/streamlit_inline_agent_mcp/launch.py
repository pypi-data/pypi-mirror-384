import os
import sys

from streamlit.web import cli

def main():
    script_path =os.path.join(os.path.dirname(__file__),"mcp_agent_ui.py")
    cli.main_run([str(script_path)] + sys.argv[1:])

if __name__ == "__main__":
    main()