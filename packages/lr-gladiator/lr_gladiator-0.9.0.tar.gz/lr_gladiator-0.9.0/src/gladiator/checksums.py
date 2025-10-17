#! /usr/bin/env python
# -*- coding: utf-8 -*-
# src/gladiator/checksums.py
from __future__ import annotations
from pathlib import Path
import hashlib
import base64


def sha256_file(path: Path, chunk_size: int = 128 * 1024) -> str:
    """
    Return the lowercase hex SHA-256 of the file at `path`.
    Streams the file in chunks to support large files.
    """
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            h.update(chunk)
    return h.hexdigest()


def md5_base64_file(path: Path, chunk_size: int = 128 * 1024) -> str:
    """
    Return base64-encoded MD5 digest of the file at `path`,
    suitable for the Content-MD5 header per RFC 1864.
    """
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            h.update(chunk)
    return base64.b64encode(h.digest()).decode("ascii")
