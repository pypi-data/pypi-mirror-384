"""
FileSystem module for rexpand-pyutils-file.

This module provides the FileSystem class for file system operations.
"""

import gzip
import logging
from os.path import isfile

from rexpand_pyutils_file.utils import get_or_create_folder_path
from rexpand_pyutils_file.downloader import download_file as static_download_file
from rexpand_pyutils_file.finder import (
    IGNORED_FILE_SET,
    get_file_paths,
    get_folder_paths,
    refine_path as static_refine_path,
)
from rexpand_pyutils_file.reader import (
    DEFAULT_ENCODING,
    DEFAULT_VERBOSE,
    read_text,
    read_csv,
    read_excel,
    read_html,
    read_json,
    read_npy,
    read_npz,
)
from rexpand_pyutils_file.writer import (
    DEFAULT_OVERWRITE,
    DEFAULT_EXCEL_SHEET_NAME,
    write_csv,
    write_excel,
    write_html,
    write_json,
    write_text,
    write_npy,
    write_npz,
)


class FileSystem:
    """
    A class for file system operations.

    This class provides methods for reading, writing, finding, and downloading files.
    It also provides methods for unzipping files and refining paths.
    """

    def __init__(self, path=None, verbose=DEFAULT_VERBOSE, encoding=DEFAULT_ENCODING):
        """
        Initialize the FileSystem class.

        Args:
            path (str, optional): The default path to use for operations. Defaults to None.
            verbose (bool, optional): Whether to print verbose output. Defaults to DEFAULT_VERBOSE.
            encoding (str, optional): The encoding to use for file operations. Defaults to DEFAULT_ENCODING.
        """
        self.path = path
        self.verbose = verbose
        self.encoding = encoding

    def __get_path(self, path):
        """
        Get the path to use for operations.

        Args:
            path (str, optional): The path to use. If None, use the default path.

        Returns:
            str: The path to use for operations.

        Raises:
            Exception: If no path is specified.
        """
        path = path if path is not None else self.path

        if not path:
            raise Exception("Path must be specified")

        return path

    def read(
        self,
        path=None,
        verbose=None,
        encoding=None,
        excel_sheet_name=None,
    ):
        """
        Read a file.

        Args:
            path (str, optional): The path to the file. If None, use the default path.
            verbose (bool, optional): Whether to print verbose output. If None, use the default verbose setting.
            encoding (str, optional): The encoding to use. If None, use the default encoding.
            excel_sheet_name (str, optional): The name of the sheet to read from an Excel file. If None, read the first sheet.

        Returns:
            The contents of the file.

        Raises:
            Exception: If the file type is not supported.
        """
        path = self.__get_path(path)
        verbose = verbose if verbose is not None else self.verbose
        encoding = encoding if encoding is not None else self.encoding

        if isfile(path):
            if path[-5:] == ".json":
                return read_json(file_path=path, verbose=verbose, encoding=encoding)
            elif path[-5:] == ".html":
                return read_html(file_path=path, verbose=verbose, encoding=encoding)
            elif path[-4:] == ".txt" or path[-4:] == ".log" or path[-3:] == ".md" or path[-4:] == ".mmd":
                return read_text(file_path=path, verbose=verbose, encoding=encoding)
            elif path[-4:] == ".csv":
                return read_csv(file_path=path, verbose=verbose, encoding=encoding)
            elif path[-5:] == ".xlsx":
                return read_excel(
                    file_path=path, sheet_name=excel_sheet_name, verbose=verbose
                )
            elif path[-4:] == ".npy":
                return read_npy(file_path=path, verbose=verbose)
            elif path[-4:] == ".npz":
                return read_npz(file_path=path, verbose=verbose)
            else:
                raise Exception(f"Unsupported file type for {path}")
        else:
            if verbose:
                logging.warning(f"File not found: {path}")
            return None

    def write(
        self,
        data,
        path=None,
        verbose=None,
        csv_and_excel_overwrite=DEFAULT_OVERWRITE,
        encoding=None,
        csv_fieldnames=None,
        excel_sheet_name=DEFAULT_EXCEL_SHEET_NAME,
        excel_enable_str_conversion=False,
    ):
        """
        Write data to a file.

        Args:
            data: The data to write.
            path (str, optional): The path to the file. If None, use the default path.
            verbose (bool, optional): Whether to print verbose output. If None, use the default verbose setting.
            csv_and_excel_overwrite (bool, optional): Whether to overwrite existing CSV or Excel files. Defaults to DEFAULT_OVERWRITE.
            encoding (str, optional): The encoding to use. If None, use the default encoding.
            csv_fieldnames (list, optional): The fieldnames to use for CSV files. If None, use the keys from the data.
            excel_sheet_name (str, optional): The name of the sheet to write to an Excel file. Defaults to DEFAULT_EXCEL_SHEET_NAME.
            excel_enable_str_conversion (bool, optional): Whether to enable string conversion for Excel files. Defaults to False.

        Returns:
            None

        Raises:
            Exception: If the file type is not supported.
        """
        path = self.__get_path(path)
        verbose = verbose if verbose is not None else self.verbose
        encoding = encoding if encoding is not None else self.encoding

        get_or_create_folder_path(path)

        if path[-5:] == ".json":
            return write_json(
                file_path=path, data=data, verbose=verbose, encoding=encoding
            )
        elif path[-5:] == ".html":
            return write_html(
                file_path=path, data=data, verbose=verbose, encoding=encoding
            )
        elif path[-4:] == ".txt" or path[-4:] == ".log" or path[-3:] == ".md" or path[-4:] == ".mmd":
            return write_text(
                file_path=path, data=data, verbose=verbose, encoding=encoding
            )
        elif path[-4:] == ".csv":
            return write_csv(
                file_path=path,
                data=data,
                fieldnames=csv_fieldnames,
                verbose=verbose,
                overwrite=csv_and_excel_overwrite,
                encoding=encoding,
            )
        elif path[-5:] == ".xlsx":
            return write_excel(
                file_path=path,
                data=data,
                sheet_name=excel_sheet_name,
                verbose=verbose,
                overwrite=csv_and_excel_overwrite,
                enable_str_conversion=excel_enable_str_conversion,
            )
        elif path[-4:] == ".npy":
            return write_npy(file_path=path, data=data, verbose=verbose)
        elif path[-4:] == ".npz":
            return write_npz(file_path=path, data=data, verbose=verbose)
        else:
            raise Exception(f"Unsupported file type for {path}")

    def unzip(self, path=None, output_path=None, verbose=None):
        """
        Unzip a gzip file.

        Args:
            path (str, optional): The path to the gzip file. If None, use the default path.
            output_path (str, optional): The path to write the unzipped data to. If None, return the unzipped data.
            verbose (bool, optional): Whether to print verbose output. If None, use the default verbose setting.

        Returns:
            The unzipped data if output_path is None, otherwise None.

        Raises:
            Exception: If the file type is not supported.
        """
        path = self.__get_path(path)
        verbose = verbose if verbose is not None else self.verbose

        if not isfile(path):
            if verbose:
                logging.warning(f"File not found: {path}")
            return None

        get_or_create_folder_path(path)

        if path[-3:] == ".gz":
            with gzip.open(path, "rb") as gz_file:
                data = gz_file.read()

                if output_path:
                    with open(output_path, "wb") as out_file:
                        out_file.write(data)

                    if verbose:
                        logging.info(
                            f"Unzipped data from {path} and wrote data to {output_path}"
                        )
                else:
                    if verbose:
                        logging.info(f"Unzipped data from {path} ")

                return data
        else:
            raise Exception(f"Unsupported file type for {path}")

    def download(self, url, file_path_without_extension=None, verbose=None):
        """
        Download a file from a URL.

        Args:
            url (str): The URL to download from.
            file_path_without_extension (str, optional): The path to save the file to, without the extension. If None, use the default path.
            verbose (bool, optional): Whether to print verbose output. If None, use the default verbose setting.

        Returns:
            The path to the downloaded file.
        """
        path = self.__get_path(file_path_without_extension)
        verbose = verbose if verbose is not None else self.verbose

        get_or_create_folder_path(path)

        return static_download_file(
            url=url, file_path_without_extension=path, verbose=verbose
        )

    def find_files(
        self,
        path=None,
        ignored_file_set=IGNORED_FILE_SET,
        file_suffix=None,
        recursive=False,
    ):
        """
        Find files in a directory.

        Args:
            path (str, optional): The path to the directory. If None, use the default path.
            ignored_file_set (set, optional): A set of file names to ignore. Defaults to IGNORED_FILE_SET.
            file_suffix (str, optional): A suffix to filter files by. If None, return all files.
            recursive (bool, optional): Whether to search recursively. Defaults to False.

        Returns:
            A list of file paths.
        """
        path = path if path is not None else self.path
        file_paths = get_file_paths(path, ignored_file_set, recursive)
        if file_suffix:
            if file_suffix[0] != ".":
                file_suffix = "." + file_suffix

            return [
                file_path
                for file_path in file_paths
                if file_path[-len(file_suffix) :] == file_suffix
            ]

        return file_paths

    def find_folders(self, path=None, ignored_folder_set=set(), recursive=False):
        """
        Find folders in a directory.

        Args:
            path (str, optional): The path to the directory. If None, use the default path.
            ignored_folder_set (set, optional): A set of folder names to ignore. Defaults to an empty set.
            recursive (bool, optional): Whether to search recursively. Defaults to False.

        Returns:
            A list of folder paths.
        """
        path = path if path is not None else self.path
        return get_folder_paths(path, ignored_folder_set, recursive)

    def refine_path(self, path=None):
        """
        Refine a path.

        Args:
            path (str, optional): The path to refine. If None, use the default path.

        Returns:
            The refined path.
        """
        path = path if path is not None else self.path
        return static_refine_path(path)


