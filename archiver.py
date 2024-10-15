#!/usr/bin/python

from pathlib import Path
import time
from typing import List, Tuple
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
import os
import traceback
from arguments import ArchiverSettings, get_settings
from post import get_post_id
from cookies import parse_cookies
import signal
import sys
from selenium.webdriver.common.action_chains import ActionChains
from helpers import (
    LOAD_SLEEP_SECS,
    init_driver,
    get_post_link,
)
from post_builder import PostBuilder


class Archiver:
    """
    The main archiver "task"; this handles the overall job of archiving community posts from a URL.
    """

    def __init__(self, settings: ArchiverSettings) -> None:
        width = 1920

        if settings.headless and settings.take_screenshots:
            # I found these good settings for taking screenshots
            height = 1920
        else:
            height = 1080
            # If not headless, this might need to be tweaked.

        self.driver = init_driver(
            settings.driver,
            settings.headless,
            settings.profile_dir,
            settings.profile_name,
            width,
            height,
        )

        def signal_handler(sig_num, frame):
            self.driver.quit()
            sys.exit(1)

        signal.signal(signal.SIGINT, signal_handler)

        self.driver.set_window_size(width, height)  # just in case it wasn't set

        # Make sure the output directory exists... if not, then try and make it.
        output_dir = settings.output_dir or "archive-output"
        if settings.output_dir is not None:
            Path(output_dir).mkdir(parents=True, exist_ok=True)

        self.cookie_path = settings.cookie_path
        self.url = settings.url
        self.output_dir = output_dir
        self.seen = set()
        self.max_posts = settings.max_posts
        self.members_only = settings.members_only
        self.skip_existing = settings.skip_existing
        self.take_screenshots = settings.take_screenshots
        self.action = ActionChains(self.driver)

    def find_posts(self) -> List[Tuple[WebElement, str]]:
        posts = []

        for potential_post in self.driver.find_elements(By.ID, "post"):
            post_link = get_post_link(potential_post)
            if post_link is None:
                continue

            url = post_link.get_attribute("href")
            if url is None or url in self.seen:
                continue

            posts.append((potential_post, url))

        return posts

    def handle_post(self, post: WebElement, url: str):
        post_builder = PostBuilder(
            driver=self.driver,
            take_screenshots=self.take_screenshots,
            post=post,
            url=url,
            output_dir=self.output_dir,
            action=self.action,
            members_only=self.members_only,
        )
        post_builder.process_post()

    def at_max_posts(self) -> bool:
        return self.max_posts is not None and len(self.seen) >= self.max_posts

    def scrape(self):
        MAX_SAME_SEEN = 120

        try:
            self.driver.get(self.url)

            # Validate that the cookies path is valid if set, then set cookies.
            if self.cookie_path is not None:
                if os.path.exists(self.cookie_path):
                    time.sleep(LOAD_SLEEP_SECS)

                    path = Path(self.cookie_path)
                    cookies = parse_cookies(path)

                    for cookie in cookies:
                        if cookie.domain in self.url:
                            self.driver.add_cookie(cookie.__dict__)

                    self.driver.refresh()
                else:
                    raise Exception(
                        f"Cookies path at {self.cookie_path} doesn't exist!"
                    )

            time.sleep(LOAD_SLEEP_SECS)
            num_seen = len(self.seen)
            same_seen = 0

            while True:
                try:
                    posts = self.find_posts()
                    for post, url in posts:

                        if not self.should_skip_post(url):
                            self.action.move_to_element(post).perform()
                            self.handle_post(post, url)
                        else:
                            print(f"Skipping `{url}` as it already exists.")

                        self.seen.add(url)

                        if self.at_max_posts():
                            print(f"Hit maximum posts ({self.max_posts}). Halting.")
                            return
                except:
                    continue

                self.driver.execute_script("window.scrollBy(0, 500);")
                time.sleep(LOAD_SLEEP_SECS)

                new_seen = len(self.seen)
                if num_seen == new_seen:
                    same_seen += 1
                else:
                    same_seen = 0

                if same_seen >= MAX_SAME_SEEN:
                    break

                num_seen = new_seen

        except Exception:
            print("Encountered a fatal error:")
            traceback.print_exc()

    def should_skip_post(self, url: str) -> bool:
        """
        If we have skip_existing set, then we want to skip posts if the path already exists.
        """

        if not self.skip_existing:
            return False

        id = get_post_id(url)
        dir = os.path.join(self.output_dir, id)

        return Path(dir).exists()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.driver.quit()


def main():
    (settings, rerun) = get_settings()

    try:
        print(f"Running the archiver {rerun} time(s) on `{settings.url}`...")
        for i in range(rerun):
            with Archiver(settings) as archiver:
                if rerun > 1:
                    print(f"===== Run {i + 1} ======")
                archiver.scrape()
    finally:
        print("Done!")


if __name__ == "__main__":
    main()
