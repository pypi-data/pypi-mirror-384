from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TypeVar, List, TYPE_CHECKING, Union, Optional, Any

from balderhub.guicontrol.lib.utils.element_bridges.base_element_bridge import BaseElementBridge, RawElementT

from ..driver.base_webdriver_driver_class import BaseWebdriverDriverClass
from ..selector import Selector

BaseWebdriverDriverClassT = TypeVar('BaseWebdriverDriverClassT', bound=BaseWebdriverDriverClass)

if TYPE_CHECKING:
    from .fully_reidentifiable_element_bridge import FullyReidentifiableElementBridge
    from .not_reidentifiable_element_bridge import NotReidentifiableElementBridge
    from .partly_reidentifiable_element_bridge import PartlyReidentifiableElementBridge


# pylint: disable-next=too-many-public-methods
class BaseWebdriverElementBridge(BaseElementBridge, ABC):
    """
    The abstract base class implementation for every element bridge. It holds common properties and methods that are
    used in all kinds of web element bridge classes.
    """

    def __init__(self, driver: BaseWebdriverDriverClassT, parent: Optional[BaseWebdriverElementBridge]):
        """
        Creates a new instance

        :param driver: the base driver class
        :param parent: the parent web element bridge (if this element has a parent element)
        """
        super().__init__(driver, parent)

    @property
    def driver(self) -> BaseWebdriverDriverClassT:
        """
        :return: returns the driver class, this bridge was created from
        """
        return self._driver

    @property
    def parent(self) -> Union[BaseWebdriverElementBridge, None]:
        """
        :return: returns the defined parent web element bridge if a parent does exist
        """
        return self._parent

    @abstractmethod
    def find_raw_element(self, selector: Selector) -> RawElementT:
        """
        Method to find a specific raw web element by its selector that is a child of the current one

        :param selector: the selector specifying the element (relative to this one)
        :return: the raw web element (depending on the underlying framework)
        """

    @abstractmethod
    def find_raw_elements(self, selector: Selector) -> List[RawElementT]:
        """
        Method to find raw web elements matching the provided relative selector as a child of the current one

        :param selector: the selector specifying the elements (relative to this one)
        :return: the raw web element (depending on the underlying framework)
        """

    @abstractmethod
    def find_bridge(
            self,
            selector: Selector
    ) -> Union[FullyReidentifiableElementBridge, PartlyReidentifiableElementBridge]:
        """
        Method to directly returning the bridge of a specific raw web element by its selector that is a child of the
        current one. In case that the element can be reidentified completely by the selector (f.e. because the selector
        is By.ID) the method returns a :class:`FullyReidentifiableElementBridge` object. Otherwise, the method returns
        a :class:`PartlyReidentifiableElementBridge` object.

        :param selector: the selector specifying the element (relative to this one)
        :return: the bridge object of the element specified by the selector
        """

    @abstractmethod
    def find_bridges(self, selector: Selector) -> List[NotReidentifiableElementBridge]:
        """
        Method to directly returning a list of bridge objects for raw web elements matching the provided relative
        selector as a child of the current one

        :param selector: the selector specifying the elements (relative to this one)
        :return: a list with all matching bridge objects (depending on the underlying framework)
        """

    @abstractmethod
    def exists(self) -> bool:
        """
        This method returns True if the element exists. An element exists if it is still part of the DOM.

        .. note::
            This does not mean, that it needs to be visible! Use the :meth:`BaseWebElementBridge.is_displayed` method
            instead.`

        :return: returns True if the element does exist otherwise false.
        """

    @abstractmethod
    def is_displayed(self) -> bool:
        """
        This method returns True if the element is visible.

        :return: returns True if the element does exist otherwise false.
        """

    @abstractmethod
    def get_text_content(self) -> str:
        """
        This method returns the text of the element as a string.

        :return: returns the text of the element as a string
        """

    @abstractmethod
    def is_clickable(self) -> bool:
        """
        This method returns True if the element is (theoretically) clickable.

        :return: returns True if the element is (theoretically) clickable, otherwise False.
        """

    ########################################################################################################
    # STATE (Section 12.4: https://www.w3.org/TR/webdriver2/#state)
    ########################################################################################################

    @abstractmethod
    def is_selected(self) -> bool:
        """
        The Is Element Selected command determines if the referenced element is selected or not. This operation only
        makes sense on input elements of the Checkbox- and Radio Button states, or on option elements.

        Reference: https://www.w3.org/TR/webdriver2/#is-element-selected

        :return: returns True if the element is selected.
        """

    @abstractmethod
    def get_attribute(self, name: Any) -> Union[str, None]:
        """
        Reference: https://www.w3.org/TR/webdriver2/#get-element-attribute

        :param name: the attribute name
        :return: a attribute value or None if there is no attribute for the provided name
        """

    @abstractmethod
    def get_property(self, name: Any) -> Any:
        """
        Reference: https://www.w3.org/TR/webdriver2/#get-element-property

        :param name: the property name
        :return: the element property value
        """

    @abstractmethod
    def get_css_value(self, name: Any) -> str:
        """
        Reference: https://www.w3.org/TR/webdriver2/#get-element-css-value

        :param name: the css property name
        :return: the element css value
        """

    @abstractmethod
    def get_tag_name(self) -> str:
        """
        Reference: https://www.w3.org/TR/webdriver2/#get-element-tag-name

        :return: the element tag name as string
        """

    @abstractmethod
    def get_rect(self) -> tuple[int, int, int, int]:
        """
        Reference: https://www.w3.org/TR/webdriver2/#get-element-rect

        :return: the rect of the element (x, y, width, height)
        """

    @abstractmethod
    def is_enabled(self) -> bool:
        """
        Reference: https://www.w3.org/TR/webdriver2/#is-element-enabled

        :return: returns True if the element is enabled.
        """

    #@abstractmethod
    #def get_computed_role(self):
    #    """
    #    Reference: https://www.w3.org/TR/webdriver2/#get-computed-role
    #    """

    #@abstractmethod
    #def get_computed_label(self):
    #    """
    #    Reference: https://www.w3.org/TR/webdriver2/#get-computed-label
    #    """

    ########################################################################################################
    # INTERACTIONS (Section 12.5: https://www.w3.org/TR/webdriver2/#element-interaction)
    # ==================================================================================
    # The element interaction commands provide a high-level instruction set for manipulating form controls. Unlike
    # Actions, they will implicitly scroll elements into view and check that it is an interactable element.
    #
    # Some resettable elements define their own clear algorithm. Unlike their associated reset algorithms, changes
    # made to form controls as part of these algorithms do count as changes caused by the user (and thus, e.g. do
    # cause input events to fire). When the clear algorithm is invoked for an element that does not define its own
    # clear algorithm, its reset algorithm must be invoked instead.
    #
    # The clear algorithm for input elements is to set the dirty value flag and dirty checkedness flag back to
    # false, set the value of the element to an empty string, set the checkedness of the element to true if the
    # element has a checked content attribute and false if it does not, empty the list of selected files, and then
    # invoke the value sanitization algorithm iff the type attribute's current state defines one.
    #
    # The clear algorithm for textarea elements is to set the dirty value flag back to false, and set the raw value
    # of element to an empty string.
    #
    # The clear algorithm for output elements is set the element's value mode flag to default and then to set the
    # element's textContent IDL attribute to an empty string (thus clearing the element's child nodes).
    ########################################################################################################

    @abstractmethod
    def click(self) -> None:
        """
        This method clicks the element.

        Reference:

        The Element Click command scrolls into view the element if it is not already pointer-interactable, and clicks
        its in-view center point.

        If the element's center point is obscured by another element, an element click intercepted error is returned.
        If the element is outside the viewport, an element not interactable error is returned.
        """

    @abstractmethod
    def clear(self):
        """
        Clears the element

        Reference: https://www.w3.org/TR/webdriver2/#element-clear
        """

    @abstractmethod
    def send_keys(self, text: str) -> None:
        """
        This method inserts a text into the field.

        Reference: https://www.w3.org/TR/webdriver2/#element-send-keys

        The Element Send Keys command scrolls into view the form control element and then sends the provided keys to
        the element. In case the element is not keyboard-interactable, an element not interactable error is returned.

        :param text: the text that should be inserted into the field
        """

    # TODO no part of the official Webdriver2 spec
    # @abstractmethod
    # def select_by_text(self, text_of_option_to_select: str) -> None:
    #     """
    #     This method selects the element by shown text.
    #     :param text_of_option_to_select: the expected text in the option that should be selected
    #     """
    #     pass
    #
    # @abstractmethod
    # def select_by_option_index(self, index: int) -> None:
    #     """
    #     This method selects the element by index.
    #     :param index: the option index that should be selected
    #     """
    #     pass
    #
    # @abstractmethod
    # def select_by_option_value(self, value: str):
    #     """
    #     This method selects the element by value.
    #     :param value: the option value that should be selected
    #     """
    #     pass
    #
    # @abstractmethod
    # def get_text_content(self) -> str:
    #     """
    #     This method returns the text content of the element.
    #
    #     :return: the full text content of the element
    #     """
    #     pass

    @abstractmethod
    def scroll_to_beginning(self, *args, **kwargs):
        """
        This method scrolls to the beginning of the scrollable element. It needs to make sure, that after calling it,
        the scrollable element is always at the beginning of its content. It raises an error, in case the element can
        not be scrolled.
        """

    @abstractmethod
    def scroll_for(self, scroll_steps: int, *args, **kwargs):
        """
        This method scrolls for one step.

        todo what unit should we use for scroll_steps?

        :param scroll_steps: the number of steps to scroll (positive: scrolls forward, negative: scrolls backward)
        """

    @abstractmethod
    def scroll_to_end(self, *args, **kwargs):
        """
        This method scrolls to the end of the scrollable element.  It needs to make sure, that after calling it, the
        scrollable element is always at the end of its content. It raises an error, in case the element can not
        be scrolled.
        """
