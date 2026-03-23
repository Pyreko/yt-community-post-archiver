import importlib.util
import sys
import types
from enum import Enum


def _load_module(name: str, path: str):
    package_module = types.ModuleType("yt_community_post_archiver")
    package_module.__path__ = []  # type: ignore[attr-defined]
    package_module.__version__ = "0.0.0"
    sys.modules["yt_community_post_archiver"] = package_module

    helpers_module = types.ModuleType("yt_community_post_archiver.helpers")

    class Driver(Enum):
        FIREFOX = 1
        CHROME = 2

    helpers_module.Driver = Driver
    sys.modules["yt_community_post_archiver.helpers"] = helpers_module

    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None
    assert spec.loader is not None

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_cookie_alias_sets_cookie_path(monkeypatch):
    arguments_module = _load_module(
        "arguments_module", "src/yt_community_post_archiver/arguments.py"
    )

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "yt-community-post-archiver",
            "https://www.youtube.com/@example/posts",
            "--cookie",
            "/tmp/cookies.txt",
        ],
    )

    (settings, _) = arguments_module.get_settings()
    assert settings.cookie_path == "/tmp/cookies.txt"


def test_cookie_path_option_sets_cookie_path(monkeypatch):
    arguments_module = _load_module(
        "arguments_module", "src/yt_community_post_archiver/arguments.py"
    )

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "yt-community-post-archiver",
            "https://www.youtube.com/@example/posts",
            "--cookie-path",
            "/tmp/cookies.txt",
        ],
    )

    (settings, _) = arguments_module.get_settings()
    assert settings.cookie_path == "/tmp/cookies.txt"
