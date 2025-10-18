from typing import Union, List
import balderhub.gui.lib.scenario_features
import balderhub.webdriver.lib.scenario_features
import balderhub.webdriver.lib.utils.driver
from balderhub.url.lib.utils.url import Url


class HtmlPage(balderhub.gui.lib.scenario_features.PageFeature):
    """
    The base scenario feature that describes a specific html page. You can use this feature to follow the POM
    (page object model) for writing your tests.

    Every page is applicable to a subset of different :class:`balderhub.url.lib.utils.Url` objects. You can specify this
    in :meth:`HtmlPage.applicable_on_url_schema`.
    """

    guicontrol = balderhub.webdriver.lib.scenario_features.WebdriverControlFeature()

    @property
    def driver(self) -> balderhub.webdriver.lib.utils.driver.BaseWebdriverDriverClass:
        """
        :return: returns the driver of this page
        """
        return self.guicontrol.driver

    @property
    def applicable_on_url_schema(self) -> Union[Url, List[Url]]:
        """
        This method needs to be overwritten by child classes. It should return one or more
        :class:`balderhub.url.lib.utils.Url` objects that describe a schema, on which this page is applicable.

        For example:

        .. code-block:: python

            from balderhub.html.lib.scenario_features import HtmlPage
            from balderhub.url.lib.utils import Url

            class MyPage(HtmlPage):

                def applicable_on_url_schema(self) -> Url:
                    return Url('http://example.com/article/<int:article_id>/')

        This makes the page applicable on domains like `http://example.com/article/1/` or also
        `http://example.com/article/555/`, but not on `http://example.com/article/a/`.

        :return: a specific :class:`balderhub.url.lib.utils.Url` object or a list of it
        """
        raise NotImplementedError

    def is_applicable(self):
        current_url = self.guicontrol.driver.current_url

        expected_schema = self.applicable_on_url_schema
        if isinstance(expected_schema, list):
            for cur_schema in expected_schema:
                if not isinstance(cur_schema, Url):
                    raise ValueError('the provided value in `applicable_on_url_schema` needs to be an `Url` '
                                     'object or a list of `Url` objects')
        elif isinstance(expected_schema, Url):
            expected_schema = [expected_schema]
        else:
            raise TypeError('the provided value in `applicable_on_url_schema` needs to be an `Url` object or a list '
                            'of `Url` objects')

        for cur_schema in expected_schema:
            if cur_schema.compare(current_url, allow_schemas=True):
                return True
        return False
