import typing
import traceback
import types
import time
import re
import os
import base64
from abc import abstractmethod

from asyncio.exceptions import (
    InvalidStateError,
)
from playwright import (
    sync_api,
)

from graphex import (
    String,
    Boolean,
    Node,
    InputSocket,
    OptionalInputSocket,
    OutputSocket,
    ListOutputSocket,
    LinkOutputSocket,
    GraphexLogger,
    Number,
    ListInputSocket,
    DataContainer,
)

from graphex_webautomation_plugin import (
    datatypes,
    exceptions,
    constants,
)


class PlaywrightCommandNode(Node, is_template=True):
    @abstractmethod
    def _run_impl(self):
        pass

    def run(self):
        if hasattr(self, "tab_input") and getattr(self, "tab_input") is not None:
            page: sync_api.Page = getattr(self, "tab_input")
        elif hasattr(self, "locator_input") and getattr(self, "locator_input") is not None:
            page: sync_api.Page = getattr(self, "locator_input").page
        else:
            raise Exception("tab_input or locator_input must be defined")

        try:
            self._run_impl()
        except Exception as e:
            if "playwright" in e.__class__.__module__:
                self.logger.error(
                    "Error with playwright command. Attempting to display image below."
                )

                try:
                    self.logger.image(
                        base64.b64encode(
                            page.screenshot(
                                type="png",
                                full_page=False,
                            )
                        ).decode("utf-8")
                    )
                except Exception as screen_error:
                    self.logger.warning(
                        f"Attempted screenshot, but got this error: {str(screen_error)}"
                    )
            raise e


class CreatePlaywrightBrowserContext(Node, include_forward_link=False):
    name: str = "Create Playwright Browser Context"
    description: str = "Creates a synchronous browser context. Actions within 'Browser Actions' branch must be done within a single thread."
    categories: typing.List[str] = [
        "Web Automation",
        "Playwright",
    ]
    color: str = constants.COLOR_PLAYWRIGHT

    width = InputSocket(
        datatype=Number, name="Browser Width", description="Width of browser.", input_field=1920
    )
    height = InputSocket(
        datatype=Number, name="Browser Height", description="Height of browser.", input_field=1080
    )
    ignore_https_errors = OptionalInputSocket(
        datatype=Boolean,
        name="Ignore HTTPS Errors",
        description="Whether to ignore HTTPS errors when sending network requests.",
        input_field=True,
    )
    timeout = InputSocket(
        datatype=Number,
        name="Timeout",
        description="Timeout (ms) Playwright uses to wait for elements or actions.",
        input_field=30000,
    )
    browser_type = InputSocket(
        datatype=String,
        name="Browser Type",
        description="Browser to choose (Chromium or Firefox). These browsers must be installed on the machine.",
        input_field="chromium",
    )

    with_body = LinkOutputSocket(
        name="Browser Actions",
        description="Actions in this branch happen within the created browser context.",
    )
    browser_context = OutputSocket(
        name="Browser Context",
        datatype=datatypes.SyncBrowserContext,
        description="The Browser Context used to perform actions.",
    )
    completed = LinkOutputSocket(
        name="Completed",
        description="Branch to run when the 'Browser Actions' branch has completed.",
    )

    def run(self):
        with sync_api.sync_playwright() as playwright:
            browser: typing.Optional[sync_api.Browser] = None
            browser_context: typing.Optional[sync_api.BrowserContext] = None
            try:
                self.log(
                    f"Opening New Browser ({self.browser_type.capitalize()} {int(self.width)}x{int(self.height)})"
                )

                if self.browser_type.lower() not in ["chromium", "firefox"]:
                    raise ValueError(
                        f"'Browser Type' was '{self.browser_type.lower()}', must be either chromium or firefox"
                    )

                browser = (
                    playwright.chromium.launch(headless=True, timeout=self.timeout)
                    if self.browser_type == "chromium"
                    else playwright.firefox.launch(headless=True, timeout=self.timeout)
                )

                browser_context = browser.new_context(
                    ignore_https_errors=self.ignore_https_errors,
                    accept_downloads=True,
                    viewport=sync_api.ViewportSize(width=int(self.width), height=int(self.height)),
                )
                self.browser_context = browser_context

                for node in self.forward("Browser Actions"):
                    self._runtime.execute_node(node)

            except InvalidStateError as e:
                self.log(
                    f"Error with asynchronous operations: {str(e)}",
                    level="ERROR",
                )
            finally:
                if browser_context:
                    browser_context.close()
                if browser:
                    browser.close()

    def run_next(
        self,
    ):
        for node in self.forward("Completed"):
            self._runtime.execute_node(node)


class OpenPlaywrightPage(Node):
    name: str = "Playwright Browser: Open Tab"
    description: str = "Opens a Playwright Tab within a synchronous browser context. Actions on the tab persist after any action."
    categories: typing.List[str] = [
        "Web Automation",
        "Playwright",
    ]
    color: str = constants.COLOR_PLAYWRIGHT_TAB

    url = OptionalInputSocket(
        datatype=String,
        name="URL",
        description="Optional URL to open in the tab. If not provided, the tab will open to the browser's default page.",
        input_field="",
    )

    browser_context = InputSocket(
        name="Browser Context",
        datatype=datatypes.SyncBrowserContext,
        description="Browser Context",
    )

    output_tab = OutputSocket(
        datatype=datatypes.PlaywrightTab,
        name="Browser Tab",
        description="Playwright browser tab.",
    )

    def run(self):
        self.output_tab = self.browser_context.new_page()

        if self.url:
            self.log(f"Opening Tab: {self.url}")
            try:
                self.output_tab.goto(self.url)
            except sync_api.TimeoutError:
                raise exceptions.URLNotReachable(self.url)
        else:
            self.log("Opening default tab.")


class GoToPage(Node):
    name: str = "Playwright Tab: Go To URL"
    description: str = "Go to a URL on Playwright Tab. This will replace the current URL of the tab with the provided URL."
    categories: typing.List[str] = ["Web Automation", "Playwright", "Tab"]
    color: str = constants.COLOR_PLAYWRIGHT_TAB

    tab_input = InputSocket(
        datatype=datatypes.PlaywrightTab,
        name="Browser Tab",
        description="Playwright browser tab.",
    )
    url = InputSocket(
        datatype=String,
        name="URL",
        description="URL to navigate to in the Playwright tab.",
        input_field="",
    )

    output_tab = OutputSocket(
        datatype=datatypes.PlaywrightTab,
        name="Browser Tab",
        description="Playwright browser tab (same as input).",
    )

    def log_prefix(self):
        return f"[{self.name} - {self.tab_input.url}] "

    def run(self):
        self.output_tab = self.tab_input
        try:
            self.log(f"Swapping to URL: {self.url}")
            self.tab_input.goto(self.url)
        except sync_api.TimeoutError:
            raise exceptions.URLNotReachable(self.url)


class GetPageURL(Node):
    name: str = "Playwright Tab: Extract URL"
    description: str = "Get the current URL of the given tab."
    categories: typing.List[str] = ["Web Automation", "Playwright", "Tab"]
    color: str = constants.COLOR_PLAYWRIGHT_TAB

    tab_input = InputSocket(
        datatype=datatypes.PlaywrightTab,
        name="Browser Tab",
        description="Playwright browser tab.",
    )

    output_tab = OutputSocket(
        datatype=datatypes.PlaywrightTab,
        name="Browser Tab",
        description="Playwright browser tab (same as input).",
    )
    url = OutputSocket(
        datatype=String,
        name="URL",
        description="Current page URL",
    )

    def run(self):
        self.output_tab = self.tab_input
        self.url = self.tab_input.url


