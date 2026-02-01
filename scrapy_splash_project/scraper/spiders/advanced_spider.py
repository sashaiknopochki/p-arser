import scrapy
from scrapy_splash import SplashRequest


class AdvancedSpider(scrapy.Spider):
    name = "advanced"

    start_urls = ["https://example.com"]

    # Lua script for advanced interactions
    script = """
    function main(splash, args)
        -- Set user agent
        splash:set_user_agent('Mozilla/5.0 (compatible; MyBot/1.0)')

        -- Visit the URL
        assert(splash:go(args.url))

        -- Wait for page to load
        assert(splash:wait(args.wait))

        -- Execute custom JavaScript (example: scroll to bottom)
        splash:evaljs("window.scrollTo(0, document.body.scrollHeight);")

        -- Wait a bit more after scrolling
        splash:wait(1)

        -- You can interact with elements
        -- splash:evaljs("document.querySelector('#some-button').click();")
        -- splash:wait(2)

        -- Return results
        return {
            html = splash:html(),
            png = splash:png(),  -- Screenshot
            har = splash:har(),  -- HTTP Archive for network requests
        }
    end
    """

    def start_requests(self):
        """
        Use Lua script for advanced scenarios:
        - Custom JavaScript execution
        - Taking screenshots
        - Capturing network traffic
        - Simulating user interactions
        """
        for url in self.start_urls:
            yield SplashRequest(
                url=url,
                callback=self.parse,
                endpoint="execute",  # Use 'execute' endpoint for Lua scripts
                args={
                    "lua_source": self.script,
                    "wait": 3,
                    "timeout": 120,
                },
            )

    def parse(self, response):
        """
        Parse response from Lua script.
        response.data contains the dictionary returned by the Lua script.
        """
        self.logger.info(f"Parsing: {response.url}")

        # Access the HTML
        # Note: When using execute endpoint, we get response normally
        # but we can also access response.data for custom return values

        # Example: Extract data
        title = response.css("title::text").get()

        yield {
            "url": response.url,
            "title": title,
            "status": response.status,
        }

        # The PNG screenshot is available in response.data['png']
        # The HAR file is in response.data['har']
        # You could save these to files if needed
