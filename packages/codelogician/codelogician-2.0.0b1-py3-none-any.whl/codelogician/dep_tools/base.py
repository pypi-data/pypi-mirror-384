from __future__ import annotations

from enum import IntEnum
from pathlib import Path
from typing import ClassVar, Literal, Self

import networkx as nx
from pydantic import BaseModel, Field, model_validator

from ..tools.base import (
    DepGraph,
    NodeMixin,
    nx_graph_from_adjacency_list,
)
from ..tools.filesystem import Dir, File, FileSystem

class SymbolKind(IntEnum):
    """A symbol kind.
    Imported from multilspy.lsp_protocol_handler.lsp_types.SymbolKind.
    """

    File = 1
    Module = 2
    Namespace = 3
    Package = 4
    Class = 5
    Method = 6
    Property = 7
    Field = 8
    Constructor = 9
    Enum = 10
    Interface = 11
    Function = 12
    Variable = 13
    Constant = 14
    String = 15
    Number = 16
    Boolean = 17
    Array = 18
    Object = 19
    Key = 20
    Null = 21
    EnumMember = 22
    Struct = 23
    Event = 24
    Operator = 25
    TypeParameter = 26


Range = tuple[tuple[int, int], tuple[int, int]]


class Symbol(BaseModel, NodeMixin):
    """A mix of LSP's SymbolInformation and DocumentSymbol."""

    name: str
    relative_path: Path = Field()
    kind: SymbolKind
    range: Range | None = Field(
        None,
        description="The range of the symbol. None represents a file-level symbol.",
    )
    detail: str | None = Field(None)
    container_name: str | None = Field(None, alias="containerName")
    children: list[Symbol] = Field(default_factory=list)

    @property
    def path_key(self) -> str:
        return str(self.relative_path)

    def __repr__(self) -> str:
        return str(self.relative_path)


class Module(Symbol):
    """A module."""

    name: str | None = Field(
        None,
        description="The name of the module. Automatically generated from the relative "
        "path for Python and IML modules.",
    )
    kind: Literal[SymbolKind.Module] = Field(SymbolKind.Module)
    content: str
    src_lang: str

    def __hash__(self) -> int:
        return hash((self.relative_path, self.content))

    @model_validator(mode="after")
    def validate_path(self) -> Self:
        if self.src_lang == "python" and not self.relative_path.suffix == ".py":
            raise ValueError("Python module must have a .py extension")
        elif self.src_lang == "iml" and not self.relative_path.suffix == ".iml":
            raise ValueError("IML module must have a .iml extension")
        return self


class ModuleDep[T: Module](DepGraph[T]):
    FILE_EXTENSION_MAP: ClassVar[dict[str, str]] = {
        "python": ".py",
        "iml": ".iml",
    }

    def __init__(self, nx_graph: nx.DiGraph):
        # Check if all nodes have the same source language
        src_langs = {node.src_lang for node in nx_graph.nodes}
        if len(src_langs) != 1:
            raise ValueError(
                f"All nodes must have the same source language, but got {src_langs}"
            )
        # Check if the source language is supported
        src_lang = next(iter(src_langs))
        if src_lang not in self.FILE_EXTENSION_MAP:
            raise ValueError(
                f"Unsupported source language: {src_lang}. Supported languages: "
                f"{list(self.FILE_EXTENSION_MAP.keys())}"
            )

        self.src_lang = src_lang
        super().__init__(nx_graph)

    @classmethod
    def from_adjacency_list(
        cls,
        nodes: list[T],
        adjacency_list: dict[str, set[str]],
    ) -> Self:
        nx_graph = nx_graph_from_adjacency_list(
            nodes=nodes, adjacency_list=adjacency_list
        )
        return cls(nx_graph)

    def into_file_system(
        self,
        repo_path: Path,
        filter_empty: bool = True,
    ) -> FileSystem:
        nodes: list[Module] = self.nodes

        src_lang = self.src_lang
        file_extension = self.FILE_EXTENSION_MAP[src_lang]
        ignore_patterns = None

        files, dirs = [], []
        for node in nodes:
            rel_path = node.relative_path
            if filter_empty:
                if src_lang == "iml" and not node.body.strip():
                    continue
                elif src_lang == "python" and not node.content.strip():
                    continue  #

            files.append(
                File(
                    relative_path=rel_path,
                    content=node.content,
                )
            )
            for dir_path in rel_path.parents:
                dir = Dir(relative_path=dir_path)
                if dir not in dirs:
                    dirs.append(dir)

        return FileSystem.from_nodes(
            nodes=files + dirs,
            repo_path=repo_path,
            file_extensions=[file_extension],
            ignore_patterns=ignore_patterns,
        )