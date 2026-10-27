"""Convenience entrypoint for running the Streamlit dashboard the same way
app.py is run — a plain `python run_streamlit.py`, no separate `streamlit
run` command needed. This is what PyCharm's Run button executes; using
`streamlit run streamlit_app.py` from a terminal works identically and is
the normal way to start it outside an IDE.
"""
from __future__ import annotations
import pathlib
import sys

try:
    from streamlit.web import cli as stcli
except ImportError:
    sys.exit(
        "\n  Streamlit is not installed in this Python environment.\n"
        "  Install it, then run this file again:\n\n"
        f"      {sys.executable} -m pip install -r requirements-streamlit.txt\n")


def _skip_first_run_prompt():
    """Streamlit's very first run on a machine asks, on stdin, whether to
    join its mailing list, which blocks forever under a non-interactive
    runner (including PyCharm's Run button). Pre-writing an empty-email
    credentials file answers that prompt once, permanently, exactly as
    typing a blank line and pressing Enter would."""
    cred = pathlib.Path.home() / ".streamlit" / "credentials.toml"
    if not cred.exists():
        cred.parent.mkdir(parents=True, exist_ok=True)
        cred.write_text('[general]\nemail = ""\n')


if __name__ == "__main__":
    _skip_first_run_prompt()
    target = pathlib.Path(__file__).resolve().parent / "streamlit_app.py"
    sys.argv = ["streamlit", "run", str(target)]
    sys.exit(stcli.main())
