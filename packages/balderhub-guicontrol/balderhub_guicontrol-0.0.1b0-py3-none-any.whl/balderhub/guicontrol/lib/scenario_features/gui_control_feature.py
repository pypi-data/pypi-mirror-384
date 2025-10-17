from __future__ import annotations
from typing import Union

import balder

from ..utils.driver.base_driver_class import BaseDriverClass


class GuiControlFeature(balder.Feature):
    """
    Basic scenario feature implementation of a GUI control tool. It offers a simple interface for creating and
    quiting the tool.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._driver: Union[BaseDriverClass, None] = None

    @property
    def driver(self) -> BaseDriverClass:
        """
        :return: returns the base driver class (holds the custom implementation of the guicontrol tool)
        """
        return self._driver

    def create(self) -> None:
        """
        set up the guicontrol tool resource
        """
        raise NotImplementedError("this method needs to be implemented in subclass")

    def quit(self) -> bool:
        """
        releases all resources belonging to the driver

        :return: returns true in case the driver was initialized and quit call was successful
        """
        if self._driver is not None:
            self._driver.quit()
            return True
        return False
