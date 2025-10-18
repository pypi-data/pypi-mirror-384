from __future__ import annotations

from selenium.common import NoSuchElementException
from selenium.webdriver.remote.webelement import WebElement
from balderhub.gui.lib.utils import BaseSelector
from balderhub.webdriver.lib.utils.web_element_bridges import FullyReidentifiableElementBridge

from .selenium_web_element_bridge import SeleniumWebElementBridge
from ..selector import Selector


class SeleniumFullyReidentifiableElementBridge(FullyReidentifiableElementBridge, SeleniumWebElementBridge):
    """
    Selenium element bridge for elements that can be fully reidentified (f.e. because they are defined by an
    absolute ref).
    """
    def re_identify_raw_element(self) -> WebElement:
        if self.parent is None:
            self._raw_element = self.driver.find_raw_element(self.selector)
        else:
            self._raw_element = self.parent.find_raw_element(self.selector)
        return self._raw_element

    def find_bridge(self, selector: BaseSelector) -> SeleniumFullyReidentifiableElementBridge:
        return SeleniumFullyReidentifiableElementBridge(self.driver, selector.translate_to(Selector), parent=self)

    def exists(self) -> bool:
        try:
            if self.parent is None:
                if self.driver.find_raw_element(self.selector):
                    return True
            else:
                if self.parent.find_raw_element(self.selector):
                    return True
        except NoSuchElementException:
            return False
        return False
