from abc import ABC, abstractmethod
from .list_container_mixin import ListContainerMixin

class PaginatedContainerMixin(ListContainerMixin, ABC):
    """
    This mixin is used for list container with a pagination functionality
    """

    class PageDoesNotExist(Exception):
        """
        This exception is raised when a page does not exist.
        """

    @property
    @abstractmethod
    def current_page(self) -> int:
        """
        :return: returns the current page number
        """

    @property
    @abstractmethod
    def min_max_page(self) -> tuple[int, int]:
        """
        :return: returns the min and the max page that exists for this paginated list
        """

    @abstractmethod
    def go_to_page(self, page: int) -> None:
        """
        This method goes to the provided page.
        :param page: the page index to go
        :raises PageDoesNotExist: if the page provided page does not exist
        """

    @abstractmethod
    def go_to_next_page(self):
        """
        This method goes to the next page
        :raises PageDoesNotExist: if the current page is the latest already
        """

    @abstractmethod
    def go_to_previous_page(self):
        """
        This method goes to the previous page
        :raises PageDoesNotExist: if the current page is the latest already
        """
