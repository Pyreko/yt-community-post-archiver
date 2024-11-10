import json
import os
from dataclasses import dataclass
from datetime import UTC, datetime

from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

from yt_community_post_archiver.post import get_post_id


def _get_comment_id(url: str) -> str:
    return url.split("/")[-1].split("?")[-1]


@dataclass
class Comment:
    author: str | None
    relative_date: str | None
    member_length: str | None
    likes: str | None
    is_hearted: bool
    is_pinned: bool
    contents: str | None
    replies: str | None
    link: str | None
    when_archived: str

    def save(self, output_dir: str, post_url: str):
        post_id = get_post_id(post_url)
        comment_dir = os.path.join(output_dir, post_id, "comments")
        if not os.path.exists(comment_dir):
            try:
                os.mkdir(comment_dir)
            except Exception:
                print(f"err: couldn't make directory at {comment_dir}")
                return

        comment_id = _get_comment_id(self.link) if self.link else "unknown"
        comment_path = os.path.join(comment_dir, f"{comment_id}.json")

        try:
            with open(comment_path, "w", encoding="utf-8") as f:
                json.dump(
                    self.__dict__,
                    f,
                    ensure_ascii=False,
                    indent=4,
                    default=lambda o: o.__dict__,
                    skipkeys=True,
                )
        except Exception:
            print(f"err: couldn't save comment data dump at {comment_path}")


def _get_author(comment: WebElement) -> str | None:
    possible_author = comment.find_elements(By.ID, "author-text")
    if possible_author:
        author = possible_author[0].text.strip()
        if author:
            return author

    possible_author = comment.find_elements(By.ID, "channel-name")
    if possible_author:
        possible_author = possible_author[0].find_elements(
            By.TAG_NAME, "yt-formatted-string"
        )
        author = possible_author[0].text.strip()
        return author if author else None

    return None


def _get_relative_date(comment: WebElement) -> str | None:
    possible_relative_date = comment.find_elements(By.ID, "published-time-text")
    relative_date = possible_relative_date[0].text.strip()
    return relative_date if relative_date else None


def _get_member_length(comment: WebElement) -> str | None:
    possible_member_length = comment.find_elements(By.ID, "custom-badge")

    if not possible_member_length:
        return None

    possible_text = possible_member_length[0].find_elements(
        By.TAG_NAME, "yt-img-shadow"
    )

    if not possible_text:
        return None

    length = possible_text[0].get_attribute("shared-tooltip-text").strip()
    return length if length else None


def _get_likes(comment: WebElement) -> str | None:
    possible_likes = comment.find_elements(By.ID, "vote-count-middle")

    if not possible_likes:
        return None

    likes = possible_likes[0].text.strip()
    return likes if likes else None


def _get_is_hearted(comment: WebElement) -> bool:
    possible_hearts = comment.find_elements(By.ID, "creator-heart-button")
    if not possible_hearts:
        return False

    return possible_hearts[0].is_displayed()


def _get_is_pinned(comment: WebElement) -> bool:
    possible_pins = comment.find_elements(By.ID, "pinned-comment-badge")
    if not possible_pins:
        return False

    return possible_pins[0].is_displayed()


def _get_contents(comment: WebElement) -> str | None:
    # This is SO hardcoded holy SHIT. Definitely test this one.
    # Also I could probably do this all with bs4 but for whatever
    # reason we get this mess lol.

    comment_html = comment.get_attribute("innerHTML")
    if not comment_html:
        return None

    soup = BeautifulSoup(comment_html, "html.parser")

    content_wrapper = soup.find(id="content-text")
    if not content_wrapper:
        return None

    content_wrapper = content_wrapper.find("span")
    if not content_wrapper:
        return None

    text = ""

    for c in content_wrapper.descendants:
        if c.name == "img":
            emote_name = c.get("alt")
            if emote_name:
                text += f"<::{emote_name}::>"
        elif c.name is None:
            text += c.text

    return text


def _get_replies(comment: WebElement) -> str | None:
    possible_replies = comment.find_elements(By.ID, "more-replies")
    if not possible_replies:
        return None

    replies = possible_replies[0].text.strip()
    return replies if replies else None


def build_comment(comment: WebElement, link: str) -> Comment:
    author = _get_author(comment)
    relative_date = _get_relative_date(comment)
    member_length = _get_member_length(comment)
    likes = _get_likes(comment)
    is_hearted = _get_is_hearted(comment)
    is_pinned = _get_is_pinned(comment)
    contents = _get_contents(comment)
    replies = _get_replies(comment)

    return Comment(
        author=author,
        relative_date=relative_date,
        member_length=member_length,
        likes=likes,
        is_hearted=is_hearted,
        is_pinned=is_pinned,
        contents=contents,
        replies=replies,
        link=link,
        when_archived=str(datetime.now(tz=UTC)),
    )
