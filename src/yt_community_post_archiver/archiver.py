#!/usr/bin/python

import os
import signal
import sys
import time
import traceback
from pathlib import Path

from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import MoveTargetOutOfBoundsException

from yt_community_post_archiver.arguments import ArchiverSettings, get_settings
from yt_community_post_archiver.cookies import parse_cookies
from yt_community_post_archiver.helpers import (
    LOAD_SLEEP_SECS,
    Driver,
    close_current_tab,
    get_post_link,
    init_driver,
)
from yt_community_post_archiver.post import get_post_id
from yt_community_post_archiver.post_builder import PostBuilder, get_true_comment_count


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
            # If not headless, this might need to be tweaked.
            height = 1080

        self.driver = init_driver(
            settings.driver,
            settings.headless,
            settings.profile_dir,
            settings.profile_name,
            width,
            height,
        )
        self.driver_type = settings.driver

        def signal_handler(_sig_num, _frame):
            print("interrupt signal sent, halting...")
            self.driver.quit()
            sys.exit(1)

        signal.signal(signal.SIGINT, signal_handler)

        self.driver.set_window_size(width, height)  # just in case it wasn't set

        # Make sure the output directory exists... if not, then try and make it.
        output_dir = settings.output_dir or "archive-output"
        Path(os.path.abspath(output_dir)).mkdir(parents=True, exist_ok=True)

        self.cookie_path = settings.cookie_path
        self.url = settings.url
        self.output_dir = output_dir
        self.seen = set()
        self.max_posts = settings.max_posts
        self.members = settings.members
        self.skip_existing = settings.skip_existing
        self.take_screenshots = settings.take_screenshots
        self.save_comments_types = settings.save_comments_types
        self.max_comments = settings.max_comments

        # NB: DO NOT TRY AND RE-USE THE ACTIONCHAINS FOR OTHER TABS.
        # This will cause an exception as the ActionChains becomes invalid, for
        # whatever reason, if it is used in a new tab.
        self.action = ActionChains(self.driver)

    def find_posts(self) -> list[tuple[WebElement, str]]:
        posts = []

        for potential_post in self.driver.find_elements(By.ID, "post"):
            post_link = get_post_link(potential_post)
            if post_link is None:
                continue

            url = post_link.get_attribute("href")
            if url is None or url in self.seen:
                continue

            # print((potential_post, url))
            posts.append((potential_post, url))

        return posts

    def handle_post(self, post: WebElement, url: str):
        """
        Try to obtain and process a post. This will retry internally up to 5 times.
        """

        MAX_ATTEMPTS = 5
        attempts = 0

        while True:
            try:
                self.action.scroll_to_element(post).perform()
                self.seen.add(url)
                post_builder = PostBuilder(
                    driver=self.driver,
                    take_screenshots=self.take_screenshots,
                    post=post,
                    url=url,
                    output_dir=self.output_dir,
                    members=self.members,
                    save_comments_types=self.save_comments_types,
                    max_comments=self.max_comments,
                )
                post_builder.process_post()
                break
            except SystemExit:
                raise SystemExit
            except MoveTargetOutOfBoundsException as ex:
                match self.driver_type:
                    case Driver.CHROME:
                        attempts += 1

                        if attempts == MAX_ATTEMPTS:
                            raise ex

                        time.sleep(1)
                    case Driver.FIREFOX:
                        # See https://stackoverflow.com/questions/44777053/selenium-movetargetoutofboundsexception-with-firefox
                        self.driver.execute_script("window.scrollBy(0, 100);")

            except Exception as ex:
                attempts += 1

                if attempts == MAX_ATTEMPTS:
                    raise ex

                time.sleep(1)

    def at_max_posts(self) -> bool:
        return self.max_posts is not None and len(self.seen) >= self.max_posts

    def could_scroll(self) -> bool:
        """
        Try and scroll. If we should no longer scroll, this will return False.

        This will internally try up to 3 times.
        """

        MAX_ATTEMPTS = 3
        scroll_attempts = 0
        while True:
            try:
                # Check the current URL isn't a post. If it is, try closing the current tab;
                # if no tab is left, the root URL was a post, so halt.
                if get_true_comment_count(self.driver) is not None:
                    if not close_current_tab(self.driver):
                        return False

                self.driver.execute_script("window.scrollBy(0, 500);")
                return True
            except SystemExit:
                raise SystemExit
            except Exception as ex:
                scroll_attempts += 1
                if scroll_attempts == MAX_ATTEMPTS:
                    raise ex

    def scrape(self):
        # Could use a scrollbar height check instead but idk why but that was flaky sometimes.
        MAX_SAME_SEEN = 30

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
                posts = self.find_posts()
                for post, url in posts:
                    if self.at_max_posts():
                        print(f"Hit maximum posts ({self.max_posts}). Halting.")
                        return

                    if not self.should_skip_post(url) and url not in self.seen:
                        self.handle_post(post, url)
                    else:
                        print(f"Skipping `{url}` as it already exists.")

                if not self.could_scroll():
                    break

                time.sleep(LOAD_SLEEP_SECS)
                new_seen = len(self.seen)
                if num_seen == new_seen:
                    same_seen += 1
                else:
                    same_seen = 0

                if same_seen >= MAX_SAME_SEEN:
                    break

                num_seen = new_seen
        except SystemExit:
            raise SystemExit
        except Exception:
            print("Encountered a fatal error:")
            traceback.print_exc()
            self.driver.quit()
            sys.exit(1)

    def should_skip_post(self, url: str) -> bool:
        """
        If we have skip_existing set, then we want to skip posts if the path already exists.
        """

        if not self.skip_existing:
            return False

        post_id = get_post_id(url)
        post_output_dir = os.path.join(self.output_dir, post_id)

        return Path(post_output_dir).exists()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.driver.quit()


def main():
    (settings, rerun) = get_settings()

    try:
        if rerun == 1:
            print(f"Running the archiver on `{settings.url}`...")
        else:
            print(f"Running the archiver {rerun} times on `{settings.url}`...")
        for i in range(rerun):
            with Archiver(settings) as archiver:
                if rerun > 1:
                    print(f"===== Run {i + 1} ======")
                archiver.scrape()
        print("Done!")
    except SystemExit as sys_ex:
        sys.exit(sys_ex.code)
    except Exception:
        print("Encountered a fatal error:")
        traceback.print_exc()
        sys.exit(1)
