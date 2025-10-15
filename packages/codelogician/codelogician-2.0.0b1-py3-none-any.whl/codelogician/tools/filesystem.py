#
#   Imandra Inc.
#
#   filesystem.py
#

from __future__ import annotations

import fnmatch
import networkx as nx

from functools import partial
from pathlib import Path

import structlog
from pydantic import BaseModel

from .base import DepGraph, NodeMixin, nx_graph_from_adjacency_list

logger = structlog.get_logger(__name__)

class File(BaseModel, NodeMixin):
  """File entry with content and relative path"""

  relative_path: Path
  content: str

  def __hash__(self) -> int:
    return hash(self.relative_path)

  @property
  def path_key(self) -> str:
    return str(self.relative_path)

  def __repr__(self) -> str:
    parts = self.relative_path.parts
    if parts == ():
      return "."
    return str(parts[-1])

class Dir(BaseModel, NodeMixin):
  """Directory entry with relative path"""
  relative_path: Path

  def __hash__(self) -> int:
    return hash(self.relative_path)

  @property
  def path_key(self) -> str:
    return str(self.relative_path)

  def __repr__(self) -> str:
    return str(self.relative_path)


FSEntry = File | Dir

class FileSystem(DepGraph[FSEntry]):
  """ """
  def __init__(
    self,
    nx_graph: nx.DiGraph,
    repo_path: Path,
    file_extensions: list[str] | None = None,
    ignore_patterns: list[str] | None = None,
  ):
    super().__init__(nx_graph)

    if not self.is_tree:
      raise ValueError("FileSystem must be a tree")

    self.repo_path = repo_path
    self.file_extensions = file_extensions
    self.ignore_patterns = ignore_patterns

  @staticmethod
  def from_disk(
      repo_path: Path,
      file_extensions: list[str] | None = None,
      respect_gitignore: bool = True,
    ) -> FileSystem:
      """Walk the file tree and return a FileSystem object

        Args:
            repo_path: The root path of the repository
            file_extensions: The file extensions to include in the file tree
            respect_gitignore: Whether to respect the gitignore file

        Returns:
            A FileSystem object with relative paths as nodes and edges indicating
            containment
      """

      if not (isinstance (repo_path, Path)):
         raise Exception (f"Attempting to read from disk but path is not a proper Path object: {repo_path}")

      if file_extensions is None:
        file_extensions = []
      else:
        file_extensions = [ext.lstrip(".") for ext in file_extensions]

      if respect_gitignore:
            ignore_patterns = load_gitignore(repo_path)
            ignore_predicate = partial(is_ignored, patterns=ignore_patterns)
      else:
        ignore_patterns = []

        def ignore_predicate(path: Path) -> bool:
            return False

      data: dict[FSEntry, set[FSEntry]] = {}

      # Convert repo_path to relative path for consistent handling
      repo_path = repo_path.resolve()

      # Walk through all files and directories
      for entry in repo_path.rglob("*"):
            # Get relative path from repo root
            rel_path = entry.relative_to(repo_path)

            # Skip if ignored
            if ignore_predicate(rel_path):
                logger.debug("Ignoring entry by gitignore", entry=rel_path)
                continue

            # Filter by file extensions if specified
            if (
                file_extensions
                and entry.is_file()
                and not any(entry.suffix == f".{ext}" for ext in file_extensions)
            ):
                logger.debug("Ignoring entry by file extension", entry=rel_path)
                continue

            # Create FSEntry object with content
            if entry.is_file():
                try:
                    content = entry.read_text(encoding="utf-8")
                    fs_entry = File(relative_path=rel_path, content=content)
                except Exception as e:
                    logger.warning(
                        "Failed to read file content", entry=rel_path, error=e
                    )
                    continue
            else:
                fs_entry = Dir(relative_path=rel_path)

            # Add entry to data structure
            if fs_entry not in data:
                data[fs_entry] = set()

            # Add parent-child relationship
            if rel_path != Path():  # Skip root
                parent_path = rel_path.parent
                parent_fs_entry = Dir(relative_path=parent_path)

                if parent_fs_entry not in data:
                    data[parent_fs_entry] = set()
                data[parent_fs_entry].add(fs_entry)

        # Unpack
      nodes = list(data.keys())
      adj_list = {
            node.path_key: {tgt.path_key for tgt in tgts} for node, tgts in data.items()
      }

      nx_graph = nx_graph_from_adjacency_list(nodes=nodes, adjacency_list=adj_list)

      return FileSystem (
        nx_graph=nx_graph,
        repo_path=repo_path,
        file_extensions=file_extensions,
        ignore_patterns=ignore_patterns,
      )


def load_gitignore(repo_path: Path) -> list[str]:
    """Load gitignore patterns from .gitignore file"""
    patterns = []
    gitignore_file = repo_path / ".gitignore"

    # Default patterns to always ignore
    default_patterns = [
        ".venv/",
        "venv/",
        "__pycache__/",
        "*.pyc",
        "*.pyo",
        "*.pyd",
        ".Python",
        "build/",
        "develop-eggs/",
        "dist/",
        "downloads/",
        "eggs/",
        ".eggs/",
        "lib/",
        "lib64/",
        "parts/",
        "sdist/",
        "var/",
        "wheels/",
        "*.egg-info/",
        ".git/",
        ".*",
    ]
    patterns.extend(default_patterns)

    if gitignore_file.exists():
      try:
        with gitignore_file.open("r", encoding="utf-8") as f:
          for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
              patterns.append(line)
      except Exception:
        pass  # Ignore errors reading gitignore

    return patterns


def is_ignored(path: Path, patterns: list[str]) -> bool:
  """Check if a path matches any gitignore pattern"""
  path_str = str(path)
  path_parts = path.parts

  def matches(pattern):
    # Remove leading/trailing slashes for consistent matching
    pattern = pattern.strip("/")

    # Check if any part of the path matches the pattern
    # or if individual path parts
    return (fnmatch.fnmatch(path_str, pattern)
            or fnmatch.fnmatch(path_str, f"*/{pattern}")
            or fnmatch.fnmatch(path_str, f"{pattern}/*")
            or any(fnmatch.fnmatch(p, pattern) for p in path_parts))

  return any(map(matches, patterns))

def experiment():

  fs = FileSystem.from_disk(Path("data/code4"))

  from code_logician.dep_graph.symbol_dep.python import build_py_dep_graph
  py_dep = build_py_dep_graph(fs)
  print(py_dep.edges_repr())
# two.py --> one.py

  print (fs.edges_repr())
  print (fs.graph_repr())

if __name__ == "__main__":
  experiment()
