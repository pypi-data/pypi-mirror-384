import os
import csv
import json
import logging
import pandas as pd
import numpy as np
from typing import Optional, Dict

DEFAULT_ENCODING = "utf-8"
DEFAULT_VERBOSE = True

# Can be 'ignore', 'replace', or 'backslashreplace'
DEFAULT_READING_ERROR_HANDLING = "backslashreplace"


def read_json(
    file_path: str,
    verbose=DEFAULT_VERBOSE,
    encoding=DEFAULT_ENCODING,
    json_load_extra_args={},
):
    data = None

    if os.path.isfile(file_path):
        with open(
            file_path, encoding=encoding, errors=DEFAULT_READING_ERROR_HANDLING
        ) as jsonFile:
            data = json.load(jsonFile, **json_load_extra_args)

            if verbose:
                logging.info(f"Read JSON data from {file_path}")
    else:
        if verbose:
            logging.warning(f"File not found: {file_path}")

    return data


def read_html(file_path: str, verbose=DEFAULT_VERBOSE, encoding=DEFAULT_ENCODING):
    data = None

    if os.path.isfile(file_path):
        with open(
            file_path, encoding=encoding, errors=DEFAULT_READING_ERROR_HANDLING
        ) as file:
            data = "".join(file.readlines())

        if verbose:
            logging.info(f"Read HTML data from {file_path}")
    else:
        if verbose:
            logging.warning(f"File not found: {file_path}")

    return data


def read_text(file_path: str, verbose=DEFAULT_VERBOSE, encoding=DEFAULT_ENCODING):
    data = None

    if os.path.isfile(file_path):
        with open(
            file_path, encoding=encoding, errors=DEFAULT_READING_ERROR_HANDLING
        ) as file:
            data = "".join(file.readlines())

        if verbose:
            logging.info(f"Read TXT data from {file_path}")
    else:
        if verbose:
            logging.warning(f"File not found: {file_path}")

    return data


def read_csv(
    file_path: str,
    delimiter: str = ",",
    quotechar: str = '"',
    escapechar: str | None = None,
    doublequote: bool = True,
    skipinitialspace: bool = False,
    lineterminator: str = "\r\n",
    quoting=0,
    strict: bool = False,
    verbose=DEFAULT_VERBOSE,
    encoding=DEFAULT_ENCODING,
    filter_na: bool = False,
    replace_na: bool = True,
    strip_bom: bool = True,
) -> list[dict] | None:
    data = None

    if os.path.isfile(file_path):
        with open(
            file_path,
            newline="",
            encoding=encoding,
            errors=DEFAULT_READING_ERROR_HANDLING,
        ) as csvfile:
            spamreader = csv.DictReader(
                csvfile,
                delimiter=delimiter,
                quotechar=quotechar,
                escapechar=escapechar,
                doublequote=doublequote,
                skipinitialspace=skipinitialspace,
                lineterminator=lineterminator,
                quoting=quoting,
                strict=strict,
            )

            # Handle BOM character in column names if needed
            if strip_bom:
                # Get the fieldnames and strip BOM from them
                fieldnames = spamreader.fieldnames
                if fieldnames and any(name.startswith("\ufeff") for name in fieldnames):
                    # Create a mapping of original names to cleaned names
                    name_mapping = {
                        name: name.replace("\ufeff", "") for name in fieldnames
                    }
                    # Create a new DictReader with cleaned fieldnames
                    spamreader = csv.DictReader(
                        csvfile,
                        fieldnames=[name_mapping[name] for name in fieldnames],
                        delimiter=delimiter,
                        quotechar=quotechar,
                        escapechar=escapechar,
                        doublequote=doublequote,
                        skipinitialspace=skipinitialspace,
                        lineterminator=lineterminator,
                        quoting=quoting,
                        strict=strict,
                    )
                    # Reset file pointer to beginning
                    csvfile.seek(0)
                    # Skip header row
                    next(spamreader)

            data = [row for row in spamreader]

            if filter_na:
                # Filter out rows with NA values
                filtered_data = []
                for row in data:
                    # Check if any value in the row is None, empty string, or 'NA'
                    if not any(
                        val is None or val == "" or val.upper() == "NA"
                        for val in row.values()
                    ):
                        filtered_data.append(row)
                data = filtered_data
            elif replace_na:
                # Replace NA values with empty strings
                for row in data:
                    for key in row:
                        if (
                            row[key] is None
                            or row[key] == ""
                            or str(row[key]).upper() == "NA"
                        ):
                            row[key] = ""

            if verbose:
                logging.info(f"Read CSV data from {file_path} with {len(data)} rows")
    else:
        if verbose:
            logging.warning(f"File not found: {file_path}")

    return data


