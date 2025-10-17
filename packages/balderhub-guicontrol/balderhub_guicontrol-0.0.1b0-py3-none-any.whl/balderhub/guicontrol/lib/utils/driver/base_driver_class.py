from __future__ import annotations
from abc import ABC, abstractmethod

from typing import TYPE_CHECKING

from balderhub.gui.lib.utils.base_selector import BaseSelector



if TYPE_CHECKING:
    from ..element_bridges.base_element_bridge import BaseElementBridge


class BaseDriverClass(ABC):
    """
    This is the base driver class. It provides a general interface for getting bridges. These bridges allow a custom
    implementation for any type of gui control interface.
    """

    @abstractmethod
    def find_bridge(self, selector: BaseSelector) -> BaseElementBridge:
        """
        This method returns a specific bridge object identified by the provided selector.

        :param selector: the selector to identify the element
        :return: the bridge object
        """

    @abstractmethod
    def find_bridges(self, selector: BaseSelector) -> BaseElementBridge:
        """
        This method returns a list of bridge objects identified by the provided selector.

        :param selector: the selector to identify the elements
        :return: a list of bridge objects
        """

    @abstractmethod
    def quit(self):
        """
        This method releases all resources belonging to this driver.
        """
