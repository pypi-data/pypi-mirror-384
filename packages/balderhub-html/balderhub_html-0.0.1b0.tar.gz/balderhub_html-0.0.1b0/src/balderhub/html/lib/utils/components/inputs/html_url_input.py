from balderhub.gui.lib.utils.mixins import TypeableMixin

from ..abstract_html_input_element import AbstractHtmlInputElement


class HtmlUrlInput(AbstractHtmlInputElement, TypeableMixin):
    """
    The element is implemented like described here:
    https://developer.mozilla.org/en-US/docs/Web/HTML/Element/input/url
    """

    def type_text(self, text: str, clean_before: bool = False):
        if clean_before:
            self._bridge.clear()

        return self._bridge.send_keys(text)
