# -*- coding: UTF-8 -*-
import os
import io
import hashlib

def_headers = {'User-Agent': 'Mozilla/5.0 (iPad; CPU OS 12_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148'}
version = "1.6.6"


# print for debugging
def printD(msg, end=None):
    print(f"[Civitai Helper] {msg}", end=end)


def read_chunks(file, size=io.DEFAULT_BUFFER_SIZE):
    """Yield pieces of data from a file-like object until EOF."""
    while True:
        chunk = file.read(size)
        if not chunk:
            break
        yield chunk


# Now, hashing use the same way as pip's source code.
def gen_file_sha256(filname):
    blocksize = 1 << 20
    h = hashlib.sha256()
    length = 0
    with open(os.path.realpath(filname), 'rb') as f:
        for block in read_chunks(f, size=blocksize):
            length += len(block)
            h.update(block)

    hash_value = h.hexdigest()
    # printD(f"sha256: {hash_value} [{hr_size(length)}]")
    return hash_value


# get subfolder list
def get_subfolders(folder: str):
    if not folder:
        printD("folder can not be None")
        return

    if not os.path.isdir(folder):
        printD("path is not a folder")
        return

    prefix_len = len(folder)
    subfolders = []
    for root, dirs, files in os.walk(folder, followlinks=True):
        for dir in dirs:
            full_dir_path = os.path.join(root, dir)
            # get subfolder path from it
            subfolder = full_dir_path[prefix_len:]
            subfolders.append(subfolder)

    return subfolders


# get relative path
def get_relative_path(item_path: str, parent_path: str) -> str:
    # item path must start with parent_path
    if not item_path:
        return ""
    if not parent_path:
        return ""
    if not item_path.startswith(parent_path):
        return item_path

    relative = item_path[len(parent_path):]
    if relative[:1] == "/" or relative[:1] == "\\":
        relative = relative[1:]

    # printD("relative:"+relative)
    return relative


# get relative path
def shorten_path(filepath: str) -> str:
    idx = filepath.find("models" + os.sep)
    if idx >= 0:
        return filepath[idx + 7:]
    return filepath


# human readable size format
def hr_size(size, decimal_places=2):
    for unit in ['B', 'KB', 'MB', 'GB', 'TB', 'PB']:
        if size < 1024.0 or unit == 'PB':
            break
        size /= 1024.0
    return f"{size:.{decimal_places}f} {unit}"
