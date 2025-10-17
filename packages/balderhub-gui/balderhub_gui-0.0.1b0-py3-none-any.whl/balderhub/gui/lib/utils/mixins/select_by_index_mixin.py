from abc import ABC, abstractmethod


class SelectByIndexMixin(ABC):
    """
    mixin class that describes that this element has selectable elements that can be selected-by-index
    """
    @abstractmethod
    def select_by_index(self, index: int) -> None:
        """
        This method selects the element by its index
        :param index: the index to select
        """
