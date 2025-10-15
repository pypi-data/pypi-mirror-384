from typing import Optional, List
from playwright import sync_api


class GraphexPlaywrightUtilsException(Exception):
    """Base class for all Graphex ESXi Utils exceptions."""

    pass


class DownloadDidNotStart(GraphexPlaywrightUtilsException):
    """
    Raised when a download is expected but did not occur within a timeout.

    :param timeout: the timeout in ms.
    """

    def __init__(self, expected_downloads: int, actual_downloads: int):
        super().__init__(
            f"Was expecting {expected_downloads} download{'s' if expected_downloads>1 else ''} but only {actual_downloads} download{'s' if expected_downloads>1 else ''} occured."
        )


class DownloadFailed(GraphexPlaywrightUtilsException):
    """
    Raised when a download is expected but did not occur within a timeout.

    :param timeout: the timeout in ms.
    """

    def __init__(self, url: str, msg: str):
        super().__init__(f"Download failed for url {url}:{msg}")


class DownloadTimedOut(GraphexPlaywrightUtilsException):
    """
    Raised when a download is expected but did not occur within a timeout.

    :param timeout: the timeout in ms.
    """

    def __init__(self, urls: List[str], timeout: int):
        super().__init__(
            f"Download started for url{'s' if len(urls)>1 else ''} {', '.join(urls)}, but failed to finished within {timeout}."
        )


class URLNotReachable(GraphexPlaywrightUtilsException):
    """
    Raised when creating a Page Datatype with a url that is not reachable.

    :param timeout: the timeout in ms.
    """

    def __init__(self, url: str):
        super().__init__(f"Playwright browser can not access {url}.")


class FileAlreadyExists(GraphexPlaywrightUtilsException):
    """
    Raised if file aready exists on local system.

    :param filename: path to file
    """

    def __init__(self, filename: str):
        super().__init__(f"Path {filename} already exists on local system.")


class InvalidDestinationError(GraphexPlaywrightUtilsException):
    """
    Invalid desition for local system.

    :param filename: path to file
    """

    def __init__(self, filename: str):
        super().__init__(
            f"Path {filename} is invalid on local system. Path must be directory, or absolute path where parent directories exist."
        )


class PageOrLocatorNotBoth(GraphexPlaywrightUtilsException):
    """
    Invalid desition for local system.

    :param filename: path to file
    """

    def __init__(self, is_none: bool):
        pre_msg = (
            "Neither Page or Locator input is selected."
            if is_none
            else "Both Page and Locator input are selected."
        )
        super().__init__(f"{pre_msg} Page or Locator input must be selected, but not both.")


class Path(GraphexPlaywrightUtilsException):
    """
    Raised if file aready exists on local system.

    :param filename: path to file
    """

    def __init__(self, filename: str):
        super().__init__(f"Path {filename} already exists on local system.")


class IncorrectFileType(GraphexPlaywrightUtilsException):
    """
    Raised if file aready exists on local system.

    :param filename: path to file
    """

    def __init__(self, filename: str):
        super().__init__(f"'{filename}' is of incorrect type. Must be 'png' or 'jpeg'.")


class PlaywrightScriptError(Exception):
    def __init__(
        self, script: str, lineno: Optional[int], original_exception: BaseException
    ) -> None:
        self.script = script
        self.lineno = lineno
        self.original_exception = original_exception

    def __str__(self) -> str:
        lines = self.script.splitlines()
        max_lineno = len(lines)
        width = len(str(max_lineno))  # Determine the width of the line numbers
        output = []
        exception_name = type(self.original_exception).__name__  # Get the name of the exception
        error_marker = f"({exception_name}) ---> "
        prefix_len = len(error_marker)

        if self.lineno:
            output.append("Playwright script error:")
            for idx, line in enumerate(lines, start=1):
                if idx == self.lineno:
                    prefix = error_marker
                else:
                    prefix = " " * (prefix_len - 1)

                # Combine the three formatted strings
                formatted_line = f"{prefix}{idx:>{width}}: {line}"
                output.append(formatted_line)
        error_message = "\n".join(output)

        pre_message = ""
        if isinstance(self.original_exception, sync_api.TimeoutError):
            pre_message = "Timeout errors may arise if: \na) The specified element is not present on the page, or \nb) The element is not on the page yet due to loading delays."
        if self.lineno:
            return f"{error_message}\n\n {pre_message} \n\n Original {exception_name} Exception at line {self.lineno}:\n {self.original_exception}"
        else:
            return f"{pre_message} \n\nOriginal {exception_name} Exception \n: {self.original_exception}"
