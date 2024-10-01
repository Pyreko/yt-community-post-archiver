#!/usr/bin/python

from enum import Enum
from pathlib import Path
import shlex
import time
from typing import List, Optional, Tuple, TypeVar
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
import argparse
import os
import traceback
from arguments import get_args
from post import Poll, Post, PollEntry
from cookies import parse_cookies
import signal
import sys
from selenium.webdriver.common.action_chains import ActionChains
from datetime import timezone, datetime


class Driver(Enum):
    """
    The backing browser to use for scraping.
    """

    FIREFOX = 1
    CHROME = 2


class Archiver:
    def __init__(
        self,
        url: str,
        output_dir: Optional[str],
        members_only: bool,
        headless: bool,
        cookie_path: Optional[str] = None,
        max_posts: Optional[str] = None,
        profile_dir: Optional[str] = None,
        profile_name: Optional[str] = None,
        driver: Driver = Driver.CHROME,
    ) -> None:
        WIDTH = 1920
        HEIGHT = 1080

        match driver:
            case Driver.CHROME:
                options = webdriver.ChromeOptions()
                options.add_argument(f"--window-size={WIDTH},{HEIGHT}")
                options.add_argument("--disable-gpu")

                if headless:
                    options.add_argument("--headless")

                if profile_dir:
                    profile_name = (
                        profile_name if profile_name is not None else "Default"
                    )

                    options.add_argument(f"--user-data-dir={profile_dir}")
                    options.add_argument(f"--profile-directory={profile_name}")
            case Driver.FIREFOX:
                options = webdriver.FirefoxOptions()
                options.add_argument(f"-width={WIDTH}")
                options.add_argument(f"-height={HEIGHT}")

                if headless:
                    options.add_argument("-headless")

        match driver:
            case Driver.CHROME:
                self.driver = webdriver.Chrome(options)
            case Driver.FIREFOX:
                self.driver = webdriver.Firefox(options)

        def signal_handler(sig, frame):
            self.driver.quit()
            sys.exit(1)

        signal.signal(signal.SIGINT, signal_handler)

        self.driver.set_window_size(WIDTH, HEIGHT)  # just in case it wasn't set

        # Make sure the output directory exists... if not, then try and make it.
        output_dir = "archive-output" if output_dir is None else output_dir
        if output_dir is not None:
            if not os.path.isdir(output_dir):
                os.mkdir(output_dir)

        self.cookie_path = cookie_path
        self.url = url
        self.output_dir = output_dir
        self.seen = set()
        self.max_posts = max_posts
        self.members_only = members_only

    def filter_post_href(self, candidate: WebElement) -> bool:
        href = candidate.get_attribute("href")
        if href is not None:
            return "https://www.youtube.com/post/" in href

        return False

    def find_posts(self) -> List[Tuple[WebElement, str]]:
        posts = []

        for potential_post in self.driver.find_elements(By.ID, "post"):
            post_link = next(
                filter(
                    self.filter_post_href,
                    potential_post.find_elements(By.TAG_NAME, "a"),
                ),
                None,
            )
            url = post_link.get_attribute("href")

            if url is None:
                continue

            if url in self.seen:
                continue

            posts.append((potential_post, url))

        return posts

    def handle_post(self, post: WebElement) -> None:
        post_link = next(
            filter(self.filter_post_href, post.find_elements(By.TAG_NAME, "a")), None
        )

        url = post_link.get_attribute("href")

        if url is None:
            return

        relative_date = post_link.text

        is_members = bool(
            post.find_elements(By.CLASS_NAME, "ytd-sponsors-only-badge-renderer")
        )

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

        comment_elements = post.find_elements(By.CSS_SELECTOR, "[aria-label=Comment]")
        num_comments = comment_elements[0].text if comment_elements else None

        thumbs_elements = post.find_elements(By.ID, "vote-count-middle")
        num_thumbs_up = thumbs_elements[0].text if thumbs_elements else None

        text_elements = post.find_elements(By.ID, "content")
        if not text_elements:
            return
        text = text_elements[0].get_attribute("innerText")

        poll_elements = post.find_elements(By.CLASS_NAME, "choice-info")

        # We want to click on the poll if we are signed in, and can't see a percentage.
        poll_reclick = None
        if self.driver.find_elements(By.ID, "avatar-btn"):
            if poll_elements:
                for p in poll_elements:
                    percentage = p.find_elements(By.CLASS_NAME, "vote-percentage")
                    if len(percentage) > 0:
                        percentage_text = percentage[0].get_attribute("innerText")
                        if len(percentage_text) == 0:
                            # Try and click on the entry.
                            poll_reclick = p
                            p.click()
                            time.sleep(0.5)
                            break

        poll_elements = post.find_elements(By.CLASS_NAME, "choice-info")
        if poll_elements:
            poll_entries = [
                PollEntry(p)
                for p in filter(
                    lambda p: p is not None,
                    (p.get_attribute("innerText") for p in poll_elements),
                )
            ]

            if poll_reclick is not None:
                try:
                    poll_reclick.click()
                finally:
                    poll_reclick = None

            poll_total_votes_ele = post.find_elements(By.ID, "vote-info")
            if poll_total_votes_ele:
                poll_total_votes = poll_total_votes_ele[0].text
            else:
                poll_total_votes = None

            poll = Poll(poll_entries, poll_total_votes)
        else:
            poll = None

        # We skip the first image since that's always the profile picture.
        current_time = datetime.now(tz=timezone.utc)
        post = Post(
            url=url,
            text=text,
            links=links,
            images=images[1:],
            is_members=is_members,
            relative_date=relative_date,
            num_comments=num_comments,
            num_thumbs_up=num_thumbs_up,
            poll=poll,
            when_archived=str(current_time),
        )

        print(f"Handling {url}")
        post.save(self.output_dir)

    def at_max_posts(self) -> bool:
        return self.max_posts is not None and len(self.seen) >= self.max_posts

    def scrape(self):
        LOAD_SLEEP_SECS = 1
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
            action = ActionChains(self.driver)

            MAX_WRONG_URL = 5
            wrong_url = 0

            while True:
                # Assert we're on the passed-in URL... if not, refresh up to 5 times and try again.
                if self.driver.current_url != self.url:
                    wrong_url += 1

                    if wrong_url >= MAX_WRONG_URL:
                        print(
                            f"keep seeing the wrong URL (seeing `{self.driver.current_url}`, want `{self.url}`), halting"
                        )
                        return
                    else:
                        self.driver.get(self.url)
                        time.sleep(LOAD_SLEEP_SECS)
                        continue
                else:
                    wrong_url = 0

                try:
                    posts = self.find_posts()
                    for post, url in posts:
                        action.move_to_element(post).perform()
                        self.handle_post(post)

                        self.seen.add(url)

                        if self.at_max_posts():
                            print(f"Hit maximum posts ({self.max_posts}). Halting.")
                            return
                except:
                    continue

                self.driver.execute_script("window.scrollBy(0, 500);")
                # self.driver.execute_script("window.scrollBy(0, 100000);")
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

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.driver.quit()


def main():
    args = get_args()

    # Hack to handle backslashes.
    url = shlex.split(args.url)[0]
    output_dir = args.output_dir
    cookie_path = args.cookie_path
    rerun = int(args.rerun) if args.rerun and int(args.rerun) > 0 else 1
    max_posts = int(args.max_posts) if args.max_posts else None
    members_only = bool(args.members_only)
    profile_dir = args.profile_dir
    profile_name = args.profile_name
    headless = not (args.not_headless)

    if args.driver is None or args.driver == "chrome":
        driver = Driver.CHROME
    elif args.driver == "firefox":
        driver = Driver.FIREFOX
    else:
        raise Exception("Unsupported driver type!")

    try:
        print(f"Running the archiver {rerun} time(s) on `{url}`...")
        for i in range(rerun):
            with Archiver(
                url=url,
                output_dir=output_dir,
                cookie_path=cookie_path,
                max_posts=max_posts,
                headless=headless,
                driver=driver,
                members_only=members_only,
                profile_dir=profile_dir,
                profile_name=profile_name,
            ) as archiver:
                if rerun > 1:
                    print(f"===== Run {i + 1} ======")
                archiver.scrape()
    finally:
        print("Done!")


if __name__ == "__main__":
    main()
