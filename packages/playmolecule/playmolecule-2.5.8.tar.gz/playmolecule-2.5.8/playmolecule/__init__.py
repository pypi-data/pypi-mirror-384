# (c) 2015-2023 Acellera Ltd http://www.acellera.com
# All Rights Reserved
# Distributed under HTMD Software License Agreement
# No redistribution in whole or part
#
import os
import logging.config
from playmolecule.apps import _set_root, JobStatus, ExecutableDirectory, slurm_mps
from playmolecule._version import get_versions
from playmolecule._update import update_apps

__version__ = get_versions()["version"]

dirname = os.path.dirname(__file__)

try:
    logging.config.fileConfig(
        os.path.join(dirname, "logging.ini"), disable_existing_loggers=False
    )
except Exception:
    print("playmolecule: Logging setup failed")


logger = logging.getLogger(__name__)
PM_APP_ROOT = os.environ.get("PM_APP_ROOT", None)
PM_SKIP_SETUP = os.environ.get("PM_SKIP_SETUP", False)
if not PM_SKIP_SETUP and PM_APP_ROOT is None:
    raise RuntimeError(
        "Could not find environment variable PM_APP_ROOT. Please set the variable to set the path to the app root."
    )

if PM_APP_ROOT is not None and not PM_SKIP_SETUP:
    # Necessary for PMWS URL but also good for paths
    while PM_APP_ROOT[-1] == "/":
        PM_APP_ROOT = PM_APP_ROOT[:-1]
    _set_root(PM_APP_ROOT)


def describe_apps():
    from playmolecule.apps import _function_dict

    sorted_keys = sorted(_function_dict.keys())
    for func_path in sorted_keys:
        func = _function_dict[func_path]
        if "name" in func.__manifest__:
            name = func.__manifest__["name"]
        else:
            name = func_path.split(".")[-1]
        print(name, func_path)
        desc = func.__doc__.strip().split("\n")[0]
        print(f"    {desc}")


protocols = None
# Add the acellera-protocols folder as a submodule
if not PM_SKIP_SETUP:
    root_dir = PM_APP_ROOT
    prot_dir = os.path.join(root_dir, "acellera-protocols")

    if os.path.exists(root_dir) and os.path.exists(prot_dir):
        from glob import glob
        import importlib
        import sys

        sys.path.insert(0, prot_dir)

        for file in glob(os.path.join(prot_dir, "**", "*.py"), recursive=True):
            if file.endswith("__init__.py"):
                continue
            rel_path = os.path.relpath(file[:-3], prot_dir)
            mod_name = rel_path.replace(os.path.sep, ".")
            parts = mod_name.split(".")

            for i in range(len(parts)):
                submod = ".".join(parts[: i + 1])
                sys.modules[__name__ + "." + submod] = importlib.import_module(
                    submod, package=__name__
                )

            # Append tutorials to the docs of the protocol
            dirname = os.path.dirname(file)
            pieces = rel_path.split(os.path.sep)
            # Check if the loaded module is the actual protocol file
            if len(pieces) == 4 and pieces[1] == pieces[3]:
                # Check if there are files/tutorials
                nb_tuts = glob(os.path.join(dirname, "files", "tutorials", "*.ipynb"))
                if len(nb_tuts):
                    # Modify the docs of the protocol
                    main_func = getattr(sys.modules[__name__ + "." + submod], pieces[1])
                    main_func.__doc__ = (
                        main_func.__doc__
                        + "\n\nNotes\n-----\nTutorials are available for this protocol:\n\n"
                        + "\n".join([f"    - {t}" for t in nb_tuts])
                    )

        protocols = sys.modules[__name__ + ".protocols"]
