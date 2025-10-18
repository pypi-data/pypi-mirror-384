from __future__ import annotations

from typing import Union
from selenium import webdriver

from ..scenario_features.selenium_feature import SeleniumFeature
from ..utils.drivers.selenium_ie_driver import SeleniumIEDriver


class SeleniumIeWebdriverFeature(SeleniumFeature):
    """
    Setup Feature to work with Selenium and IE Webdriver
    """

    def create(self):
        self._driver =SeleniumIEDriver(
            selenium_service=self.selenium_service,
            selenium_options=self.selenium_options,
            keep_alive=self.keep_alive
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
