"""Dependency Extractor for FPGA Projects.

This script extracts dependency ZIP files into a specified folder structure,
facilitating the integration of third-party components and libraries.
It automatically detects all ZIP files in the current directory and
extracts them to a target location, handling Windows long path limitations
and ensuring a clean extraction environment.

This tool is designed to work with the NI GitHub FPGA project workflow,
managing external dependencies that may come from GitHub repositories
or other external sources.
"""

# Copyright (c) 2025 National Instruments Corporation
#
# SPDX-License-Identifier: MIT
#
import os
import shutil


def _validate_source_folder(source_folder):
    """Validates the source folder and checks for ZIP files.

    Args:
        source_folder (str): Folder containing ZIP files to extract.

    Raises:
        FileNotFoundError: If source folder doesn't exist
        ValueError: If no ZIP files are found in the source folder
    """
    # Check if source folder exists
    if not os.path.exists(source_folder):
        raise FileNotFoundError(
            f"Dependencies folder not found.\nPlease ensure that you are running extract-deps from the correct folder.\n"
        )

    # Check if there are any zip files in the source folder
    zip_files = [f for f in os.listdir(source_folder) if f.endswith(".zip")]
    if not zip_files:
        raise ValueError(f"No ZIP files found in source folder: {source_folder}")


def extract_deps_from_zip():
    """Extracts the contents of all ZIP files from source_folder into the deps_folder.

    Args:
        deps_folder (str): Target folder where ZIP contents will be extracted.
        source_folder (str, optional): Folder containing ZIP files to extract.
                                      If None, uses current directory.
    """
    cwd = os.getcwd()
    # This code assumes you are running extract-deps from the target folder
    # For example - c:\github\flexrio\targets\pxie-7903
    #
    # The extract-deps function is NOT target specific.  It extracts dependencies for
    # the entire repo.  However, since all other nihdl commands are run from the target
    # folder, we set it up for extract-deps to run from there too for consistnecy.
    #
    deps_folder = os.path.join(cwd, "..", "..", "dependencies", "githubdeps")
    source_folder = os.path.join(cwd, "..", "..", "dependencies")

    deps_folder = os.path.abspath(deps_folder)
    source_folder = os.path.abspath(source_folder)

    # Validate the source folder and its contents
    try:
        _validate_source_folder(source_folder)
    except Exception as e:
        print(f"Error: {e}")
        return

    # Handle long paths on Windows
    # The \\?\ prefix allows paths over 260 characters on Windows systems
    if os.name == "nt":
        deps_folder_long = f"\\\\?\\{deps_folder}"
    else:
        deps_folder_long = deps_folder

    print(f"Using dependencies folder: {deps_folder}")
    print(f"Using long path: {deps_folder_long}")

    # Clean and create target directory
    print(f"Cleaning target directory: {deps_folder}")
    shutil.rmtree(deps_folder_long, ignore_errors=True)
    os.makedirs(deps_folder_long, exist_ok=True)

    # Determine source directory
    print(f"Looking for ZIP files in: {source_folder}")

    # Find all zip files in the source directory
    # This allows batch processing of multiple dependency archives
    zip_files = [f for f in os.listdir(source_folder) if f.endswith(".zip")]
    print(f"Found {len(zip_files)} ZIP files")

    # Extract each zip file
    # Process files sequentially, reporting success or failure for each
    for zip_file in zip_files:
        try:
            zip_path = os.path.join(source_folder, zip_file)
            print(f"Extracting '{zip_file}' into '{deps_folder}'...")
            shutil.unpack_archive(zip_path, deps_folder_long, "zip")
            print(f"Successfully extracted '{zip_file}'")
        except Exception as e:
            print(f"Error extracting '{zip_file}': {e}")

    # Check extraction results
    # This helps verify that the extraction process produced output files
    extracted_files = os.listdir(deps_folder)
    print(f"Extracted {len(extracted_files)} items to {deps_folder}")
