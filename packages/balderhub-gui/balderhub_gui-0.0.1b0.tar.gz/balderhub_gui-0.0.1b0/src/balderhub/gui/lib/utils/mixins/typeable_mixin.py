from abc import ABC, abstractmethod


class TypeableMixin(ABC):
    """
    mixin class that describes that you can type text in this checkbox
    """
    @abstractmethod
    def type_text(self, text: str, clean_before: bool = False)-> None:
        """
        This method types a text in this element.

        :param text: the text that should be inserted
        :param clean_before: True if the system should make sure that all previous filled text is deleted before
                             inserting any new text
        """
