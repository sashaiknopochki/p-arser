import scrapy


class NoSplashSpider(scrapy.Spider):
    """
    This spider demonstrates what happens when you try to scrape
    a JavaScript-rendered page WITHOUT using Splash.

    Run with: scrapy crawl no_splash -o no_splash_output.json

    You'll see it gets 0 items because the quotes are loaded via JavaScript!
    """

    name = "no_splash"
    start_urls = ["https://quotes.toscrape.com/js/"]

    def parse(self, response):
        self.logger.info(f"Parsing: {response.url}")

        # Try to extract quotes (will find nothing!)
        quotes = response.css("div.quote")
        self.logger.warning(f"Found {len(quotes)} quotes (without Splash)")

        for quote in quotes:
            yield {
                "text": quote.css("span.text::text").get(),
                "author": quote.css("small.author::text").get(),
                "tags": quote.css("div.tags a.tag::text").getall(),
            }
