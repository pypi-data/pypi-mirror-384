from abc import ABC, abstractmethod


class SelectByHiddenValueMixin(ABC):
    """
    mixin class that describes that this element has selectable elements that can be selected-by-value
    """

    @abstractmethod
    def select_by_value(self, value: object) -> None:
        """
        This method selects the element by its value
        :param value: the value to select
        """
