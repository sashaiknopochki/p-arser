# Splash Cheat Sheet

## Basic SplashRequest

```python
from scrapy_splash import SplashRequest

yield SplashRequest(
    url='https://example.com',
    callback=self.parse,
    endpoint='render.html',
    args={'wait': 2}
)
```

## Common Endpoints

### 1. render.html (Most Common)
Returns rendered HTML after JavaScript execution.

```python
yield SplashRequest(
    url=url,
    endpoint='render.html',
    args={
        'wait': 2,        # Wait 2 seconds
        'timeout': 90,    # Request timeout
    }
)
```

### 2. render.json
Returns HTML + metadata (images, screenshots, etc.)

```python
yield SplashRequest(
    url=url,
    endpoint='render.json',
    args={
        'html': 1,        # Include HTML
        'png': 1,         # Include screenshot
        'wait': 2,
    }
)
```

### 3. execute (Lua Scripts)
For complex interactions - scrolling, clicking, custom JavaScript.

```python
script = """
function main(splash, args)
    assert(splash:go(args.url))
    assert(splash:wait(2))
    
    -- Scroll to bottom
    splash:evaljs("window.scrollTo(0, document.body.scrollHeight);")
    splash:wait(1)
    
    return {html = splash:html()}
end
"""

yield SplashRequest(
    url=url,
    endpoint='execute',
    args={'lua_source': script}
)
```

## Useful Lua Script Snippets

### Click a Button
```lua
splash:evaljs("document.querySelector('#load-more').click();")
splash:wait(2)  -- Wait for content to load
```

### Fill and Submit a Form
```lua
splash:evaljs("document.querySelector('#search').value = 'query';")
splash:evaljs("document.querySelector('form').submit();")
splash:wait(3)
```

### Scroll to Load Infinite Scroll
```lua
for i=1,5 do
    splash:evaljs("window.scrollTo(0, document.body.scrollHeight);")
    splash:wait(1)
end
```

### Wait for Element to Appear
```lua
-- Wait up to 10 seconds for element
splash:wait_for_resume([[
    function main(splash) {
        var checkExist = setInterval(function() {
            if (document.querySelector('.target-element')) {
                clearInterval(checkExist);
                splash.resume();
            }
        }, 100);
        
        setTimeout(function() {
            clearInterval(checkExist);
            splash.resume();
        }, 10000);
    }
]], 10)
```

### Take a Screenshot
```lua
return {
    html = splash:html(),
    png = splash:png(),
}
```

### Capture Network Traffic
```lua
return {
    html = splash:html(),
    har = splash:har(),  -- HTTP Archive
}
```

## Common args Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `wait` | float | Seconds to wait after page load |
| `timeout` | float | Maximum request timeout |
| `html` | int | Return HTML (1=yes, 0=no) |
| `png` | int | Return screenshot |
| `har` | int | Return network traffic log |
| `width` | int | Viewport width (default: 1024) |
| `height` | int | Viewport height (default: 768) |
| `js_source` | string | JavaScript code to execute |
| `lua_source` | string | Lua script for complex scenarios |

## Debugging Tips

### 1. Test in Splash UI
Visit `http://localhost:8050` and test your Lua scripts interactively.

### 2. Increase Verbosity
In docker-compose.yml:
```yaml
environment:
  - SPLASH_VERBOSITY=5  # Maximum verbosity
```

### 3. Save Screenshots
```python
def parse(self, response):
    # When using render.json with png=1
    if 'png' in response.data:
        with open('screenshot.png', 'wb') as f:
            f.write(base64.b64decode(response.data['png']))
```

### 4. Inspect Network Requests
```python
def parse(self, response):
    if 'har' in response.data:
        har_data = response.data['har']
        for entry in har_data['log']['entries']:
            print(f"Request: {entry['request']['url']}")
```

## Performance Tips

1. **Use caching** during development (already configured)
2. **Adjust wait times** - don't wait longer than necessary
3. **Limit concurrent requests** - Splash is resource-intensive
4. **Reuse Lua scripts** - define once, use multiple times
5. **Use render.html** when possible - faster than execute endpoint

## Common Patterns

### Pattern 1: Infinite Scroll
```python
script = """
function main(splash, args)
    splash:go(args.url)
    splash:wait(2)
    
    -- Scroll 5 times
    for i=1,5 do
        splash:evaljs("window.scrollTo(0, document.body.scrollHeight);")
        splash:wait(1)
    end
    
    return {html = splash:html()}
end
"""
```

### Pattern 2: Login and Scrape
```python
script = """
function main(splash, args)
    splash:go(args.url)
    splash:wait(1)
    
    -- Fill login form
    splash:evaljs("document.querySelector('#username').value = 'user';")
    splash:evaljs("document.querySelector('#password').value = 'pass';")
    splash:evaljs("document.querySelector('form').submit();")
    splash:wait(3)
    
    -- Now on authenticated page
    return {html = splash:html()}
end
"""
```

### Pattern 3: Handle Pop-ups
```python
script = """
function main(splash, args)
    splash:go(args.url)
    splash:wait(2)
    
    -- Close cookie banner
    splash:evaljs("var btn = document.querySelector('.cookie-accept'); if(btn) btn.click();")
    splash:wait(0.5)
    
    return {html = splash:html()}
end
"""
```
