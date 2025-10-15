from __future__ import annotations

import ast
from pathlib import Path
from typing import Literal, Self, cast

from imandra.u.agents.code_logician.base import ModuleInfo
from inline_snapshot import snapshot
from pydantic import BaseModel, Field, model_validator

from ..tools.filesystem import Dir, FileSystem
from .base import Module, ModuleDep

NameAndDoc = tuple[str, str | None]
CodeElements = tuple[list[NameAndDoc], list[NameAndDoc], list[str], str | None]


class PythonModule(Module):
    """A Python module."""

    src_lang: Literal["python"] = "python"
    imports: list[AstImport | AstImportFrom]
    elements: CodeElements

    @classmethod
    def from_content(cls, relative_path: Path, content: str) -> Self:
        try:
            elements = _parse_code_elements(ast.parse(content))
        except Exception as e:
            print(f"Failed to parse code elements from {relative_path}: {e}")
            elements = ([], [], [], None)

        return cls(
            relative_path=relative_path,
            content=content,
            imports=parse_imports(content),
            elements=elements,
        )

    @model_validator(mode="after")
    def gen_name(self) -> Self:
        self.name = rel_path_to_python_module_name(self.relative_path)
        return self

    def to_CL_src_module_info(self) -> ModuleInfo:  # noqa: N802
        return ModuleInfo(
            name=self.name,
            relative_path=self.relative_path,
            content=self.content,
            src_lang=self.src_lang,
        )


def _parse_code_elements(tree: ast.Module) -> CodeElements:
    """Parse functions, classes, constants from a Python file

    Returns:
        functions (list[tuple[str, str | None]]): functions and their docstrings
        classes (list[tuple[str, str | None]]): classes and their docstrings
        constants (list[str]): constants
        docstring (str | None): file-level docstring
    """
    functions = []
    classes = []
    constants = []
    docstring = None

    # fmt: off
    def maybe_docstring(node):
        def maybe_head(x): return x[0] if len(x) > 0 else None
        def value_of_expr(x): return x.value if isinstance(x, ast.Expr) else None
        def value_of_const(x): return x.value if isinstance(x, ast.Constant) else None
        def str_val(x): return x if isinstance(x, str) else None
        return value_of_const(value_of_expr(maybe_head(node.body)))
    # fmt: on

    # Get module docstring
    docstring = maybe_docstring(tree)

    def name_and_docstring(node):
        return node.name, maybe_docstring(node)

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            node = cast(ast.FunctionDef | ast.AsyncFunctionDef, node)
            functions.append(name_and_docstring(node))
        elif isinstance(node, ast.ClassDef):
            classes.append(name_and_docstring(node))
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id.isupper():
                    constants.append(target.id)

    return functions, classes, constants, docstring


def rel_path_to_python_module_name(path: Path) -> str:
    """
    Example:
    - `basic.py` -> `basic`
    - `utils/helpers.py` -> `utils.helpers`
    - `advanced/geometry/shapes.py` -> `advanced.geometry.shapes`
    """
    parts = list(path.parts)
    parts = [p.removesuffix(".py") for p in parts]
    return ".".join(parts)


def build_py_dep_graph(
    fs: FileSystem,
) -> ModuleDep[PythonModule]:
    # Parse all Python modules
    py_modules: list[PythonModule] = []
    for node in fs.nodes:
        rel_path = node.relative_path
        if isinstance(node, Dir) or rel_path.suffix != ".py":
            continue

        # Create module name from relative path
        py_modules.append(PythonModule.from_content(rel_path, node.content))

    # Build adjacency list for dependencies
    adjacency_list: dict[str, set[str]] = {}

    for py_module in py_modules:
        adjacency_list[py_module.path_key] = set()

        for import_ast in py_module.imports:
            target_module = resolve_import(import_ast, py_module, py_modules)
            if target_module and target_module != py_module:
                adjacency_list[py_module.path_key].add(target_module.path_key)

    return ModuleDep.from_adjacency_list(py_modules, adjacency_list)


class AstImport(BaseModel):
    """Serializable ast.Import"""

    lineno: int = Field(description="Line number where import appears")
    col_offset: int = Field(description="Column offset where import appears")
    end_lineno: int | None = Field(None, description="Line number where import ends")
    end_col_offset: int | None = Field(
        None, description="Column offset where import ends"
    )
    aliases: list[str] = Field(description="Aliases used in import")

    @classmethod
    def from_ast(cls, node: ast.Import) -> Self:
        return cls(
            lineno=node.lineno,
            col_offset=node.col_offset,
            end_lineno=node.end_lineno,
            end_col_offset=node.end_col_offset,
            aliases=[alias.name for alias in node.names],
        )


