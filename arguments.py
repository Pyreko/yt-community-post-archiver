import argparse


def get_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Archives YouTube community posts.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "-o", "--output-dir", type=str, required=False, help="The directory to save to."
    )
    parser.add_argument(
        "-p",
        "--profile-dir",
        type=str,
        required=False,
        help="The path to where your Chrome profiles are stored. Will not do anything if cookies are set.",
    )
    parser.add_argument(
        "-n",
        "--profile-name",
        type=str,
        required=False,
        help="The profile you want to use. If not set and profile_dir is set, the default profile is used. Will not do anything if cookies are set.",
    )
    parser.add_argument(
        "-c",
        "--cookie-path",
        type=str,
        required=False,
        default=None,
        help="The path to a cookies file in the Netscape format.",
    )
    parser.add_argument(
        "-r",
        "--rerun",
        type=str,
        required=False,
        default=1,
        help="How many times to rerun the archiver. Must be greater than 0.",
    )
    parser.add_argument(
        "-m",
        "--max-posts",
        type=str,
        required=False,
        default=None,
        help="Set a limit on how many posts to download.",
    )
    parser.add_argument(
        "-d",
        "--driver",
        type=str,
        required=False,
        default="chrome",
        help="Specify which browser driver to use.",
        choices=["firefox", "chrome"],
    )
    parser.add_argument(
        "--members-only", help="Only save members posts.", action="store_true"
    )
    parser.add_argument(
        "--not-headless",
        help="Show the Chrome/Firefox browser window when scraping. May affect behaviour.",
        action="store_true",
    )
    parser.add_argument("url", type=str, help="The URL to try and grab posts from.")

    return parser.parse_args()
