"""Minimal sideload helper with typed sideload interface."""

from __future__ import annotations

import importlib.util
import inspect
from os import PathLike, fspath
from pathlib import Path
from types import ModuleType
from typing import TYPE_CHECKING, Protocol, cast

if TYPE_CHECKING:
    from importlib.machinery import ModuleSpec


StrPath = str | PathLike[str]


# Legacy-compatible entry point
def _resolve_module_file(base_path: StrPath, module: str) -> str:
    path_str = fspath(base_path)
    if not path_str:
        message = "base_path must be a non-empty string"
        raise ValueError(message)

    base_dir = Path(path_str)
    if not base_dir.exists():
        message = f"base_path does not exist: {base_dir}"
        raise FileNotFoundError(message)

    module_path = Path(module)
    if module_path.is_absolute() and module_path.is_file():
        return module_path.as_posix()

    candidates: list[Path] = []
    if module.endswith(".py"):
        candidates.append(base_dir / module)
    else:
        dotted_parts = module.split(".")
        if len(dotted_parts) > 1:
            *pkg_parts, mod_part = dotted_parts
            candidates.append(base_dir.joinpath(*pkg_parts, f"{mod_part}.py"))
        candidates.append(base_dir / f"{module}.py")
        candidates.append(base_dir / module / "__init__.py")

    for candidate in candidates:
        if candidate.is_file():
            return candidate.as_posix()

    message = (
        f"Cannot resolve module file for module={module} under base_path={base_dir}"
    )
    raise ImportError(message)


def _create_spec(module_file: str) -> ModuleSpec:
    spec = importlib.util.spec_from_file_location(
        f"sideload_{abs(hash(module_file))}",
        module_file,
    )
    if spec is None or spec.loader is None:
        message = f"Failed to create module spec for {module_file}"
        raise ImportError(message)
    return spec


def _load_module(base_path: StrPath, module: str) -> ModuleType:
    module_file = _resolve_module_file(base_path, module)
    spec = _create_spec(module_file)
    module_obj = importlib.util.module_from_spec(spec)
    loader = spec.loader
    if loader is None:
        message = f"Loader missing for module spec {spec.name}"
        raise ImportError(message)
    loader.exec_module(module_obj)
    return module_obj


def _get_attribute(module_obj: ModuleType, attr_name: str) -> object:
    if not hasattr(module_obj, attr_name):
        module_file_raw = cast("object | None", getattr(module_obj, "__file__", None))
        if isinstance(module_file_raw, str):
            module_file = module_file_raw
        elif module_file_raw is None:
            module_file = "<unknown>"
        else:
            module_file = str(module_file_raw)
        message = (
            f"{ModuleType.__name__} loaded from "
            f"{module_file} has no attribute {attr_name!r}"
        )
        raise AttributeError(message)

    attr = cast("object", getattr(module_obj, attr_name))
    if inspect.isclass(attr):
        attr_type = cast("type[object]", attr)
        return attr_type()
    return attr


class ModuleLoader(Protocol):
    def load_module(self, base_path: StrPath, module: str) -> ModuleType: ...

    def get_attribute(self, module_obj: ModuleType, attr_name: str) -> object: ...


class DefaultModuleLoader:
    def load_module(self, base_path: StrPath, module: str) -> ModuleType:
        return _load_module(base_path, module)

    def get_attribute(self, module_obj: ModuleType, attr_name: str) -> object:
        return _get_attribute(module_obj, attr_name)


class PyModuleSideload:
    """Utility class that sideloads Python modules safely."""

    def __init__(self, module_loader: ModuleLoader | None = None) -> None:
        self._module_loader: ModuleLoader = module_loader or DefaultModuleLoader()

    def run(
        self, base_path: StrPath, module: str, obj: str | None = None
    ) -> ModuleType | object:
        module_obj = self._module_loader.load_module(base_path, module)
        if obj is None:
            return module_obj
        return self._module_loader.get_attribute(module_obj, obj)


class ModuleSideloadRunner(PyModuleSideload):
    def run(
        self, base_path: StrPath, module: str, obj: str | None = None
    ) -> ModuleType | object:
        """Load a module file under base_path and return module or attribute.

        base_path: directory containing modules or packages
        module: a filename (foo.py), a dotted name (pkg.mod) or a module name
        obj: optional attribute name to return from the module
        """
        return super().run(base_path, module, obj)


# Packaging-friendly aliases
x_cls_make_py_mod_sideload_x = ModuleSideloadRunner
xclsmakepymodsideloadx = ModuleSideloadRunner

__all__ = [
    "ModuleSideloadRunner",
    "PyModuleSideload",
    "x_cls_make_py_mod_sideload_x",
    "xclsmakepymodsideloadx",
]
