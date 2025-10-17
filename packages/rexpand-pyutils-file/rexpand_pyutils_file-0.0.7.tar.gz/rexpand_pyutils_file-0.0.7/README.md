# rexpand-pyutils-file

A comprehensive Python utility package for file system operations, providing easy-to-use functions for reading, writing, finding, and downloading files.

## Features

- **File Reading**: Read JSON, CSV, Excel, HTML, text files (including .txt, .log, .md) with a simple API
- **File Writing**: Write data to JSON, CSV, Excel, HTML, and text files with customizable options
- **File Finding**: Find files and folders in directories with filtering options and recursive search
- **File Downloading**: Download files from URLs with automatic extension detection
- **File Compression**: Unzip gzip (.gz) files
- **Path Refinement**: Clean and normalize file paths with cross-platform support

## Installation

You can install the package using pip:

```bash
pip install rexpand-pyutils-file
```

## Usage

```python
from rexpand_pyutils_file import read_file, write_file, find_files

# Read a JSON file
data = read_file("path/to/file.json")

# Write data to a CSV file
write_file("path/to/output.csv", data)

# Find all CSV files in a directory
csv_files = find_files("path/to/directory", file_suffix="csv")
```

## API Reference

### Main Functions

- `read_file(path, verbose=None, encoding=None, excel_sheet_name=None)`: Read a file (supports .json, .csv, .xlsx, .html, .txt, .log, .md)
- `write_file(path, data, verbose=None, encoding=None, csv_and_excel_overwrite=True, csv_fieldnames=None, excel_sheet_name="Sheet1", excel_enable_str_conversion=False)`: Write data to a file
- `download_file(url, file_path_without_extension, verbose=None)`: Download a file from a URL
- `unzip_file(path, output_path=None, verbose=None)`: Unzip a gzip (.gz) file
- `find_files(path, ignored_file_set=None, file_suffix=None, recursive=False)`: Find files in a directory
- `find_folders(path, ignored_folder_set=None, recursive=False)`: Find folders in a directory
- `refine_path(path)`: Refine a path with cross-platform support

## License

This project is licensed under the MIT License - see the LICENSE file for details.
