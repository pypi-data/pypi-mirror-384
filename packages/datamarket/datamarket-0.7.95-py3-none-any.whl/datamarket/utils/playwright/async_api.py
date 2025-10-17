########################################################################################################################
# IMPORTS

import asyncio
import logging
from datetime import timedelta
from random import randint
from types import TracebackType
from typing import Optional, Self

# 'BdbQuit' import is removed as it's no longer used
from camoufox.async_api import AsyncCamoufox as Camoufox
from playwright.async_api import (
    Browser,
    BrowserContext,
    Error as PlaywrightError,
    Page,
    TimeoutError as PlaywrightTimeoutError,
)
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_delay,
    wait_exponential,
)

from datamarket.interfaces.proxy import ProxyInterface


########################################################################################################################
# SETUP LOGGER

logger = logging.getLogger(__name__)

########################################################################################################################
# ASYNC HELPER FUNCTIONS


async def human_type(page: Page, text: str, delay: int = 100):
    for char in text:
        await page.keyboard.type(char, delay=randint(int(delay * 0.5), int(delay * 1.5)))


async def human_press_key(page: Page, key: str, count: int = 1, delay: int = 100, add_sleep: bool = True) -> None:
    """Asynchronously presses a key with a random delay, optionally sleeping between presses."""
    for _ in range(count):
        await page.keyboard.press(key, delay=randint(int(delay * 0.5), int(delay * 1.5)))
        if add_sleep:
            await asyncio.sleep(randint(int(delay * 1.5), int(delay * 2.5)) / 1000)


########################################################################################################################
# ASYNC CRAWLER CLASS


class PlaywrightCrawler:
    """An robust, proxy-enabled asynchronous Playwright crawler with captcha bypass and retry logic."""

    def __init__(self, proxy_interface: ProxyInterface):
        """
        Initializes the async crawler with a proxy interface.

        Args:
            proxy_interface (ProxyInterface): An async-compatible object to fetch proxy credentials.
        """
        self.proxy_interface = proxy_interface
        self.pw: Optional[Camoufox] = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None

    async def __aenter__(self) -> Self:
        """Initializes the browser context when entering the `async with` statement."""
        await self.init_context()
        return self

    async def __aexit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        """Safely closes the browser context upon exit."""
        if self.pw:
            await self.pw.__aexit__(exc_type, exc_val, exc_tb)

    @retry(
        wait=wait_exponential(exp_base=2, multiplier=3, max=90),
        stop=stop_after_delay(timedelta(minutes=10)),
        before_sleep=before_sleep_log(logger, logging.INFO),
        reraise=True,
    )
    async def init_context(self) -> Self:
        """Initializes a new async browser instance and context with a fresh proxy."""
        try:
            # Correctly wrap the blocking I/O call
            host, port, user, pwd = await asyncio.to_thread(self.proxy_interface.get_proxies, raw=True, use_auth=True)
            proxy_url = f"http://{host}:{port}"
            proxy_cfg = {"server": proxy_url}

            if user and pwd:
                proxy_cfg.update({"username": user, "password": pwd})

            logger.info(f"Starting browser with proxy: {proxy_url}")
            self.pw = Camoufox(headless=True, geoip=True, humanize=True, proxy=proxy_cfg)
            self.browser = await self.pw.__aenter__()
            self.context = await self.browser.new_context()
            self.page = await self.context.new_page()
        except Exception as e:
            logger.error(f"Failed to initialize browser context: {e}")
            if self.pw:
                await self.pw.__aexit__(type(e), e, e.__traceback__)
            raise
        return self

    async def restart_context(self) -> None:
        """Closes the current browser instance and initializes a new one."""
        logger.info("Restarting browser context...")
        if self.pw:
            await self.pw.__aexit__(None, None, None)
        await self.init_context()

    @retry(
        retry=retry_if_exception_type((PlaywrightTimeoutError, PlaywrightError)),
        wait=wait_exponential(exp_base=2, multiplier=3, max=90),
        stop=stop_after_delay(timedelta(minutes=10)),
        before_sleep=before_sleep_log(logger, logging.INFO),
        reraise=True,
    )
    async def _goto_with_retry(self, url: str) -> Page:
        """
        Asynchronously navigates to a URL with retries for common Playwright errors.
        Restarts the browser context on repeated failures.
        """
        if not (self.page and not self.page.is_closed()):
            logger.warning("Page is not available or closed. Restarting context.")
            await self.restart_context()

        assert self.page is not None
        await self.page.goto(url, timeout=30000, wait_until="domcontentloaded")
        return self.page

    async def goto(self, url: str) -> Page:
        """
        Ensures the browser is initialized and navigates to the given URL.
        Public wrapper for the internal retry-enabled navigation method.
        """
        if not self.page:
            logger.info("Browser context not found, initializing now...")
            await self.init_context()
        return await self._goto_with_retry(url)