class BringTabToFront(PlaywrightCommandNode):
    name: str = "Playwright Tab: Bring To Front"
    description: str = "Activates and brings the specified Playwright tab to the foreground, simulating a click on the tab in the browser."
    categories: typing.List[str] = ["Web Automation", "Playwright", "Tab"]
    color: str = constants.COLOR_PLAYWRIGHT_TAB

    tab_input = InputSocket(
        datatype=datatypes.PlaywrightTab,
        name="Browser Tab",
        description="Playwright browser tab.",
    )

    output_tab = OutputSocket(
        datatype=datatypes.PlaywrightTab,
        name="Browser Tab",
        description="Playwright browser tab (same as input).",
    )

    def _run_impl(self):
        self.output_tab = self.tab_input
        self.tab_input.bring_to_front()


class LogScreenshot(Node):
    name: str = "Playwright Tab: Log Screen Shot"
    description: str = "Take a screenshot of the current browser page and display the image."
    categories: typing.List[str] = ["Web Automation", "Playwright", "Tab"]
    color: str = constants.COLOR_PLAYWRIGHT_TAB

    tab_input = InputSocket(
        datatype=datatypes.PlaywrightTab,
        name="Browser Tab",
        description="Playwright browser tab.",
    )
    fullscreen = InputSocket(
        datatype=Boolean,
        name="Fullscreen?",
        description="When true, takes a screenshot of the full scrollable page instead of the currently visible viewport.",
        input_field=False,
    )

    output_tab = OutputSocket(
        datatype=datatypes.PlaywrightTab,
        name="Browser Tab",
        description="Playwright browser tab (same as input).",
    )

    def log_prefix(self):
        return f"[{self.name} - {self.tab_input.url}] "

    def run(self):
        self.output_tab = self.tab_input
        self.debug("Taking screenshot.")
        self.logger.image(
            base64.b64encode(
                self.tab_input.screenshot(
                    type="png",
                    full_page=self.fullscreen,
                )
            ).decode("utf-8")
        )


class SaveScreenshot(Node):
    name: str = "Playwright Tab: Save Screenshot"
    description: str = "Save screenshot to local file. Must be a PNG or JPEG."
    categories: typing.List[str] = ["Web Automation", "Playwright", "Tab"]
    color: str = constants.COLOR_PLAYWRIGHT_TAB

    tab_input = InputSocket(
        datatype=datatypes.PlaywrightTab,
        name="Browser Tab",
        description="Playwright browser tab.",
    )
    dir = InputSocket(
        datatype=String,
        name="Directory",
        description="The directory in which to to save file.",
        input_field=".",
    )
    basename = OptionalInputSocket(
        datatype=String,
        name="Filename",
        description="Filename of image, i.e. image.png. Must be of type *.png or *.jpeg. If not provided, a name will be automatically generated.",
    )
    fullscreen = InputSocket(
        datatype=Boolean,
        name="Fullscreen?",
        description="When True, takes a screenshot of the full scrollable page instead of the currently visible viewport.",
        input_field=False,
    )
    overwrite = OptionalInputSocket(
        datatype=Boolean,
        name="Overwrite?",
        description="If True will overwrite file if it exists. Defaults to False",
        input_field=False,
    )
    image_log = InputSocket(
        datatype=Boolean,
        name="Log Image?",
        description="If True, also log the screenshot image.",
        input_field=True,
    )

    output_tab = OutputSocket(
        datatype=datatypes.PlaywrightTab,
        name="Browser Tab",
        description="Playwright browser tab (same as input).",
    )
    path = OutputSocket(
        datatype=String, name="Image Path", description="The absolute path to the saved image."
    )

    def log_prefix(self):
        return f"[{self.name} - {self.tab_input.url}] "

    def run(self):
        self.output_tab = self.tab_input
        basename = self.basename if self.basename else f"screenshot-{time.time_ns()}.png"
        image_type = os.path.splitext(basename)[1].lstrip(".")

        if not image_type or image_type not in ["png", "jpeg"]:
            raise exceptions.IncorrectFileType(basename)

        dir_abs = os.path.abspath(self.dir)
        if not os.path.exists(dir_abs) or not os.path.isdir(dir_abs):
            raise exceptions.InvalidDestinationError(dir_abs)

        filepath = os.path.join(dir_abs, basename)
        if not self.overwrite and os.path.exists(filepath):
            raise exceptions.FileAlreadyExists(filepath)

        if os.path.exists(filepath):
            os.remove(filepath)

        self.debug(f"Saving screenshot to {filepath}")
        self.path = filepath

        screenshot = self.tab_input.screenshot(
            type="png" if image_type == "png" else "jpeg",
            path=filepath,
            full_page=self.fullscreen,
        )

        if self.image_log:
            self.logger.image(base64.b64encode(screenshot).decode("utf-8"))


class ExpectDownloadOnTab(Node, include_forward_link=False):
    name: str = "Playwright Tab: Expect Download"
    description: str = "Perform actions on tab and wait for download."
    categories: typing.List[str] = ["Web Automation", "Playwright", "Tab"]
    color: str = constants.COLOR_PLAYWRIGHT_TAB

    tab_input = InputSocket(
        datatype=datatypes.PlaywrightTab,
        name="Browser Tab",
        description="Playwright browser tab.",
    )
    timeout = OptionalInputSocket(
        datatype=Number,
        name="Download Timeout",
        description="The maximum time (ms) to wait for the download to start. If not set, default timeout for browser is used. If set to 0 timeout is disabled.",
    )
    dst = InputSocket(
        datatype=String,
        name="Local Download Directory",
        description="The local directory where the file should be downloaded. If a file with the suggested name already exists, a (num) counter will be appended unless the 'overwrite' option is enabled.",
        input_field=".",
    )
    overwrite = OptionalInputSocket(
        datatype=Boolean,
        name="Overwrite Files?",
        description="Overwrite existing files if they are present.",
        input_field=False,
    )

    with_body = LinkOutputSocket(
        name="Download Actions",
        description="Actions expected to cause a download.",
    )
    output_tab = OutputSocket(
        datatype=datatypes.PlaywrightTab,
        name="Browser Tab",
        description="Playwright browser tab (same as input).",
    )
    download = OutputSocket(
        name="Download path",
        datatype=String,
        description="Path where the file was downloaded.",
    )
    completed = LinkOutputSocket(
        name="Completed",
        description="Branch to run when the 'Download Actions' branch has completed",
    )

    def run(self):
        self.output_tab = self.tab_input
        with self.tab_input.expect_download(timeout=self.timeout) as download_expect:
            for node in self.forward("Browser Actions"):
                self._runtime.execute_node(node)
        download = download_expect.value

        # this will force the node to wait for the download
        download.path()

        if not os.path.exists(self.dst) and not os.path.isdir(self.dst):
            raise exceptions.InvalidDestinationError(self.dst)

        filename = os.path.join(
            self.dst,
            download.suggested_filename,
        )

        if os.path.exists(filename) and not self.overwrite:
            raise exceptions.FileAlreadyExists(filename)
        if os.path.exists(filename):
            os.remove(filename)

        download.save_as(filename)

        self.download = filename


