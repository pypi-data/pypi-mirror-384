# -*- coding: utf-8 -*-

import os


def _is_file_like(obj):
    """
    Check if an object is file-like.

    A file-like object is one that has either read() or write() methods.

    Args:
        obj: The object to check

    Returns:
        bool: True if the object has read or write method, False otherwise
    """
    return hasattr(obj, 'read') or hasattr(obj, 'write')

def kv_read(file):
    """
    Read key-value pairs from a file or file-like object.

    The key-value pairs in the file should be in the format "key = value".
    Empty lines and lines without valid key-value pairs are ignored.

    Args:
        file: File path string or file-like object

    Returns:
        dict: Dictionary containing all key-value pairs
    """
    ret = {}

    if _is_file_like(file):
        # If it's a file-like object, use it directly
        f = file
        f.seek(0)
    else:
        # If it's a file path, check if file exists
        if not os.path.exists(file):
            return ret
        f = open(file, 'r')
    lines = f.readlines()
    if not _is_file_like(file):
        f.close()

    # Parse each line
    for s in lines:
        s = s.strip()
        if not s:
            # Skip empty lines
            continue
        p = s.find('=')
        if p <= 0:
            # Skip lines without '=' or '=' at first position
            continue
        k = s[0:p].strip()
        v = s[p + 1:].strip()
        if not k or not v:
            # Skip lines with empty key or value
            continue
        ret[k] = v

    return ret


def kv_write(file, arr):
    """
    Write key-value pairs dictionary to a file or file-like object.

    Args:
        file: File path string or file-like object
        arr: Dictionary containing key-value pairs
    """
    if _is_file_like(file):
        # If it's a file-like object, use it directly and clear content
        f = file
        f.seek(0)
        f.truncate()
    else:
        # If it's a file path, open file for writing
        f = open(file, 'w')
    for k, v in arr.items():
        # Write each key-value pair in format "key = value"
        f.write("{0} = {1}\n".format(k, v))
    if not _is_file_like(file):
        f.close()

def kv_get(file, key):
    """
    Get the value of a specified key from a file.

    Args:
        file: File path string or file-like object
        key: The key to get value for

    Returns:
        str or None: The value corresponding to the key, or None if key doesn't exist
    """
    arr = kv_read(file)
    return arr.get(key)


def kv_set(file, key, val):
    """
    Set the value of a specified key in a file.

    Args:
        file: File path string or file-like object
        key: The key to set
        val: The value to set
    """
    arr = kv_read(file)
    arr[key] = val
    kv_write(file, arr)