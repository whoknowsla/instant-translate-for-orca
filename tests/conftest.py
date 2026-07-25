import os
import pathlib
import site
import sys

# Keep all Orca extension settings in process memory. Tests must never write to
# the developer's real dconf database.
os.environ["GSETTINGS_BACKEND"] = "memory"

# uv runs checks in an isolated project environment, while Orca and PyGObject
# are installed by the Linux distribution. Expose the base system Python's
# site-packages without allowing those packages to override uv-managed tools.
if sys.prefix != sys.base_prefix:
    for system_site_packages in site.getsitepackages([sys.base_prefix]):
        if system_site_packages not in sys.path:
            sys.path.append(system_site_packages)

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