class ExecutePlaywrightPageScript(Node):
    name: str = "Playwright Tab: Execute Script"
    description: str = """
Execute a series of commands for a Playwright browser tab with an option for expected downloads.
In the case of downloads this node will fail if the there is no download, or a download fails. Actions taken on tab persist after this node completes.
""".strip()
    categories: typing.List[str] = ["Web Automation", "Playwright", "Tab"]
    color: str = constants.COLOR_PLAYWRIGHT_TAB

    tab_input = InputSocket(
        datatype=datatypes.PlaywrightTab,
        name="Browser Tab",
        description="Playwright browser tab.",
    )
    page_script = InputSocket(
        datatype=String,
        name="Page Script",
        description="Python method for executing commands on a Playwright page. To extract values, add them to the 'output' data container. This dictionary with string keys is a local variable that doesn't need declaration.",
    )
    expected_downloads = InputSocket(
        datatype=Number,
        name="# Expected Downloads",
        description="Number of expected downloads.",
        input_field=0,
    )
    dst = InputSocket(
        datatype=String,
        name="Local Download Directory",
        description="Directory to save downloaded files. The suggested filename is used, with a (num) counter appended if a file with the same name already exists.",
        input_field=".",
    )
    overwrite = OptionalInputSocket(
        datatype=Boolean,
        name="Overwrite Files?",
        description="If True, overwrite existing files. If False, keep both files by appending a counter to the new file's name.",
        input_field=False,
    )

    output_tab = OutputSocket(
        datatype=datatypes.PlaywrightTab,
        name="Browser Tab",
        description="Playwright browser tab (same as input).",
    )
    pulled_values = OutputSocket(
        datatype=DataContainer,
        name="Parsed Output Values",
        description="Values extracted from the page script execution.",
    )
    downloads = ListOutputSocket(
        datatype=String,
        name="Download Filepaths",
        description="Paths of the downloaded files using suggested filenames. If a file with the same name already exists in the directory, a (<num>) is appended.",
    )

    def log_prefix(self):
        return f"[{self.name} - {self.tab_input.url}] "

    def run(self):
        self.output_tab = self.tab_input
        self.downloads = []

        self.debug(
            "Executing Script:\n" + re.sub(r"^", "  │  ", self.page_script, flags=re.MULTILINE)
        )
        with PlaywrightScriptExecutor(
            page=self.tab_input,
            script=self.page_script,
            logger=self._runtime.logger,
            num_expected_downloads=int(self.expected_downloads),
        ) as page_script_executor:
            self.pulled_values = page_script_executor.execute()
            page_script_executor.wait_for_download()

            if not os.path.isdir(self.dst) and self.expected_downloads > 0:
                raise exceptions.InvalidDestinationError(self.dst)

            for download in page_script_executor.downloads:
                download_path = os.path.join(self.dst, download.suggested_filename)

                if os.path.exists(download_path) and not self.overwrite:
                    raise exceptions.FileAlreadyExists(download_path)

                self.downloads.append(download_path)

                download.save_as(download_path)


class CreateLocator(Node):
    name: str = "Create Playwright Locator"
    description: str = "Creates a generic locator from a given CSS or XPath locator. Read https://playwright.dev/python/docs/locators for more details."
    categories: typing.List[str] = ["Web Automation", "Playwright", "Locator"]
    color: str = constants.COLOR_PLAYWRIGHT_LOCATOR

    locator_input = OptionalInputSocket(
        datatype=datatypes.PlaywrightLocator,
        name="Locator",
        description="The Playwright locator object. Specify this or 'Browser Tab', but not both.",
    )
    tab_input = OptionalInputSocket(
        datatype=datatypes.PlaywrightTab,
        name="Browser Tab",
        description="Playwright browser tab. Specify this or 'Locator', but not both.",
    )
    selector = InputSocket(
        datatype=String,
        name="Selector",
        description="The CSS or XPath selector used to identify an element on the page.",
        input_field="",
    )

    locator_output = OutputSocket(
        datatype=datatypes.PlaywrightLocator,
        name="New Locator",
        description="Playwright locator object used to filter DOM of browser.",
    )

    def run(self):
        if not (self.tab_input is None) ^ (self.locator_input is None):
            raise exceptions.PageOrLocatorNotBoth(self.tab_input is None)
        if self.tab_input:
            self.locator_output = self.tab_input.locator(self.selector)
        elif self.locator_input:
            self.locator_output = self.locator_input.locator(self.selector)


class FilterRegexTextLocator(Node):
    name: str = "Playwright Locator: Filter By Regex"
    description: str = "Filters a locator's elements and their descendant child elements based on regex pattern matching their text. This matches elements containing specified text somewhere inside, possibly in a child or a descendant element."
    categories: typing.List[str] = ["Web Automation", "Playwright", "Locator"]
    color: str = constants.COLOR_PLAYWRIGHT_LOCATOR

    locator_input = InputSocket(
        datatype=datatypes.PlaywrightLocator,
        name="Locator",
        description="The Playwright locator object to filter.",
    )
    pattern = InputSocket(
        datatype=String,
        name="Regex",
        description="The regex pattern to match the text within the locator's elements.",
        input_field=None,
    )
    invert = InputSocket(
        datatype=Boolean,
        name="Invert Search",
        description="When True, match elements that DO NOT contain the specified regex. Otherwise (when False), match elements that contain the specified regex.",
        input_field=False,
    )
    multiline = InputSocket(
        datatype=Boolean,
        name="Multiline",
        description="When specified, the pattern character '^' matches at the beginning of the string and at the beginning of each line (immediately following each newline); and the pattern character '$' matches at the end of the string and at the end of each line (immediately preceding each newline).",
        input_field=True,
    )
    ignore_case = InputSocket(
        datatype=Boolean,
        name="Ignore Case",
        description="Perform case-insensitive matching; expressions like [A-Z] will also match lowercase letters.",
        input_field=False,
    )
    dot_all = InputSocket(
        datatype=Boolean,
        name="Dot-All",
        description="Make the '.' special character match any character at all, including a newline; without this flag, '.' will match anything except a newline.",
        input_field=False,
    )

    locator_output = OutputSocket(
        datatype=datatypes.PlaywrightLocator,
        name="New Locator",
        description="The new Playwright locator object matching the given regex filter.",
    )

    def run(self):
        flags = 0
        if self.multiline:
            flags = flags | re.MULTILINE
        if self.ignore_case:
            flags = flags | re.IGNORECASE
        if self.dot_all:
            flags = flags | re.DOTALL

        regex = re.compile(self.pattern, flags=flags)
        if self.invert:
            self.locator_output = self.locator_input.filter(has_not_text=regex)
        else:
            self.locator_output = self.locator_input.filter(has_text=regex)


class FilterSubstringLocator(Node):
    name: str = "Playwright Locator: Filter By Substring"
    description: str = "Filters the locator's elements based on the presence of a specified substring in their text. The search is case-insensitive."
    categories: typing.List[str] = ["Web Automation", "Playwright", "Locator"]
    color: str = constants.COLOR_PLAYWRIGHT_LOCATOR

    locator_input = InputSocket(
        datatype=datatypes.PlaywrightLocator,
        name="Locator",
        description="The Playwright locator object to filter.",
    )
    has_text = InputSocket(
        datatype=String,
        name="Text",
        description="The substring text to match against the locator's elements.",
    )
    invert = InputSocket(
        datatype=Boolean,
        name="Invert Search",
        description="When True, match elements that DO NOT contain the specified text. Otherwise (when False), match elements that contain the specified text.",
        input_field=False,
    )

    locator_output = OutputSocket(
        datatype=datatypes.PlaywrightLocator,
        name="New Locator",
        description="The new Playwright locator object matching the given substring filter.",
    )

    def run(self):
        if self.invert:
            self.locator_output = self.locator_input.filter(has_not_text=self.has_text)
        else:
            self.locator_output = self.locator_input.filter(has_text=self.has_text)


