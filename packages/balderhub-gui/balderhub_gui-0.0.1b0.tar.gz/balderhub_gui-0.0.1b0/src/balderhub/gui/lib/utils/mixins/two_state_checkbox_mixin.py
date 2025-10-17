from abc import ABC, abstractmethod


class TwoStateCheckboxMixin(ABC):
    """
    mixin class that describes that this element is a two-state checkbox
    """

    @abstractmethod
    def is_checked(self) -> bool:
        """
        This method returns True if the element is checked, otherwise False
        :return: True if the element is checked, otherwise False
        """
