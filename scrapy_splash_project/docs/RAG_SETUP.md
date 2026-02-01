# RAG Spider - Website Parser for RAG Systems

## Overview

This spider parses websites and saves each page as a separate JSON file, organized in folders matching the website structure. Perfect for feeding into RAG (Retrieval-Augmented Generation) systems.

## Features

- ✅ JavaScript rendering support via Splash
- ✅ Each page = separate JSON file
- ✅ Automatic folder structure based on URL paths
- ✅ Clean text extraction (removes HTML tags, scripts, styles)
- ✅ Rich metadata for RAG indexing
- ✅ UTF-8 support for international content

## Output Structure

```
output/
  domain.com/
    index_abc123.json          # Homepage
    subfolder/
      page1_def456.json        # /subfolder/page1
      page2_ghi789.json        # /subfolder/page2
```

## JSON Metadata Structure

Each JSON file contains:

### Core Identification
```json
{
  "url": "https://example.com/page",
  "url_hash": "md5_hash_of_url",
  "domain": "example.com",
  "path": "/page",
  "path_parts": ["page"]
}
```

### Content Metadata
```json
{
  "title": "Page Title",
  "description": "Meta description",
  "keywords": "Meta keywords",
  "language": "en"
}
```

### Page Content
```json
{
  "body_html": "<body>Full HTML</body>",
  "body_text": "Clean text without HTML tags",
  "text_length": 1234
}
```

### Technical Metadata
```json
{
  "status_code": 200,
  "parsed_at": "2026-02-01T19:34:31.082533",
  "parsed_at_timestamp": 1769970871.082539
}
```

## Recommended Metadata for RAG

The current implementation includes these important fields for RAG:

1. **url** - Source URL (for citations)
2. **url_hash** - Unique identifier for deduplication
3. **domain** - For domain-specific filtering
4. **title** - Document title (high semantic value)
5. **description** - Summary (if available)
6. **language** - For language-specific processing
7. **body_text** - Main content for embedding
8. **parsed_at** - For cache invalidation/freshness
9. **parsed_at_timestamp** - Sortable timestamp

## Usage

### Single Page
```bash
scrapy crawl rag -a url=https://example.com/page
```

### Output Location
```bash
output/example.com/page_abc123.json
```

## Example Output

See `output/quotes.toscrape.com/js_0393073f.json` for a real example.

## Why This Structure?

### Separate JSON Files
- ✅ Easy to add/remove individual documents
- ✅ Incremental updates (reparse only changed pages)
- ✅ Parallel processing for embeddings
- ✅ Simple version control (git diff works)

### Folder Organization
- ✅ Mirrors website structure
- ✅ Easy to find specific pages
- ✅ Supports partial site updates
- ✅ Human-readable organization

### Metadata Richness
- ✅ **url**: For citation generation
- ✅ **title**: High-value semantic signal
- ✅ **language**: Multi-lingual RAG support
- ✅ **parsed_at**: Cache management
- ✅ **body_text**: Clean content for embeddings
- ✅ **body_html**: Fallback for complex parsing

## Processing for RAG

After parsing, you can:

1. **Clean the text** - `body_text` is already cleaned of HTML
2. **Chunk the content** - Split long pages into smaller chunks
3. **Generate embeddings** - Use OpenAI, Cohere, or local models
4. **Store in vector DB** - Pinecone, Weaviate, ChromaDB, etc.
5. **Use metadata** - For filtering, routing, and citations

## Next Steps

1. Test with your specific URLs
2. Adjust wait times if needed (currently 5 seconds)
3. Add URL list support for batch processing
4. Implement full-site crawling
5. Add scheduling (cron) for monthly updates

## Known Limitations

- Pages using iframes may need custom handling
- Very complex SPAs might need longer wait times or custom Lua scripts
- Currently processes one page at a time (will expand to full-site crawling)
