# Scrapy + Splash Web Scraper

A web scraping project using Scrapy and Splash to parse JavaScript-rendered websites.

## Project Structure

```
scrapy_splash_project/
├── docker-compose.yml          # Splash container configuration
├── requirements.txt            # Python dependencies
├── scrapy.cfg                  # Scrapy deployment configuration
├── scraper/                    # Scrapy project directory
│   ├── __init__.py
│   ├── items.py               # Data models for scraped items
│   ├── middlewares.py         # Custom middlewares
│   ├── pipelines.py           # Data processing pipelines
│   ├── settings.py            # Scrapy & Splash configuration
│   └── spiders/               # Spider directory
│       ├── __init__.py
│       ├── example_spider.py  # Basic Splash spider
│       └── advanced_spider.py # Advanced Lua script example
```

## Setup Instructions

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 2. Start Splash Container

```bash
docker-compose up -d
```

This starts Splash on `http://localhost:8050`. You can verify it's running by visiting that URL in your browser.

### 3. Run a Spider

**Basic example (scrapes quotes):**
```bash
scrapy crawl example -o output.json
```

**Advanced example (with Lua script):**
```bash
scrapy crawl advanced -o advanced_output.json
```

## Key Components

### SplashRequest vs Regular Request

- **Regular Request**: Downloads static HTML only
- **SplashRequest**: Renders JavaScript and returns fully loaded page

```python
# Instead of:
yield scrapy.Request(url=url, callback=self.parse)

# Use:
yield SplashRequest(
    url=url,
    callback=self.parse,
    endpoint='render.html',
    args={'wait': 2}
)
```

### Splash Endpoints

1. **render.html** - Simple HTML rendering (most common)
2. **render.json** - Returns HTML + metadata
3. **render.png** - Takes screenshot
4. **execute** - Runs custom Lua scripts for advanced scenarios

### Common SplashRequest Arguments

```python
args={
    'wait': 2,              # Wait N seconds for JS to execute
    'timeout': 90,          # Maximum request timeout
    'html': 1,              # Return HTML (default for render.html)
    'png': 1,               # Include screenshot
    'har': 1,               # Include network traffic log
    'js_source': '...',     # Execute custom JavaScript
}
```

## Configuration (settings.py)

The key Splash settings configured:

```python
SPLASH_URL = 'http://localhost:8050'
DUPEFILTER_CLASS = 'scrapy_splash.SplashAwareDupeFilter'
HTTPCACHE_STORAGE = 'scrapy_splash.SplashAwareFSCacheStorage'

SPIDER_MIDDLEWARES = {
    'scrapy_splash.SplashDeduplicateArgsMiddleware': 100,
}

DOWNLOADER_MIDDLEWARES = {
    'scrapy_splash.SplashCookiesMiddleware': 723,
    'scrapy_splash.SplashMiddleware': 725,
    'scrapy.downloadermiddlewares.httpcompression.HttpCompressionMiddleware': 810,
}
```

## Tips & Best Practices

1. **Wait Time**: Set `wait` parameter based on how long the page takes to render
2. **Caching**: HTTP cache is enabled to avoid re-rendering pages during development
3. **Rate Limiting**: Configured with `DOWNLOAD_DELAY = 1` to be respectful to servers
4. **Lua Scripts**: Use for complex scenarios (scrolling, clicking, waiting for elements)
5. **Debug**: Visit `http://localhost:8050` to test Splash rendering interactively

## Stopping Splash

```bash
docker-compose down
```

## Troubleshooting

**Connection Refused Error:**
- Make sure Splash is running: `docker-compose ps`
- Check Splash logs: `docker-compose logs splash`

**JavaScript Not Rendering:**
- Increase `wait` time in SplashRequest args
- Check the page in Splash UI at `http://localhost:8050`

**Slow Performance:**
- Splash is resource-intensive; consider limiting concurrent requests
- Use caching during development to avoid repeated renders
