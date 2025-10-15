import hashlib
import os
from pathlib import Path
import requests
import zipfile
from tqdm import tqdm
from typing import Sequence
from urllib.parse import urlparse

def file_sha256(path: str | Path, bufsize: int = 1 << 20) -> str:
    """
    Compute SHA-256 for a file.

    Args:
        path: File path
        bufsize: Read buffer size (default 1MB)

    Returns:
        Hex digest string
    """
    path = Path(path)
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(bufsize), b""):
            h.update(chunk)
    return h.hexdigest()


def download_from_urls(urls: Sequence[str], folder: str | Path) -> str:
    """
    Try downloading a file from a list of candidate URLs (in order) into `folder`.
    Uses `download_from_url` for the actual download (with resume support).

    Returns:
        The downloaded file path (string).

    Raises:
        The last exception if all candidates fail.
    """
    last_err = None
    for u in urls:
        try:
            return download_from_url(u, str(folder))
        except Exception as e:
            last_err = e
            continue
    raise RuntimeError(f"All sources failed. Last error: {last_err}")

def download_from_url(url: str, folder: str) -> str:
    """
    Downloads a file from the specified URL and saves it in the given folder. If the download
    is interrupted, it attempts to resume it from where it left off.

    Args:
        url (str): The URL from which to download the file.
        folder (str): The directory where the file will be saved. The directory will be
                      created if it does not exist.

    Returns:
        str: The path to the downloaded file.

    Raises:
        ValueError: If the URL does not contain a valid filename.
        requests.exceptions.RequestException: For issues like network problems, or invalid responses.

    Example:
        download_from_url("http://example.com/file.zip", "/path/to/download/folder")
    """
    print(f"Downloading {url} to {folder}")

    # Extracting the filename from the URL
    filename = os.path.basename(urlparse(url).path)
    if not filename:
        raise ValueError("URL does not contain a valid filename")

    # Create the full path for the file to be saved
    file_path = os.path.join(folder, filename)

    # Ensure directory exists
    if not os.path.exists(folder):
        os.makedirs(folder)

    mode = 'wb'
    headers = {}
    if os.path.exists(file_path):
        existing_size = os.path.getsize(file_path)
        headers['Range'] = f'bytes={existing_size}-'
        mode = 'ab'
        print(f"Resuming download at byte {existing_size}")
    else:
        existing_size = 0

    response = requests.get(url, stream=True, headers=headers)
    if response.status_code != 200 and response.status_code != 206:
        raise requests.exceptions.RequestException(f"Failed to download the file: {response.status_code}")

    total_size = int(response.headers.get('content-length', 0)) + existing_size

    progress_bar = tqdm(total=total_size, unit='iB', unit_scale=True, initial=existing_size)

    with open(file_path, mode) as file:
        for data in response.iter_content(1024):
            file.write(data)
            progress_bar.update(len(data))
    progress_bar.close()

    if total_size != 0 and progress_bar.n != total_size:
        print("ERROR, something went wrong while downloading the file")
    else:
        print(f"File downloaded and saved as {file_path}")

    return file_path


def extract_file(zip_file_path: str, extract_to: str=None, delete_zip: bool=False) -> None:
    """
    Extracts a zip file to a specified directory or the same location as the zip file, displaying
    a progress bar during the extraction process. If no directory is specified, it defaults to the
    directory containing the zip file. Optionally, the zip file can be deleted after successful extraction.

    Args:
        zip_file_path (str): The full path to the zip file to be extracted. This must be a valid path
                             pointing to an existing zip file.
        extract_to (str, optional): The directory to which the zip contents will be extracted. If None,
                                    the contents will be extracted to the same directory as the zip file.
                                    This directory will be created if it does not already exist.
        delete_zip (bool): If True, the zip file will be deleted after extraction. Defaults to False.

    Raises:
        FileNotFoundError: If the zip_file_path does not exist or is invalid.
        zipfile.BadZipFile: If the zip_file_path is not a zip file or it is a corrupted zip file.
        PermissionError: If the function does not have permission to create directories or delete files
                         in the specified paths.

    Example:
        extract_file("/path/to/your/file.zip", "/path/to/destination/folder", True)
    """
    if not os.path.exists(zip_file_path):
        raise FileNotFoundError(f"No zip file found at {zip_file_path}")

    # Determine the directory to extract to
    if extract_to is None:
        extract_to = os.path.dirname(zip_file_path)

    # Ensure the extraction directory exists
    if not os.path.exists(extract_to):
        try:
            os.makedirs(extract_to)
        except PermissionError:
            raise PermissionError(f"Permission denied to create directory at {extract_to}")

    # Extract the zip file with a progress bar
    try:
        with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
            total_files = len(zip_ref.infolist())
            with tqdm(total=total_files, unit='files', desc="Extracting files") as progress_bar:
                for file in zip_ref.infolist():
                    zip_ref.extract(file, extract_to)
                    progress_bar.update(1)
            print(f"Files extracted to {extract_to}")
    except zipfile.BadZipFile:
        raise zipfile.BadZipFile(f"The file at {zip_file_path} is not a valid zip file or is corrupted.")

    # Optionally delete the zip file
    if delete_zip:
        try:
            os.remove(zip_file_path)
            print(f"Zip file {zip_file_path} deleted after extraction.")
        except PermissionError:
            raise PermissionError(f"Permission denied to delete file at {zip_file_path}")

def resolve_root(root: Path | None, create: bool = False) -> Path:
    """
    Resolve the dataset root directory.

    Precedence:
      1) Use the provided `root` argument if not None.
      2) Else, use the `PRT_DATA_ROOT` environment variable if set and non-empty.
      3) Else, default to `~/datasets`.

    Parameters
    ----------
    root : Path | None
        Candidate root directory.
    create : bool, optional (default: False)
        If True, create the directory (with parents) when it does not exist.

    Returns
    -------
    Path
        Absolute, user-expanded path.

    Raises
    ------
    NotADirectoryError
        If the resolved path exists and is not a directory.
    """
    if root is not None:
        path = Path(root).expanduser()
    else:
        env_val = os.getenv("PRT_DATA_ROOT", "").strip()
        path = Path(env_val).expanduser() if env_val else (Path.home() / "datasets")

    if create:
        path.mkdir(parents=True, exist_ok=True)

    if path.exists() and not path.is_dir():
        raise NotADirectoryError(f"Resolved path exists but is not a directory: {path}")

    return path.resolve()