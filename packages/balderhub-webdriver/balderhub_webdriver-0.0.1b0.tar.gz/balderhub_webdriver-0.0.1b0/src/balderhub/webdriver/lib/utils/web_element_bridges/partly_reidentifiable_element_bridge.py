from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Union, TYPE_CHECKING


from .base_webdriver_element_bridge import BaseWebdriverElementBridge, RawElementT, BaseWebdriverDriverClassT
from ..selector import Selector


if TYPE_CHECKING:
    from .not_reidentifiable_element_bridge import NotReidentifiableElementBridge


class PartlyReidentifiableElementBridge(BaseWebdriverElementBridge, ABC):
    """
    A partly reidentifiable element bridge specifies a bridge that does only have a relative selector to another bridge
    object that is not re-identifiable. This type of bridges are only reidentifiable if their parent element is in a
    reliable state.
    """
    def __init__(
            self,
            driver: BaseWebdriverDriverClassT,
            relative_selector: Selector,
            parent: Union[PartlyReidentifiableElementBridge, NotReidentifiableElementBridge]
    ):
        super().__init__(driver=driver, parent=parent)
        self._relative_selector = relative_selector

    def __eq__(self, other):
        if not isinstance(other, PartlyReidentifiableElementBridge):
            raise TypeError(f'can not compare elements from different bridge type (this is {self.__class__} '
                            f'| other is {other.__class__})')
        if self.parent != other.parent:
            return False
        if self.relative_selector != other.relative_selector:
            return False
        return True

    @property
    def raw_element(self) -> RawElementT:
        if self._raw_element is None:
            self.re_identify_raw_element()
        return self._raw_element

    @property
    def parent(self) -> Union[PartlyReidentifiableElementBridge, NotReidentifiableElementBridge]:
        return super().parent

    @abstractmethod
    def re_identify_raw_element(self) -> RawElementT:
        """
        This method re-identifies the element by requesting it again from the main driver. This method automatically
        updates the internal reference for this object.

        :return: the re-identified raw element
        """

    @property
    def relative_selector(self) -> Selector:
        """
        :return: returns the relative selector.
        """
        return self._relative_selector