class FilterNestedLocator(Node):
    name: str = "Playwright Locator: Filter By Nested Elements"
    description: str = "Filters the locator's elements based on those containing elements matching a specified sub-locator."
    categories: typing.List[str] = ["Web Automation", "Playwright", "Locator"]
    color: str = constants.COLOR_PLAYWRIGHT_LOCATOR

    locator_input = InputSocket(
        datatype=datatypes.PlaywrightLocator,
        name="Locator",
        description="The Playwright locator object to filter.",
    )
    sub_locator = InputSocket(
        datatype=datatypes.PlaywrightLocator,
        name="Sub-Locator",
        description="Filters the locator's elements based on those containing elements matching a specified sub-locator.",
    )
    invert = InputSocket(
        datatype=Boolean,
        name="Invert Search",
        description="When True, match elements that DO NOT contain the specified sub-locator. Otherwise (when False), match elements that contain the specified sub-locator.",
        input_field=False,
    )

    locator_output = OutputSocket(
        datatype=datatypes.PlaywrightLocator,
        name="New Locator",
        description="The new Playwright locator object matching the given sub-locator filter.",
    )

    def run(self):
        if self.invert:
            self.locator_output = self.locator_input.filter(has_not=self.sub_locator)
        else:
            self.locator_output = self.locator_input.filter(has=self.sub_locator)


class GetAllElementsFromLocator(Node):
    name: str = "Playwright Locator: Get All Elements"
    description: str = (
        "Retrieves all elements matching the given locator and returns them as individual locators."
    )
    categories: typing.List[str] = ["Web Automation", "Playwright", "Locator"]
    color: str = constants.COLOR_PLAYWRIGHT_LOCATOR

    locator_input = InputSocket(
        datatype=datatypes.PlaywrightLocator,
        name="Locator",
        description="Playwright locator object.",
    )

    locators = ListOutputSocket(
        datatype=datatypes.PlaywrightLocator,
        name="Matching Elements",
        description="List of Playwright locators, each corresponding to an individual element.",
    )

    def run(self):
        self.locators = self.locator_input.all()


class GetFirstElement(Node):
    name: str = "Playwright Locator: Get First Element"
    description: str = "Retrieves first element matching the given locator."
    categories: typing.List[str] = ["Web Automation", "Playwright", "Locator"]
    color: str = constants.COLOR_PLAYWRIGHT_LOCATOR

    locator_input = InputSocket(
        datatype=datatypes.PlaywrightLocator,
        name="Locator",
        description="Playwright locator object.",
    )

    locator_output = OutputSocket(
        datatype=datatypes.PlaywrightLocator,
        name="New Locator",
        description="The new Playwright locator object matching the given sub-locator filter.",
    )

    def run(self):
        self.locator_output = self.locator_input.first


class GetLastElement(Node):
    name: str = "Playwright Locator: Get Last Element"
    description: str = "Retrieves last element matching the given locator."
    categories: typing.List[str] = ["Web Automation", "Playwright", "Locator"]
    color: str = constants.COLOR_PLAYWRIGHT_LOCATOR

    locator_input = InputSocket(
        datatype=datatypes.PlaywrightLocator,
        name="Locator",
        description="Playwright locator object.",
    )

    locator_output = OutputSocket(
        datatype=datatypes.PlaywrightLocator,
        name="New Locator",
        description="The new Playwright locator object matching the given sub-locator filter.",
    )

    def run(self):
        self.locator_output = self.locator_input.last


class GetNthElement(Node):
    name: str = "Playwright Locator: Get Nth Element"
    description: str = "Retrieves nth element matching the given locator."
    categories: typing.List[str] = ["Web Automation", "Playwright", "Locator"]
    color: str = constants.COLOR_PLAYWRIGHT_LOCATOR

    locator_input = InputSocket(
        datatype=datatypes.PlaywrightLocator,
        name="Locator",
        description="Playwright locator object.",
    )

    locators = OutputSocket(
        datatype=datatypes.PlaywrightLocator,
        name="Locator",
        description="List of Playwright locators, each corresponding to an individual element.",
    )

    index = InputSocket(
        datatype=Number,
        name="Index",
        description="Index to grab element from. Will error out if exceeds count.",
    )

    locator_output = OutputSocket(
        datatype=datatypes.PlaywrightLocator,
        name="New Locator",
        description="The new Playwright locator object matching the given sub-locator filter.",
    )

    def run(self):
        self.locator_output = self.locator_input.all()[self.index]


class GetByRole(Node):
    name: str = "Playwright Locator: Get By Role"
    description: str = "Returns a locator that filters to elements of a given role."
    categories: typing.List[str] = ["Web Automation", "Playwright", "Locator"]
    color: str = constants.COLOR_PLAYWRIGHT_LOCATOR

    locator_input = OptionalInputSocket(
        datatype=datatypes.PlaywrightLocator,
        name="Locator",
        description="The Playwright locator object. Specify this or 'Browser Tab', but not both.",
    )
    tab_input = OptionalInputSocket(
        datatype=datatypes.PlaywrightTab,
        name="Browser Tab",
        description="Playwright browser tab. Specify this or 'Locator', but not both.",
    )
    role = InputSocket(
        datatype=String,
        name="Role",
        description="The ARIA role of the elements to fetch.",
    )

    is_checked = OptionalInputSocket(
        datatype=Boolean,
        name="Is Checked?",
        description="When true, will find elements that are marked as checked via its attributes. Vice-versa when false. When unset, this is ignored. Elements `aria-checked` or native `<input type=checkbox>` controls have a 'checked' attribute.",
    )

    is_disabled = OptionalInputSocket(
        datatype=Boolean,
        name="Is Disabled?",
        description="When true, will find elements that are marked as enabled via its attributes. Vice-versa when false. When unset, this is ignored. This is for elements that have an `aria-disabled` or `disabled` attribute.",
    )

    is_expanded = OptionalInputSocket(
        datatype=Boolean,
        name="Is Expanded?",
        description="When true, will find elements that are marked as expanded via its attributes. Vice-versa when false. When unset, this is ignored. This is for elements that have an `aria-expanded` attribute.",
    )

    included_hidden = OptionalInputSocket(
        datatype=Boolean,
        name="Include Hidden?",
        description="When true, hidden elements are included as defined by ARIA. By default hidden elements are not included.",
    )

    is_pressed = OptionalInputSocket(
        datatype=Boolean,
        name="Pressed?",
        description="When true, will find elements that are pressed. Vice-versa when false. When unset, this is ignored. This is for elements for elements that are marked as pressed/unpressed as defined by ARIA.",
    )

    is_selected = OptionalInputSocket(
        datatype=Boolean,
        name="Selected?",
        description="When true, will find elements that are selected. Vice-versa when false. When unset, this is ignored. This is for elements for elements that are marked as selected/unselected as defined by ARIA.",
    )

    level = OptionalInputSocket(
        datatype=Number,
        name="Level",
        description="Used to match elements against the 'level' attribute. This is usually present for roles `heading`, `listitem`, `row`, `treeitem`, with default values for `<h1>-<h6>` elements.",
    )

    locator_output = OutputSocket(
        datatype=datatypes.PlaywrightLocator,
        name="New Locator",
        description="The new Playwright locator object matching the given role filter.",
    )

    def run(self):
        if not (self.tab_input is None) ^ (self.locator_input is None):
            raise exceptions.PageOrLocatorNotBoth(self.tab_input is None)

        if self.tab_input:
            self.locator_output = self.tab_input.get_by_role(
                self.role,
                checked=self.is_checked,
                disabled=self.is_disabled,
                expanded=self.is_expanded,
                include_hidden=self.included_hidden,
                pressed=self.is_pressed,
                selected=self.is_selected,
                level=self.level,
            )  # type: ignore
        elif self.locator_input:
            self.locator_output = self.locator_input.get_by_role(
                self.role,
                checked=self.is_checked,
                disabled=self.is_disabled,
                expanded=self.is_expanded,
                include_hidden=self.included_hidden,
                pressed=self.is_pressed,
                selected=self.is_selected,
                level=self.level,
            )


