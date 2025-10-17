from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TypeVar
import time

AbstractElementTypeT = TypeVar("AbstractElementTypeT", bound="AbstractElement")


class AbstractElement(ABC):
    """
    The base class for any kind of elements mostly used in another element or a :class:`PageFeature`
    """

    @abstractmethod
    def exists(self) -> bool:
        """
        Callback that checks if this element exists.

        .. note::
            The existence of an element does not necessarily mean that it visible.

        :return: True if it does exist, otherwise False
        """

    def exists_within(self, time_sec: float) -> bool:
        """
        This method waits for a maximum of `time_sec` seconds for the existence of this element. If the element does
        not exist within the provided time `time_sec`, the method returns False.

        :param time_sec: the maximum time to wait for this element to exist
        :return: True if it does exist, otherwise False
        """
        start_time = time.perf_counter()
        while time.perf_counter() - start_time < time_sec:
            if self.exists():
                return True
            time.sleep(0.01)
        return False

    def wait_to_exist_for(self: AbstractElementTypeT, timeout_sec: float) -> AbstractElementTypeT:
        """
        This method waits for a maximum of `timeout_sec` seconds for the existence of this element.

        :param timeout_sec: the maximum time in seconds to wait for this element to exist
        :raises TimeoutError: if timeout is exceeded
        """
        if not self.exists_within(time_sec=timeout_sec):
            raise TimeoutError(f'element {self} does not exist within {timeout_sec} seconds')
        return self

    def was_removed_within(self, time_sec: float) -> bool:
        """
        This method waits for a maximum of `time_sec` seconds for the removement of this element. If the element still
        exists after `time_sec`, the method returns False.

        :param time_sec: the maximum time to wait for this element to be removed
        :return: True if it does not exist anymore (within the `time_sec`), otherwise False
        """
        start_time = time.perf_counter()
        while time.perf_counter() - start_time < time_sec:
            if not self.exists():
                return True
            time.sleep(0.01)
        return False

    def wait_to_be_removed_for(self: AbstractElementTypeT, timeout_sec: float) -> AbstractElementTypeT:
        """
        This method waits for a maximum of `timeout_sec` seconds for the removement of this element.

        :param timeout_sec: the maximum time to wait for this element to be removed
        :raises TimeoutError: if timeout is exceeded
        """
        if not self.was_removed_within(time_sec=timeout_sec):
            raise TimeoutError(f'element {self} was not removed within {timeout_sec} seconds')
        return self
