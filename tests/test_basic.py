import os
import sys
import subprocess


def test_basic_works(tmp_path):
    """Simple testing to make sure we can download a few files. This does not verify validity or anything."""

    to_download = 10

    subprocess.run(
        [
            "python3",
            "archiver.py",
            "https://www.youtube.com/@IRyS/community",
            "-o",
            tmp_path,
            "-m",
            str(to_download),
        ],
        check=True,
    )

    if not os.path.isdir(tmp_path):
        sys.exit(1)

    num_files = 0
    for _, _, files in os.walk(tmp_path):
        if "post.txt" in files:
            num_files += 1

    assert num_files == to_download
