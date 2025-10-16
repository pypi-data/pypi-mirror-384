"""
This script is run by mkdocs to insert variables into the mkdocs environment
that can then be accessed inside the Markdown documents
e.g.
{{ __version__ }}
"""

import os

_this_file_dir = os.path.dirname(os.path.abspath(__file__))


def define_env(env):
    # extract the __version__ number of the module
    # don't try and import it because we can't be sure what context this will be run in
    breathe_design_init_file_path = os.path.join(
        _this_file_dir, "breathe_design", "__init__.py"
    )
    with open(breathe_design_init_file_path, "r") as f:
        lines = f.readlines()
    version = None
    for line in lines:
        if "__version__" not in line:
            continue
        parts = line.split(" = ")
        version = parts[1].strip().strip('"')
    print(version)
    env.variables["breathe_design_version"] = version
