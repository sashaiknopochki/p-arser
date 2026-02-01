# Solution for Iframe-Heavy Sites (like integreat.app)

## The Problem

Some modern sites like `integreat.app` load their content entirely in iframes using complex JavaScript. Splash has difficulty extracting content from iframes.

## Solution: Use Playwright Instead

Playwright is a more powerful browser automation tool that can access iframe content.

### Setup

1. **Install Playwright dependencies:**
```bash
pip install scrapy-playwright playwright
playwright install chromium
```

2. **Use the `playwright` spider:**
```bash
scrapy crawl playwright -a url=https://integreat.app/staedteregion-aachen/de/wichtige-aemter
```

## When to Use Which Spider

### Use `rag` spider (Splash) for:
- ✅ Most modern JavaScript sites (React, Vue, Angular)
- ✅ Sites that render content in the main page
- ✅ Faster performance
- ✅ Lower resource usage
- ✅ **Recommended default**

Examples: Most e-commerce, blogs, documentation sites

### Use `playwright` spider for:
- ✅ Sites using iframes for content
- ✅ Sites with complex JavaScript interactions
- ✅ Sites that Splash can't render properly
- ✅ When you need full browser capabilities

Examples: integreat.app, some enterprise portals

## How Playwright Works

The `playwright` spider:
1. Launches a real Chromium browser
2. Waits for JavaScript to execute (10 seconds by default)
3. Detects and accesses iframe content
4. Extracts the fullest content available
5. Returns clean text for RAG

## Performance Comparison

| Feature | Splash (rag) | Playwright |
|---------|--------------|------------|
| Speed | ⚡ Fast | 🐢 Slower |
| Memory | 💾 Low | 💾💾 High |
| Iframe Support | ❌ Limited | ✅ Full |
| Browser | Lightweight | Full Chromium |
| Setup | Docker only | Pip + browser |

## Testing Your Sites

To find out which spider to use:

1. **Try Splash first:**
```bash
scrapy crawl rag -a url=https://yoursite.com -s CLOSESPIDER_PAGECOUNT=1
```

2. **Check the output:**
```bash
cat output/yoursite_com/*/\*.json | grep text_length
```

3. **If text_length is too small (<200), try Playwright:**
```bash
scrapy crawl playwright -a url=https://yoursite.com -s CLOSESPIDER_PAGECOUNT=1
```

## Batch Processing with Mixed Spiders

For sites that need Playwright, you'll need to run them separately:

**Splash sites (input/urls_splash.json):**
```bash
scrapy crawl rag -a input_file=input/urls_splash.json
```

**Playwright sites (input/urls_playwright.json):**
```bash
scrapy crawl playwright -a url=https://integreat.app/...
```

*Note: Playwright spider doesn't support batch mode yet - you'd need to run each URL separately or extend the spider.*

## Hybrid Approach

You can use both in your workflow:
1. Run Splash for 90% of sites (fast)
2. Manually identify problematic sites
3. Re-run those specific sites with Playwright

## Troubleshooting Playwright

### Installation Issues
```bash
# If playwright install fails
playwright install --force chromium
```

### Memory Issues
- Playwright uses ~500MB per browser instance
- Reduce `CONCURRENT_REQUESTS` if system is slow
- Close other applications

### Still No Content
- Increase wait time in `playwright_page_methods`
- Check if site requires login or cookies
- Some sites may block automation (captcha, bot detection)

## Recommendation

**For your RAG project:**
1. Start with Splash (`rag` spider) for all sites
2. Test output quality
3. Only switch to Playwright for problematic sites
4. Document which sites need Playwright in your URLs file

Most sites will work fine with Splash - Playwright is the "heavy artillery" for special cases.
