from selenium.webdriver.common.by import By as SeleniumBy

import balderhub.webdriver.lib.utils
from balderhub.gui.lib.utils.base_selector import BaseSelector


class Selector(balderhub.webdriver.lib.utils.Selector):
    """
    Specific BalderHUb selenium selector
    """

    class By(BaseSelector.By):
        """
        Enum to specify the type of selector
        """
        ID = "id"
        XPATH = "xpath"
        LINK_TEXT = "link text"
        PARTIAL_LINK_TEXT = "partial link text"
        NAME = "name"
        TAG_NAME = "tag name"
        CLASS_NAME = "class name"
        CSS_SELECTOR = "css selector"

    def get_selenium_selector(self) -> tuple[SeleniumBy, str]:
        """
        :return: returns the raw selenium selector reference for this balderhub selector
        """
        return {
            Selector.By.ID: SeleniumBy.ID,
            Selector.By.XPATH: SeleniumBy.XPATH,
            Selector.By.LINK_TEXT: SeleniumBy.LINK_TEXT,
            Selector.By.PARTIAL_LINK_TEXT: SeleniumBy.PARTIAL_LINK_TEXT,
            Selector.By.NAME: SeleniumBy.NAME,
            Selector.By.TAG_NAME: SeleniumBy.TAG_NAME,
            Selector.By.CLASS_NAME: SeleniumBy.CLASS_NAME,
            Selector.By.CSS_SELECTOR: SeleniumBy.CSS_SELECTOR,
        }[self.by_type], self.identifier
