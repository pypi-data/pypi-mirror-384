import json
import nbformat
from nbclient import NotebookClient
import os

_THIS_FILE_DIR = os.path.dirname(os.path.abspath(__file__))


def get_temp_dir(subdir: str):
    """Get the path to the temporary directory for the given subdirectory

    If the directory does not exist, it will be created.

    Args:
        subdir (str): _description_

    Returns:
        _type_: _description_
    """
    path = os.path.join(_THIS_FILE_DIR, "_temp", subdir)
    if not os.path.exists(path):
        os.makedirs(path)
    return path


def run_notebooks(notebook_path, use_m2m_auth):
    """
    Execute the notebook in a clean Jupyter kernel and fail if any cell errors.
    We also inject a setup cell that reproduces the same patching as the fixture,
    but *inside the kernel* the notebook runs in.
    """
    # Grab the token value from your fixture so we can mirror the patch in the kernel.
    # Your fixture yields the mock, whose return_value is the token string.
    token_value = use_m2m_auth.return_value

    # Load the notebook
    nb = nbformat.read(notebook_path, as_version=4)

    # Inject a setup cell at the very top that applies the same patch logic
    # NOTE: the patch needs to happen in the *kernel process* executing the notebook.
    setup_code = f"""
from unittest.mock import patch
from breathe_design.device_flow_auth import device_auth
# Start a patcher that lasts for the entire notebook run.
__pytest_nb_patcher = patch.object(device_auth, "get_token", return_value={json.dumps(token_value)})
__pytest_nb_patcher.start()
"""
    nb.cells.insert(0, nbformat.v4.new_code_cell(setup_code))

    # Execute with nbclient; set working dir to the notebook's folder so relative paths work
    client = NotebookClient(
        nb,
        kernel_name="python3",
        timeout=1200,
        resources={"metadata": {"path": str(notebook_path.parent)}},
        allow_errors=False,  # raise on first error
    )

    # Run! If any cell errors, nbclient will raise and pytest will fail.
    client.execute()
