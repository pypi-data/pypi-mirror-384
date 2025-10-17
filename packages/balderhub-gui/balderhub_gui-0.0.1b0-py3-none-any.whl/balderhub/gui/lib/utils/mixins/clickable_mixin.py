from abc import ABC, abstractmethod
from typing import TypeVar
import time

ClickableMixinTypeT = TypeVar("ClickableMixinTypeT", bound="ClickableMixin")


class ClickableMixin(ABC):
    """
    mixin class that describes a clickable element
    """

    @abstractmethod
    def click(self) -> None:
        """
        Executes a click at the element
        """

    @abstractmethod
    def is_clickable(self) -> bool:
        """
        This method checks if the element is theoretically clickable. This means, that no other element does cover it
        up.

        :return: True if the element should be theoretically clickable, False otherwise.
        """

    def is_clickable_within(self, time_sec: float) -> bool:
        """
        This method waits for a maximum of `time_sec` seconds for the element to be clickable. If the element is not
        clickable within the provided time `time_sec`, the method returns False.

        :param time_sec: the maximum time to wait for this element to be clickable
        :return: True if it is clickable, otherwise False
        """
        start_time = time.perf_counter()
        while time.perf_counter() - start_time < time_sec:
            if self.is_clickable():
                return True
            time.sleep(0.01)
        return False

    def wait_to_be_clickable_for(self: ClickableMixinTypeT, timeout_sec: float) -> ClickableMixinTypeT:
        """
        This method waits for a maximum of `timeout_sec` seconds for the element to be clickable.

        :param timeout_sec: the maximum time in seconds to wait for this element to be clickable
        :raises TimeoutError: if timeout is exceeded
        """
        if not self.is_clickable_within(time_sec=timeout_sec):
            raise TimeoutError(f'element {self} is not clickable within {timeout_sec} seconds')
        return self
