from __future__ import annotations

from typing import TYPE_CHECKING, Union

from selenium.common import StaleElementReferenceException

from balderhub.gui.lib.utils import BaseSelector
from balderhub.webdriver.lib.utils.web_element_bridges import NotReidentifiableElementBridge

from .selenium_web_element_bridge import SeleniumWebElementBridge
from ..selector import Selector

if TYPE_CHECKING:
    from .selenium_partly_reidentifiable_element_bridge import SeleniumPartlyReidentifiableElementBridge


class SeleniumNotReidentifiableElementBridge(NotReidentifiableElementBridge, SeleniumWebElementBridge):
    """
    Selenium element bridge for elements that can not be reidentified (f.e. because they were the result of
    ``get_elements()``).
    """
    def find_bridge(self, selector: BaseSelector) -> SeleniumPartlyReidentifiableElementBridge:
        # pylint: disable-next=import-outside-toplevel
        from .selenium_partly_reidentifiable_element_bridge import SeleniumPartlyReidentifiableElementBridge

        return SeleniumPartlyReidentifiableElementBridge(self.driver, selector.translate_to(Selector), parent=self)

    @property
    def parent(self) -> Union[NotReidentifiableElementBridge, None]:
        return self._parent

    def exists(self):
        try:
            self.raw_element.is_displayed()
            return True
        except StaleElementReferenceException:
            return False
