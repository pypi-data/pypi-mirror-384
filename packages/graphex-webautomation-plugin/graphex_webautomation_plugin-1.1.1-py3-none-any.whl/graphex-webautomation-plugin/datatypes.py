# from graphex import String
from graphex_webautomation_plugin import constants
from graphex.datatype import DataType
from playwright import sync_api
from graphex import String

SyncBrowserContext = DataType(
    true_type=sync_api.BrowserContext,
    name="Playwright Browser Context",
    description="Playwright synchronous browser context.",
    color=constants.COLOR_PLAYWRIGHT,
    categories=["Web Automation", "Playwright"],
)


PlaywrightTab = DataType(
    true_type=sync_api.Page,
    name="Playwright Browser Tab",
    description="Playwright browser tab.",
    color=constants.COLOR_PLAYWRIGHT_TAB,
    categories=["Web Automation", "Playwright"],
)


PlaywrightLocator = DataType(
    true_type=sync_api.Locator, 
	name="Playwright Locator", 
	description="Playwright Locator", 
	color=constants.COLOR_PLAYWRIGHT_LOCATOR, 
	categories=["Web Automation", "Playwright"]
)


@SyncBrowserContext.cast(to=String)
def SyncBrowserContext_to_String(value: sync_api.BrowserContext) -> str:
    return str(value)


@PlaywrightTab.cast(to=String)
def PlaywrightTab_to_String(value: sync_api.Page) -> str:
    return str(value)


@PlaywrightLocator.cast(to=String)
def PlaywrightLocator_to_String(value: sync_api.Locator) -> str:
    return str(value)
