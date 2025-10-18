from balderhub.gui.lib.utils.mixins import TwoStateCheckboxMixin

from ..abstract_html_input_element import AbstractHtmlInputElement


class HtmlCheckboxInput(AbstractHtmlInputElement, TwoStateCheckboxMixin):
    """
    The element is implemented like described here:
    https://developer.mozilla.org/en-US/docs/Web/HTML/Element/input/checkbox
    """

    def is_checked(self):
        return self._bridge.is_selected()
