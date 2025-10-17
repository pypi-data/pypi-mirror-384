"""
rexpand-pyutils-file - Python utilities for file system operations.

This package provides a comprehensive set of utilities for file system operations,
including reading, writing, finding, and downloading files.
"""

from rexpand_pyutils_file.file_system import (
    FileSystem,
    read_file,
    write_file,
    download_file,
    unzip_file,
    find_files,
    find_folders,
    refine_path,
)

__version__ = "0.0.7"

__all__ = [
    "FileSystem",
    "read_file",
    "write_file",
    "download_file",
    "unzip_file",
    "find_files",
    "find_folders",
    "refine_path",
]
