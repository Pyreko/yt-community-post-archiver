# A series of helper functions to avoid cluttering the main archiver code file.

import os
import time
from enum import Enum, unique

from selenium import webdriver
from selenium.webdriver.chrome.webdriver import WebDriver as ChromeWebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.webdriver import WebDriver as FirefoxWebDriver
from selenium.webdriver.remote.webelement import WebElement

LOAD_SLEEP_SECS = 1


@unique
class Driver(Enum):
    """
    The backing browser to use for scraping.
    """

    FIREFOX = 1
    CHROME = 2


def init_driver(
    driver: Driver,
    headless: bool,
    profile_dir: str | None,
    profile_name: str | None,
    width: int,
    height: int,
) -> ChromeWebDriver | FirefoxWebDriver:
    """
    Initialize the driver and return it, based on the settings passed.
    """

    match driver:
        case Driver.CHROME:
            options = webdriver.ChromeOptions()
            options.add_argument(f"--window-size={width},{height}")
            options.add_argument("--disable-gpu")

            if headless:
                options.add_argument("--headless=new")

            if profile_dir:
                profile_name = profile_name if profile_name is not None else "Default"

                options.add_argument(f"--user-data-dir={profile_dir}")
                options.add_argument(f"--profile-directory={profile_name}")

            return webdriver.Chrome(options)
        case Driver.FIREFOX:
            options = webdriver.FirefoxOptions()
            options.add_argument(f"--window-size={width},{height}")

            if headless:
                options.add_argument("-headless")

            if profile_dir:
                options.set_preference("profile", f"{profile_dir}")

            return webdriver.Firefox(options)
        case _:
            raise Exception("Unsupported driver type!")


def __is_post(candidate: WebElement) -> bool:
    href = candidate.get_attribute("href")
    if href is not None:
        return "community?" in href and "lb=" in href

    return False


def get_post_link(element: WebElement) -> WebElement | None:
    return next(
        filter(
            __is_post,
            element.find_elements(By.TAG_NAME, "a"),
        ),
        None,
    )


def find_post_element(driver: ChromeWebDriver | FirefoxWebDriver) -> WebElement | None:
    potential_posts = driver.find_elements(By.ID, "post")
    if not potential_posts:
        return None

    post = potential_posts[0]

    return post


def close_current_tab(driver: ChromeWebDriver | FirefoxWebDriver) -> bool:
    """
    Try to close the current tab. Return True if there is still a tab after, and False if there
    is no tabs after.
    """

    if len(driver.window_handles) > 1:
        driver.close()
        driver.switch_to.window(driver.window_handles[0])
        time.sleep(0.5)
        return True
    else:
        return False
