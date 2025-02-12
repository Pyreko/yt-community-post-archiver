import io
import os
import time
from dataclasses import dataclass
from datetime import UTC, datetime

from PIL import Image
from selenium.webdriver.chrome.webdriver import WebDriver as ChromeWebDriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.webdriver import WebDriver as FirefoxWebDriver
from selenium.webdriver.remote.webelement import WebElement

from yt_community_post_archiver.arguments import CommentType, MembersPostType
from yt_community_post_archiver.comment import build_comment
from yt_community_post_archiver.helpers import (
    LOAD_SLEEP_SECS,
    close_current_tab,
    find_post_element,
    get_post_link,
)
from yt_community_post_archiver.post import Poll, PollEntry, Post, get_post_id


def _is_members_post(post: WebElement) -> bool:
    return bool(post.find_elements(By.CLASS_NAME, "ytd-sponsors-only-badge-renderer"))


def get_true_comment_count(
    driver: ChromeWebDriver | FirefoxWebDriver,
) -> str | None:
    comment_elements = driver.find_elements(By.TAG_NAME, "ytd-comments")
    if comment_elements:
        count = comment_elements[0].find_elements(By.ID, "count")
        if count:
            return count[0].text.split()[0]

    return None


def _get_likes(post: WebElement) -> int | None:
    thumbs_elements = post.find_elements(By.ID, "vote-count-middle")
    return thumbs_elements[0].text if thumbs_elements else None


def _get_links(post: WebElement) -> list[str]:
    # Filter out the first link as it will always be the channel. Also filter out any accounts.google.com links.
    return list(
        dict.fromkeys(
            filter(
                lambda link: link is not None and ("accounts.google.com" not in link),
                (
                    link.get_attribute("href")
                    for link in post.find_elements(By.TAG_NAME, "a")
                ),
            )
        )
    )[1:]


def _get_images(post: WebElement) -> list[str]:
    # To get all images, we may need to load them all. Look for a button indicating multiple images first, click it
    # until it disappears, at which point all images should be loaded.
    img_buttons = post.find_elements(By.ID, "right-arrow")
    for img_button in img_buttons:
        if "ytd-post-multi-image-renderer" in img_button.get_attribute("class"):
            while img_button.is_displayed():
                img_button.click()

    return [
        # Basically replace s640 or whatever with a bigger value. 3840 seems to be ok.
        url.split("=")[0] + "=s3840"
        for url in filter(
            lambda img: img is not None,
            (
                img.get_attribute("src")
                for img in post.find_elements(By.TAG_NAME, "img")
            ),
        )
    ]