# Convenience functions that use the FileSystem class
def read_file(path, verbose=None, encoding=None, excel_sheet_name=None):
    """
    Read a file.

    Args:
        path (str): The path to the file.
        verbose (bool, optional): Whether to print verbose output. Defaults to None.
        encoding (str, optional): The encoding to use. Defaults to None.
        excel_sheet_name (str, optional): The name of the sheet to read from an Excel file. If None, read the first sheet.

    Returns:
        The contents of the file.
    """
    return FileSystem().read(
        path=path, verbose=verbose, encoding=encoding, excel_sheet_name=excel_sheet_name
    )


def write_file(
    path,
    data,
    verbose=None,
    encoding=None,
    csv_and_excel_overwrite=DEFAULT_OVERWRITE,
    csv_fieldnames=None,
    excel_sheet_name=DEFAULT_EXCEL_SHEET_NAME,
    excel_enable_str_conversion=False,
):
    """
    Write data to a file.

    Args:
        path (str): The path to the file.
        data: The data to write.
        verbose (bool, optional): Whether to print verbose output. Defaults to None.
        encoding (str, optional): The encoding to use. Defaults to None.
        csv_and_excel_overwrite (bool, optional): Whether to overwrite existing CSV or Excel files. Defaults to DEFAULT_OVERWRITE.
        csv_fieldnames (list, optional): The fieldnames to use for CSV files. If None, use the keys from the data.
        excel_sheet_name (str, optional): The name of the sheet to write to an Excel file. Defaults to DEFAULT_EXCEL_SHEET_NAME.
        excel_enable_str_conversion (bool, optional): Whether to enable string conversion for Excel files. Defaults to False.

    Returns:
        None
    """
    return FileSystem().write(
        data=data,
        path=path,
        verbose=verbose,
        csv_and_excel_overwrite=csv_and_excel_overwrite,
        encoding=encoding,
        csv_fieldnames=csv_fieldnames,
        excel_sheet_name=excel_sheet_name,
        excel_enable_str_conversion=excel_enable_str_conversion,
    )


