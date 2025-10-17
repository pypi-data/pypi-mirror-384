"""
# custom_settings
"DRISSIONPAGE_HEADLESS": False, # default
"DRISSIONPAGE_BLOCK_IMAGES": False, # default
"DRISSIONPAGE_CONCURRENT_TABS": 6, # 4
"DRISSIONPAGE_BLOCKED_URLS": [
    # 浏览器不加载媒体文件
    '*.jpg*', '*.jpeg*', '*.png*', '*.gif*', '*.svg*', '*.webp*', '*bfasset.costco-static.com*',   # Images
],

#
yield scrapy.Request(
            url=_url, headers=self.headers,
            callback=self.parse,
            meta={
                'dp_page_type': 'drissionpage', # 固定识别
                'drissionpage': {
                    'wait_time': 1,
                    'timeout': 10,
                },
            },
            priority=99
        )
"""

import asyncio
import logging
from typing import Dict, Optional, Union, TypeVar

from DrissionPage import ChromiumPage
from DrissionPage._configs.chromium_options import ChromiumOptions
from DrissionPage.common import Settings
from scrapy import signals
from scrapy.crawler import Crawler
from scrapy.http import Request, Response, TextResponse
from scrapy.spiders import Spider

# --- Type Hinting Definitions ---
SpiderType = TypeVar('SpiderType', bound=Spider)
ResponseType = TypeVar('ResponseType', bound=Response)

# Configure DrissionPage to create separate tab objects for each tab
Settings.set_singleton_tab_obj(False)


class _TabManager:
    """
    A wrapper class to manage a browser tab and its associated semaphore.

    This ensures that when a tab is closed, the semaphore is released,
    allowing another concurrent request to be processed. This object is what
    is exposed as `response.page` in the spider.
    """

    def __init__(self, tab: ChromiumPage, semaphore: asyncio.Semaphore):
        """
        Initializes the TabManager.

        :param tab: The DrissionPage Tab object to manage.
        :param semaphore: The asyncio.Semaphore controlling concurrent access.
        """
        self._tab = tab
        self._semaphore = semaphore
        self._closed = False
        self.logger = logging.getLogger(__name__)

    def __getattr__(self, name: str):
        """
        Delegates attribute access to the underlying Tab object.
        This makes the wrapper transparent to the spider, so you can call
        `response.page.run_js(...)` just like a regular Tab object.

        :param name: The name of the attribute to access.
        :return: The attribute from the underlying Tab object.
        """
        if name.startswith('_'):
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")
        return getattr(self._tab, name)

    def close(self) -> None:
        """
        Closes the browser tab and releases the semaphore.

        This method is designed to be called from the spider once processing
        of the page is complete (e.g., in a try/finally block).
        It is safe to call this method multiple times.
        """
        if not self._closed:
            tab_url = "unknown"
            try:
                tab_url = self._tab.url
                self.logger.debug(f"Closing tab for URL: {tab_url}")
                self._tab.close()
            except Exception as e:
                self.logger.error(f"Error closing DrissionPage tab for {tab_url}: {e}", exc_info=True)
            finally:
                self._semaphore.release()
                self._closed = True
                self.logger.debug(
                    f"Tab closed and semaphore released for {tab_url}. Semaphore value: {self._semaphore._value}")


class DrissionResponse(TextResponse):
    """
    A Scrapy Response that integrates the DrissionPage tab object.

    The `page` attribute holds a `_TabManager` instance, which provides access to the
    DrissionPage tab and handles resource cleanup when `response.page.close()` is called.
    """

    def __init__(self, *args, page: _TabManager, **kwargs):
        """
        Initializes the DrissionResponse.

        :param page: An instance of the _TabManager class.
        """
        super().__init__(*args, **kwargs)
        self.page = page


class BrowserManager:
    """
    Manages the lifecycle of a single ChromiumPage browser instance.
    This class ensures that the browser is started only once and closed gracefully.
    """

    def __init__(self, settings):
        """
        Initializes the BrowserManager using Scrapy settings.
        """
        self.settings = settings
        self._browser: Optional[ChromiumPage] = None
        self._lock = asyncio.Lock()  # Use asyncio.Lock for async environments
        self.logger = logging.getLogger(__name__)

    async def get_browser(self) -> ChromiumPage:
        """
        Provides a thread-safe, single instance of the browser.
        If the browser is not already running, it starts a new one.

        :return: The ChromiumPage browser instance.
        """
        async with self._lock:
            if self._browser is None or not self._is_browser_alive():
                if self._browser is not None:
                    self.logger.warning("Browser instance is not alive, creating new instance...")
                else:
                    self.logger.info("Initializing new browser instance...")
                try:
                    co = ChromiumOptions()
                    if self.settings.getbool('DRISSIONPAGE_HEADLESS', False):
                        co.headless()  # Use the headless() method

                    if self.settings.getbool('DRISSIONPAGE_BLOCK_IMAGES', False):
                        co.no_imgs(True)  # Use the no_imgs method

                    self._browser = ChromiumPage(addr_or_opts=co)
                    self.logger.info("Browser instance created successfully.")
                except Exception as e:
                    self.logger.error(f"Failed to create browser instance: {e}", exc_info=True)
                    raise
            return self._browser

    def _is_browser_alive(self) -> bool:
        """
        Checks if the browser instance is still alive and responsive.

        :return: True if browser is alive, False otherwise.
        """
        if self._browser is None:
            return False
        try:
            # Try to access a simple property to check if browser is responsive
            _ = self._browser.title
            return True
        except Exception as e:
            self.logger.warning(f"Browser health check failed: {e}")
            return False

    def close(self) -> None:
        """
        Closes the browser instance if it exists.
        """
        if self._browser is not None:
            self.logger.info("Closing browser instance.")
            try:
                # Close all open tabs first
                try:
                    tab_count = len(self._browser.tabs)
                    self.logger.debug(f"Closing {tab_count} open tabs before quitting browser.")
                    for tab in self._browser.tabs:
                        try:
                            tab.close()
                        except Exception as tab_error:
                            self.logger.warning(f"Error closing individual tab: {tab_error}")
                except Exception as tabs_error:
                    self.logger.warning(f"Error accessing tabs during cleanup: {tabs_error}")

                # Quit the browser
                self._browser.quit()
                self.logger.info("Browser instance closed successfully.")
            except Exception as e:
                self.logger.error(f"Error closing browser instance: {e}", exc_info=True)
            finally:
                self._browser = None


