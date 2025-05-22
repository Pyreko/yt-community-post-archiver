import argparse
import shlex
from dataclasses import dataclass
from enum import Enum, unique

from yt_community_post_archiver.helpers import Driver

__version__ = "0.1.7"


@unique
class CommentType(Enum):
    """
    The different types of comment types we can try and save.
    """

    ALL = 1
    HEARTED = 2
    PINNED = 3
    CREATOR = 4
    MEMBERS = 5

    @staticmethod
    def from_str(s: str):
        match s:
            case "all":
                return CommentType.ALL
            case "hearted":
                return CommentType.HEARTED
            case "pinned":
                return CommentType.PINNED
            case "creator":
                return CommentType.CREATOR
            case "members":
                return CommentType.MEMBERS
            case _:
                raise Exception("Unsupported comment type!")


@unique
class MembersPostType(Enum):
    """
    Whether to store members posts only or ignore members posts entirely.
    """

    MEMBERS_ONLY = 1
    NO_MEMBERS = 2

    @staticmethod
    def from_str(s: str):
        match s:
            case "members-only":
                return MembersPostType.MEMBERS_ONLY
            case "no-members":
                return MembersPostType.NO_MEMBERS
            case _:
                raise Exception("Unsupported members post type!")


@dataclass
class ArchiverSettings:
    url: str
    output_dir: str | None
    members: MembersPostType | None
    headless: bool
    cookie_path: str | None
    max_posts: int | None
    profile_dir: str | None
    profile_name: str | None
    binary_override: str | None
    driver: Driver
    save_comments_types: set[CommentType]
    max_comments: int | None
    take_screenshots: bool
    skip_existing: bool


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
        help="The path to where your driver profiles are stored (e.g. ~/.config/chromium). Will not do anything if cookies are set.",
    )
    parser.add_argument(
        "-n",
        "--profile-name",
        type=str,
        required=False,
        help="[Only for Chrome driver] The profile you want to use. If not set and profile_dir is set, the default profile is used. Will not do anything if cookies are set.",
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
        type=int,
        required=False,
        default=None,
        help="Set a limit on how many posts to check. Skipped posts will count towards this.",
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
        "--binary-override",
        type=str,
        required=False,
        help="Override the default driver binary. You probably don't need this unless you want to scrape using developer/canary/beta versions.",
    )
    parser.add_argument(
        "--members",
        type=str,
        required=False,
        help="Control whether to store members-only posts or ignore members-only posts. Don't set to save all posts seen.",
        choices=["members-only", "no-members"],
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
        choices=["all", "hearted", "pinned", "creator", "members"],
    )
    parser.add_argument(
        "--max-comments",
        type=int,
        required=False,
        default=None,
        help="Set a limit on how many comments to grab per post.",
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="Skip any posts if the save location already contains data.",
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        help="Prints version information.",
        version=f"%(prog)s {__version__}",
    )

    parser.add_argument("url", type=str, help="The URL to try and grab posts from.")

    return parser


def get_settings() -> tuple[ArchiverSettings, int]:
    args = _create_parser().parse_args()

    rerun = int(args.rerun) if args.rerun and int(args.rerun) > 0 else 1

    if args.driver is None or args.driver == "chrome":
        driver = Driver.CHROME
    elif args.driver == "firefox":
        driver = Driver.FIREFOX
    else:
        raise Exception("Unsupported driver type!")

    return (
        ArchiverSettings(
            url=shlex.split(args.url)[0],
            output_dir=args.output_dir,
            cookie_path=args.cookie_path,
            max_posts=args.max_posts,
            headless=(not args.not_headless),
            driver=driver,
            members=MembersPostType.from_str(args.members) if args.members else None,
            profile_dir=args.profile_dir,
            profile_name=args.profile_name,
            binary_override=args.binary_override,
            save_comments_types=(
                set([CommentType.from_str(ty) for ty in args.save_comments])
                if args.save_comments
                else set()
            ),
            max_comments=args.max_comments,
            take_screenshots=args.take_screenshots,
            skip_existing=args.skip_existing,
        ),
        rerun,
    )
