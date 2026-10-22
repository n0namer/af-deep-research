from __future__ import annotations

import ast
import asyncio
import dataclasses
import importlib.util
import inspect
import sys
import pytest
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).resolve().parents[1]


def _load_module(path: Path, name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_async_extractor_contract_accepts_keyword_context():
    source = (ROOT / "reasoners/deep_research_ext/final_verifier.py").read_text()
    tree = ast.parse(source)
    function = next(
        node for node in tree.body
        if isinstance(node, ast.AsyncFunctionDef)
        and node.name == "extract_material_draft_claims"
    )
    names = [arg.arg for arg in function.args.kwonlyargs]
    assert {"document_package", "ai_call"}.issubset(names)
    assert not any(arg.arg == "_extractor" for arg in function.args.args)
    signature = inspect.signature(
        lambda *, document_package, ai_call, model=None, api_key=None: None
    )
    assert all(
        parameter.kind is inspect.Parameter.KEYWORD_ONLY
        for parameter in signature.parameters.values()
    )


def test_dataclass_loader_registers_module_before_exec():
    source = """
from dataclasses import dataclass
@dataclass
class Payload:
    value: int
"""
    namespace = {}
    module_name = "r30_dynamic_payload"
    spec = importlib.util.spec_from_loader(module_name, loader=None)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    exec(compile(source, "<dynamic>", "exec"), module.__dict__)
    assert dataclasses.is_dataclass(module.Payload)
    assert module.Payload(7).value == 7
    del sys.modules[module_name]


def test_package_relative_import_executes_inside_package():
    package_name = "r30_pkg"
    package = ModuleType(package_name)
    package.__path__ = [str(ROOT / "reasoners/deep_research_ext")]
    sys.modules[package_name] = package
    try:
        module = ModuleType(f"{package_name}.child")
        module.__package__ = package_name
        sibling = ModuleType(f"{package_name}.sibling")
        sibling.VALUE = 42
        sys.modules[sibling.__name__] = sibling
        exec("from .sibling import VALUE", module.__dict__)
        assert module.VALUE == 42
    finally:
        for name in list(sys.modules):
            if name == package_name or name.startswith(package_name + "."):
                sys.modules.pop(name, None)


def test_negative_async_extractor_rejects_positional_binding():
    async def extractor(*, document_package, ai_call):
        return document_package, ai_call

    try:
        asyncio.run(extractor({}, lambda: None))
    except TypeError as exc:
        assert "positional" in str(exc)
    else:
        raise AssertionError("invalid positional binding unexpectedly accepted")


def test_negative_dataclass_loader_without_sys_modules_is_rejected():
    module_name = "r30_missing_registration"
    spec = importlib.util.spec_from_loader(module_name, loader=None)
    module = importlib.util.module_from_spec(spec)
    with pytest.raises(Exception):
        exec(
            compile("@dataclasses.dataclass\nclass Payload:\n    value: int\n", "<dynamic>", "exec"),
            module.__dict__,
        )


def test_negative_relative_import_without_package_is_rejected():
    module = ModuleType("r30_no_package")
    with pytest.raises(ImportError):
        exec("from .sibling import VALUE", module.__dict__)
