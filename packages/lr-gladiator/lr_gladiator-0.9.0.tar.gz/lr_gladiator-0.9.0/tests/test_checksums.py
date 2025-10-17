# tests/test_md5_content_header.py
from pathlib import Path
from gladiator.checksums import md5_base64_file
import hashlib, base64, os, tempfile


def test_md5_base64_file_matches_python():
    payload = b"hello world"
    with tempfile.NamedTemporaryFile(delete=False) as tf:
        tf.write(payload)
        p = Path(tf.name)
    try:
        expected = base64.b64encode(hashlib.md5(payload).digest()).decode("ascii")
        assert md5_base64_file(p) == expected
    finally:
        os.unlink(p)