class GetByAccessibilityName(Node):
    name: str = "Playwright Locator: Get By Role, Filter by Name Substring"
    description: str = "Returns a locator that filters to elements of a given role filted by he ARIA name, given a substring."
    categories: typing.List[str] = ["Web Automation", "Playwright", "Locator"]
    color: str = constants.COLOR_PLAYWRIGHT_LOCATOR

    locator_input = OptionalInputSocket(
        datatype=datatypes.PlaywrightLocator,
        name="Locator",
        description="The Playwright locator object. Specify this or 'Browser Tab', but not both.",
    )
    tab_input = OptionalInputSocket(
        datatype=datatypes.PlaywrightTab,
        name="Browser Tab",
        description="Playwright browser tab. Specify this or 'Locator', but not both.",
    )

    role = InputSocket(
        datatype=String,
        name="Role",
        description="The ARIA role of the elements to fetch.",
    )

    name_substring = InputSocket(
        datatype=String,
        name="Name Substring",
        description="Search by ARIA name. By default search is case case-insensitive and searches for a substring, use `Exact?` to control this behavior.",
        input_field="",
    )

    exact = OptionalInputSocket(
        datatype=Boolean,
        name="Exact?",
        description="If true, search by ARIA name is whole string and case sensitive.",
        input_field=False,
    )

    locator_output = OutputSocket(
        datatype=datatypes.PlaywrightLocator,
        name="New Locator",
        description="The new Playwright locator object matching the given role filter.",
    )

    def run(self):
        if not (self.tab_input is None) ^ (self.locator_input is None):
            raise exceptions.PageOrLocatorNotBoth(self.tab_input is None)

        if self.tab_input:
            self.locator_output = self.tab_input.get_by_role(
                role=self.role, name=self.name_substring, exact=self.exact
            )  # type: ignore
        elif self.locator_input:
            self.locator_output = self.locator_input.get_by_role(
                role=self.role, name=self.name_substring, exact=self.exact
            )


class GetByAccessibilityNameRegex(Node):
    name: str = "Playwright Locator: Get By Role, Filter by Name Regex"
    description: str = "Returns a locator that filters to elements of a given role filted by he ARIA name, given a regex."
    categories: typing.List[str] = ["Web Automation", "Playwright", "Locator"]
    color: str = constants.COLOR_PLAYWRIGHT_LOCATOR

    locator_input = OptionalInputSocket(
        datatype=datatypes.PlaywrightLocator,
        name="Locator",
        description="The Playwright locator object. Specify this or 'Browser Tab', but not both.",
    )
    tab_input = OptionalInputSocket(
        datatype=datatypes.PlaywrightTab,
        name="Browser Tab",
        description="Playwright browser tab. Specify this or 'Locator', but not both.",
    )

    role = InputSocket(
        datatype=String,
        name="Role",
        description="The ARIA role of the elements to fetch.",
    )

    pattern = InputSocket(
        datatype=String,
        name="Regex",
        description="The regex pattern to search for.",
    )
    multiline = InputSocket(
        datatype=Boolean,
        name="Multiline",
        description="When specified, the pattern character '^' matches at the beginning of the string and at the beginning of each line (immediately following each newline); and the pattern character '$' matches at the end of the string and at the end of each line (immediately preceding each newline).",
        input_field=True,
    )
    ignore_case = InputSocket(
        datatype=Boolean,
        name="Ignore Case",
        description="Perform case-insensitive matching; expressions like [A-Z] will also match lowercase letters.",
        input_field=False,
    )
    dot_all = InputSocket(
        datatype=Boolean,
        name="Dot-All",
        description="Make the '.' special character match any character at all, including a newline; without this flag, '.' will match anything except a newline.",
        input_field=False,
    )

    locator_output = OutputSocket(
        datatype=datatypes.PlaywrightLocator,
        name="New Locator",
        description="The new Playwright locator object matching the given role filter.",
    )

    def run(self):
        if not (self.tab_input is None) ^ (self.locator_input is None):
            raise exceptions.PageOrLocatorNotBoth(self.tab_input is None)

        flags = 0
        if self.multiline:
            flags = flags | re.MULTILINE
        if self.ignore_case:
            flags = flags | re.IGNORECASE
        if self.dot_all:
            flags = flags | re.DOTALL

        regex = re.compile(self.pattern, flags=flags)

        if self.tab_input:
            self.locator_output = self.tab_input.get_by_role(
                role=self.role, name=regex
            )  # type: ignore
        elif self.locator_input:
            self.locator_output = self.locator_input.get_by_role(role=self.role, name=regex)


class GetByPlaceHolder(Node):
    name: str = "Playwright Locator: Get By Placeholder"
    description: str = "Retrieve elements by their placeholder value."
    categories: typing.List[str] = ["Web Automation", "Playwright", "Locator"]
    color: str = constants.COLOR_PLAYWRIGHT_LOCATOR

    locator_input = OptionalInputSocket(
        datatype=datatypes.PlaywrightLocator,
        name="Locator",
        description="The Playwright locator object. Specify this or 'Browser Tab', but not both.",
    )
    tab_input = OptionalInputSocket(
        datatype=datatypes.PlaywrightTab,
        name="Browser Tab",
        description="Playwright browser tab. Specify this or 'Locator', but not both.",
    )
    placeholder = InputSocket(
        datatype=String,
        name="Placeholder",
        description="The placeholder attribute value to match.",
    )

    locator_output = OutputSocket(
        datatype=datatypes.PlaywrightLocator,
        name="Locator",
        description="The new Playwright locator object matching the given placeholder filter.",
    )

    def run(self):
        if not (self.tab_input is None) ^ (self.locator_input is None):
            raise exceptions.PageOrLocatorNotBoth(self.tab_input is None)
        if self.tab_input:
            self.locator_output = self.tab_input.get_by_placeholder(self.placeholder)
        elif self.locator_input:
            self.locator_output = self.locator_input.get_by_placeholder(self.placeholder)


class GetByText(Node):
    name: str = "Playwright Locator: Get By Text"
    description: str = "Retrieve elements by the text they contain."
    categories: typing.List[str] = ["Web Automation", "Playwright", "Locator"]
    color: str = constants.COLOR_PLAYWRIGHT_LOCATOR

    locator_input = OptionalInputSocket(
        datatype=datatypes.PlaywrightLocator,
        name="Locator",
        description="The Playwright locator object. Specify this or 'Browser Tab', but not both.",
    )
    tab_input = OptionalInputSocket(
        datatype=datatypes.PlaywrightTab,
        name="Browser Tab",
        description="Playwright browser tab. Specify this or 'Locator', but not both.",
    )
    text = InputSocket(
        datatype=String,
        name="Text",
        description="The text to search for.",
    )
    exact = InputSocket(
        datatype=Boolean,
        name="Exact Match",
        description="If `True`, search for an exact match of the text; otherwise, allow partial matches.",
        input_field=False,
    )

    locator_output = OutputSocket(
        datatype=datatypes.PlaywrightLocator,
        name="Locator",
        description="The new Playwright locator object matching the given text.",
    )

    def run(self):
        if not (self.tab_input is None) ^ (self.locator_input is None):
            raise exceptions.PageOrLocatorNotBoth(self.tab_input is None)
        if self.tab_input:
            self.locator_output = self.tab_input.get_by_text(self.text, exact=self.exact)
        elif self.locator_input:
            self.locator_output = self.locator_input.get_by_text(self.text, exact=self.exact)


