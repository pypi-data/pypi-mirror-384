from abc import ABC, abstractmethod


class CircleMixin(ABC):
    """
    mixin class that describes a circle object
    """

    @property
    @abstractmethod
    def diameter(self) -> float:
        """
        :return: returns the circle diameter
        """
