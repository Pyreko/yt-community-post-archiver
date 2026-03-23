import importlib.util
from pathlib import Path


def _load_module(name: str, path: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None
    assert spec.loader is not None

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_parse_cookies_supports_httponly_prefix(tmp_path: Path):
    cookies_module = _load_module(
        "cookies_module", "src/yt_community_post_archiver/cookies.py"
    )

    cookie_file = tmp_path / "cookies.txt"
    cookie_file.write_text(
        "# Netscape HTTP Cookie File\n"
        "#HttpOnly_.youtube.com\tTRUE\t/\tTRUE\t2147483647\tSID\tabc\n"
        ".youtube.com\tTRUE\t/\tTRUE\t2147483647\tSAPISID\tdef\n"
    )

    cookies = cookies_module.parse_cookies(cookie_file)

    assert len(cookies) == 2
    assert cookies[0].domain == ".youtube.com"
    assert cookies[0].httpOnly is True
    assert cookies[0].secure is True
    assert cookies[0].name == "SID"
