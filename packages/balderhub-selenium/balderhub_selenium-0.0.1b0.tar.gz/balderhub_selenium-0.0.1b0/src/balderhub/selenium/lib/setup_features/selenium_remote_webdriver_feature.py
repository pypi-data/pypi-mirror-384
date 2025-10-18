from __future__ import annotations

from typing import Union

from selenium.webdriver.common.options import BaseOptions

from ..scenario_features.selenium_feature import SeleniumFeature
from ..utils.drivers import SeleniumRemoteDriver


class SeleniumRemoteWebdriverFeature(SeleniumFeature):
    """
    Setup Feature to work with Selenium and Remote Webdriver like Selenium Grid
    """

    def create(self):
        self._driver = SeleniumRemoteDriver(
            command_executor=self.command_executor,
            selenium_options=self.selenium_options,
            file_detector=self.file_detector,
            keep_alive=self.keep_alive,
        )

    @property
    def command_executor(self) -> str:
        """
        :return: returns the command executor
        """
        return "http://127.0.0.1:4444"

    @property
    def selenium_options(self) -> BaseOptions:
        """
        :return: returns the selenium options
        """
        raise NotImplementedError()

    @property
    def keep_alive(self) -> bool:
        """
        :return: True if ``keep_alive`` of selenium session should be enabled, otherwise False
        """
        return True

    @property
    def file_detector(self) -> Union[object, None]:
        """
        :return: returns the selenium session file detector or None if no one should be set
        """
        return None
