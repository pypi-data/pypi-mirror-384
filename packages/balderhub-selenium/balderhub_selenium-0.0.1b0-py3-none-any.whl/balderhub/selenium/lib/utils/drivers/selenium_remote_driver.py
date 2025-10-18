from selenium import webdriver

from .base_selenium_driver import BaseSeleniumDriver


class SeleniumRemoteDriver(BaseSeleniumDriver):
    """
    This driver is used when you directly want to use a remote webdriver
    """
    def __init__(self, command_executor, selenium_options, file_detector=None, keep_alive=True):
        super().__init__()
        self._driver = webdriver.Remote(command_executor=command_executor, keep_alive=keep_alive,
                                        file_detector=file_detector, options=selenium_options)
