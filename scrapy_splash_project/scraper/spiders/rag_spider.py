import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

import scrapy
from scrapy_splash import SplashRequest


class RagSpider(scrapy.Spider):
    """
    Spider for parsing websites for RAG (Retrieval-Augmented Generation).
    Extracts clean text from body, saves each page as separate JSON.

    Usage:
    Single URL (crawls all same-domain links):
      scrapy crawl rag -a url=https://example.com

    Batch mode (from input file):
      scrapy crawl rag -a input_file=input/urls_example.json
    """

    name = "rag"

    custom_settings = {
        "ITEM_PIPELINES": {
            "scraper.pipelines.RagPipeline": 300,
        },
        # Disable offsite middleware to avoid conflicts with Splash
        "DOWNLOADER_MIDDLEWARES": {
            "scrapy.downloadermiddlewares.offsite.OffsiteMiddleware": None,
        },
    }

    def __init__(self, url=None, input_file=None, *args, **kwargs):
        super(RagSpider, self).__init__(*args, **kwargs)

        self.start_urls = []
        self.allowed_domains = []
        self.domain_map = {}  # Maps URL to its domain for filtering

        # Mode 1: Single URL
        if url:
            self.start_urls = [url]
            self._add_domain_from_url(url)
            self.logger.info(f"Single URL mode: {url}")

        # Mode 2: Batch from input file
        elif input_file:
            self._load_urls_from_file(input_file)
            self.logger.info(
                f"Batch mode: Loaded {len(self.start_urls)} URLs from {input_file}"
            )

        else:
            raise ValueError(
                "Please provide URL or input_file:\n"
                "  scrapy crawl rag -a url=https://example.com\n"
                "  scrapy crawl rag -a input_file=input/urls_example.json"
            )

        self.logger.info(f"Allowed domains: {self.allowed_domains}")
        self.logger.info(f"Starting with {len(self.start_urls)} URLs")

    def _add_domain_from_url(self, url):
        """Extract and add domain from URL to allowed list"""
        parsed = urlparse(url)
        domain = parsed.netloc

        # Store domain for this URL
        self.domain_map[url] = domain

        # Add both www and non-www versions
        if domain.startswith("www."):
            base = domain[4:]
            if domain not in self.allowed_domains:
                self.allowed_domains.append(domain)
            if base not in self.allowed_domains:
                self.allowed_domains.append(base)
        else:
            if domain not in self.allowed_domains:
                self.allowed_domains.append(domain)
            www_domain = f"www.{domain}"
            if www_domain not in self.allowed_domains:
                self.allowed_domains.append(www_domain)

    def _load_urls_from_file(self, input_file):
        """Load URLs from JSON input file"""
        file_path = Path(input_file)
        if not file_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_file}")

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        urls = data.get("urls", [])
        if not urls:
            raise ValueError(f"No URLs found in {input_file}")

        for url in urls:
            self.start_urls.append(url)
            self._add_domain_from_url(url)

    lua_script = """
    function main(splash, args)
        splash:set_user_agent('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

        -- Increase viewport for better rendering
        splash:set_viewport_size(1920, 1080)

        assert(splash:go(args.url))

        -- Initial wait for page structure
        assert(splash:wait(3))

        -- Wait for dynamic content to load
        -- Check for actual content in body, not just container
        local max_wait = 15
        local check_interval = 1
        local elapsed = 0

        while elapsed < max_wait do
            -- Get body text length
            local body = splash:select('body')
            if body then
                local text = body:text()
                -- If body has substantial content (more than just "enable JS" message)
                if text and string.len(text) > 200 then
                    break
                end
            end
            splash:wait(check_interval)
            elapsed = elapsed + check_interval
        end

        -- Final wait to ensure everything is loaded
        splash:wait(2)

        return {html = splash:html()}
    end
    """

    def start_requests(self):
        for url in self.start_urls:
            yield SplashRequest(
                url=url,
                callback=self.parse,
                endpoint="execute",
                args={
                    "lua_source": self.lua_script,
                    "timeout": 120,
                },
            )

    def parse(self, response):
        """Extract page content and metadata for RAG"""

        # Generate unique ID from URL
        url_hash = hashlib.md5(response.url.encode()).hexdigest()

        # Extract metadata
        title = response.css("title::text").get()
        if title:
            title = title.strip()

        description = response.css('meta[name="description"]::attr(content)').get()
        keywords = response.css('meta[name="keywords"]::attr(content)').get()

        # Extract language
        lang = response.css("html::attr(lang)").get() or "unknown"

        # Extract body content
        body_html = response.css("body").get()

        # Extract clean text from body (removing scripts, styles, etc.)
        body_text = self.extract_clean_text(response)

        # Parse URL path for folder structure
        parsed_url = urlparse(response.url)
        path_parts = [p for p in parsed_url.path.split("/") if p]

        yield {
            "url": response.url,
            "url_hash": url_hash,
            "domain": parsed_url.netloc,
            "path": parsed_url.path,
            "path_parts": path_parts,  # For folder structure
            # Metadata
            "title": title,
            "description": description,
            "keywords": keywords,
            "language": lang,
            # Content
            "body_html": body_html,  # Full body HTML
            "body_text": body_text,  # Clean text only
            "text_length": len(body_text) if body_text else 0,
            # Technical metadata
            "status_code": response.status,
            "parsed_at": datetime.utcnow().isoformat(),
            "parsed_at_timestamp": datetime.utcnow().timestamp(),
        }

        # Follow all same-domain links
        current_domain = parsed_url.netloc
        for link in response.css("a::attr(href)").getall():
            absolute_url = response.urljoin(link)
            link_domain = urlparse(absolute_url).netloc

            # Check if link is same domain (or www variant)
            if self._is_same_domain(current_domain, link_domain):
                yield SplashRequest(
                    url=absolute_url,
                    callback=self.parse,
                    endpoint="execute",
                    args={
                        "lua_source": self.lua_script,
                        "timeout": 120,
                    },
                )

    def _is_same_domain(self, domain1, domain2):
        """Check if two domains are the same (accounting for www)"""
        # Normalize domains (remove www)
        d1 = domain1.replace("www.", "")
        d2 = domain2.replace("www.", "")
        return d1 == d2

    def extract_clean_text(self, response):
        """
        Extract clean text from body, removing:
        - Scripts
        - Styles
        - Comments
        - Extra whitespace
        """
        # Remove script and style tags
        body = response.css("body").get()
        if not body:
            return ""

        # Remove script tags and their content
        body = re.sub(
            r"<script[^>]*>.*?</script>", "", body, flags=re.DOTALL | re.IGNORECASE
        )

        # Remove style tags and their content
        body = re.sub(
            r"<style[^>]*>.*?</style>", "", body, flags=re.DOTALL | re.IGNORECASE
        )

        # Remove HTML comments
        body = re.sub(r"<!--.*?-->", "", body, flags=re.DOTALL)

        # Remove all HTML tags
        text = re.sub(r"<[^>]+>", " ", body)

        # Decode HTML entities
        from html import unescape

        text = unescape(text)

        # Clean up whitespace
        text = re.sub(r"\s+", " ", text)
        text = text.strip()

        return text
