from typing import List
from abc import ABC, abstractmethod
from ..components.abstract_element import AbstractElement


class ListContainerMixin(ABC):
    """
    mixin class that describes that the element is a list-container
    """

    @abstractmethod
    def get_child_elements(self) -> List[AbstractElement]:
        """
        This method returns a list of elements that are contained within this container.
        :return: the list of elements that are contained within this container.
        """
