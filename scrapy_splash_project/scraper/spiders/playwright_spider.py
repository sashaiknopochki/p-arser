"""
Alternative spider using Playwright for complex sites like integreat.app
that use iframes and advanced JavaScript.

Install: pip install scrapy-playwright playwright
Then: playwright install chromium

Usage: scrapy crawl playwright -a url=https://integreat.app/staedteregion-aachen/de/wichtige-aemter
"""

import hashlib
import re
from datetime import datetime
from urllib.parse import urlparse

import scrapy


class PlaywrightSpider(scrapy.Spider):
    name = "playwright"

    custom_settings = {
        "DOWNLOAD_HANDLERS": {
            "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
            "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
        },
        "TWISTED_REACTOR": "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
        "ITEM_PIPELINES": {
            "scraper.pipelines.RagPipeline": 300,
        },
        "PLAYWRIGHT_BROWSER_TYPE": "chromium",
        "PLAYWRIGHT_LAUNCH_OPTIONS": {
            "headless": True,
        },
    }

    def __init__(self, url=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if not url:
            raise ValueError(
                "Please provide URL: scrapy crawl playwright -a url=https://example.com"
            )

        self.start_urls = [url]
        parsed = urlparse(url)
        domain = parsed.netloc

        if domain.startswith("www."):
            self.allowed_domains = [domain, domain[4:]]
        else:
            self.allowed_domains = [domain, f"www.{domain}"]

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(
                url,
                meta={
                    "playwright": True,
                    "playwright_include_page": True,
                    "playwright_page_methods": [
                        ("wait_for_timeout", 10000),  # Wait 10 seconds
                    ],
                },
                callback=self.parse,
                errback=self.errback,
            )

    async def parse(self, response):
        page = response.meta["playwright_page"]

        # Wait for content to load
        try:
            await page.wait_for_selector("body", timeout=10000)

            # Get all iframes
            frames = page.frames
            self.logger.info(f"Found {len(frames)} frames")

            # Try to get content from main frame or first iframe
            content_html = await page.content()

            # If main content is empty, try iframes
            if len(content_html) < 1000:
                for frame in frames[1:]:  # Skip main frame
                    try:
                        frame_content = await frame.content()
                        if len(frame_content) > len(content_html):
                            content_html = frame_content
                            self.logger.info(
                                f"Using iframe content: {len(frame_content)} bytes"
                            )
                    except:
                        pass

        except Exception as e:
            self.logger.error(f"Error getting content: {e}")
            content_html = await page.content()

        finally:
            await page.close()

        # Parse the response
        url_hash = hashlib.md5(response.url.encode()).hexdigest()
        parsed_url = urlparse(response.url)
        path_parts = [p for p in parsed_url.path.split("/") if p]

        # Extract metadata from original response
        title = response.css("title::text").get()
        if title:
            title = title.strip()

        # Clean text from HTML
        body_text = self.extract_clean_text(content_html)

        yield {
            "url": response.url,
            "url_hash": url_hash,
            "domain": parsed_url.netloc,
            "path": parsed_url.path,
            "path_parts": path_parts,
            "title": title,
            "description": response.css(
                'meta[name="description"]::attr(content)'
            ).get(),
            "keywords": response.css('meta[name="keywords"]::attr(content)').get(),
            "language": response.css("html::attr(lang)").get() or "unknown",
            "body_html": content_html,
            "body_text": body_text,
            "text_length": len(body_text) if body_text else 0,
            "status_code": response.status,
            "parsed_at": datetime.utcnow().isoformat(),
            "parsed_at_timestamp": datetime.utcnow().timestamp(),
        }

    def extract_clean_text(self, html):
        """Extract clean text from HTML"""
        if not html:
            return ""

        # Remove script and style tags
        html = re.sub(
            r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE
        )
        html = re.sub(
            r"<style[^>]*>.*?</style>", "", html, flags=re.DOTALL | re.IGNORECASE
        )
        html = re.sub(r"<!--.*?-->", "", html, flags=re.DOTALL)

        # Remove HTML tags
        text = re.sub(r"<[^>]+>", " ", html)

        # Decode HTML entities
        from html import unescape

        text = unescape(text)

        # Clean whitespace
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    async def errback(self, failure):
        page = failure.request.meta.get("playwright_page")
        if page:
            await page.close()
