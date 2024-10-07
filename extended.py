# Used to get some type hints to work.
from __future__ import annotations

from ctypes import c_bool
from multiprocessing import Process, SimpleQueue, Value
from multiprocessing.sharedctypes import Synchronized
from typing import Optional
from helpers import Driver, init_driver
from selenium.webdriver.chrome.webdriver import WebDriver as ChromeWebDriver
from selenium.webdriver.firefox.webdriver import WebDriver as FirefoxWebDriver


def extended_archive_task(
    driver: ChromeWebDriver | FirefoxWebDriver,
    cookie_path: Optional[str],
    url_queue: SimpleQueue[str],
    cancellation_token: Synchronized[bool],
):
    while True:
        with cancellation_token.get_lock():
            if cancellation_token.value:
                break

        try:
            url = url_queue.get()

            # TODO: process url
        finally:
            # If we throw then stop.
            break

    driver.quit()


class ExtendedArchiver:
    """
    An "extended" archiver task; this is intended to be opened in a separate thread
    to further enhance scraped data from the main archival job.
    """

    def __init__(
        self,
        cancellation_token: Synchronized[bool],
        headless: bool,
        cookie_path: Optional[str],
        profile_dir: Optional[str],
        profile_name: Optional[str],
        driver: Driver,
        width: int,
        height: int,
    ) -> None:
        web_driver = init_driver(driver, headless, None, None, width, height)

        self.url_queue = SimpleQueue()
        self.cancellation_token = cancellation_token
        self.task = Process(
            target=extended_archive_task,
            args=[
                web_driver,
                cookie_path,
                self.url_queue,
                self.cancellation_token,
            ],
        )

    def add_url(self, url: str):
        self.url_queue.put(url)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        with self.cancellation_token.get_lock():
            self.cancellation_token.value = False
