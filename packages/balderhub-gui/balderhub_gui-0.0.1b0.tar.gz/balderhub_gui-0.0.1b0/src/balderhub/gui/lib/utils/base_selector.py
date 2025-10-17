from __future__ import annotations
from typing import TypeVar
import enum
from abc import ABC


ConvertedBaseSelectorTypeT = TypeVar('ConvertedBaseSelectorTypeT', bound='BaseSelector')


class BaseSelector(ABC):
    """
    Base class that is used to identify GUI elements. It is normally overwritten in sub packages.
    """
    class By(enum.Enum):
        """
        Enum that describes the selecting type
        """

    class NoTranslationPossibleError(Exception):
        """
        raised when no translation is possible, because no translation was defined.
        """

    translations: dict[type[BaseSelector], dict[BaseSelector.By, BaseSelector.By]] = {}

    def __init__(self, by_type: By, identifier: str):
        self._by_type = by_type
        self._identifier = identifier

    def __eq__(self, other):
        return self.by_type == other.by_type and self.identifier == other.identifier

    def __str__(self):
        return f"Selector<{self._by_type}: {self._identifier}>"

    @property
    def by_type(self) -> By:
        """
        :return: the used selecting type
        """
        return self._by_type

    @property
    def identifier(self) -> str:
        """
        :return: the value of the selector, that is used to identify the element
        """
        return self._identifier

    def translate_to(self, other_selector_type: type[ConvertedBaseSelectorTypeT]) -> ConvertedBaseSelectorTypeT:
        """
        This method translates the given selector value to the corresponding selector value of the provided selector \
        type.

        :param other_selector_type: the selector type object this selector should translate to
        :return: the same selector value like this selector but as translated object from type given in
                 ``other_selector_type``
        """
        if not isinstance(other_selector_type, type) or not issubclass(other_selector_type, BaseSelector):
            raise TypeError(f'other_selector_type must be a subclass of `{BaseSelector.__name__}`')

        if self.__class__ == other_selector_type:
            return self

        translation_from_self = self.translations.get(other_selector_type)
        translation_from_other = other_selector_type.translations.get(self.__class__)
        reversed_translation_from_other = None
        if translation_from_other is not None:
            # reverse it
            reversed_translation_from_other = {v: k for k, v in translation_from_other.items()}
            if len(reversed_translation_from_other) != len(translation_from_other):
                raise KeyError('unable to reverse translation because some values are used more than once')

        if translation_from_self is None and translation_from_other is None:
            raise self.NoTranslationPossibleError(
                'can not translate selector because neither this selector has a translation nor the other element '
                'provides a translation for these specific types')

        result_from_self = translation_from_self[self.by_type] if translation_from_self is not None else None
        result_from_other = \
            reversed_translation_from_other[self.by_type] if reversed_translation_from_other is not None else None

        if result_from_self is not None and result_from_other is not None and result_from_self != result_from_other:
            raise self.NoTranslationPossibleError(
                f'both selector types define a own translation that return different results - {self.__class__} '
                f'returns `{result_from_self}` and {other_selector_type} returns `{result_from_other}`')

        new_by = result_from_self if translation_from_other is None else result_from_other
        return other_selector_type(new_by, self.identifier)
