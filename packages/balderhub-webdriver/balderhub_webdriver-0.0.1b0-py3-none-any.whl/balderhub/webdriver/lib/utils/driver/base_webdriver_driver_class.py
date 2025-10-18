from __future__ import annotations
from abc import ABC, abstractmethod

from typing import Optional, Union, Any, TYPE_CHECKING

from balderhub.guicontrol.lib.utils.driver import BaseDriverClass
from balderhub.url.lib.utils import Url

from ..selector import Selector

if TYPE_CHECKING:
    from ..web_element_bridges.base_webdriver_element_bridge import BaseWebdriverElementBridge
    from ..web_element_bridges.fully_reidentifiable_element_bridge import FullyReidentifiableElementBridge
    from ..web_element_bridges.not_reidentifiable_element_bridge import NotReidentifiableElementBridge
    from ..web_element_bridges.partly_reidentifiable_element_bridge import PartlyReidentifiableElementBridge


class BaseWebdriverDriverClass(BaseDriverClass, ABC):
    """
    This is the base driver class for any ``balderhub-guicontrol`` packages that supports the webdriver interface.
    """
    # TODO need to add context stuff here: https://www.w3.org/TR/webdriver2/#contexts

    @abstractmethod
    def get_bridge_for_raw_element(
            self,
            raw_element,
            parent: Optional[BaseWebdriverElementBridge]=None
    ) -> NotReidentifiableElementBridge:
        """
        This method returns the bridge object for a raw selenium element.

        :param raw_element: the raw element of the browser-automation tool that is used here
        :param parent: the parent bridge of the element that is a parent of this element (or None if there is no parent
                       specified)
        :return: the newly created bridge object
        """

    @abstractmethod
    def find_bridge(
            self,
            selector: Selector
    ) -> Union[FullyReidentifiableElementBridge, PartlyReidentifiableElementBridge]:
        """
        This method returns a specific bridge object identified by a selector. In case that the element can be
        reidentified completely by the selector (f.e. because the selector is By.ID) the method returns a

        :class:`FullyReidentifiableElementBridge` object. Otherwise, the method returns a
        :class:`PartlyReidentifiableElementBridge` object.

        :param selector: the selector to identify the element
        :return: the bridge object (if it is reidentifiable a :class:`FullyReidentifiableElementBridge` object,
                 otherwise :class:`PartlyReidentifiableElementBridge`)
        """

    @abstractmethod
    def find_bridges(self, selector: Selector) -> list[NotReidentifiableElementBridge]:
        """
        This method returns a list of bridge objects identified by the provided selector.

        :param selector: the selector to identify the elements
        :return: a list of :class:`NotReidentifiableElementBridge` objects (can not be reidentifiable because all have
                 the same selector)
        """

    @abstractmethod
    def quit(self):
        """
        This method releases all resources belonging to this driver.
        """

    ########################################################################################################
    # NAVIGATION (Section 10: https://www.w3.org/TR/webdriver2/#navigation)
    # =====================================================================
    # The commands in this section allow navigation of the session's current top-level browsing context to new URLs and
    # introspection of the document currently loaded in this browsing context.
    ########################################################################################################

    @abstractmethod
    def navigate_to(self, url: Union[Url, str]):
        """
        Opens the provided URL in the related browser window

        :param url: the URL that should be opened
        """

    @abstractmethod
    def go_back(self):
        """
        This command causes the browser to traverse one step backward in the joint session history of session's
        current top-level browsing context. This is equivalent to pressing the back button in the browser or
        invoking window.history.back.

        Reference: https://www.w3.org/TR/webdriver2/#back
        """

    @abstractmethod
    def go_forward(self):
        """
        This command causes the browser to traverse one step forwards in the joint session history of session's current
        top-level browsing context. This is equivalent to pressing the forward button in the browser chrome or invoking
        ``window.history.forward``.

        Reference: https://www.w3.org/TR/webdriver2/#forward
        """

    @abstractmethod
    def refresh(self):
        """
        This command causes the browser to reload the page.

        Reference: https://www.w3.org/TR/webdriver2/#refresh
        """

    @property
    @abstractmethod
    def page_title(self) -> str:
        """
        :return: the title of the page
        """

    @property
    @abstractmethod
    def current_url(self) -> Url:
        """
        :return: returns the current opened URL
        """

    ########################################################################################################
    # DOCUMENT (Section 13: https://www.w3.org/TR/webdriver2/#document)
    ########################################################################################################

    @abstractmethod
    def get_page_source(self) -> str:
        """
        The Get Page Source command returns a string serialization of the DOM of session's current browsing context
        active document.

        Reference: https://www.w3.org/TR/webdriver2/#get-page-source

        :return: a string serialization of the DOM of session's current browsing context
        """

    @abstractmethod
    def execute_sync_script(self, script: str, *args: Any) -> Any:
        """
        This command executes the given script in the current browser context.

        Reference: https://www.w3.org/TR/webdriver2/#execute-script

        :param script: the script to be executed in the current browser context
        :param args: arguments to be passed to the script
        """

    @abstractmethod
    def execute_async_script(self, script: str, *args: Any) -> Any:
        """
        This command executes the given script in the current browser context.

        Reference: https://www.w3.org/TR/webdriver2/#execute-async-script

        :param script: the script to be executed in the current browser context
        :param args: arguments to be passed to the script
        """

    ########################################################################################################
    # COOKIES (Section 14: https://www.w3.org/TR/webdriver2/#cookies)
    # ===============================================================
    # This section describes the interaction with cookies as described in [RFC6265].
    #
    # A cookie is described in [RFC6265] by a name-value pair holding the cookie's data, followed by zero or more
    # attribute-value pairs describing its characteristics.
    ########################################################################################################

    @abstractmethod
    def get_all_cookies(self) -> list[dict]:
        """
        This method returns a list of all cookies in the current browser context.

        Reference: https://www.w3.org/TR/webdriver2/#get-all-cookies
        """

    @abstractmethod
    def get_cookie(self, name: str) -> Union[dict, None]:
        """
        This method returns a specific cookie by name.

        Reference: https://www.w3.org/TR/webdriver2/#get-named-cookie

        :param name: the name of the cookie
        :return: the content of the dictionary or None if the cookie is not found
        """

    @abstractmethod
    def add_cookie(self, cookie_dict: dict) -> None:
        """
        This method adds a specific cookie to the current browser context.

        Reference: https://www.w3.org/TR/webdriver2/#add-cookie

        :param cookie_dict: the content of the cookie as dictionary
        """

    @abstractmethod
    def delete_cookie(self, name: str):
        """
        This method deletes a specific cookie from the current browser context.

        Reference: https://www.w3.org/TR/webdriver2/#delete-cookie

        :param name: the name of the cookie that should be deleted
        """

    @abstractmethod
    def delete_all_cookies(self):
        """
        This method deletes all cookies in the current browser context.

        Reference: https://www.w3.org/TR/webdriver2/#delete-all-cookies
        """