def download_file(url, file_path_without_extension, verbose=None):
    """
    Download a file from a URL.

    Args:
        url (str): The URL to download from.
        file_path_without_extension (str): The path to save the file to, without the extension.
        verbose (bool, optional): Whether to print verbose output. Defaults to None.

    Returns:
        The path to the downloaded file.
    """
    return FileSystem().download(
        url=url,
        file_path_without_extension=file_path_without_extension,
        verbose=verbose,
    )


def unzip_file(path, output_path=None, verbose=None):
    """
    Unzip a gzip file.

    Args:
        path (str): The path to the gzip file.
        output_path (str, optional): The path to write the unzipped data to. If None, return the unzipped data.
        verbose (bool, optional): Whether to print verbose output. Defaults to None.

    Returns:
        The unzipped data if output_path is None, otherwise None.
    """
    return FileSystem().unzip(path=path, output_path=output_path, verbose=verbose)


def find_files(
    path, ignored_file_set=IGNORED_FILE_SET, file_suffix=None, recursive=False
):
    """
    Find files in a directory.

    Args:
        path (str): The path to the directory.
        ignored_file_set (set, optional): A set of file names to ignore. Defaults to IGNORED_FILE_SET.
        file_suffix (str, optional): A suffix to filter files by. If None, return all files.
        recursive (bool, optional): Whether to search recursively. Defaults to False.

    Returns:
        A list of file paths.
    """
    return FileSystem().find_files(
        path=path,
        ignored_file_set=ignored_file_set,
        file_suffix=file_suffix,
        recursive=recursive,
    )


def find_folders(path, ignored_folder_set=set(), recursive=False):
    """
    Find folders in a directory.

    Args:
        path (str): The path to the directory.
        ignored_folder_set (set, optional): A set of folder names to ignore. Defaults to an empty set.
        recursive (bool, optional): Whether to search recursively. Defaults to False.

    Returns:
        A list of folder paths.
    """
    return FileSystem().find_folders(
        path=path, ignored_folder_set=ignored_folder_set, recursive=recursive
    )


def refine_path(path):
    """
    Refine a path.

    Args:
        path (str): The path to refine.

    Returns:
        The refined path.
    """
    return FileSystem().refine_path(path=path)
