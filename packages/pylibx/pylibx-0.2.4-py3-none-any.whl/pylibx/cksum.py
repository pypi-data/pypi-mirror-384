# -*- coding: utf-8 -*-

import os
import sys
import zlib

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


def crc32(filename):
    """
    Calculate CRC32 checksum of a file.

    Args:
        filename: Path to the file to calculate checksum for

    Returns:
        int: CRC32 checksum value
    """
    block_size = 1024 * 1024
    crc = 0

    if not os.path.exists(filename):
        return crc
    with open(filename, 'rb') as f:
        while True:
            buffer = f.read(block_size)
            if len(buffer) == 0:  # EOF or file empty. return hashes
                if sys.version_info[0] < 3 and crc < 0:
                    crc += 2 ** 32
                return crc
            crc = zlib.crc32(buffer, crc)
    return crc


def cksum_read(sum_file):
    """
    Read checksum data from a file or file-like object.

    The checksum data in the file should be in CSV format with columns:
    filename, mtime, size, crc32

    Args:
        sum_file: File path string or file-like object containing checksum data

    Returns:
        dict: Dictionary with filename as key and checksum info as value
    """
    cksum = {}
    
    if _is_file_like(sum_file):
        # If it's a file-like object, use it directly
        f = sum_file
        f.seek(0)
    else:
        # If it's a file path, check if file exists
        if not os.path.exists(sum_file):
            return cksum
        f = open(sum_file, 'r')
    
    lines = f.readlines()
    if not _is_file_like(sum_file):
        f.close()
        
    cols = []
    for s in lines:
        s = s.strip()
        if not s:
            continue
        arr = s.split(',')
        if not cols:
            for x in arr:
                cols.append(x)
            continue

        if len(arr) != len(cols):
            continue

        fn = ''
        val = {}
        i = 0
        for x in arr:
            if not fn:
                fn = x
            else:
                val[cols[i]] = x
            i += 1
        cksum[fn] = val
    return cksum


def cksum_write(sum_file, cksum):
    """
    Write checksum data to a file or file-like object.

    Args:
        sum_file: File path string or file-like object to write checksum data to
        cksum: Dictionary containing checksum data to write
    """
    if not cksum:
        if not _is_file_like(sum_file) and os.path.exists(sum_file):
            os.unlink(sum_file)
        return

    if _is_file_like(sum_file):
        # If it's a file-like object, use it directly and clear content
        f = sum_file
        f.seek(0)
        f.truncate()
    else:
        # If it's a file path, open file for writing
        f = open(sum_file, 'w')
        
    f.write("filename,mtime,size,crc32\n")
    si = sorted(cksum.items(), key=lambda item: item[0])
    for sv in si:
        k = sv[0]
        v = sv[1]
        f.write("{0},{1},{2},{3}\n".format(k, v['mtime'], v['size'], v['crc32']))
        
    if not _is_file_like(sum_file):
        f.close()


def cksum_stat(file_path):
    """
    Get file statistics including modification time, size and CRC32 checksum.

    Args:
        file_path: Path to the file to get statistics for

    Returns:
        dict: Dictionary containing mtime, size and crc32 values
    """
    fs = os.stat(file_path)
    val = dict()
    val['mtime'] = str(int(fs.st_mtime))
    val['size'] = str(int(fs.st_size))
    val['crc32'] = hex(crc32(file_path))[2:].zfill(8)
    return val


def cksum_clr(sum_file, filename):
    """
    Remove a file's checksum entry from the checksum file.

    Args:
        sum_file: Path to the checksum file or file-like object
        filename: Name of the file to remove from checksum data
    """
    cksum = cksum_read(sum_file)
    del cksum[filename]
    cksum_write(sum_file, cksum)


def cksum_set(sum_file, filename, val=None):
    """
    Add or update a file's checksum entry in the checksum file.

    Args:
        sum_file: Path to the checksum file or file-like object
        filename: Name of the file to add/update checksum data for
        val: Optional checksum data dictionary. If provided and valid, 
             will be used directly instead of generating from file stats.
             Expected format: {'mtime': str, 'size': str, 'crc32': str}
    """
    if val is not None and isinstance(val, dict) and \
       'mtime' in val and 'size' in val and 'crc32' in val:
        # Use provided val directly
        pass
    else:
        # Generate val from file stats
        val = cksum_stat(os.path.join(os.path.dirname(sum_file), filename))
        
    cksum = cksum_read(sum_file)
    cksum[filename] = val
    cksum_write(sum_file, cksum)


def cksum_get(sum_file, filename):
    """
    Get checksum data for a specific file from the checksum file.

    Args:
        sum_file: Path to the checksum file or file-like object
        filename: Name of the file to get checksum data for

    Returns:
        dict or None: Checksum data for the specified file, or None if not found
    """
    cksum = cksum_read(sum_file)
    return cksum.get(filename)