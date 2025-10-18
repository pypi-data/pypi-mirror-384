from __future__ import annotations

from typing import TypeVar, Union
from balderhub.gui.lib.utils.components.abstract_element import AbstractElement
from balderhub.webdriver.lib.utils.driver import BaseWebdriverDriverClass
from balderhub.webdriver.lib.utils.web_element_bridges import BaseWebdriverElementBridge
from balderhub.gui.lib.utils.mixins import ClickableMixin, VisibleMixin

from ..selector import Selector

T = TypeVar("T", bound=BaseWebdriverDriverClass)


class HtmlElement(AbstractElement, VisibleMixin, ClickableMixin):
    """
    This is a general version of an html element. It is used as base class for all specific html elements inside this
    package.

    The element is implemented like described here: https://developer.mozilla.org/en-US/docs/Web/API/HTMLElement.
    """

    def __init__(self, bridge: BaseWebdriverElementBridge):
        self._bridge = bridge

    def __eq__(self, other):
        return self.bridge == other.bridge

    @classmethod
    def by_selector(cls, driver: T, selector: Selector, parent: Union[HtmlElement, BaseWebdriverElementBridge] = None):
        """
        THis method returns the element by a provided selector.

        :param driver: the guicontrol driver
        :param selector: the selector to identify the element
        :param parent: optional a parent html element, if the selector is relative
        :return: the html element that is identified by the selector
        """
        if parent is None:
            bridge = driver.find_bridge(selector)
        else:
            if isinstance(parent, HtmlElement):
                parent = parent.bridge
            bridge = parent.find_bridge(selector)
        return cls(bridge)

    @classmethod
    def by_raw_element(
            cls,
            driver: T,
            web_element: HtmlElement,
            parent: Union[HtmlElement, BaseWebdriverElementBridge] = None
    ):
        """
        This method returns the html element by the raw guicontrol engine element.

        :param driver: the guicontrol driver
        :param web_element: the raw guicontrol engine element (f.e. ``WebElement`` if guicontrol engine is
                            ``balderhub-selenium``)
        :param parent: optional a parent html element, if the selector is relative
        :return: the html element that is identified by the selector
        """
        if parent is not None and isinstance(parent, HtmlElement):
            parent = parent.bridge
        bridge = driver.get_bridge_for_raw_element(web_element, parent)
        return cls(bridge)

    @property
    def bridge(self) -> BaseWebdriverElementBridge:
        """
        :return: returns the underlying bridge object
        """
        return self._bridge

    @property
    def driver(self) -> T:
        """
        :return: returns the underlying guicontrol driver
        """
        return self._bridge.driver

    @property
    def raw_element(self):
        """
        :return: returns the raw guicontrol engine element
        """
        return self._bridge.raw_element

    @property
    def parent_bridge(self) -> BaseWebdriverElementBridge:
        """
        :return: returns the bridge of the paren element (if any)
        """
        return self._bridge.parent

    @property
    def text(self) -> str:
        """
        :return: returns the text of the element
        """
        return self._bridge.get_text_content()

    def click(self):
        """
        clicks this element
        """
        return self._bridge.click()

    def exists(self) -> bool:
        """
        :return: returns True if this element exists, False otherwise
        """
        return self._bridge.exists()

    def is_visible(self) -> bool:
        """
        :return: returns True if this element is visible, False otherwise
        """
        return self._bridge.is_displayed()

    def is_clickable(self) -> bool:
        """
        :return: returns true if this element is clickable, False otherwise
        """
        return self._bridge.is_clickable()
