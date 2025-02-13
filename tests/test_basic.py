import os
import subprocess
import sys

import pytest

ARCHIVER = "yt_community_post_archiver"

pytestmark = pytest.mark.parametrize("driver", ["chrome", "firefox"])


def test_basic_works(tmp_path, driver):
    """
    Simple testing to make sure we can download a few files. This does not verify validity or anything.
    """

    to_download = 5

    subprocess.run(
        [
            "python3",
            "-m",
            ARCHIVER,
            "https://www.youtube.com/@IRyS/community",
            "-d",
            driver,
            "-o",
            tmp_path,
            "-m",
            str(to_download),
        ],
        cwd="src/",
        check=True,
    )

    if not os.path.isdir(tmp_path):
        sys.exit(1)

    num_files = 0
    for _, _, files in os.walk(tmp_path):
        if "post.json" in files:
            num_files += 1

    assert num_files == to_download


def test_poll(tmp_path, driver):
    """
    Simple testing to make sure we can download a poll. This does not verify validity or anything.
    """

    subprocess.run(
        [
            "python3",
            "-m",
            ARCHIVER,
            "https://www.youtube.com/post/UgkxeuDjcdp6k56ltsrTvTAHhz0IokY3kOkn",
            "-d",
            driver,
            "-o",
            tmp_path,
            "-m",
            "1",
        ],
        cwd="src/",
        check=True,
    )

    if not os.path.isdir(tmp_path):
        sys.exit(1)

    num_files = 0
    for _, _, files in os.walk(tmp_path):
        if "post.json" in files:
            num_files += 1

    assert num_files == 1


def test_screenshots(tmp_path, driver):
    """
    Simple test to try screenshots.
    """

    to_download = 2

    subprocess.run(
        [
            "python3",
            "-m",
            ARCHIVER,
            "https://www.youtube.com/@IRyS/community",
            "-d",
            driver,
            "-o",
            tmp_path,
            "-m",
            str(to_download),
            "--take-screenshots",
        ],
        cwd="src/",
        check=True,
    )

    if not os.path.isdir(tmp_path):
        sys.exit(1)

    num_files = 0
    num_screenshots = 0
    for _, _, files in os.walk(tmp_path):
        if "post.json" in files:
            num_files += 1

        if "screenshot.png" in files:
            num_screenshots += 1

    assert num_files == to_download
    assert num_screenshots == to_download


def test_screenshots_2(tmp_path, driver):
    """
    Simple test to try screenshots. This tests some known hard cases.
    """

    for count, to_test in enumerate(
        [
            # Test if a "more" button is not there.
            "https://www.youtube.com/channel/UC8rcEBzJSleTkf_-agPM20g/community?lb=UgkxuIldX2ZZVVkHmMwkat9iD1idsNbBvpel",
            # Test if a "more" button IS there.
            "https://www.youtube.com/channel/UC8rcEBzJSleTkf_-agPM20g/community?lb=UgkxmfOxusAblKXyexE0_5TfO3MHoRXyqbSP",
        ]
    ):

        test_tmp_path = os.path.join(tmp_path, str(count))

        subprocess.run(
            [
                "python3",
                "-m",
                ARCHIVER,
                to_test,
                "-d",
                driver,
                "-o",
                test_tmp_path,
                "--take-screenshots",
            ],
            cwd="src/",
            check=True,
        )

        if not os.path.isdir(test_tmp_path):
            sys.exit(1)

        num_files = 0
        num_screenshots = 0
        for _, _, files in os.walk(test_tmp_path):
            if "post.json" in files:
                num_files += 1

            if "screenshot.png" in files:
                num_screenshots += 1

        assert num_files == 1
        assert num_screenshots == 1


def test_single_image(tmp_path, driver):
    """
    Simple testing to make sure we can handle single images.
    """

    subprocess.run(
        [
            "python3",
            "-m",
            ARCHIVER,
            "https://www.youtube.com/post/UgkxqhALbEMFN0N-bjHVhp5LK4bq0RUwSOz7",
            "-d",
            driver,
            "-o",
            tmp_path,
            "-m",
            "1",
        ],
        cwd="src/",
        check=True,
    )

    if not os.path.isdir(tmp_path):
        sys.exit(1)

    num_pics = 0
    for _, _, files in os.walk(tmp_path):
        num_pics += sum(
            1 if (".png" in file or ".jpg") in file else 0 for file in files
        )

    assert num_pics == 1


def test_multi_images(tmp_path, driver):
    """
    Simple testing to make sure we can handle multiple images.
    """

    subprocess.run(
        [
            "python3",
            "-m",
            ARCHIVER,
            "https://www.youtube.com/post/Ugkx3chE1Bm5UFsuMTrcpkT2L9BuMJUBQIuX",
            "-d",
            driver,
            "-o",
            tmp_path,
            "-m",
            "1",
        ],
        cwd="src/",
        check=True,
    )

    if not os.path.isdir(tmp_path):
        sys.exit(1)

    num_pics = 0
    for _, _, files in os.walk(tmp_path):
        print(files)
        num_pics += sum(
            1 if (".png" in file or ".jpg" in file) else 0 for file in files
        )

    assert num_pics == 2


# Ideally, test all of ["all", "hearted", "pinned", "creator", "members"],
# but this is a bit hard with posts so...
@pytest.mark.parametrize("comment_type", ["all", "members"])
def test_comments(tmp_path, driver, comment_type):
    """
    Simple test to ensure comments work.
    """

    test_path = os.path.join(tmp_path, comment_type)

    subprocess.run(
        [
            "python3",
            "-m",
            ARCHIVER,
            "https://www.youtube.com/post/UgkxuIldX2ZZVVkHmMwkat9iD1idsNbBvpel",
            "-d",
            driver,
            "-o",
            test_path,
            "--save-comments",
            comment_type,
            "--max-comments",
            "5",
        ],
        cwd="src/",
        check=True,
    )

    if not os.path.isdir(test_path):
        sys.exit(1)

    num_files = 0
    num_comments = 0

    for _, _, files in os.walk(test_path):
        if "post.json" in files:
            num_files += 1

    for root, _, files in os.walk(test_path):
        if root.endswith("comments"):
            num_comments = len(files)
            break

    assert num_files == 1
    assert num_comments == 5
