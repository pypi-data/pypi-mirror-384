from abc import ABC
from .html_element import HtmlElement


class AbstractHtmlInputElement(HtmlElement, ABC):
    """
    This is an abstract class that is used by all more specific input elements in
    ``balderhub.html.utils.components.input``.``

    The element is implemented like described here: https://developer.mozilla.org/en-US/docs/Web/API/HTMLInputElement
    """
