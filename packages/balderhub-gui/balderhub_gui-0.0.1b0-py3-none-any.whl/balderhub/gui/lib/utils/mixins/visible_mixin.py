from abc import ABC, abstractmethod
from typing import TypeVar
import time

VisibleMixinTypeT = TypeVar("VisibleMixinTypeT", bound="VisibleMixin")


class VisibleMixin(ABC):
    """
    mixin class that describes a visible element
    """

    @abstractmethod
    def is_visible(self) -> bool:
        """
        This method returns True if the element is visible.

        .. note::
            This method also returns True if the element is theoretically visible but not visible because other
            elements cover it up.

        :return: True if the element is shown, otherwise it returns False
        """

    def is_visible_within(self, time_sec: float) -> bool:
        """
        This method waits for a maximum of `time_sec` seconds for the element to be visible. If the element is not
        shown within the provided time `time_sec`, the method returns False.

        :param time_sec: the maximum time to wait for this element to be visbile
        :return: True if it is visible, otherwise False
        """
        start_time = time.perf_counter()
        while time.perf_counter() - start_time < time_sec:
            if self.is_visible():
                return True
            time.sleep(0.01)
        return False

    def wait_to_be_visible_for(self: VisibleMixinTypeT, timeout_sec: float) -> VisibleMixinTypeT:
        """
        This method waits for a maximum of `timeout_sec` seconds for the element to be visible.

        :param timeout_sec: the maximum time in seconds to wait for this element to be visible
        :raises TimeoutError: if timeout is exceeded
        """
        if not self.is_visible_within(time_sec=timeout_sec):
            raise TimeoutError(f'element {self} was not visible within {timeout_sec} seconds')
        return self

    def was_hidden_within(self, time_sec: float) -> bool:
        """
        This method waits for a maximum of `time_sec` seconds for the hiddenness of this element. If the element is
        still visible after `time_sec`, the method returns False.

        :param time_sec: the maximum time to wait for this element to be hidden
        :return: True if it is not shown anymore (within the `time_sec`), otherwise False
        """
        start_time = time.perf_counter()
        while time.perf_counter() - start_time < time_sec:
            if not self.is_visible():
                return True
            time.sleep(0.01)
        return False

    def wait_to_be_hidden_for(self: VisibleMixinTypeT, timeout_sec: float) -> VisibleMixinTypeT:
        """
        This method waits for a maximum of `timeout_sec` seconds for the element to be hidden.

        :param timeout_sec: the maximum time to wait for this element to be hidden
        :raises TimeoutError: if timeout is exceeded
        """
        if not self.was_hidden_within(time_sec=timeout_sec):
            raise TimeoutError(f'element {self} was not hidden within {timeout_sec} seconds')
        return self
