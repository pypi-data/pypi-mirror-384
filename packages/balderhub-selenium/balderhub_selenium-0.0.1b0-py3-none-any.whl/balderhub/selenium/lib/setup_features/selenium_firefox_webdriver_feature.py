from __future__ import annotations
from typing import Union

from selenium import webdriver

from ..scenario_features.selenium_feature import SeleniumFeature
from ..utils.drivers.selenium_firefox_driver import SeleniumFirefoxDriver


class SeleniumFirefoxWebdriverFeature(SeleniumFeature):
    """
    Setup Feature to work with Selenium and Firefox Webdriver
    """
    def create(self):
        self._driver =SeleniumFirefoxDriver(
            selenium_service=self.selenium_service,
            selenium_options=self.selenium_options,
            keep_alive=self.keep_alive,
        )

    @property
    def selenium_service(self) -> Union[webdriver.FirefoxService, None]:
        """
        :return: returns the selenium service
        """
        return None

    @property
    def selenium_options(self) -> Union[webdriver.FirefoxOptions, None]:
        """
        :return: returns the selenium options
        """
        return None

    @property
    def keep_alive(self) -> bool:
        """
        :return: True if ``keep_alive`` of selenium session should be enabled, otherwise False
        """
        return True
