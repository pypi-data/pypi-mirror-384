"""
Utility functions for downloading and uncompressing data files.
"""

import gzip
import os
import shutil
import urllib.request


def download_data(url, out_path, uncompress=False):
    """
    Download a file from a URL to a specified output path. If uncompress is True
    and the file is a .gz file, it will be uncompressed after download. If the file
    already exists at the output path, it will not be downloaded again.

    Parameters:
    -----------
    url : str
        The URL of the file to download.
    out_path : str
        The directory where the file should be saved.
    uncompress : bool, optional
        Whether to uncompress the file if it is a .gz file. Default is False.

    Returns:
    --------
    out_file : str
        The path to the downloaded (and possibly uncompressed) file.
    """
    if uncompress:
        return download_data_and_uncompress(url, out_path)

    filename = os.path.basename(url)
    out_file = os.path.join(out_path, filename)

    if os.path.exists(out_file):
        return out_file

    if not os.path.exists(out_path):
        os.makedirs(out_path)

    urllib.request.urlretrieve(url, out_file)

    return out_file


def download_data_and_uncompress(url, out_path):
    """
    Download a .gz file from a URL to a specified output path and uncompress it.
    If the uncompressed file already exists at the output path, it will not be
    downloaded again.

    Parameters:
    -----------
    url : str
        The URL of the .gz file to download.
    out_path : str
        The directory where the uncompressed file should be saved.

    Returns:
    --------
    out_file : str
        The path to the downloaded and uncompressed file.
    """
    if not url.endswith(".gz"):
        raise ValueError("URL must point to a .gz file if uncompress is True")

    filename = os.path.basename(url)
    gz_file = os.path.join(out_path, filename)
    out_file = os.path.join(out_path, filename[:-3])  # remove .gz

    if os.path.exists(out_file):
        return out_file

    if not os.path.exists(out_path):
        os.makedirs(out_path)

    urllib.request.urlretrieve(url, gz_file)
    uncompress_gz(gz_file, out_file)
    os.remove(gz_file)

    return out_file


def uncompress_gz(gz_path, out_path):
    """
    Uncompress a .gz file.
    """
    with gzip.open(gz_path, "rb") as f_in:
        with open(out_path, "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)
