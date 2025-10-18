from __future__ import annotations

import balderhub.webdriver.lib.scenario_features

from ..utils.drivers.base_selenium_driver import BaseSeleniumDriver


class SeleniumFeature(balderhub.webdriver.lib.scenario_features.WebdriverControlFeature):
    """
    The specific browser automation tool feature implementation for selenium environments.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._driver = None

    def create(self) -> None:
        """
        sets up the selenium driver
        """
        raise NotImplementedError("this method needs to be implemented in subclass")

    @property
    def driver(self) -> BaseSeleniumDriver:
        return self._driver
