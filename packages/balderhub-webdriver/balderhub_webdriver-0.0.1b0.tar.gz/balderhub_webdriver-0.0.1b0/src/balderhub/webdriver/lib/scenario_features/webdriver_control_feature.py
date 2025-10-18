from __future__ import annotations
from typing import Union

from balderhub.guicontrol.lib.scenario_features import GuiControlFeature

from ..utils.driver.base_webdriver_driver_class import BaseWebdriverDriverClass


class WebdriverControlFeature(GuiControlFeature):
    """
    Basic scenario feature implementation for controlling GUIs over the Webdriver protocol.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._driver: Union[BaseWebdriverDriverClass, None] = None

    def create(self) -> None:
        """
        set up the used guicontrol webdriver tool
        """
        raise NotImplementedError("this method needs to be implemented in subclass")

    @property
    def driver(self) -> BaseWebdriverDriverClass:
        return self._driver
