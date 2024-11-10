from dataclasses import dataclass
from pathlib import Path


@dataclass
class Cookie:
    """
    A cookie file entry. The names map exactly the to the dictionaries
    that Selenium expects, so you can just call `cookie.__dict__`.
    """

    domain: str
    # include_subdomains: bool
    path: str
    httpOnly: bool
    expiry: int
    name: str
    value: str


def __to_bool(val: str) -> bool:
    return True if val.lower() == "true" else False


def parse_cookies(cookies_file: Path) -> list[Cookie]:
    """
    Parses the given `cookies_file` path following the spec as defined by
    https://everything.curl.dev/http/cookies/fileformat, and
    returns a list of cookies. If any fail, it will just silently just
    skip it.
    """

    cookie_list = []

    with open(cookies_file) as f:
        for line in f:
            line = line.lstrip()

            # Ignore empty lines or comments.
            if len(line) == 0 or line.startswith("#"):
                continue

            # Ensure files end with newlines.
            if not line.endswith("\n"):
                continue

            fields = line.rstrip().split("\t")

            if len(fields) != 7:
                continue

            cookie = Cookie(
                domain=fields[0],
                path=fields[2],
                httpOnly=__to_bool(fields[3]),
                expiry=int(fields[4]),
                name=fields[5],
                value=fields[6],
            )
            cookie_list.append(cookie)

    return cookie_list