class AstImportFrom(AstImport):
    """Serializable ast.ImportFrom"""

    module: str | None = Field(description="Module being imported from")
    level: int = Field(description="Level of import (0=absolute, 1+=relative)")

    @classmethod
    def from_ast(cls, node: ast.ImportFrom) -> Self:
        return cls(
            lineno=node.lineno,
            col_offset=node.col_offset,
            end_lineno=node.end_lineno,
            end_col_offset=node.end_col_offset,
            aliases=[alias.name for alias in node.names],
            module=node.module,
            level=node.level,
        )


def parse_imports(content: str) -> list[AstImport | AstImportFrom]:
    """Parse import statements from a Python file"""
    imports = []
    tree = ast.parse(content)

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.append(AstImport.from_ast(node))

        elif isinstance(node, ast.ImportFrom):
            imports.append(AstImportFrom.from_ast(node))
    return imports


def resolve_import(
    import_ast: AstImport | AstImportFrom,
    importing_module: PythonModule,
    all_modules: list[PythonModule],
) -> PythonModule | None:
    """Resolve an import statement to a target module."""

    if isinstance(import_ast, AstImportFrom):
        if import_ast.level == 0:
            if import_ast_module := import_ast.module:
                return find_module_by_name(import_ast_module, all_modules)
        elif import_ast.level > 0:
            return resolve_relative_import(import_ast, importing_module, all_modules)
    elif isinstance(import_ast, AstImport) and import_ast.aliases:
        target_name = import_ast.aliases[0].split(".")[0]  # Get root module name
        return find_module_by_name(target_name, all_modules)

    return None

def find_module_by_name(
    target_name: str,
    all_modules: list[PythonModule],
) -> PythonModule | None:
    """Find a module by name, trying different matching strategies."""

    # Try exact match first
    for module in all_modules:
        if module.name == target_name:
            return module

    # Try matching just the filename (stem)
    for module in all_modules:
        if module.relative_path.stem == target_name:
            return module

    # Try matching as root of dotted name
    for module in all_modules:
        module_name = cast(str, module.name)
        if module_name.split(".")[0] == target_name:
            return module

    return None

def resolve_relative_import(
    import_ast: AstImportFrom,
    importing_module: PythonModule,
    all_modules: list[PythonModule],
) -> PythonModule | None:
    """Handle relative imports like 'from .foo import bar'."""

    importing_dir = importing_module.relative_path.parent

    # Go up 'level-1' directories (level=1 means current dir)
    target_dir = importing_dir
    for _ in range(import_ast.level - 1):
        target_dir = target_dir.parent
        if str(target_dir) == ".":  # Reached root
            break

    # If module is specified, append it to target_dir
    if import_ast.module:
        target_path = target_dir / import_ast.module
    else:
        target_path = target_dir

    # Look for module with matching path
    for module in all_modules:
        if module.relative_path.with_suffix("") == target_path:
            return module

    return None


def test_parse_imports():
    content = """\
from basic import add, multiply, is_positive
from utils.helpers import max_of_three\
"""
    ast_imports = parse_imports(content)
    assert ast_imports == snapshot(
        [
            AstImportFrom(
                lineno=1,
                col_offset=0,
                end_lineno=1,
                end_col_offset=44,
                aliases=["add", "multiply", "is_positive"],
                module="basic",
                level=0,
            ),
            AstImportFrom(
                lineno=2,
                col_offset=0,
                end_lineno=2,
                end_col_offset=38,
                aliases=["max_of_three"],
                module="utils.helpers",
                level=0,
            ),
        ]
    )


def experiment():
    from tools.filesystem import FileSystem
    fs = FileSystem.from_disk(Path("data/code4"))
    
    py_dep = build_py_dep_graph(fs)
    
    for node in py_dep.nodes:
        print (node)
        print (f"imports: {node.imports}")
        print (f"relative_path: {node.relative_path}")
        print (f"")
        print (f"node.content: {node.content}")

    #print (py_dep.nodes)

    for e in py_dep.nx_graph.edges():
        print (e)

if __name__ == "__main__":
    #import pytest
    experiment()
    #pytest.main([__file__])