def _get_approximate_num_comments(post: WebElement) -> int | None:
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
    post: WebElement, driver: ChromeWebDriver | FirefoxWebDriver
) -> Poll | None:
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
    driver: ChromeWebDriver | FirefoxWebDriver
    post: WebElement
    url: str
    take_screenshots: bool
    output_dir: str
    members: MembersPostType | None
    save_comments_types: set[CommentType]
    max_comments: int | None

    def __open_post_in_tab(self, url: str) -> WebElement | None:
        self.driver.switch_to.new_window("tab")
        self.driver.get(url)
        time.sleep(LOAD_SLEEP_SECS)

        return find_post_element(self.driver)

    def __take_screenshots(self, new_tab_post: WebElement | None):
        if new_tab_post is None:
            return

        action = ActionChains(self.driver)
        more = new_tab_post.find_elements(By.CLASS_NAME, "more-button")
        if more:
            # NB: DO NOT TRY AND RE-USE THE ACTIONCHAINS FROM THE ORIGINAL ARCHIVER!
            # This will cause an exception as the ActionChains becomes invalid, for
            # whatever reason, if it is used in a new tab.
            if more[0].is_displayed():
                action.scroll_to_element(more[0]).perform()
                more[0].click()

        action.scroll_to_element(new_tab_post).perform()
        post_id = get_post_id(self.url)
        screenshot = os.path.join(self.output_dir, post_id, "screenshot.png")
        img_bytes = new_tab_post.screenshot_as_png
        img = Image.open(io.BytesIO(img_bytes))
        img.save(screenshot)

    def __get_comments(self):
        seen_comments = set()

        def get_link(comment: WebElement) -> str | None:
            possible_relative_date = comment.find_elements(By.ID, "published-time-text")
            if not possible_relative_date:
                return None

            possible_links = possible_relative_date[0].find_elements(By.TAG_NAME, "a")
            return possible_links[0].get_attribute("href") if possible_links else None

        def get_comment_elements() -> list[tuple[WebElement, str]]:
            prospective_comments = self.driver.find_elements(
                By.TAG_NAME, "ytd-comment-thread-renderer"
            )
            to_return = []

            for pc in prospective_comments:
                link = get_link(pc)
                if link and link not in seen_comments:
                    to_return.append((pc, link))

            return to_return

        comments = get_comment_elements()

        if not comments:
            return

        save_comments_types = self.save_comments_types
        action = ActionChains(self.driver)

        def is_creator(comment_element: WebElement) -> bool:
            return (
                CommentType.CREATOR in save_comments_types
                and comment_element.find_elements(By.ID, "author-comment-badge")
            )

        def is_hearted(comment_element: WebElement) -> bool:
            return (
                CommentType.HEARTED in save_comments_types
                and comment_element.find_elements(By.ID, "creator-heart-button")
            )

        def is_pinned(comment_element: WebElement) -> bool:
            return (
                CommentType.PINNED in save_comments_types
                and comment_element.find_elements(By.ID, "pinned-comment-badge")
            )

        def is_members(comment_element: WebElement) -> bool:
            return (
                CommentType.MEMBERS in save_comments_types
                and comment_element.find_elements(By.ID, "custom-badge")
            )

        comments_saved = 0
        no_new_comments_counter = 0

        while True:
            for comment_element, link in comments:
                if not (
                    (CommentType.ALL in save_comments_types)
                    or is_creator(comment_element)
                    or is_hearted(comment_element)
                    or is_pinned(comment_element)
                    or is_members(comment_element)
                ):
                    continue

                if (
                    self.max_comments is not None
                    and comments_saved >= self.max_comments
                ):
                    return

                action.scroll_to_element(comment_element).perform()
                seen_comments.add(link)
                comment = build_comment(comment_element, link)
                # print(comment.__dict__)
                comments_saved += 1
                comment.save(self.output_dir, self.url)

            self.driver.execute_script("window.scrollBy(0, 500);")
            time.sleep(LOAD_SLEEP_SECS)

            comments = get_comment_elements()
            if len(comments) == 0:
                no_new_comments_counter += 1

                if no_new_comments_counter >= 5:
                    break

    def process_post(self) -> Post | None:
        post = self.post
        url = self.url

        post_link = get_post_link(post)
        if post_link is None:
            return

        relative_date = post_link.text
        is_members = _is_members_post(post)

        if self.members is not None:
            if self.members == MembersPostType.MEMBERS_ONLY and (not is_members):
                print(
                    "Skipping as it is not a members post and members-only is configured."
                )
                return

            if self.members == MembersPostType.NO_MEMBERS and is_members:
                print("Skipping as it is a members post and no-members is configured.")
                return

        links = _get_links(post)
        images = _get_images(post)
        approximate_num_comments = _get_approximate_num_comments(post)
        num_thumbs_up = _get_likes(post)
        text = _get_text(post)
        poll = _get_poll(post, self.driver)

        # The following block may require opening things in a new tab.
        num_comments = get_true_comment_count(self.driver)
        opened_post: None | WebElement = None
        opened_tab = False

        # If there are no comments then we must not be in the post link itself.
        if num_comments is None:
            opened_post = self.__open_post_in_tab(url)
            num_comments = get_true_comment_count(self.driver)
            opened_tab = True
        else:
            opened_post = post

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
            when_archived=str(datetime.now(tz=UTC)),
        )

        post.save(self.output_dir)

        if self.take_screenshots:
            self.__take_screenshots(opened_post)

        if self.save_comments_types:
            self.__get_comments()

        if opened_tab and opened_post is not None:
            close_current_tab(self.driver)
