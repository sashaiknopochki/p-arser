# Complete RAG Website Parser Guide

## Overview

A complete system for parsing websites and preparing them for RAG (Retrieval-Augmented Generation) systems. Automatically crawls entire websites, renders JavaScript, and saves each page as a separate JSON file with rich metadata.

## Features

✅ **JavaScript Rendering** - Handles modern SPAs via Splash  
✅ **Full-Site Crawling** - Automatically follows all same-domain links  
✅ **Batch Processing** - Parse multiple websites from a single input file  
✅ **Smart Folder Structure** - Mirrors website organization with clean naming  
✅ **Subdomain Handling** - Groups subdomains under parent domain  
✅ **Clean Text Extraction** - Strips HTML tags, scripts, and styles  
✅ **Rich Metadata** - Perfect for RAG indexing and citations  
✅ **Git-Friendly** - Output and input data folders ignored by git  

## Quick Start

### 1. Start Splash
```bash
cd /Users/grace_scale/PycharmProjects/p-arser/scrapy_splash_project
docker-compose up -d
```

### 2. Parse a Single Website
```bash
# Crawls the site and all same-domain pages
scrapy crawl rag -a url=https://example.com
```

### 3. Batch Parse Multiple Websites
```bash
# Create input/urls.json with your URLs
scrapy crawl rag -a input_file=input/urls.json
```

## Input Format

Create `input/urls.json`:
```json
{
  "urls": [
    "https://example.com",
    "https://another-site.com",
    "https://docs.myapp.io"
  ]
}
```

The spider will:
1. Visit each URL
2. Parse the page
3. Follow all same-domain links
4. Save each page as separate JSON

## Output Structure

```
output/
  example_com/
    index_abc123.json
    about_def456.json
    docs/
      getting-started_ghi789.json
      
  myapp_io/
    docs/
      index_jkl012.json
      api_mno345.json
```

### Folder Naming Rules

1. **Dots → Underscores**: `example.com` → `example_com`
2. **Subdomains**: `docs.example.com` → `example_com/docs/`
3. **Path Structure**: `/docs/api` → `docs/api_hash.json`

### Example Outputs

**Domain**: `integreat.app`  
**Folder**: `integreat_app/`

**Domain**: `docs.integreat.app`  
**Folder**: `integreat_app/docs/`

**Domain**: `api.docs.integreat.app`  
**Folder**: `integreat_app/docs/api/`

## JSON Metadata

Each JSON file contains:

```json
{
  "url": "https://example.com/page",
  "url_hash": "md5_hash",
  "domain": "example.com",
  "path": "/page",
  "path_parts": ["page"],
  
  "title": "Page Title",
  "description": "Meta description",
  "keywords": "keywords",
  "language": "en",
  
  "body_html": "<body>...</body>",
  "body_text": "Clean text content",
  "text_length": 1234,
  
  "status_code": 200,
  "parsed_at": "2026-02-01T20:01:33.644984",
  "parsed_at_timestamp": 1769974893.644984
}
```

## Advanced Usage

### Limit Pages (for testing)
```bash
scrapy crawl rag -a url=https://example.com -s CLOSESPIDER_PAGECOUNT=10
```

### Adjust Wait Time
Edit `scraper/spiders/rag_spider.py` and change `wait` in the Lua script:
```python
assert(splash:wait(5))  # Change to 10 for slower sites
```

### Control Concurrency
Edit `scraper/settings.py`:
```python
CONCURRENT_REQUESTS_PER_DOMAIN = 1  # Increase for faster crawling
DOWNLOAD_DELAY = 2  # Decrease for faster crawling
```

## Folder Structure

```
scrapy_splash_project/
├── docker-compose.yml      # Splash configuration
├── requirements.txt        # Python dependencies
├── input/                  # URL lists (git-ignored)
│   └── urls_example.json
├── output/                 # Parsed websites (git-ignored)
│   └── example_com/
├── scraper/
│   ├── spiders/
│   │   └── rag_spider.py   # Main spider
│   ├── pipelines.py        # Output processing
│   └── settings.py         # Configuration
└── docs/                   # Documentation
```

