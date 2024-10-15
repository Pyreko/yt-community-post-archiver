from dataclasses import dataclass
import os
import time
from typing import List, Optional, Union
from selenium.webdriver.chrome.webdriver import WebDriver as ChromeWebDriver
from selenium.webdriver.firefox.webdriver import WebDriver as FirefoxWebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.by import By
from helpers import (
    LOAD_SLEEP_SECS,
    close_current_tab,
    find_post_element,
    get_post_link,
)
from datetime import timezone, datetime
import io
from PIL import Image
from selenium.webdriver.common.action_chains import ActionChains
from post import Poll, PollEntry, Post, get_post_id


def _is_members_post(post: WebElement) -> bool:
    return bool(post.find_elements(By.CLASS_NAME, "ytd-sponsors-only-badge-renderer"))


def get_true_comment_count(
    driver: Union[ChromeWebDriver, FirefoxWebDriver],
) -> Optional[str]:
    comment_elements = driver.find_elements(By.TAG_NAME, "ytd-comments")
    if comment_elements:
        count = comment_elements[0].find_elements(By.ID, "count")
        if count:
            return count[0].text.split()[0]

    return None


def _get_likes(post: WebElement) -> Optional[int]:
    thumbs_elements = post.find_elements(By.ID, "vote-count-middle")
    return thumbs_elements[0].text if thumbs_elements else None


def _get_links(post: WebElement) -> List[str]:
    # Filter out the first link as it will always be the channel.
    return list(
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


def _get_images(post: WebElement) -> List[str]:
    # To get all images, we may need to load them all. Look for a button indicating multiple images first, click it
    # until it disappears, at which point all images should be loaded.
    img_buttons = post.find_elements(By.ID, "right-arrow")
    for img_button in img_buttons:
        if "ytd-post-multi-image-renderer" in img_button.get_attribute("class"):
            while img_button.is_displayed():
                img_button.click()

    return [
        url.split("=")[0] + "=s3840"
        for url in filter(
            lambda img: img is not None,
            (
                img.get_attribute("src")
                for img in post.find_elements(By.TAG_NAME, "img")
            ),
        )
    ]


def _get_approximate_num_comments(post: WebElement) -> Optional[int]:
    comment_elements = post.find_elements(By.ID, "reply-button-end")
    return (
        comment_elements[0].text.strip().split("\n")[0].strip()
        if comment_elements
        else None
    )


def _get_text(post: WebElement) -> str:
    text_elements = post.find_elements(By.ID, "content")
    if not text_elements:
        return
    return text_elements[0].get_attribute("innerText") or ""


def _get_poll(
    post: WebElement, driver: Union[ChromeWebDriver, FirefoxWebDriver]
) -> Optional[Poll]:
    poll_elements = post.find_elements(By.CLASS_NAME, "choice-info")
    if poll_elements:
        # We want to click on the poll if we are signed in, and can't see a percentage.
        poll_reclick = None
        if driver.find_elements(By.ID, "avatar-btn"):
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

            return Poll(poll_entries, poll_total_votes)

    return None


@dataclass
class PostBuilder:
    driver: Union[ChromeWebDriver, FirefoxWebDriver]
    post: WebElement
    url: str
    take_screenshots: bool
    output_dir: str
    members_only: bool

    def __open_post_in_tab(self, url: str) -> Optional[WebElement]:
        self.driver.switch_to.new_window("tab")
        self.driver.get(url)
        time.sleep(LOAD_SLEEP_SECS)

        return find_post_element(self.driver)

    def __take_screenshots(self, new_tab_post: Optional[WebElement]):
        if new_tab_post is not None:
            more = new_tab_post.find_elements(By.CLASS_NAME, "more-button")
            if more:
                # NB: DO NOT TRY AND RE-USE THE ACTIONCHAINS FROM THE ORIGINAL ARCHIVER!
                # This will cause an exception as the ActionChains becomes... invalid, for
                # whatever reason, if it is used in a new tab.
                action = ActionChains(self.driver)
                action.move_to_element(more[0])
                if more[0].is_displayed():
                    more[0].click()

            id = get_post_id(self.url)
            screenshot = os.path.join(self.output_dir, id, "screenshot.png")
            img_bytes = new_tab_post.screenshot_as_png
            img = Image.open(io.BytesIO(img_bytes))
            img.save(screenshot)

    def process_post(self) -> Optional[Post]:
        post = self.post
        url = self.url

        print(f"Handling `{url}`")

        post_link = get_post_link(post)
        if post_link is None:
            return

        relative_date = post_link.text
        is_members = _is_members_post(post)

        if self.members_only and (not is_members):
            print(
                "Skipping as it is not a members post and members-only is configured."
            )
            return

        links = _get_links(post)
        images = _get_images(post)
        approximate_num_comments = _get_approximate_num_comments(post)
        num_thumbs_up = _get_likes(post)
        text = _get_text(post)
        poll = _get_poll(post, self.driver)

        # The following block may require opening things in a new tab.
        num_comments = get_true_comment_count(self.driver)
        new_tab_post: Union[None, WebElement] = None

        # If there are no comments then we must not be in the post link itself.
        if num_comments is None:
            new_tab_post = self.__open_post_in_tab(url)
            num_comments = get_true_comment_count(self.driver)
        else:
            new_tab_post = post

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
            when_archived=str(datetime.now(tz=timezone.utc)),
        )

        post.save(self.output_dir)

        if self.take_screenshots:
            self.__take_screenshots(new_tab_post)

        if new_tab_post is not None:
            close_current_tab(self.driver)
