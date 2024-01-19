#!/usr/bin/python

from dataclasses import dataclass
import time
from typing import List, Optional, TypeVar
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
import argparse
import json
import os
import requests
import traceback


@dataclass
class Post:
    url: str
    text: str
    images: List[str]
    is_members: bool
    relative_date: str
    num_comments: Optional[str]
    num_thumbs_up: Optional[str]

    def save(self, output_dir: str):
        id = self.url.split("/")[-1]
        dir = os.path.join(output_dir, id)

        # print(f"Trying to save `{id}` at `{dir}`...")

        if not os.path.exists(dir):
            try:
                os.mkdir(dir)
            except:
                print(f"err: couldn't make directory at {dir}")
                return

        try:
            data_path = os.path.join(dir, "post.txt")
            with open(data_path, "w", encoding="utf-8") as f:
                json.dump(self.__dict__, f, ensure_ascii=False, indent=4)
        except:
            print(f"err: couldn't save data dump at {data_path}")

        for itx, image in enumerate(self.images):
            try:
                img_name = f"{id}-{itx}.png"
                img_path = os.path.join(dir, img_name)

                if not os.path.exists(img_path):
                    img_data = requests.get(image).content
                    with open(img_path, "wb") as f:
                        f.write(img_data)
                else:
                    # print(f"Skipping saving image at {img_path} as it's already been saved.")
                    pass
            except:
                print(f"err: couldn't save image `{image}` dump at {img_path}")


class Archiver:
    def __init__(
        self,
        url: str,
        output_dir: Optional[str],
        profile_dir: Optional[str] = None,
    ) -> None:
        options = webdriver.ChromeOptions()
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--start-maximized")

        if profile_dir is not None:
            split_dir = profile_dir.rsplit("/", 1)
            user_data_dir = split_dir[0]
            profile_dir = split_dir[1]

            options.add_argument(f"--user-data-dir={user_data_dir}")
            options.add_argument(f"--profile-directory={profile_dir}")
        else:
            # For some reason this doesn't work if I set a profile...????
            options.add_argument("--headless")

        # Make sure the output directory exists... if not, then try and make it.
        output_dir = "archive-output" if output_dir is None else output_dir
        if output_dir is not None:
            if not os.path.isdir(output_dir):
                os.mkdir(output_dir)

        self.driver = webdriver.Chrome(options)
        self.url = url
        self.output_dir = output_dir
        self.seen = set()

    def filter_post_href(self, candidate: WebElement) -> bool:
        href = candidate.get_attribute("href")
        if href is not None:
            return "https://www.youtube.com/post/" in href

        return False

    def find_posts(self) -> List[WebElement]:
        posts = self.driver.find_elements(By.ID, "post")
        return posts

    def handle_post(self, post: WebElement) -> None:
        post_link = next(filter(self.filter_post_href, post.find_elements(By.TAG_NAME, "a")), None)

        url = post_link.get_attribute("href")
        if url in self.seen:
            return

        relative_date = post_link.text

        is_members = bool(post.find_elements(By.CLASS_NAME, "ytd-sponsors-only-badge-renderer"))

        images = [
            url.split("=")[0] + "=s3840"
            for url in filter(
                lambda img: img is not None,
                (img.get_attribute("src") for img in post.find_elements(By.TAG_NAME, "img")),
            )
        ]

        comment_elements = post.find_elements(By.CSS_SELECTOR, "[aria-label=Comment]")
        num_comments = comment_elements[0].text if comment_elements else None

        thumbs_elements = post.find_elements(By.ID, "vote-count-middle")
        num_thumbs_up = thumbs_elements[0].text if thumbs_elements else None

        # This may need retries due to the above click.
        try:
            text_elements = post.find_elements(By.ID, "content")
            if not text_elements:
                return
        except:
            pass

        text = text_elements[0].get_attribute("innerText")

        # We skip the first image since that's always the profile picture.
        post = Post(
            url=url,
            text=text,
            images=images[1:],
            is_members=is_members,
            relative_date=relative_date,
            num_comments=num_comments,
            num_thumbs_up=num_thumbs_up,
        )
        self.seen.add(url)
        post.save(self.output_dir)

    def scrape(self):
        LOAD_SLEEP_SECS = 3
        MAX_SAME_SEEN = 60

        try:
            self.driver.get(self.url)
            time.sleep(LOAD_SLEEP_SECS)

            num_seen = len(self.seen)
            same_seen = 0

            while True:
                try:
                    posts = self.find_posts()
                    for post in posts:
                        self.handle_post(post)
                except:
                    continue

                self.driver.execute_script("window.scrollBy(0, 250);")
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
    parser = argparse.ArgumentParser(description="Archives YouTube community posts.")
    parser.add_argument("url", type=str, help="The URL to try and grab posts from.")
    parser.add_argument("-o", "--output_dir", type=str, required=False, help="The directory to save to.")
    parser.add_argument("-p", "--profile_dir", type=str, required=False, help="The path to an existing Chrome profile.")
    parser.add_argument(
        "-r", "--rerun", type=str, required=False, help="How many times to rerun the archiver. Should be at least 1."
    )

    args = parser.parse_args()
    url = args.url
    output_dir = args.output_dir
    profile_dir = args.profile_dir
    rerun = int(args.rerun) if args.rerun and int(args.rerun) > 0 else 1

    try:
        print(f"Running the archiver {rerun} time(s).")
        for i in range(rerun):
            print(f"===== Run {i + 1} ======")
            with Archiver(url, output_dir, profile_dir) as archiver:
                archiver.scrape()
    finally:
        print("Done!")


if __name__ == "__main__":
    main()
