import importlib.util
import pathlib
import sys

from orca.extension import Extension
from orca.extension_loader import ExtensionLoader


def _package_dir() -> pathlib.Path:
    return pathlib.Path(__file__).parents[1] / "instant_translate"


def test_package_exposes_metadata_to_orcas_non_executing_scanner():
    metadata = ExtensionLoader.get_metadata(str(_package_dir()))

    assert metadata.class_name == "InstantTranslate"
    assert metadata.group_label == "Instant Translate"
    assert metadata.version == "1.0"


def test_package_loads_under_orca_user_extension_namespace():
    """Reproduce Orca's package-loading namespace exactly."""

    package_dir = _package_dir()
    module_name = "orca_user_extension.instant_translate"
    namespace = "orca_user_extension"
    original_modules = {
        name: module
        for name, module in sys.modules.items()
        if name == namespace or name.startswith(f"{namespace}.")
    }

    for name in original_modules:
        sys.modules.pop(name, None)

    try:
        spec = importlib.util.spec_from_file_location(
            module_name,
            package_dir / "__init__.py",
            submodule_search_locations=[str(package_dir)],
        )
        assert spec is not None
        assert spec.loader is not None

        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)

        assert issubclass(module.InstantTranslate, Extension)
    finally:
        for name in list(sys.modules):
            if name == namespace or name.startswith(f"{namespace}."):
                sys.modules.pop(name, None)
        sys.modules.update(original_modules)
