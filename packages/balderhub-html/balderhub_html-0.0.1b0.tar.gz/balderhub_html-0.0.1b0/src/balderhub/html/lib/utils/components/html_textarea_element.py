from balderhub.gui.lib.utils.mixins import TypeableMixin

from .html_element import HtmlElement


class HtmlTextareaElement(HtmlElement, TypeableMixin):
    """
    The element is implemented like described here: https://developer.mozilla.org/en-US/docs/Web/API/HTMLTextAreaElement
    """

    def type_text(self, text: str, clean_before: bool = False):
        if clean_before:
            self._bridge.clear()
        return self._bridge.send_keys(text)
