# EVIKA /audit Endpoint Documentation

## Overview

The `/audit` endpoint is the core functionality of the EVIKA SaaS backend. It provides comprehensive website auditing with AEO (Answer Engine Optimization) and GEO (Geographic Optimization) signal extraction.

## Endpoint Details

- **URL**: `POST /audit`
- **Content-Type**: `application/json`
- **Authentication**: None (public endpoint)

## Request Format

```json
{
  "url": "https://example.com"
}
```

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `url` | string | Yes | The website URL to audit |

## Response Format

```json
{
  "site_id": "uuid-generated",
  "url": "https://example.com",
  "brand_name": "Example Brand",
  "description": "Short description of the site",
  "products": ["Product A", "Product B"],
  "location": "Detected Location",
  "faqs": ["Sample FAQ 1", "Sample FAQ 2"],
  "topics": ["topic1", "topic2"],
  "competitors": ["Competitor A", "Competitor B"],
  "pages_crawled": 15,
  "success": true
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `site_id` | string | Unique identifier for this audit |
| `url` | string | The audited website URL |
| `brand_name` | string | Extracted brand name |
| `description` | string | Website description |
| `products` | array | List of detected products/services |
| `location` | string | Geographic location if detected |
| `faqs` | array | List of FAQ questions found |
| `topics` | array | Main topics/keywords |
| `competitors` | array | Competitor mentions |
| `pages_crawled` | integer | Number of pages analyzed |
| `success` | boolean | Whether the audit completed successfully |

## How It Works

### Step 1: Website Crawling
- Uses ScrapingBee API for JavaScript-enabled crawling
- Limits to 15 pages maximum to control costs
- Extracts HTML, title, meta description, and images from each page

### Step 2: Signal Extraction
Extracts the following AEO + GEO signals:

#### AEO Signals (Answer Engine Optimization)
- **FAQs**: Question and answer pairs from schema markup and content
- **Schema Markup**: JSON-LD structured data (FAQ, Article, Product, etc.)
- **Alt Text Issues**: Images with missing or weak alt text
- **Brand Name**: From title, og:site_name, or schema.org/Organization
- **Products/Services**: From headings and schema.org/Product

#### GEO Signals (Geographic Optimization)
- **Hreflang Tags**: Language targeting signals
- **Local Business Schema**: Address and location data
- **Geo Meta Tags**: Geographic targeting information
- **Location Detection**: From content and schema markup

### Step 3: Data Storage
Saves all extracted data to Supabase with the following tables:

#### `sites` Table
- `id` (UUID, Primary Key)
- `url` (TEXT)
- `brand_name` (TEXT)
- `description` (TEXT)
- `location` (TEXT)
- `industry` (TEXT)
- `created_at` (TIMESTAMP)

#### `pages` Table
- `id` (UUID, Primary Key)
- `site_id` (UUID, Foreign Key)
- `url` (TEXT)
- `title` (TEXT)
- `raw_text` (TEXT)
- `images` (JSONB)
- `created_at` (TIMESTAMP)

#### `audits` Table
- `id` (UUID, Primary Key)
- `site_id` (UUID, Foreign Key)
- `url` (TEXT)
- `results` (JSONB) - Contains all extracted signals
- `created_at` (TIMESTAMP)

### Step 4: Response Generation
Returns a structured overview with the unique `site_id` for future reference.

## Development Mode

The endpoint includes a development mode that uses mock data instead of making real ScrapingBee API calls. This is controlled by the `DEVELOPMENT_MODE` environment variable:

```bash
export DEVELOPMENT_MODE=true
```

When in development mode:
- ScrapingBee API calls are skipped
- Mock data is returned instead
- No credits are consumed
- All functionality is preserved for testing

## Error Handling

The endpoint includes comprehensive error handling:

- **Crawl Failures**: Returns error with site_id for tracking
- **Schema Issues**: Continues execution even if Supabase schema setup fails
- **Signal Extraction**: Gracefully handles missing or malformed data
- **Network Issues**: Provides fallback responses

## Example Usage

### cURL
```bash
curl -X POST "http://localhost:8000/audit" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'
```

### Python
```python
import requests

response = requests.post(
    "http://localhost:8000/audit",
    json={"url": "https://example.com"}
)

result = response.json()
print(f"Site ID: {result['site_id']}")
print(f"Brand: {result['brand_name']}")
```

### JavaScript
```javascript
const response = await fetch('http://localhost:8000/audit', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    url: 'https://example.com'
  })
});

const result = await response.json();
console.log('Site ID:', result.site_id);
```

## Testing

The endpoint includes comprehensive testing:

1. **Unit Tests**: Test individual components (crawler, signal extractor)
2. **Integration Tests**: Test complete workflow
3. **Server Tests**: Test FastAPI endpoint functionality

Run tests:
```bash
python3 test_audit_endpoint.py
python3 test_server.py
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DEVELOPMENT_MODE` | Use mock data instead of ScrapingBee | `true` |
| `SCRAPINGBEE_API_KEY` | ScrapingBee API key | Required for production |
| `SUPABASE_URL` | Supabase project URL | Required |
| `SUPABASE_SERVICE_KEY` | Supabase service key | Required |

### ScrapingBee Configuration

The crawler is configured with:
- JavaScript rendering enabled
- Premium proxies
- 30-second timeout
- US-based proxies
- Resource blocking disabled

## Limitations

- Maximum 15 pages per audit (configurable)
- ScrapingBee API rate limits apply
- JavaScript-heavy sites may require additional processing time
- Some anti-bot measures may block crawling

## Future Enhancements

- Support for additional languages
- Enhanced competitor detection
- Real-time audit progress tracking
- Batch audit capabilities
- Advanced schema validation

## Support

For issues or questions:
1. Check the test results first
2. Verify environment variables are set
3. Check Supabase connection
4. Review ScrapingBee API limits
