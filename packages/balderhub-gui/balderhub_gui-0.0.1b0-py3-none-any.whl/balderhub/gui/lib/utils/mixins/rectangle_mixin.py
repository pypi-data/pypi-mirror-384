from abc import ABC, abstractmethod


class RectangleMixin(ABC):
    """
    mixin class that describes a rectangle object
    """

    @property
    @abstractmethod
    def width(self) -> float:
        """
        :return: returns the width of the element
        """

    @property
    @abstractmethod
    def height(self) -> float:
        """
        :return: returns the height of the element
        """
