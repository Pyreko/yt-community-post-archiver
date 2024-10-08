#!/usr/bin/python

from pathlib import Path
import time
from typing import List, Optional, Tuple
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
import os
import traceback
from arguments import ArchiverSettings, get_settings
from post import Post, get_post_id
from cookies import parse_cookies
import signal
import sys
from selenium.webdriver.common.action_chains import ActionChains
from datetime import timezone, datetime
from helpers import (
    find_post_element,
    get_comment_count,
    get_poll,
    init_driver,
    get_post_link,
    is_members_post,
)
import io
from PIL import Image

LOAD_SLEEP_SECS = 1


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

    def open_post_in_tab(self, url: str) -> Optional[WebElement]:
        self.driver.switch_to.new_window("tab")
        self.driver.get(url)
        time.sleep(LOAD_SLEEP_SECS)

        return find_post_element(self.driver)

    def handle_post(self, post: WebElement, url: str):
        print(f"Handling `{url}`")

        post_link = get_post_link(post)
        if post_link is None:
            return

        relative_date = post_link.text

        is_members = is_members_post(post)

        if self.members_only and (not is_members):
            # print("Skipping as it is not a members post.")
            return

        # Filter out the first link as it will always be the channel.
        links = list(
            dict.fromkeys(
                filter(
                    lambda link: link is not None,
                    (
                        link.get_attribute("href")
                        for link in post.find_elements(By.TAG_NAME, "a")
                    ),
                )
            )
        )[1:]

        # To get all images, we may need to load them all. Look for a button indicating multiple images first, click it
        # until it disappears, at which point all images should be loaded.
        img_buttons = post.find_elements(By.ID, "right-arrow")
        for img_button in img_buttons:
            if "ytd-post-multi-image-renderer" in img_button.get_attribute("class"):
                while img_button.is_displayed():
                    img_button.click()

        images = [
            url.split("=")[0] + "=s3840"
            for url in filter(
                lambda img: img is not None,
                (
                    img.get_attribute("src")
                    for img in post.find_elements(By.TAG_NAME, "img")
                ),
            )
        ]

        comment_elements = post.find_elements(By.ID, "reply-button-end")
        approximate_num_comments = (
            comment_elements[0].text.strip().split("\n")[0].strip()
            if comment_elements
            else None
        )

        thumbs_elements = post.find_elements(By.ID, "vote-count-middle")
        num_thumbs_up = thumbs_elements[0].text if thumbs_elements else None

        text_elements = post.find_elements(By.ID, "content")
        if not text_elements:
            return
        text = text_elements[0].get_attribute("innerText")

        poll = get_poll(post, self.driver)

        # The following block may require opening things in a new tab.
        num_comments = get_comment_count(self.driver)
        need_new_tab = num_comments is None
        new_tab_post = None

        if need_new_tab:
            new_tab_post = self.open_post_in_tab(url)
            num_comments = get_comment_count(self.driver)

        current_time = datetime.now(tz=timezone.utc)
        post = Post(
            url=url,
            text=text,
            links=links,
            # We skip the first image since that's always the profile picture.
            images=images[1:],
            is_members=is_members,
            relative_date=relative_date,
            approximate_num_comments=approximate_num_comments,
            num_comments=num_comments,
            num_thumbs_up=num_thumbs_up,
            poll=poll,
            when_archived=str(current_time),
        )

        post.save(self.output_dir)

        if self.take_screenshots:
            if new_tab_post is not None:
                more = new_tab_post.find_elements(By.CLASS_NAME, "more-button")
                if more:
                    self.action.move_to_element(more[0])
                    if more[0].is_displayed():
                        more[0].click()

                id = get_post_id(url)
                screenshot = os.path.join(self.output_dir, id, "screenshot.png")
                img_bytes = new_tab_post.screenshot_as_png
                img = Image.open(io.BytesIO(img_bytes))
                img.save(screenshot)

        if need_new_tab:
            self.driver.close()
            self.driver.switch_to.window(self.driver.window_handles[0])
            time.sleep(0.5)

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
