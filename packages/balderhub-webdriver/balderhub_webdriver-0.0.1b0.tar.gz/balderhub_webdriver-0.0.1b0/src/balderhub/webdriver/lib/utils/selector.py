from balderhub.gui.lib.utils import BaseSelector


class Selector(BaseSelector):
    """
    This selector class is the common selector for guicontrol packages that supports the webdriver protocol.
    """

    class By(BaseSelector.By):
        """
        This is implemented based on https://www.w3.org/TR/webdriver2/#locator-strategies.
        """
        CSS_SELECTOR = "css selector"
        LINK_TEXT = "link text"
        PARTIAL_LINK_TEXT = "partial link text"
        TAG_NAME = "tag name"
        XPATH = "xpath"
