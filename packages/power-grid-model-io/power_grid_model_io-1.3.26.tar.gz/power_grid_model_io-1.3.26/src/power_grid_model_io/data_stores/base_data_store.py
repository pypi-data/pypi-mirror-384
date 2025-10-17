# SPDX-FileCopyrightText: Contributors to the Power Grid Model project <powergridmodel@lfenergy.org>
#
# SPDX-License-Identifier: MPL-2.0
"""
Abstract data store class
"""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

import structlog

T = TypeVar("T")

LANGUAGE_EN = "en"
LANGUAGE_NL = "nl"
DICT_KEY_NUMBER = "key_number"
DICT_KEY_SUBNUMBER = "key_subnumber"
VISION_EXCEL_LAN_DICT = {
    LANGUAGE_EN: {
        DICT_KEY_NUMBER: "Number",
        DICT_KEY_SUBNUMBER: "Subnumber",
    },
    LANGUAGE_NL: {
        DICT_KEY_NUMBER: "Nummer",
        DICT_KEY_SUBNUMBER: "Subnummer",
    },
}


class BaseDataStore(Generic[T], ABC):
    """
    Abstract data store class
    """

    def __init__(self):
        """
        Initialize a logger
        """
        self._log = structlog.get_logger(type(self).__name__)

    @abstractmethod  # pragma: no cover
    def load(self) -> T:
        """
        The method that loads the data from one or more sources and returns it in the specified format.
        Note that the load() method does not receive a reference to the data source(s); i.e. the data source(s)
        should be set in the constructor, or in a separate member method.

        Returns: Loaded data of type <T>
        """

    @abstractmethod  # pragma: no cover
    def save(self, data: T) -> None:
        """
        The method that saves the data to one or more destinations.
        Note that the save() method does not receive a reference to the data destination(s); i.e. the data
        destination(s) should be set in the constructor, or in a separate member method.

        Args:
            data: Tha data to store shoul dbe of type <T>
        """
