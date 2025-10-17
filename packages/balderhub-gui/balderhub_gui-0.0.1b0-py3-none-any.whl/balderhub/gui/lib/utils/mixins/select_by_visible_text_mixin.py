from abc import ABC, abstractmethod


class SelectByVisibleTextMixin(ABC):
    """
    mixin class that describes that this element has selectable elements that can be selected-by-visible-text
    """
    @abstractmethod
    def select_by_text(self, visible_text: str):
        """
        This method selects the element by visible text
        :param visible_text: the visible text of the element that should be selected
        """
