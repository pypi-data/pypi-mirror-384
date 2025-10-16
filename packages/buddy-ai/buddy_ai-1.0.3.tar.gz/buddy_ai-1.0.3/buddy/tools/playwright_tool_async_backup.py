"""
Playwright tool for web automation and testing.
Provides browser automation capabilities with support for multiple browsers.
"""

from typing import Any, Dict, List, Optional, Union
from pathlib import Path
import asyncio
import json
import threading

try:
    from playwright.async_api import async_playwright, Page, Browser, BrowserContext
    from playwright.sync_api import sync_playwright, Page as SyncPage, Browser as SyncBrowser
    playwright_available = True
except ImportError:
    playwright_available = False

from buddy.tools.toolkit import Toolkit
from buddy.utils.log import logger


class PlaywrightTools(Toolkit):
    """
    Playwright toolkit for web automation, testing, and scraping.
    Supports Chrome, Firefox, Safari, and Edge browsers.
    """

    def __init__(
        self,
        browser_type: str = "chromium",  # chromium, firefox, webkit
        headless: bool = True,
        timeout: int = 30000,  # 30 seconds
        viewport: Optional[Dict[str, int]] = None,
        user_agent: Optional[str] = None,
        **kwargs
    ):
        if not playwright_available:
            raise ImportError(
                "Playwright is not installed. Install it with: pip install playwright && playwright install"
            )
        
        self.browser_type = browser_type
        self.headless = headless
        self.timeout = timeout
        self.viewport = viewport or {"width": 1280, "height": 720}
        self.user_agent = user_agent
        
        # Use sync API instead of async to avoid event loop issues
        self._playwright = None
        self._browser = None
        self._context = None
        self._page = None

        super().__init__(
            name="playwright_tools",
            tools=[
                self.start_browser,
                self.navigate_to_page,
                self.click_element,
                self.fill_input,
                self.get_text_content,
                self.get_page_html,
                self.get_page_title,
                self.take_screenshot,
                self.wait_for_element,
                self.execute_javascript,
                self.get_element_attributes,
                self.submit_form,
                self.scroll_page,
                self.close_browser,
            ],
            **kwargs,
        )

    def _ensure_browser(self):
        """Ensure browser is running using sync API."""
        if self._playwright is None:
            self._playwright = sync_playwright().start()
            
        if self._browser is None:
            if self.browser_type == "chromium":
                self._browser = self._playwright.chromium.launch(headless=self.headless)
            elif self.browser_type == "firefox":
                self._browser = self._playwright.firefox.launch(headless=self.headless)
            elif self.browser_type == "webkit":
                self._browser = self._playwright.webkit.launch(headless=self.headless)
            else:
                raise ValueError(f"Unsupported browser type: {self.browser_type}")
                
        if self._context is None:
            context_options = {"viewport": self.viewport}
            if self.user_agent:
                context_options["user_agent"] = self.user_agent
            self._context = self._browser.new_context(**context_options)
            
        if self._page is None:
            self._page = self._context.new_page()
            self._page.set_default_timeout(self.timeout)

    def start_browser(self) -> str:
        """
        Start the web browser.
        
        Returns:
            Browser startup status
        """
        try:
            if self._browser is not None:
                return "Browser is already running"
            
            self._ensure_browser()
            
            return json.dumps({
                'status': 'success',
                'message': f'{self.browser_type.title()} browser started successfully',
                'headless': self.headless,
                'window_size': self.viewport
            })
            
        except Exception as e:
            logger.error(f"Error starting browser: {e}")
            return f"Error starting browser: {e}"

    def navigate_to_page(self, url: str) -> str:
        """
        Navigate to a webpage.
        
        Args:
            url: The URL to navigate to
            
        Returns:
            Success message with page title
        """
        try:
            self._ensure_browser()
            self._page.goto(url)
            title = self._page.title()
            current_url = self._page.url
            
            return f"Successfully navigated to '{title}' at {url}"
            
        except Exception as e:
            logger.error(f"Error navigating to {url}: {e}")
            return f"Error navigating to {url}: {e}"

    def click_element(self, selector: str) -> str:
        """
        Click on an element identified by CSS selector.
        
        Args:
            selector: CSS selector for the element to click
            
        Returns:
            Success message
        """
        async def _click():
            await self._ensure_browser()
            await self._page.click(selector)
            return f"Successfully clicked element: {selector}"
            
        return asyncio.run(_click())

    def fill_input(self, selector: str, text: str) -> str:
        """
        Fill an input field with text.
        
        Args:
            selector: CSS selector for the input field
            text: Text to fill in the input
            
        Returns:
            Success message
        """
        async def _fill():
            await self._ensure_browser()
            await self._page.fill(selector, text)
            return f"Successfully filled '{selector}' with text: {text}"
            
        return asyncio.run(_fill())

    def get_text_content(self, selector: str) -> str:
        """
        Get text content of an element.
        
        Args:
            selector: CSS selector for the element
            
        Returns:
            Text content of the element
        """
        async def _get_text():
            await self._ensure_browser()
            element = await self._page.locator(selector).first
            if await element.count() == 0:
                return f"Element not found: {selector}"
            text = await element.text_content()
            return text or ""
            
        return asyncio.run(_get_text())

    def get_page_html(self, selector: Optional[str] = None) -> str:
        """
        Get HTML content of the page or specific element.
        
        Args:
            selector: Optional CSS selector for specific element
            
        Returns:
            HTML content
        """
        async def _get_html():
            await self._ensure_browser()
            if selector:
                element = await self._page.locator(selector).first
                if await element.count() == 0:
                    return f"Element not found: {selector}"
                return await element.inner_html()
            return await self._page.content()
            
        return asyncio.run(_get_html())

    def get_page_title(self) -> str:
        """
        Get the title of the current page.
        
        Returns:
            Page title
        """
        async def _get_title():
            await self._ensure_browser()
            return await self._page.title()
            
        return asyncio.run(_get_title())

    def take_screenshot(self, path: Optional[str] = None, full_page: bool = False) -> str:
        """
        Take a screenshot of the current page.
        
        Args:
            path: Optional file path to save screenshot
            full_page: Whether to capture the full scrollable page
            
        Returns:
            Path to saved screenshot or base64 encoded image
        """
        async def _screenshot():
            await self._ensure_browser()
            screenshot_path = path or f"screenshot_{int(asyncio.get_event_loop().time())}.png"
            
            await self._page.screenshot(
                path=screenshot_path,
                full_page=full_page
            )
            return f"Screenshot saved to: {screenshot_path}"
            
        return asyncio.run(_screenshot())

    def wait_for_element(self, locator_type: str, locator_value: str, timeout: Optional[int] = None) -> str:
        """
        Wait for an element to appear on the page.
        
        Args:
            locator_type: Type of locator (id, name, class_name, tag_name, css_selector, xpath)
            locator_value: Value of the locator
            timeout: Optional timeout in milliseconds
            
        Returns:
            Success message when element appears
        """
        async def _wait():
            await self._ensure_browser()
            
            by_mapping = {
                'id': f"#{locator_value}",
                'name': f"[name='{locator_value}']",
                'class_name': f".{locator_value}",
                'tag_name': locator_value,
                'css_selector': locator_value,
                'xpath': locator_value,
                'link_text': f"text={locator_value}",
                'partial_link_text': f"text*={locator_value}"
            }
            
            if locator_type not in by_mapping:
                return f"Invalid locator type: {locator_type}"
            
            # For xpath, use xpath selector, otherwise use CSS
            if locator_type == 'xpath':
                selector = f"xpath={locator_value}"
            else:
                selector = by_mapping[locator_type]
            
            wait_timeout = timeout or self.timeout
            await self._page.wait_for_selector(selector, timeout=wait_timeout)
            return f"Element appeared: {locator_type}='{locator_value}'"
            
        return asyncio.run(_wait())

    def execute_javascript(self, script: str) -> str:
        """
        Execute JavaScript code on the page.
        
        Args:
            script: JavaScript code to execute
            
        Returns:
            Result of JavaScript execution
        """
        async def _execute():
            await self._ensure_browser()
            result = await self._page.evaluate(script)
            return str(result) if result is not None else "Script executed successfully"
            
        return asyncio.run(_execute())

    def get_element_attributes(self, selector: str, attributes: List[str]) -> str:
        """
        Get attributes of an element.
        
        Args:
            selector: CSS selector for the element
            attributes: List of attribute names to retrieve
            
        Returns:
            JSON string with attribute values
        """
        async def _get_attrs():
            await self._ensure_browser()
            element = await self._page.locator(selector).first
            if await element.count() == 0:
                return f"Element not found: {selector}"
                
            attrs = {}
            for attr in attributes:
                value = await element.get_attribute(attr)
                attrs[attr] = value
                
            return json.dumps(attrs, indent=2)
            
        return asyncio.run(_get_attrs())

    def submit_form(self, form_selector: str) -> str:
        """
        Submit a form.
        
        Args:
            form_selector: CSS selector for the form element
            
        Returns:
            Success message
        """
        async def _submit():
            await self._ensure_browser()
            await self._page.locator(form_selector).press("Enter")
            return f"Form submitted: {form_selector}"
            
        return asyncio.run(_submit())

    def scroll_page(self, direction: str = "down", pixels: int = 500) -> str:
        """
        Scroll the page.
        
        Args:
            direction: Direction to scroll ('up', 'down', 'left', 'right')
            pixels: Number of pixels to scroll
            
        Returns:
            Success message
        """
        async def _scroll():
            await self._ensure_browser()
            
            script_map = {
                "down": f"window.scrollBy(0, {pixels})",
                "up": f"window.scrollBy(0, -{pixels})",
                "right": f"window.scrollBy({pixels}, 0)",
                "left": f"window.scrollBy(-{pixels}, 0)"
            }
            
            if direction not in script_map:
                return f"Invalid direction: {direction}. Use 'up', 'down', 'left', or 'right'."
                
            await self._page.evaluate(script_map[direction])
            return f"Scrolled {direction} by {pixels} pixels"
            
        return asyncio.run(_scroll())

    def close_browser(self) -> str:
        """
        Close the browser and cleanup resources.
        
        Returns:
            Success message
        """
        async def _close():
            if self._page:
                await self._page.close()
                self._page = None
            if self._context:
                await self._context.close()
                self._context = None
            if self._browser:
                await self._browser.close()
                self._browser = None
            if self._playwright:
                await self._playwright.stop()
                self._playwright = None
            return "Browser closed successfully"
            
        return asyncio.run(_close())
