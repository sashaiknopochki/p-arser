import scrapy
from scrapy_splash import SplashRequest


class ExampleSpider(scrapy.Spider):
    name = "example"

    # Example: scraping a JavaScript-heavy website
    start_urls = ["https://quotes.toscrape.com/js/"]

    def start_requests(self):
        """
        Override start_requests to use SplashRequest instead of regular Request.
        This ensures JavaScript is executed before parsing.
        """
        for url in self.start_urls:
            yield SplashRequest(
                url=url,
                callback=self.parse,
                endpoint="render.html",  # Use render.html for simple HTML rendering
                args={
                    "wait": 2,  # Wait 2 seconds for JavaScript to load
                    "timeout": 90,  # Maximum timeout
                },
            )

    def parse(self, response):
        """
        Parse the rendered HTML response.
        By the time we get here, JavaScript has already executed.
        """
        self.logger.info(f"Parsing: {response.url}")

        # Extract quotes from the page
        for quote in response.css("div.quote"):
            yield {
                "text": quote.css("span.text::text").get(),
                "author": quote.css("small.author::text").get(),
                "tags": quote.css("div.tags a.tag::text").getall(),
            }

        # Follow pagination links
        next_page = response.css("li.next a::attr(href)").get()
        if next_page:
            yield SplashRequest(
                url=response.urljoin(next_page),
                callback=self.parse,
                endpoint="render.html",
                args={
                    "wait": 2,
                    "timeout": 90,
                },
            )
