from selenium import webdriver

from .base_selenium_driver import BaseSeleniumDriver


class SeleniumFirefoxDriver(BaseSeleniumDriver):
    """
    This driver is used when you directly want to use the Firefox webdriver
    """
    def __init__(self, selenium_service=None, selenium_options=None, keep_alive=True):
        super().__init__()
        self._driver = webdriver.Firefox(options=selenium_options, service=selenium_service, keep_alive=keep_alive)
