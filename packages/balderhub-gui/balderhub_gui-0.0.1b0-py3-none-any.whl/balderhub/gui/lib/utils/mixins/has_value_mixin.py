from abc import ABC, abstractmethod


class HasValueMixin(ABC):
    """
    mixin class that describes an element that can have a value
    """

    @abstractmethod
    def get_value(self) -> object:
        """
        This method returns the value of the element.
        :return: the value of the element
        """
