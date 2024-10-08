import argparse
from dataclasses import dataclass
import shlex
from typing import List, Optional

from helpers import Driver


@dataclass
class ArchiverSettings:
    url: str
    output_dir: Optional[str]
    members_only: bool
    headless: bool
    cookie_path: Optional[str]
    max_posts: Optional[str]
    profile_dir: Optional[str]
    profile_name: Optional[str]
    driver: Driver
    save_comments: List[str]
    take_screenshots: bool
    skip_existing: bool
    # max_tasks: int


def _create_parser() -> argparse.ArgumentParser:
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
        "--members-only", action="store_true", help="Only save members posts."
    )
    parser.add_argument(
        "--not-headless",
        help="Show the Chrome/Firefox browser window when scraping. May affect behaviour.",
        action="store_true",
    )
    parser.add_argument(
        "--take-screenshots",
        action="store_true",
        help="Take screenshots of each post.",
    )
    parser.add_argument(
        "--save-comments",
        type=str,
        required=False,
        help="Specify which browser driver to use.",
        nargs="+",
        choices=["all", "hearted", "pinned", "creator"],
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="Skip any posts if the save location already contains data.",
    )
    # parser.add_argument(
    #     "--max-tasks",
    #     type=int,
    #     required=False,
    #     help="The maximum number of tasks to spawn at once. Note this is an upper bound, the actual amount used may be less.",
    # )
    # parser.add_argument("--stop-date")

    parser.add_argument("url", type=str, help="The URL to try and grab posts from.")

    return parser


def get_settings() -> tuple[ArchiverSettings, int]:
    args = _create_parser().parse_args()

    rerun = int(args.rerun) if args.rerun and int(args.rerun) > 0 else 1
    max_posts = int(args.max_posts) if args.max_posts else None

    if args.driver is None or args.driver == "chrome":
        driver = Driver.CHROME
    elif args.driver == "firefox":
        driver = Driver.FIREFOX
    else:
        raise Exception("Unsupported driver type!")

    # if args.max_tasks is not None and args.max_task < 1:
    #     print("--max-tasks must be at least 1")

    return (
        ArchiverSettings(
            url=shlex.split(args.url)[0],
            output_dir=args.output_dir,
            cookie_path=args.cookie_path,
            max_posts=max_posts,
            headless=(not args.not_headless),
            driver=driver,
            members_only=args.members_only,
            profile_dir=args.profile_dir,
            profile_name=args.profile_name,
            save_comments=args.save_comments,
            take_screenshots=args.take_screenshots,
            skip_existing=args.skip_existing,
            # max_tasks=args.max_tasks,
        ),
        rerun,
    )