def read_excel(
    file_path: str,
    sheet_name: str | None = None,
    filter_na: bool = False,
    replace_na: bool = True,
    verbose=DEFAULT_VERBOSE,
) -> list[dict] | None:
    data = None

    if os.path.isfile(file_path):
        # If sheet_name is None, read the first sheet
        if sheet_name is None:
            # Read the Excel file without specifying a sheet
            df = pd.read_excel(file_path, sheet_name=0)
            if verbose:
                logging.info(f"Read first sheet from Excel file {file_path}")
        else:
            # Read the specified sheet
            df = pd.read_excel(file_path, sheet_name=sheet_name)
            if verbose:
                logging.info(f"Read sheet '{sheet_name}' from Excel file {file_path}")

        if filter_na:
            # Drop rows with any NA values
            df = df.dropna()
        elif replace_na:
            # Replace NA values with empty strings
            df = df.fillna("")

        data = df.to_dict(
            orient="records",
        )

        if verbose:
            logging.info(f"Read EXCEL data from {file_path} with {len(data)} rows")
    else:
        if verbose:
            logging.warning(f"File not found: {file_path}")

    return data


def read_npy(
    file_path: str,
    verbose: bool = DEFAULT_VERBOSE,
    allow_pickle: bool = False,
    encoding: str = "ASCII",
) -> Optional[np.ndarray]:
    """
    Read a NumPy array from a .npy file.

    Args:
        file_path: Path to the .npy file.
        verbose: Whether to log information about the operation.
        allow_pickle: Whether to allow loading pickled object arrays.
        encoding: What encoding to use when reading Python 2 strings.

    Returns:
        The loaded NumPy array, or None if the file doesn't exist.
    """
    if not os.path.isfile(file_path):
        if verbose:
            logging.warning(f"File not found: {file_path}")
        return None

    try:
        data = np.load(
            file_path,
            allow_pickle=allow_pickle,
            encoding=encoding,
        )
        if verbose:
            logging.info(f"Read NumPy array from {file_path} with shape {data.shape}")
        return data
    except Exception as e:
        if verbose:
            logging.error(f"Error reading NumPy file {file_path}: {str(e)}")
        return None


def read_npz(
    file_path: str,
    verbose: bool = DEFAULT_VERBOSE,
    allow_pickle: bool = False,
    encoding: str = "ASCII",
) -> Optional[Dict[str, np.ndarray]]:
    """
    Read multiple NumPy arrays from a .npz file.

    Args:
        file_path: Path to the .npz file.
        verbose: Whether to log information about the operation.
        allow_pickle: Whether to allow loading pickled object arrays.
        encoding: What encoding to use when reading Python 2 strings.

    Returns:
        A dictionary of arrays, or None if the file doesn't exist.
    """
    if not os.path.isfile(file_path):
        if verbose:
            logging.warning(f"File not found: {file_path}")
        return None

    try:
        data = np.load(
            file_path,
            allow_pickle=allow_pickle,
            encoding=encoding,
        )

        # Convert to dictionary
        result = {key: data[key] for key in data.files}

        if verbose:
            logging.info(
                f"Read NumPy arrays from {file_path} with keys: {list(result.keys())}"
            )
        return result
    except Exception as e:
        if verbose:
            logging.error(f"Error reading NumPy file {file_path}: {str(e)}")
        return None