class GetByRegex(Node):
    name: str = "Playwright Locator: Get By Regex"
    description: str = "Retrieve elements by a regex matching the text they contain."
    categories: typing.List[str] = ["Web Automation", "Playwright", "Locator"]
    color: str = constants.COLOR_PLAYWRIGHT_LOCATOR

    locator_input = OptionalInputSocket(
        datatype=datatypes.PlaywrightLocator,
        name="Locator",
        description="The Playwright locator object. Specify this or 'Browser Tab', but not both.",
    )
    tab_input = OptionalInputSocket(
        datatype=datatypes.PlaywrightTab,
        name="Browser Tab",
        description="Playwright browser tab. Specify this or 'Locator', but not both.",
    )
    pattern = InputSocket(
        datatype=String,
        name="Regex",
        description="The regex pattern to search for.",
    )
    multiline = InputSocket(
        datatype=Boolean,
        name="Multiline",
        description="When specified, the pattern character '^' matches at the beginning of the string and at the beginning of each line (immediately following each newline); and the pattern character '$' matches at the end of the string and at the end of each line (immediately preceding each newline).",
        input_field=True,
    )
    ignore_case = InputSocket(
        datatype=Boolean,
        name="Ignore Case",
        description="Perform case-insensitive matching; expressions like [A-Z] will also match lowercase letters.",
        input_field=False,
    )
    dot_all = InputSocket(
        datatype=Boolean,
        name="Dot-All",
        description="Make the '.' special character match any character at all, including a newline; without this flag, '.' will match anything except a newline.",
        input_field=False,
    )

    locator_output = OutputSocket(
        datatype=datatypes.PlaywrightLocator,
        name="Locator",
        description="The new Playwright locator object matching the given regex pattern.",
    )

    def run(self):
        if not (self.tab_input is None) ^ (self.locator_input is None):
            raise exceptions.PageOrLocatorNotBoth(self.tab_input is None)

        flags = 0
        if self.multiline:
            flags = flags | re.MULTILINE
        if self.ignore_case:
            flags = flags | re.IGNORECASE
        if self.dot_all:
            flags = flags | re.DOTALL

        regex = re.compile(self.pattern, flags=flags)

        if self.tab_input:
            self.locator_output = self.tab_input.get_by_text(regex)
        elif self.locator_input:
            self.locator_output = self.locator_input.get_by_text(regex)


class GetByAltText(Node):
    name: str = "Playwright Locator: Get By Alt Text"
    description: str = "Retrieve elements by their alt text attribute."
    categories: typing.List[str] = ["Web Automation", "Playwright", "Locator"]
    color: str = constants.COLOR_PLAYWRIGHT_LOCATOR

    locator_input = OptionalInputSocket(
        datatype=datatypes.PlaywrightLocator,
        name="Locator",
        description="The Playwright locator object. Specify this or 'Browser Tab', but not both.",
    )
    tab_input = OptionalInputSocket(
        datatype=datatypes.PlaywrightTab,
        name="Browser Tab",
        description="Playwright browser tab. Specify this or 'Locator', but not both.",
    )
    alt_text = InputSocket(
        datatype=String,
        name="Alt Text",
        description="The alternative text attribute to search for.",
    )
    exact = InputSocket(
        datatype=Boolean,
        name="Exact Match",
        description="If `True`, search for an exact match of the alt text; otherwise, allow partial matches.",
        input_field=False,
    )

    locator_output = OutputSocket(
        datatype=datatypes.PlaywrightLocator,
        name="Locator",
        description="The new Playwright locator object matching the given alt-text filter.",
    )

    def run(self):
        if not (self.tab_input is None) ^ (self.locator_input is None):
            raise exceptions.PageOrLocatorNotBoth(self.tab_input is None)
        if self.tab_input:
            self.locator_output = self.tab_input.get_by_alt_text(self.alt_text, exact=self.exact)
        elif self.locator_input:
            self.locator_output = self.locator_input.get_by_alt_text(
                self.alt_text, exact=self.exact
            )


class GetByLabel(Node):
    name: str = "Playwright Locator: Get By Label"
    description: str = "Retrieve elements by their associated label."
    categories: typing.List[str] = ["Web Automation", "Playwright", "Locator"]
    color: str = constants.COLOR_PLAYWRIGHT_LOCATOR

    locator_input = OptionalInputSocket(
        datatype=datatypes.PlaywrightLocator,
        name="Locator",
        description="The Playwright locator object. Specify this or 'Browser Tab', but not both.",
    )
    tab_input = OptionalInputSocket(
        datatype=datatypes.PlaywrightTab,
        name="Browser Tab",
        description="Playwright browser tab. Specify this or 'Locator', but not both.",
    )
    label = InputSocket(
        datatype=String,
        name="Label Text",
        description="Text of the label to search for.",
    )
    exact = InputSocket(
        datatype=Boolean,
        name="Exact Match",
        description="Search for an exact label match.",
        input_field=False,
    )

    locator_output = OutputSocket(
        datatype=datatypes.PlaywrightLocator,
        name="Locator",
        description="The new Playwright locator object matching the given label filter.",
    )

    def run(self):
        if not (self.tab_input is None) ^ (self.locator_input is None):
            raise exceptions.PageOrLocatorNotBoth(self.tab_input is None)
        if self.tab_input:
            self.locator_output = self.tab_input.get_by_label(self.label, exact=self.exact)
        elif self.locator_input:
            self.locator_output = self.locator_input.get_by_label(self.label, exact=self.exact)


class LocatorOr(Node):
    name: str = "Playwright Locator: Or"
    description: str = "Combine two input locators using an 'OR' operation. The resulting locator will match elements satisfying either of the input locators."
    categories: typing.List[str] = ["Web Automation", "Playwright", "Locator"]
    color: str = constants.COLOR_PLAYWRIGHT_LOCATOR

    first_locator = InputSocket(
        name="First Locator",
        description="Primary locator for the 'OR' operation.",
        datatype=datatypes.PlaywrightLocator,
    )
    second_locator = InputSocket(
        name="Second Locator",
        description="Secondary locator for the 'OR' operation.",
        datatype=datatypes.PlaywrightLocator,
    )

    locator_output = OutputSocket(
        datatype=datatypes.PlaywrightLocator,
        name="Locator",
        description="The new Playwright locator object matching either of the given input locators.",
    )

    def run(self):
        self.locator_output = self.first_locator.or_(self.second_locator)


class LocatorAnd(Node):
    name: str = "Playwright Locator: And"
    description: str = "Combine two input locators using an 'AND' operation. The resulting locator will match elements satisfying both input locators."
    categories: typing.List[str] = ["Web Automation", "Playwright", "Locator"]
    color: str = constants.COLOR_PLAYWRIGHT_LOCATOR

    first_locator = InputSocket(
        name="First Locator",
        description="Primary locator for the 'AND' operation.",
        datatype=datatypes.PlaywrightLocator,
    )

    second_locator = InputSocket(
        name="Second Locator",
        description="Secondary locator for the 'AND' operation.",
        datatype=datatypes.PlaywrightLocator,
    )

    locator_output = OutputSocket(
        datatype=datatypes.PlaywrightLocator,
        name="Locator",
        description="The new Playwright locator object matching both of the given input locators.",
    )

    def run(self):
        self.locator_output = self.first_locator.and_(self.second_locator)