class DrissionPageMiddleware:
    """
    Scrapy middleware for handling requests with DrissionPage.
    """

    def __init__(self):
        """Initializes the middleware."""
        self.browser_managers: Dict[str, BrowserManager] = {}
        self.semaphores: Dict[str, asyncio.Semaphore] = {}
        self.logger = logging.getLogger(__name__)

    @classmethod
    def from_crawler(cls, crawler: Crawler) -> 'DrissionPageMiddleware':
        """
        Factory method to create a middleware instance from a crawler.
        Connects spider_opened and spider_closed signals.
        """
        middleware = cls()
        crawler.signals.connect(middleware.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(middleware.spider_closed, signal=signals.spider_closed)
        return middleware

    def spider_opened(self, spider: SpiderType) -> None:
        """
        Called when a spider is opened. Initializes resources for the spider.
        """
        self.logger.info(f"Spider opened: {spider.name}. Initializing DrissionPage resources.")
        # Create a BrowserManager for the spider
        self.browser_managers[spider.name] = BrowserManager(spider.settings)

        # Create a semaphore to limit concurrent tab usage
        concurrency = spider.settings.getint('DRISSIONPAGE_CONCURRENT_TABS', 4)
        self.logger.info(f"Concurrent tab limit for {spider.name} set to: {concurrency}")
        self.semaphores[spider.name] = asyncio.Semaphore(concurrency)

    def spider_closed(self, spider: SpiderType) -> None:
        """
        Called when a spider is closed. Cleans up resources.
        """
        self.logger.info(f"Spider closed: {spider.name}. Cleaning up DrissionPage resources.")
        if manager := self.browser_managers.pop(spider.name, None):
            manager.close()
        self.semaphores.pop(spider.name, None)

    async def process_request(self, request: Request, spider: SpiderType) -> Optional[Union[Request, ResponseType]]:
        """
        Processes a request asynchronously using a pooled browser tab.

        If the request meta contains `dp_page_type: 'drissionpage'`, this method
        will acquire a semaphore, open a new browser tab, navigate to the URL,
        and return a `DrissionResponse` containing the page content and the
        tab manager.
        """
        if request.meta.get('dp_page_type') != "drissionpage":
            return None

        semaphore = self.semaphores.get(spider.name)
        if not semaphore:
            self.logger.error(f"Semaphore not found for spider {spider.name}.")
            return None

        self.logger.debug(f"Acquiring semaphore for {request.url}. Current semaphore value: {semaphore._value}")
        await semaphore.acquire()
        self.logger.debug(f"Semaphore acquired for {request.url}. Remaining slots: {semaphore._value}")

        browser_manager = self.browser_managers[spider.name]
        tab = None
        tab_manager = None

        try:
            browser = await browser_manager.get_browser()
            drission_meta = request.meta.get('drissionpage', {})
            wait_time = drission_meta.get('wait_time')
            timeout = drission_meta.get('timeout')

            # Create a new tab for each request to ensure isolation
            tab = browser.new_tab()
            tab_manager = _TabManager(tab, semaphore)

            blocked_urls = spider.settings.getlist('DRISSIONPAGE_BLOCKED_URLS')
            if blocked_urls:
                tab.set.blocked_urls(blocked_urls)

            tab.get(request.url, timeout=timeout)

            if wait_time is not None:
                tab.wait(wait_time)

            # Return a response that includes the tab manager
            return DrissionResponse(
                url=tab.url,
                body=tab.html.encode('utf-8'),
                encoding='utf-8',
                request=request,
                page=tab_manager
            )
        except Exception as e:
            self.logger.error(f"Error processing DrissionRequest for {request.url}: {e}", exc_info=True)
            # If an error occurred, ensure the tab is closed and semaphore is released
            if tab_manager:
                tab_manager.close()
            elif tab:
                # If tab exists but tab_manager wasn't created, close tab and release semaphore
                try:
                    tab.close()
                except Exception as close_error:
                    self.logger.error(f"Error closing tab: {close_error}")
                finally:
                    semaphore.release()
            else:
                # If tab wasn't even created, just release the semaphore
                semaphore.release()
            return None
