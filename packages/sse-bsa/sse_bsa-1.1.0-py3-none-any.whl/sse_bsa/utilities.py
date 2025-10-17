"""
Copyright (c) Cutleast
"""

import os
from io import BufferedReader, BytesIO
from pathlib import Path
from typing import TypeAlias

from virtual_glob import InMemoryPath
from virtual_glob import glob as vglob

Stream: TypeAlias = BufferedReader | BytesIO
"""
Type alias for `BufferedReader` and `BytesIO`.
"""


def create_folder_list(folder: Path) -> list[Path]:
    """
    Creates a list with all files
    with relative paths to `folder` and returns it.
    """

    files: list[Path] = []

    for root, _, _files in os.walk(folder):
        for f in _files:
            path = os.path.join(root, f)
            files.append(Path(path).relative_to(folder.parent))

    return files


def get_stream(data: BytesIO | BufferedReader | bytes) -> Stream:
    if isinstance(data, bytes):
        return BytesIO(data)

    return data


def read_data(data: Stream | bytes, size: int) -> bytes:
    """
    Returns `size` bytes from `data`.
    """

    if isinstance(data, bytes):
        return data[:size]
    else:
        return data.read(size)


def norm(path: str) -> str:
    """
    Normalizes a path.

    Args:
        path (str): Path to normalize.

    Returns:
        str: Normalized path.
    """

    return path.replace("\\", "/")


def glob(pattern: str, files: list[str], case_sensitive: bool = False) -> list[str]:
    """
    Glob function for a list of files as strings.

    Args:
        pattern (str): Glob pattern.
        files (list[str]): List of files.
        case_sensitive (bool, optional): Case sensitive. Defaults to False.

    Returns:
        list[str]: List of matching files.
    """

    file_map: dict[str, str]
    """
    Map of original file names and normalized file names.
    """

    if case_sensitive:
        file_map = {norm(file): file for file in files}
        pattern = norm(pattern)
    else:
        file_map = {norm(file).lower(): file for file in files}
        pattern = norm(pattern).lower()

    fs: InMemoryPath = InMemoryPath.from_list(list(file_map.keys()))
    matches: list[str] = [
        file_map[p.path] for p in vglob(fs, pattern) if p.path in file_map
    ]

    return matches