class PlaywrightClick(PlaywrightCommandNode):
    name: str = "Playwright Locator: Click Element"
    description: str = "Clicks on an element using specified configurations. If the locator resolves to multiple elements, it will result in an error."
    categories: typing.List[str] = ["Web Automation", "Playwright", "Locator"]
    color: str = constants.COLOR_PLAYWRIGHT_LOCATOR

    locator_input = InputSocket(
        datatype=datatypes.PlaywrightLocator,
        name="Locator",
        description="Playwright locator object.",
    )
    button = InputSocket(
        datatype=String,
        name="Button",
        description="Specifies which mouse button to use for the click. Valid options are: left, center, or right.",
        input_field="left",
    )
    modifiers = ListInputSocket(
        datatype=String,
        name="Modifier",
        description=(
            "List of modifier keys to press during the click. Accepts: 'Alt', 'Control', 'Meta', and 'Shift'. Any other value will result in an error."
        ),
    )
    click_count = InputSocket(
        datatype=Number,
        name="Click Count",
        description="Specifies the number of consecutive clicks.",
        input_field=1,
    )
    delay = InputSocket(
        datatype=Number,
        name="Click Delay",
        description="Duration (in milliseconds) to wait between the mousedown and mouseup events.",
        input_field=0,
    )
    force = OptionalInputSocket(
        datatype=Boolean,
        name="Force",
        description="Bypasses the actionability checks. Useful when certain predefined conditions (like visibility) for actionability do not hold true.",
        input_field=False,
    )
    no_wait_after = OptionalInputSocket(
        datatype=Boolean,
        name="No Wait After",
        description="If set, the action will not wait for potential navigations to complete. Useful when navigating to inaccessible pages.",
        input_field=False,
    )
    trial = OptionalInputSocket(
        datatype=Boolean,
        name="Trial",
        description="If set, only the actionability checks are performed, without the actual action. Useful for ensuring an element is ready for interaction without actually interacting.",
        input_field=False,
    )

    locator_output = OutputSocket(
        datatype=datatypes.PlaywrightLocator,
        name="Locator",
        description="The Playwright locator object (same as input).",
    )

    def _run_impl(self):
        self.locator_output = self.locator_input
        self.locator_input.click(
            modifiers=self.modifiers,  # type: ignore
            delay=self.delay,
            button=self.button,  # type: ignore
            click_count=int(self.click_count),
            force=self.force,
            no_wait_after=self.no_wait_after,
            trial=self.trial,
        )


class PlaywrightCheck(PlaywrightCommandNode):
    name: str = "Playwright Locator: Element Check"
    description: str = "Checks on element. Used on checkbox and radio elements."
    categories: typing.List[str] = ["Web Automation", "Playwright", "Locator"]
    color: str = constants.COLOR_PLAYWRIGHT_LOCATOR

    locator_input = InputSocket(
        datatype=datatypes.PlaywrightLocator,
        name="Locator",
        description="Playwright locator object.",
    )

    force = OptionalInputSocket(
        datatype=Boolean,
        name="Force",
        description="Bypasses the actionability checks. Useful when certain predefined conditions (like visibility) for actionability do not hold true.",
        input_field=False,
    )
    no_wait_after = OptionalInputSocket(
        datatype=Boolean,
        name="No Wait After",
        description="If set, the action will not wait for potential navigations to complete. Useful when navigating to inaccessible pages.",
        input_field=False,
    )

    locator_output = OutputSocket(
        datatype=datatypes.PlaywrightLocator,
        name="Locator",
        description="The Playwright locator object (same as input).",
    )

    def _run_impl(self):
        self.locator_output = self.locator_input

        # self.locator_input.scroll_into_view_if_needed()

        self.locator_input.set_checked(True)
        # self.locator_input.check(force=self.force, no_wait_after=self.no_wait_after)


class PlaywrightFill(PlaywrightCommandNode):
    name: str = "Playwright Locator: Element Set Input Text"
    description: str = "Fills an input element with the specified text. If the locator does not resolve to a single element, the node will raise an error."
    categories: typing.List[str] = ["Web Automation", "Playwright", "Locator"]
    color: str = constants.COLOR_PLAYWRIGHT_LOCATOR

    locator_input = InputSocket(
        datatype=datatypes.PlaywrightLocator,
        name="Locator",
        description="Playwright locator object.",
    )
    fill_input = InputSocket(
        datatype=String,
        name="Text",
        description="The text to input into the element. This will replace any existing text.",
    )

    locator_output = OutputSocket(
        datatype=datatypes.PlaywrightLocator,
        name="Locator",
        description="The Playwright locator object (same as input).",
    )

    def _run_impl(self):
        self.locator_output = self.locator_input
        self.locator_input.fill(self.fill_input)


class GetInnerText(PlaywrightCommandNode):
    name: str = "Playwright Locator: Get Inner Text"
    description: str = "Retrieves the inner text of an element. The node will raise an error if the locator does not resolve to a single element."

    categories: typing.List[str] = ["Web Automation", "Playwright", "Locator"]
    color: str = constants.COLOR_PLAYWRIGHT_LOCATOR

    locator_input = InputSocket(
        datatype=datatypes.PlaywrightLocator,
        name="Locator",
        description="Playwright locator object.",
    )

    locator_output = OutputSocket(
        datatype=datatypes.PlaywrightLocator,
        name="Locator",
        description="The Playwright locator object (same as input).",
    )
    text = OutputSocket(
        datatype=String,
        name="Inner Text",
        description="The inner text of the element.",
    )

    def _run_impl(self):
        self.locator_output = self.locator_input
        self.text = self.locator_input.inner_text()


class GetTextContent(PlaywrightCommandNode):
    name: str = "Playwright Locator: Get Text Content"
    description: str = "Get Text Context of element. If locator does not resolve to single element node will error out."
    categories: typing.List[str] = ["Web Automation", "Playwright", "Locator"]
    color: str = constants.COLOR_PLAYWRIGHT_LOCATOR

    locator_input = InputSocket(
        datatype=datatypes.PlaywrightLocator,
        name="Locator",
        description="Playwright locator object.",
    )

    locator_output = OutputSocket(
        datatype=datatypes.PlaywrightLocator,
        name="Locator",
        description="The Playwright locator object (same as input).",
    )
    text = OutputSocket(
        datatype=String,
        name="Text",
        description="Text content of element.",
    )

    def _run_impl(self):
        self.locator_output = self.locator_input
        self.text = self.locator_input.text_content()


class GetAttribute(Node):
    name: str = "Playwright Locator: Get Attribute"
    description: str = "Retrieve the value of a specified attribute from an element. Requires a single element locator."
    categories: typing.List[str] = ["Web Automation", "Playwright", "Locator"]
    color: str = constants.COLOR_PLAYWRIGHT_LOCATOR

    locator_input = InputSocket(
        datatype=datatypes.PlaywrightLocator,
        name="Locator",
        description="Playwright locator object.",
    )
    attribute = InputSocket(
        datatype=String,
        name="Attribute Name",
        description="Name of the attribute to retrieve.",
    )

    locator_output = OutputSocket(
        datatype=datatypes.PlaywrightLocator,
        name="Locator",
        description="The Playwright locator object (same as input).",
    )
    attribute_value = OutputSocket(
        datatype=String,
        name="Attribute Value",
        description="Value of the specified attribute.",
    )

    def run(self):
        self.locator_output = self.locator_input
        self.attribute_value = self.locator_input.get_attribute(self.attribute) or ""


