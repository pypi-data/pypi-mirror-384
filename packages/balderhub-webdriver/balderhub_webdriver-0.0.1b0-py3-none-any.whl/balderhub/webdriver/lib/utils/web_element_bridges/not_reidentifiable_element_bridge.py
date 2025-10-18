from __future__ import annotations
from abc import ABC
from typing import Optional
from .base_webdriver_element_bridge import BaseWebdriverElementBridge, RawElementT, BaseWebdriverDriverClassT


class NotReidentifiableElementBridge(BaseWebdriverElementBridge, ABC):
    """
    A non reidentifiable element bridge can not re-identify an element by itself, because it does not specify absolute
    selectors.
    """

    def __init__(
            self,
            driver: BaseWebdriverDriverClassT,
            raw_element: RawElementT,
            parent: Optional[BaseWebdriverElementBridge] = None
    ):
        super().__init__(driver=driver, parent=parent)
        self._raw_element = raw_element

    def __eq__(self, other):
        raise TypeError('can not compare elements that were created out of web elements')
