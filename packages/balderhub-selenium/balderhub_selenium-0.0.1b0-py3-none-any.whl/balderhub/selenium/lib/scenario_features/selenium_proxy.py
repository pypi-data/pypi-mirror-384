from __future__ import annotations

import balder

import balderhub.webdriver.lib.scenario_features

from .selenium_feature import SeleniumFeature
from ..utils.drivers.base_selenium_driver import BaseSeleniumDriver


class SeleniumProxy(balderhub.webdriver.lib.scenario_features.WebdriverControlFeature):
    """
    Proxy feature implementation for selenium environments in case the selenium instance is provided within another
    device.
    """
    class Selenium(balder.VDevice):
        """vdevice that has the real :class:`SeleniumFeature`"""
        selenium = SeleniumFeature()

    @property
    def selenium_feature(self) -> SeleniumFeature:
        """
        :return: returns the orginal selenium feature instance
        """
        return self.Selenium.selenium

    @property
    def driver(self) -> BaseSeleniumDriver:
        return self.selenium_feature.driver

    def create(self) -> None:
        self.Selenium.selenium.create()