class PlaywrightScriptExecutor:
    """
    Context manager for running scripts in graphex. This will provide helpful error messages as well
    as listen if a download occurs. others will be ignored.
    """

    def __init__(
        self,
        page: sync_api.Page,
        script: str,
        logger: GraphexLogger,
        num_expected_downloads: int = 0,
    ):
        self.page: sync_api.Page = page
        self.script: str = script
        self.output: typing.Dict[str, str] = {}
        self.was_executed: bool = False
        self.downloads: typing.List[sync_api.Download] = []
        self.page.on(
            "download",
            self.__handle_download,
        )
        self.logger: GraphexLogger = logger
        self.num_expected_downloads: int = num_expected_downloads

    def __handle_download(
        self,
        download: sync_api.Download,
    ) -> None:
        """
        Handle for download listener. This sets the download object for context manager.

        Args:
            download (sync_api.Download): Playwright download object.
        """

        self.logger.debug(f"Download has started with url: {download.url}")

        # use this to keep track of downloads that have completed
        self.downloads.append(download)

    def wait_for_download(
        self,
        timeout_for_download_start=120,
    ) -> None:
        """
        Wait for download to occur.

        Args:
            timeout_for_download_start (int, optional): timeout in (sc) for download to start.
                                                        Defaults to 120.
            timeout_for_download (int, optional): timeout in (sc) for download.
                                                  Defaults to 300.

        Raises:
            exceptions.DownloadDidNotOccur: No download was started within given timeout.
            exceptions.DownloadFailed: Download started, but failed.
            exceptions.DownloadTimedOut: Download started, but failed to finish within
                                         given timeout.
        """

        if self.num_expected_downloads <= 0:
            return

        # do a wait to make sure things fall through.

        # The loop will run for a set period of time.
        # If the number of downloads is not found by that
        # period, the method will throw an exception.
        self.logger.debug(
            f'Waiting for download{"s" if self.num_expected_downloads>1 else ""} to occur.'
        )
        start_time = time.time()

        while (
            len(self.downloads) < self.num_expected_downloads
            and time.time() - start_time < timeout_for_download_start
        ):
            self.page.wait_for_timeout(10)

        if len(self.downloads) < self.num_expected_downloads:
            raise exceptions.DownloadDidNotStart(
                expected_downloads=self.num_expected_downloads,
                actual_downloads=len(self.downloads),
            )

        # print a message if more downloads occured.
        # Set it to debug so people don't think there's an issue with that.
        if len(self.downloads) > self.num_expected_downloads:
            self.logger.debug(
                f'{self.num_expected_downloads} download{"s" if len(self.downloads)>1 else ""} occured, but {self.num_expected_downloads} were expected. This'
                " is not an error in itself."
            )

        self.logger.debug("Wait for all downloads to complete.")
        # wait for downloads in completed time.
        for download in self.downloads:
            # this method will wait to return until the download fails or completes.
            failure_msg = download.failure()
            if failure_msg:
                raise exceptions.DownloadFailed(
                    download.url,
                    failure_msg,
                )

        self.logger.debug("All downloads completed.")

    def __enter__(
        self,
    ) -> "PlaywrightScriptExecutor":
        return self

    def __exit__(
        self,
        exc_type: typing.Optional[typing.Type[BaseException]],
        exc_value: typing.Optional[BaseException],
        exc_traceback: typing.Optional[types.TracebackType],
    ) -> bool:
        if exc_type and exc_value and exc_traceback and self.was_executed:
            tb_entries = traceback.extract_tb(exc_traceback)
            lineno = None
            if isinstance(
                exc_value,
                SyntaxError,
            ):
                lineno = exc_value.lineno
            else:
                #
                # The line number of the script error is extracted from the traceback.
                # For most errors, the stack looks something like this.
                #
                #      File "<script context is run from>", line <outer line number>, in <module>
                #      script_executer.execute()
                #      File <script context is run from>", line <inner line number in excute commad>, in execute
                #      exec(self.script, {}, local_vars)
                #      File "<string>", line <line number of script>, in <module>
                #
                lineno = next(
                    (
                        entry.lineno
                        for i, entry in enumerate(
                            tb_entries[1:],
                            1,
                        )
                        if entry.filename == "<string>"
                        and r"exec(self.script, {}, local_vars)" in (tb_entries[i - 1].line or "")
                    ),
                    None,  # Default if the condition is not met for any entry
                )

            try:
                if "playwright" in exc_value.__class__.__module__:
                    self.logger.error(
                        "Error with playwright script. Attempting to display image below."
                    )
                    self.logger.image(
                        base64.b64encode(
                            self.page.screenshot(
                                type="png",
                                full_page=True,
                            )
                        ).decode("utf-8")
                    )

            except Exception as e:
                self.logger.warning(f"Attempted screenshot, but got this error: {str(e)}")
            raise exceptions.PlaywrightScriptError(
                self.script,
                lineno,
                exc_value,
            ) from None

        # remove the listener for downloads
        self.page.remove_listener(
            "download",
            self.__handle_download,
        )

        return False

    def execute(
        self,
    ) -> typing.Dict[str, str]:
        """
        Execute the given Playwright script.

        The asummed local variables are

        page: Playwright page object
        output: Dictionary with str key values
        re: regex library
        time: time library

        commands are executed against page. Parsed values are stored withen output.

        Returns:
            typing.List[str]: Parsed output from script (output variable).
        """
        local_vars = {
            "page": self.page,
            "output": self.output,
            "re": re,
            "time": time,
        }  # Provide the page object as a local variable
        self.was_executed = True
        self.logger.debug(f"Executing page commands at {self.page.url}")
        exec(
            self.script,
            {},
            local_vars,
        )
        self.logger.debug("commands finished")
        return self.output


class PlaywrightCommandContext:
    """
    Context manager for executing page or locator commands.

    Managers purpose is to handle errors and give useful output,
    such as screen shots.
    """

    def __init__(
        self,
        logger: GraphexLogger,
        *,
        page: typing.Optional[sync_api.Page] = None,
        locator: typing.Optional[sync_api.Locator] = None,
    ):
        if not (page is not None) ^ (locator is not None):
            raise exceptions.PageOrLocatorNotBoth(page is None)

        if page:
            self.page = page
        elif locator:
            self.page = locator.page
        self.logger: GraphexLogger = logger

    def __enter__(
        self,
    ) -> "PlaywrightCommandContext":
        return self

    def __exit__(
        self,
        exc_type: typing.Optional[typing.Type[BaseException]],
        exc_value: typing.Optional[BaseException],
        exc_traceback: typing.Optional[types.TracebackType],
    ) -> bool:
        if not exc_value:
            return True
        else:
            try:
                if "playwright" in exc_value.__class__.__module__:
                    self.logger.error(
                        "Error with playwright command. Attempting to display image below."
                    )
                    self.logger.image(
                        base64.b64encode(
                            self.page.screenshot(
                                type="png",
                                full_page=True,
                            )
                        ).decode("utf-8")
                    )

            except Exception as e:
                self.logger.warning(f"Attempted screenshot, but got this error: {str(e)}")
            raise exc_value
