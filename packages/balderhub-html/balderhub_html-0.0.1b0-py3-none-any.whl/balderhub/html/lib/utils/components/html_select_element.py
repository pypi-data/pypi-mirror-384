from balderhub.gui.lib.utils.mixins import SelectByVisibleTextMixin, SelectByIndexMixin, SelectByHiddenValueMixin

from .html_element import HtmlElement


class HtmlSelectElement(HtmlElement, SelectByVisibleTextMixin, SelectByIndexMixin, SelectByHiddenValueMixin):
    """
    The element is implemented like described here: https://developer.mozilla.org/en-US/docs/Web/API/HTMLSelectElement
    """

    def select_by_text(self, visible_text: str):
        raise NotImplementedError() # TODO

    def select_by_index(self, index: int):
        raise NotImplementedError() # TODO

    def select_by_value(self, value: str) -> None:
        raise NotImplementedError() # TODO
