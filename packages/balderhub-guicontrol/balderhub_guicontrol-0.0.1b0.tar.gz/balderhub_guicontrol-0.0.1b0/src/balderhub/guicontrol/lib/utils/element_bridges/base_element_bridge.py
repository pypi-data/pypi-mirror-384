from __future__ import annotations
from abc import ABC
from typing import TypeVar, Union, Optional

from ..driver.base_driver_class import BaseDriverClass

RawElementT = TypeVar('RawElementT')
BaseDriverClassT = TypeVar('BaseDriverClassT', bound=BaseDriverClass)


class BaseElementBridge(ABC):
    """
    The abstract base class for every element bridge. It holds common properties and methods that are
    used in all kinds of element bridge classes.
    """

    def __init__(self, driver: BaseDriverClassT, parent: Optional[BaseElementBridge]):
        """
        Creates a new instance

        :param driver: the base driver class
        :param parent: the parent web element bridge (if this element has a parent element)
        """
        self._driver = driver
        self._parent = parent
        self._raw_element: RawElementT = None

    @property
    def driver(self) -> BaseDriverClassT:
        """
        :return: returns the driver class, this bridge was created from
        """
        return self._driver

    @property
    def parent(self) -> Union[BaseElementBridge, None]:
        """
        :return: returns the defined parent web element bridge if a parent does exist
        """
        return self._parent

    @property
    def raw_element(self) -> RawElementT:
        """
        :return: returns the raw web element (depending on the underlying framework)
        """
        return self._raw_element
