from __future__ import annotations
from typing import Union

from selenium import webdriver

from ..scenario_features.selenium_feature import SeleniumFeature
from ..utils.drivers import SeleniumSafariDriver


class SeleniumSafariWebdriverFeature(SeleniumFeature):
    """
    Setup Feature to work with Selenium and Safari Webdriver
    """

    def create(self):
        self._driver = SeleniumSafariDriver(
            selenium_service=self.selenium_service,
            selenium_options=self.selenium_options,
            keep_alive=self.keep_alive,
            reuse_service=self.reuse_service,
        )

    @property
    def selenium_service(self) -> Union[webdriver.IeService, None]:
        """
        :return: returns the selenium service
        """
        return None

    @property
    def selenium_options(self) -> Union[webdriver.IeOptions, None]:
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

    @property
    def reuse_service(self) -> bool:
        """
        :return: returns true if the selenium session should reuse the service, otherwise False
        """
        return False
