from typing import Union, Optional, Any

from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement

import balderhub.webdriver.lib.utils.driver
from balderhub.webdriver.lib.utils.web_element_bridges import BaseWebdriverElementBridge
from balderhub.gui.lib.utils import BaseSelector
from balderhub.url.lib.utils import Url

from ..web_element_bridges import SeleniumNotReidentifiableElementBridge, SeleniumFullyReidentifiableElementBridge
from ..selector import Selector


# pylint: disable-next=too-many-public-methods
class BaseSeleniumDriver(balderhub.webdriver.lib.utils.driver.BaseWebdriverDriverClass):
    """
    Base Selenium Driver class (used by all selenium browser-automation drivers)
    """

    # pylint: disable-next=unused-argument
    def __init__(self, *args, **kwargs):
        super().__init__()

        self._driver: Union[WebDriver, None] = None

    def navigate_to(self, url: Union[Url, str]):
        url = url if isinstance(url, Url) else Url(url)
        self._driver.get(url.as_string())

    def go_back(self):
        self._driver.back()

    def go_forward(self):
        self._driver.forward()

    def refresh(self):
        self._driver.refresh()

    @property
    def page_title(self) -> str:
        return self._driver.title

    def get_page_source(self) -> str:
        return self._driver.page_source

    def execute_sync_script(self, script: str, *args) -> Any:
        return self._driver.execute_script(script, *args)

    def execute_async_script(self, script: str, *args) -> Any:
        return self._driver.execute_async_script(script, *args)

    def get_all_cookies(self) -> list[dict]:
        return self._driver.get_cookies()

    def get_cookie(self, name: str) -> Union[dict, None]:
        return self._driver.get_cookie(name)

    def add_cookie(self, cookie_dict: dict) -> None:
        self._driver.add_cookie(cookie_dict=cookie_dict)

    def delete_cookie(self, name: str):
        self._driver.delete_cookie(name=name)

    def delete_all_cookies(self):
        self._driver.delete_all_cookies()

    @property
    def current_url(self) -> str:
        return self._driver.current_url

    def get_bridge_for_raw_element(
            self,
            raw_element: WebElement,
            parent: Optional[BaseWebdriverElementBridge] = None
    ) -> SeleniumNotReidentifiableElementBridge:
        return SeleniumNotReidentifiableElementBridge(self, raw_element, parent=parent)

    def find_raw_element(self, selector: BaseSelector) -> WebElement:
        """
        Returns the raw selenium element by the provided selector

        :param selector: the selector that identifies the element
        :return: the specific selenium element
        """
        return self._driver.find_element(*selector.translate_to(Selector).get_selenium_selector())

    def find_raw_elements(self, selector: BaseSelector) -> list[WebElement]:
        """
        Returns the raw selenium elements by the provided selector

        :param selector: the selector that identifies the elements
        :return: a list of raw selenium elements
        """
        return self._driver.find_elements(*selector.translate_to(Selector).get_selenium_selector())

    def find_bridge(self, selector: BaseSelector) -> SeleniumFullyReidentifiableElementBridge:
        return SeleniumFullyReidentifiableElementBridge(self, selector.translate_to(Selector), parent=None)

    def find_bridges(self, selector: BaseSelector) -> list[SeleniumNotReidentifiableElementBridge]:
        items = []
        for cur_web_element in self._driver.find_elements(*selector.translate_to(Selector).get_selenium_selector()):
            items.append(self.get_bridge_for_raw_element(raw_element=cur_web_element, parent=None))
        return items

    @property
    def selenium_webdriver(self) -> WebDriver:
        """
        :return: returns the raw selenium webdriver
        """
        return self._driver

    def quit(self):
        if self._driver is not None:
            self._driver.quit()
