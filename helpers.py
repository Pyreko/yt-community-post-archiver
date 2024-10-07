# A series of helper functions to avoid cluttering the main archiver code file.


from enum import Enum
from typing import Optional
from selenium import webdriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.webdriver import WebDriver as ChromeWebDriver
from selenium.webdriver.firefox.webdriver import WebDriver as FirefoxWebDriver


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
):
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
    driver: ChromeWebDriver | FirefoxWebDriver,
) -> Optional[str]:
    comment_elements = driver.find_elements(By.TAG_NAME, "ytd-comments")
    if comment_elements:
        count = comment_elements[0].find_elements(By.ID, "count")
        if count:
            return count[0].text.split()[0]

    return None


def is_members_post(post: WebElement) -> bool:
    return bool(post.find_elements(By.CLASS_NAME, "ytd-sponsors-only-badge-renderer"))
