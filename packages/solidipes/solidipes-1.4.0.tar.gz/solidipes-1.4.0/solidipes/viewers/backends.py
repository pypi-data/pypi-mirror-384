"""Detection of running platform and viewers' backend."""

import os

# Define possible backends
backends = ["python", "jupyter notebook", "streamlit"]


def set_backend(backend) -> None:
    """Modify current backend and relevant internal variables."""
    global current_backend

    if backend not in backends:
        raise TypeError(f'Backend "{backend}" not supported.Choose from {backends}')

    try:
        import pyvista as pv

        if backend == "python":
            pv.set_jupyter_backend(None)

        elif backend == "jupyter notebook":
            pv.set_jupyter_backend("trame")

            if "SESSION_URL" in os.environ:
                pv.global_theme.trame.server_proxy_enabled = True
                session = os.environ["SESSION_URL"]
                session = session.lstrip("https://")
                s = session.split("/")
                s = "/" + "/".join(s[1:] + ["proxy/"])
                pv.global_theme.trame.server_proxy_prefix = s

        elif backend == "streamlit":
            pv.set_jupyter_backend("trame")

    except ImportError:
        pass

    current_backend = backend


# Define current backend
current_backend = "python"

# Check if running inside Jupyter Notebook, change backend if so
try:
    shell = get_ipython().__class__.__name__  # type: ignore
    if shell == "ZMQInteractiveShell":
        set_backend("jupyter notebook")
except NameError:
    pass

# Check if running inside Streamlit, change backend if so
try:
    from streamlit.runtime.scriptrunner import get_script_run_ctx

    if get_script_run_ctx(suppress_warning=True):
        set_backend("streamlit")
except ModuleNotFoundError:
    pass
