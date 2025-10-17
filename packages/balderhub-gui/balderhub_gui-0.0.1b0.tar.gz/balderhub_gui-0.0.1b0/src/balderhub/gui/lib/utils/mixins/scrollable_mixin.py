from abc import ABC, abstractmethod


class ScrollableMixin(ABC):
    """
    mixin class that describes that the content of this element can be scrolled
    """
    @abstractmethod
    def scroll_to_beginning(self) -> None:
        """
        This method scrolls to the beginning of the scrollable area
        """

    @abstractmethod
    def scroll_once_forward(self) -> None:
        """
        This method scrolls for one element forward
        """

    @abstractmethod
    def scroll_once_backward(self) -> None:
        """
        This method scrolls for one element backward
        """

    @abstractmethod
    def scroll_to_end(self) -> None:
        """
        This method scrolls to the end of the scrollable area
        """
