import time
from balder import Feature


class PageFeature(Feature):
    """
    Base class that represents a page. This can be any type of page.
    """

    def is_applicable(self) -> bool:
        """
        Checks if this specific page can be used on the current screen.
        :return: True if this page object can be applied on the current screen, otherwise False
        """
        raise NotImplementedError

    def wait_for_page(self, timout_sec=10) -> None:
        """
        This method waits for a specific time to make sure that this page can be applied on the current screen.

        :param timout_sec: the maximum time in seconds to wait
        :raise TimeoutError: if the page cannot be applied
        """
        start_time = time.time()
        while time.time() - start_time < timout_sec:
            if self.is_applicable():
                return
        raise TimeoutError('timeout waiting for page to be visible')
