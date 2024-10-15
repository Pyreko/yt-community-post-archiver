import os
import sys
import subprocess


def test_basic_works(tmp_path):
    """
    Simple testing to make sure we can download a few files. This does not verify validity or anything.
    """

    to_download = 3

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


def test_poll(tmp_path):
    """
    Simple testing to make sure we can download a poll. This does not verify validity or anything.
    """

    subprocess.run(
        [
            "python3",
            "archiver.py",
            "https://www.youtube.com/post/UgkxeuDjcdp6k56ltsrTvTAHhz0IokY3kOkn",
            "-o",
            tmp_path,
            "-m",
            "1",
        ],
        check=True,
    )

    if not os.path.isdir(tmp_path):
        sys.exit(1)

    num_files = 0
    for _, _, files in os.walk(tmp_path):
        if "post.txt" in files:
            num_files += 1

    assert num_files == 1


def test_screenshots(tmp_path):
    """
    Simple test to try screenshots.
    """

    to_download = 2

    subprocess.run(
        [
            "python3",
            "archiver.py",
            "https://www.youtube.com/@IRyS/community",
            "-o",
            tmp_path,
            "-m",
            str(to_download),
            "--take-screenshots",
        ],
        check=True,
    )

    if not os.path.isdir(tmp_path):
        sys.exit(1)

    num_files = 0
    num_screenshots = 0
    for _, _, files in os.walk(tmp_path):
        if "post.txt" in files:
            num_files += 1

        if "screenshots.png" in files:
            num_screenshots += 1

    assert num_files == to_download
    assert num_screenshots == to_download


def test_single_image(tmp_path):
    """
    Simple testing to make sure we can handle single images.
    """

    subprocess.run(
        [
            "python3",
            "archiver.py",
            "https://www.youtube.com/post/UgkxqhALbEMFN0N-bjHVhp5LK4bq0RUwSOz7",
            "-o",
            tmp_path,
            "-m",
            "1",
        ],
        check=True,
    )

    if not os.path.isdir(tmp_path):
        sys.exit(1)

    num_pics = 0
    for _, _, files in os.walk(tmp_path):
        if any(".png" in file or ".jpg" in file for file in files):
            num_pics += 1

    assert num_pics == 1


def test_multi_images(tmp_path):
    """
    Simple testing to make sure we can handle multiple images.
    """

    subprocess.run(
        [
            "python3",
            "archiver.py",
            "https://www.youtube.com/post/Ugkx3chE1Bm5UFsuMTrcpkT2L9BuMJUBQIuX",
            "-o",
            tmp_path,
            "-m",
            "1",
        ],
        check=True,
    )

    if not os.path.isdir(tmp_path):
        sys.exit(1)

    num_pics = 0
    for _, _, files in os.walk(tmp_path):
        if any(".png" in file or ".jpg" in file for file in files):
            num_pics += 1

    assert num_pics == 2
