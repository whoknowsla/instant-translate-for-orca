import os
import pathlib
import sys

# Keep all Orca extension settings in process memory. Tests must never write to
# the developer's real dconf database.
os.environ["GSETTINGS_BACKEND"] = "memory"

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

# instant_translate/__init__.py imports orca.extension, which cannot be
# imported standalone -- it needs orca.script_manager (or plain `import
# orca`) pulled in first to resolve a circular import inside the orca
# package. Importing it here, before any test module imports anything from
# instant_translate, resolves it once for the whole test session.
import orca.script_manager  # noqa: F401


def clear_extension_settings(extension) -> None:
    for key in tuple(extension.settings._get_local_settings()):
        extension.settings.reset(key)
