from selenium import webdriver

from .base_selenium_driver import BaseSeleniumDriver


class SeleniumChromeDriver(BaseSeleniumDriver):
    """
    This driver is used when you directly want to use the chrome webdriver
    """

    def __init__(self, selenium_service=None, selenium_options=None, keep_alive=True):
        super().__init__()
        self._driver = webdriver.Chrome(service=selenium_service, options=selenium_options, keep_alive=keep_alive)
