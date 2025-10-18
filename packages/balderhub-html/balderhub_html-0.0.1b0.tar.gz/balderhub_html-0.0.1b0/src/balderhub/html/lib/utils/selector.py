import logging
from balderhub.gui.lib.utils.base_selector import BaseSelector

logger = logging.getLogger(__name__)


class Selector(BaseSelector):
    """
    General selector class for referencing HTML elements.

    You can use this selector for all kinds of guicontrol features (as long as they are supported).
    """

    class By(BaseSelector.By):
        """
        Enum to specify the type of the selector
        """
        ID = 'id'
        CLASSNAME = 'class name'
        XPATH = 'xpath'
        NAME = 'name'
        CSS_SELECTOR = 'css selector'
        TAG = "tag name"

    @classmethod
    def by_id(cls, name: str):
        """
        Helper method that returns a selector instance that uses ID as reference type

        :param name: the reference name
        :return: the new selector instance
        """
        return cls(cls.By.ID, name)

    @classmethod
    def by_tag(cls, name: str):
        """
        Helper method that returns a selector instance that uses TAG as reference type

        :param name: the reference name
        :return: the new selector instance
        """
        return cls(cls.By.TAG, name)

    @classmethod
    def by_class(cls, name: str):
        """
        Helper method that returns a selector instance that uses CLASS as reference type

        :param name: the reference name
        :return: the new selector instance
        """
        return cls(cls.By.CLASSNAME, name)

    @classmethod
    def by_xpath(cls, name: str):
        """
        Helper method that returns a selector instance that uses XPATH as reference type

        :param name: the reference name
        :return: the new selector instance
        """
        return cls(cls.By.XPATH, name)

    @classmethod
    def by_css(cls, name: str):
        """
        Helper method that returns a selector instance that uses CSS as reference type

        :param name: the reference name
        :return: the new selector instance
        """
        return cls(cls.By.CSS_SELECTOR, name)

    @classmethod
    def by_name(cls, name: str):
        """
        Helper method that returns a selector instance that uses NAME as reference type

        :param name: the reference name
        :return: the new selector instance
        """
        return cls(cls.By.NAME, name)

try:
    from balderhub.selenium.lib.utils import Selector as SeleniumSelector

    if SeleniumSelector not in Selector.translations.keys():

        logger.debug('translation for `balderhub-selenium` was added')

        Selector.translations[SeleniumSelector] = {
            Selector.By.ID: SeleniumSelector.By.ID,
            Selector.By.CLASSNAME: SeleniumSelector.By.CLASS_NAME,
            Selector.By.XPATH: SeleniumSelector.By.XPATH,
            Selector.By.NAME: SeleniumSelector.By.NAME,
            Selector.By.CSS_SELECTOR: SeleniumSelector.By.CSS_SELECTOR,
            Selector.By.TAG: SeleniumSelector.By.TAG_NAME,
        }
except ImportError:
    # do not add translation -> `balderhub-selenium` is not installed
    pass
