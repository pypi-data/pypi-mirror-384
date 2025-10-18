from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Optional, Union


from .base_webdriver_element_bridge import BaseWebdriverElementBridge, RawElementT, BaseWebdriverDriverClassT
from ..selector import Selector


class FullyReidentifiableElementBridge(BaseWebdriverElementBridge, ABC):
    """
    A fully reidentifiable element bridge specifies the element in an absolute manner. It doesn't matter if the element
    has a full absolute selector or has parents with re-identifiable selectors (so all parents need to be
    :class:`FullyReidentifiableElementBridge` objects)
    """

    def __init__(
            self,
            driver: BaseWebdriverDriverClassT,
            selector: Selector,
            parent: Optional[FullyReidentifiableElementBridge] = None
    ):
        super().__init__(driver=driver, parent=parent)
        self._selector = selector

    def __eq__(self, other):
        if not isinstance(other, FullyReidentifiableElementBridge):
            raise TypeError(f'can not compare elements from different bridge type (this is {self.__class__} '
                            f'| other is {other.__class__})')
        if self.parent != other.parent:
            return False
        if self.selector != other.selector:
            return False
        return True

    @property
    def raw_element(self) -> RawElementT:
        if self._raw_element is None:
            self.re_identify_raw_element()
        return self._raw_element

    @property
    def parent(self) -> Union[FullyReidentifiableElementBridge, None]:
        return super().parent

    @abstractmethod
    def re_identify_raw_element(self) -> RawElementT:
        """
        This method re-identifies the element by requesting it again from the main driver. This method automatically
        updates the internal reference for this object.

        :return: the re-identified raw element
        """

    @property
    def selector(self) -> Selector:
        """
        :return: the absolute selector this element bridge has.
        """
        return self._selector
