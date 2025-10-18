from __future__ import annotations
from typing import Union

from selenium import webdriver

from ..scenario_features.selenium_feature import SeleniumFeature
from ..utils.drivers.selenium_edge_driver import SeleniumEdgeDriver


class SeleniumEdgeWebdriverFeature(SeleniumFeature):
    """
    Setup Feature to work with Selenium and Edge Webdriver
    """

    def create(self):
        self._driver =SeleniumEdgeDriver(
            selenium_service=self.selenium_service,
            selenium_options=self.selenium_options,
            keep_alive=self.keep_alive
        )

    @property
    def selenium_service(self) -> Union[webdriver.EdgeService, None]:
        """
        :return: returns the selenium service
        """
        return None

    @property
    def selenium_options(self) -> Union[webdriver.EdgeOptions, None]:
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
