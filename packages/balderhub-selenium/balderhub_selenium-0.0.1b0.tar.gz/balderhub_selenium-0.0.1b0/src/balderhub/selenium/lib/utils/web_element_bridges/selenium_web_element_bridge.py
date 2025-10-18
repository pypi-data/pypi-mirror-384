from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Union, List, TYPE_CHECKING

from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions
from balderhub.gui.lib.utils import BaseSelector
from balderhub.webdriver.lib.utils.web_element_bridges import BaseWebdriverElementBridge

from ..selector import Selector

if TYPE_CHECKING:
    from ..drivers import BaseSeleniumDriver

    from .selenium_fully_reidentifiable_element_bridge import SeleniumFullyReidentifiableElementBridge
    from .selenium_partly_reidentifiable_element_bridge import SeleniumPartlyReidentifiableElementBridge
    from .selenium_not_reidentifiable_element_bridge import SeleniumNotReidentifiableElementBridge


# pylint: disable-next=too-many-public-methods
class SeleniumWebElementBridge(BaseWebdriverElementBridge, ABC):
    """
    basic web-element-bridge implementation for Selenium
    """

    @property
    def driver(self) -> BaseSeleniumDriver:
        return self._driver

    @property
    def raw_element(self) -> WebElement:
        return self._raw_element

    def find_raw_element(self, selector: BaseSelector) -> WebElement:
        return self.raw_element.find_element(*selector.translate_to(Selector).get_selenium_selector())

    def find_raw_elements(self, selector: BaseSelector) -> List[WebElement]:
        return self.raw_element.find_elements(*selector.translate_to(Selector).get_selenium_selector())

    @abstractmethod
    def find_bridge(
            self,
            selector: BaseSelector
    ) -> Union[SeleniumFullyReidentifiableElementBridge, SeleniumPartlyReidentifiableElementBridge]:
        pass

    def find_bridges(
            self,
            selector: BaseSelector
    ) -> List[SeleniumNotReidentifiableElementBridge]:
        # pylint: disable-next=import-outside-toplevel
        from .selenium_not_reidentifiable_element_bridge import SeleniumNotReidentifiableElementBridge
        result = []
        for cur_elem in self.find_raw_elements(selector.translate_to(Selector)):
            result.append(SeleniumNotReidentifiableElementBridge(self.driver, cur_elem, parent=self))
        return result

    def get_attribute(self, name: Any) -> Union[str, None]:
        return self.raw_element.get_attribute(name)

    def get_property(self, name: Any) -> Any:
        return self.raw_element.get_property(name)

    def get_css_value(self, name: Any) -> str:
        return self.raw_element.value_of_css_property(property_name=name)

    def get_tag_name(self) -> str:
        return self.raw_element.tag_name

    def get_rect(self) -> tuple[int, int, int, int]:
        rectangle = self.raw_element.rect
        return rectangle['x'], rectangle['y'], rectangle['width'], rectangle['height']

    def clear(self):
        self.raw_element.clear()

    def send_keys(self, text: str) -> None:
        self.raw_element.send_keys(text)

    def is_displayed(self) -> bool:
        return self.exists() and self.raw_element.is_displayed()

    def is_enabled(self) -> bool:
        return self.exists() and self.raw_element.is_enabled()

    def is_selected(self) -> bool:
        return self.exists() and self.raw_element.is_selected()

    def is_clickable(self) -> bool:
        if not self.exists() or not self.is_displayed():
            return False
        return bool(expected_conditions.element_to_be_clickable(self.raw_element)(self.driver.selenium_webdriver))

    def click(self):
        self.raw_element.click()

    def get_text_content(self) -> str:
        return self.raw_element.text

    def scroll_to_beginning(self, *args, **kwargs):
        self.driver.execute_sync_script("arguments[0].scrollTop = 0;", self.raw_element)

    def scroll_for(self, scroll_steps: int, *args, **kwargs):
        actions = ActionChains(self.driver)
        actions.move_to_element(self.raw_element).scroll_by_amount(0, scroll_steps).perform()

    def scroll_to_end(self, *args, **kwargs):
        self.driver.execute_sync_script("arguments[0].scrollTop = arguments[0].scrollHeight;", self.raw_element)
