import sys
import errno
import hashlib
import gzip
import os
from httpx import Client, RequestError
from re import findall
from time import time, sleep
from traceback import print_exc
from gitlab_ps_utils.decorators import stable_retry
from tqdm import tqdm

@stable_retry(retries=5, delay=60, backoff=1.2)
def download_file(url, path, filename=None, headers=None, verify=True, wait=0, client=None):
    '''
    Uses the stable_retry decorator to attempt to stream download a file, typically
    a GitLab .tar.gz file. Any requests status other than 200 will result in
    an error, prompting the stable_retry.
    '''
    is_downloadable, content_type = __is_downloadable(url, verify, headers=headers)
    if is_downloadable:
        if wait:
            print(f"Waiting {wait} before downloading file")
            sleep(wait)
        chunk_size = 1024*1024
        client = client if client else Client(verify=verify, follow_redirects=True)
        try:
            with client.stream(method='get', url=url, headers=headers) as r:
                r.raise_for_status()
                if filename is None:
                    filename = __get_filename_from_cd(
                        r.headers.get('content-disposition'))

                # Get the total file size from the Content-Length header
                total_size = int(r.headers.get('Content-Length', 0))

                # Create a progress bar using tqdm
                progress_bar = tqdm(total=total_size, unit='B', unit_scale=True, desc=filename)

                file_path = f"{path}/downloads/{filename}"
                create_local_project_export_structure(os.path.dirname(file_path))
                with open(file_path, "wb", chunk_size) as f:
                    for chunk in r.iter_bytes(chunk_size=chunk_size):
                        if chunk:
                            f.write(chunk)
                            progress_bar.update(len(chunk))

                progress_bar.close()

                did_fully_download, actual_size = __did_file_fully_download(file_path, total_size)
                if not did_fully_download:
                    raise OSError(f"File '{filename}' did not fully download.\nActual size: {actual_size}\nExpected size: {total_size}")

        except RequestError as re:
            print(
                f"Download request to {url} failed for {filename} ({path}) due to:\n{re}", file=sys.stderr)
            return None
        except Exception as e:
            print(
                f"Failed to download {filename} ({path}) from  {url} due to:\n{e}", file=sys.stderr)
            return None
        return filename
    raise ValueError(f"Invalid content type [{content_type}] for file [{filename}]")


def create_local_project_export_structure(dir_path):
    if not os.path.exists(dir_path):
        try:
            os.makedirs(dir_path)
        except OSError as exc:  # Guard against race condition
            if exc.errno != errno.EEXIST:
                raise


def is_gzip(test_file):
    '''
    Attempts to detect is a file is a valid gzip file.  This assists with detecting
    accuracy of the export.  Even if the file is detected as a GZIP, its possible the
    download still failed in some other way, and is incomplete.
    '''
    with gzip.open(test_file, 'r') as fh:
        try:
            fh.read(1)
            return True
        except gzip.BadGzipFile:
            return False


def __is_downloadable(url, verify, headers=None):
    """
        Does the url contain a downloadable resource
    """
    client = Client(verify=verify, follow_redirects=True)
    h = client.head(url, headers=headers)
    header = h.headers
    content_type = header.get('content-type')
    if 'text' in content_type.lower():
        return False, 'text'
    if 'html' in content_type.lower():
        return False, 'html'
    return True, content_type.lower()


def __get_filename_from_cd(cd):
    """
        Get filename from content-disposition
    """
    if not cd:
        return None
    fname = findall('filename=(.+)', cd)
    if len(fname) == 0:
        return None
    return fname[0]

def __did_file_fully_download(file_path, expected_size):
    actual_size = os.stat(file_path).st_size
    return actual_size == expected_size, actual_size


def is_recent_file(path, age=2592000):
    """
        Check whether a file path exists, is empty and older than 1 month
    """
    try:
        return os.path.exists(path) and os.path.getsize(path) > 0 and (time() - os.path.getmtime(path) < age)
    except OSError as ose:
        sys.exit(f"Path {path} does not exist or is inaccessible: {ose}")


def get_hash_of_dirs(directory, verbose=0):
    """
        http://akiscode.com/articles/sha-1directoryhash.shtml
        Copyright (c) 2009 Stephen Akiki
        MIT License (Means you can do whatever you want with this)
        See http://www.opensource.org/licenses/mit-license.php
        Error Codes:
        -1 -> Directory does not exist
        -2 -> General error (see stack traceback)
    """
    SHAhash = hashlib.sha1()
    if not os.path.exists(directory):
        return -1

    try:
        for root, _, files in os.walk(directory):
            for names in files:
                if verbose == 1:
                    print('Hashing', names)
                filepath = os.path.join(root, names)
                f1 = None
                try:
                    f1 = open(filepath, 'rb')
                except BaseException:
                    # You can't open the file for some reason
                    f1.close()
                    continue

                while True:
                    # Read file in as little chunks
                    buf = f1.read(4096)
                    if not buf:
                        break
                    SHAhash.update(hashlib.sha1(buf).hexdigest().encode())
                f1.close()
    except BaseException:
        # Print the stack traceback
        print_exc()
        return -2

    return SHAhash.hexdigest()


def find_files_in_folder(wildcard, directory):
    return [f for f in os.listdir(directory) if wildcard in f]
