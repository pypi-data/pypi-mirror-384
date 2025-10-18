from selenium import webdriver

from .base_selenium_driver import BaseSeleniumDriver


class SeleniumSafariDriver(BaseSeleniumDriver):
    """
    This driver is used when you directly want to use the Safari webdriver
    """
    def __init__(self, selenium_service=None, selenium_options=None, keep_alive=True, reuse_service=False):
        super().__init__()
        self._driver = webdriver.Safari(options=selenium_options, service=selenium_service, keep_alive=keep_alive,
                                        reuse_service=reuse_service)
