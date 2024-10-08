# A series of helper functions to avoid cluttering the main archiver code file.

from enum import Enum
import time
from typing import Optional, Union
from selenium import webdriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.webdriver import WebDriver as ChromeWebDriver
from selenium.webdriver.firefox.webdriver import WebDriver as FirefoxWebDriver

from post import Poll, PollEntry


class Driver(Enum):
    """
    The backing browser to use for scraping.
    """

    FIREFOX = 1
    CHROME = 2


def init_driver(
    driver: Driver,
    headless: bool,
    profile_dir: Optional[str],
    profile_name: Optional[str],
    width: int,
    height: int,
) -> Union[ChromeWebDriver, FirefoxWebDriver]:
    """
    Initialize the driver and return it, based on the settings passed.
    """

    match driver:
        case Driver.CHROME:
            options = webdriver.ChromeOptions()
            options.add_argument(f"--window-size={width},{height}")
            options.add_argument("--disable-gpu")

            if headless:
                options.add_argument("--headless")

            if profile_dir:
                profile_name = profile_name if profile_name is not None else "Default"

                options.add_argument(f"--user-data-dir={profile_dir}")
                options.add_argument(f"--profile-directory={profile_name}")

            return webdriver.Chrome(options)
        case Driver.FIREFOX:
            options = webdriver.FirefoxOptions()
            options.add_argument(f"-width={width}")
            options.add_argument(f"-height={height}")

            if headless:
                options.add_argument("-headless")

            return webdriver.Firefox(options)
        case _:
            raise Exception("Unsupported driver type!")


def is_post(candidate: WebElement) -> bool:
    href = candidate.get_attribute("href")
    if href is not None:
        return "https://www.youtube.com/post/" in href

    return False


def get_post_link(element: WebElement) -> Optional[WebElement]:
    return next(
        filter(
            is_post,
            element.find_elements(By.TAG_NAME, "a"),
        ),
        None,
    )


def get_comment_count(
    driver: Union[ChromeWebDriver, FirefoxWebDriver],
) -> Optional[str]:
    comment_elements = driver.find_elements(By.TAG_NAME, "ytd-comments")
    if comment_elements:
        count = comment_elements[0].find_elements(By.ID, "count")
        if count:
            return count[0].text.split()[0]

    return None


def is_members_post(post: WebElement) -> bool:
    return bool(post.find_elements(By.CLASS_NAME, "ytd-sponsors-only-badge-renderer"))


def get_poll(
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


def find_post_element(
    driver: Union[ChromeWebDriver, FirefoxWebDriver]
) -> Optional[WebElement]:
    potential_posts = driver.find_elements(By.ID, "post")
    if not potential_posts:
        return None

    post = potential_posts[0]

    return post
