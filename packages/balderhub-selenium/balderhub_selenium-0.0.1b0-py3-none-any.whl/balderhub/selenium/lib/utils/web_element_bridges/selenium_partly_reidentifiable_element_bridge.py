from __future__ import annotations

from selenium.common import NoSuchElementException
from selenium.webdriver.remote.webelement import WebElement

from balderhub.gui.lib.utils import BaseSelector
from balderhub.webdriver.lib.utils.web_element_bridges import PartlyReidentifiableElementBridge

from .selenium_web_element_bridge import SeleniumWebElementBridge
from ..selector import Selector


class SeleniumPartlyReidentifiableElementBridge(PartlyReidentifiableElementBridge, SeleniumWebElementBridge):
    """
    Selenium element bridge for elements that partly be reidentified (f.e. because they have a non-reidentifiable
    parent, but a relative ref).
    """
    def find_bridge(self, selector: BaseSelector) -> SeleniumPartlyReidentifiableElementBridge:
        return SeleniumPartlyReidentifiableElementBridge(self.driver, selector.translate_to(Selector), parent=self)

    def re_identify_raw_element(self) -> WebElement:
        self._raw_element = self.parent.find_raw_element(self.relative_selector)
        return self._raw_element

    def exists(self) -> bool:
        try:
            if self.parent.find_raw_element(self.relative_selector):
                return True
        except NoSuchElementException:
            return False
        return False
