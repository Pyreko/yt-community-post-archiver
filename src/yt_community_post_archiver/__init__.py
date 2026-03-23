from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("yt-community-post-archiver")
except PackageNotFoundError:
    __version__ = "unknown"

from yt_community_post_archiver.archiver import main

if __name__ == "__main__":
    main()