## Processing for RAG

After parsing, typical RAG workflow:

### 1. Load Documents
```python
import json
from pathlib import Path

docs = []
for json_file in Path("output").rglob("*.json"):
    with open(json_file) as f:
        doc = json.load(f)
        docs.append(doc)
```

### 2. Chunk Text
```python
def chunk_text(text, chunk_size=500, overlap=50):
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size - overlap):
        chunk = ' '.join(words[i:i + chunk_size])
        chunks.append(chunk)
    return chunks

for doc in docs:
    doc['chunks'] = chunk_text(doc['body_text'])
```

### 3. Generate Embeddings
```python
from openai import OpenAI

client = OpenAI()

for doc in docs:
    for chunk in doc['chunks']:
        embedding = client.embeddings.create(
            input=chunk,
            model="text-embedding-3-small"
        )
        # Store embedding with metadata
```

### 4. Store in Vector DB
```python
# Example: ChromaDB
import chromadb

client = chromadb.Client()
collection = client.create_collection("my_docs")

for doc in docs:
    collection.add(
        documents=[doc['body_text']],
        metadatas=[{
            "url": doc['url'],
            "title": doc['title'],
            "domain": doc['domain']
        }],
        ids=[doc['url_hash']]
    )
```

## Scheduling Monthly Updates

### Using Cron (macOS/Linux)
```bash
# Edit crontab
crontab -e

# Add this line (runs on 1st of each month at 2 AM)
0 2 1 * * cd /Users/grace_scale/PycharmProjects/p-arser/scrapy_splash_project && docker-compose up -d && scrapy crawl rag -a input_file=input/urls.json
```

### Using Python Script
Create `scripts/monthly_update.py`:
```python
#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path

project_dir = Path(__file__).parent.parent

# Start Splash
subprocess.run(["docker-compose", "up", "-d"], cwd=project_dir)

# Run spider
result = subprocess.run([
    "scrapy", "crawl", "rag",
    "-a", "input_file=input/urls.json"
], cwd=project_dir)

sys.exit(result.returncode)
```

Then schedule with cron:
```bash
0 2 1 * * /usr/bin/python3 /path/to/scripts/monthly_update.py
```

## Troubleshooting

### No Content Extracted
- Increase `wait` time in Lua script
- Check if site uses iframes (needs custom handling)
- Visit `http://localhost:8050` to debug Splash rendering

### Too Many Pages
- Use `CLOSESPIDER_PAGECOUNT` setting
- Filter URLs in parse method
- Add URL patterns to exclude

### Slow Performance
- Increase `CONCURRENT_REQUESTS_PER_DOMAIN`
- Decrease `DOWNLOAD_DELAY`
- Use multiple Splash instances

### Git Tracking Issues
- Ensure `.gitignore` includes `output/` and `input/*.json`
- Never commit parsed data (can be regenerated)

## Best Practices

1. **Test First**: Use `CLOSESPIDER_PAGECOUNT=5` for initial tests
2. **Monitor**: Check Splash logs with `docker-compose logs splash`
3. **Clean Data**: Periodically delete old output before reparsing
4. **Version Input**: Keep `input/urls_example.json` in git as template
5. **Document Sources**: Note in README which sites you're parsing

## Next Steps

1. ✅ Set up your input URLs
2. ✅ Test with small page limit
3. ✅ Adjust wait times if needed
4. ✅ Run full crawl
5. ✅ Process JSON for your RAG system
6. ✅ Schedule monthly updates

## Support

See additional documentation:
- `docs/RAG_SETUP.md` - Detailed JSON structure
- `docs/SPLASH_CHEATSHEET.md` - Lua script examples
- `docs/README.md` - Original setup guide
