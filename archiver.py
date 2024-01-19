#!/usr/bin/python

from dataclasses import dataclass
import time
from typing import List, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
import argparse
import json
import os
import requests


@dataclass
class Post:
    url: str
    text: str
    images: List[str]

    def record(self, output_dir: str):
        id = self.url.split("/")[-1]
        dir = os.path.join(output_dir, id)

        print(f"Trying to save `{id}` at `{dir}`...")

        text_obj = {"url": self.url, "text": self.text, "image_urls": self.images}

        if not os.path.exists(dir):
            try:
                os.mkdir(dir)
            except:
                print(f"err: couldn't make directory at {dir}")
                return

        data_path = os.path.join(dir, "post.txt")
        with open(data_path, "w", encoding="utf-8") as f:
            json.dump(text_obj, f, ensure_ascii=False, indent=4)

        for itx, image in enumerate(self.images):
            img_data = requests.get(image).content
            img_name = f"{id}-{itx}.png"
            img_path = os.path.join(dir, img_name)
            with open(img_path, "wb") as f:
                f.write(img_data)


class Archiver:
    def __init__(self, url: str, output_dir: Optional[str]) -> None:
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--start-maximized")

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
        url = next(filter(self.filter_post_href, post.find_elements(By.TAG_NAME, "a")), None).get_attribute("href")
        if url in self.seen:
            return

        # Hit "Read more" for any visible posts.
        read_more_buttons = post.find_elements(By.CLASS_NAME, "more-button")
        if len(read_more_buttons) > 0:
            read_more_button = read_more_buttons[0]
            if read_more_button.is_displayed() and read_more_button.is_enabled():
                read_more_button.click()
            else:
                return

        # Get the URL, the text, and any images
        text = post.find_element(By.ID, "content").text
        images = [
            url.split("=")[0] + "=s1080"
            for url in filter(
                lambda img: img is not None,
                (img.get_attribute("src") for img in post.find_elements(By.TAG_NAME, "img")),
            )
        ]

        # We skip the first image since that's always the profile picture.
        post = Post(url=url, text=text, images=images[1:])
        self.seen.add(url)
        post.record(self.output_dir)

    def scrape(self):
        LOAD_SLEEP_SECS = 3
        MAX_SAME_SEEN = 30

        try:
            self.driver.get(self.url)
            time.sleep(LOAD_SLEEP_SECS)

            num_seen = len(self.seen)
            same_seen = 0

            while True:
                posts = self.find_posts()
                for post in posts:
                    self.handle_post(post)

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

        except Exception as err:
            print(f"Encountered an error: {err}")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.driver.quit()


def main():
    parser = argparse.ArgumentParser(description="Archives YouTube community posts.")
    parser.add_argument("url", type=str, help="The URL to grab posts from.")
    parser.add_argument("-o", "--output_dir", type=str, required=False, help="The directory to save to.")

    args = parser.parse_args()
    url = args.url
    output_dir = args.output_dir

    try:
        with Archiver(url, output_dir) as archiver:
            archiver.scrape()
    finally:
        print("Done!")


if __name__ == "__main__":
    main()
