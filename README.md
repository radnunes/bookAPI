# Books API

A small FastAPI service for searching books by title or ISBN. Google Books provides the book results, while Open Library and Wikidata provide additional author information when available.

## How It Works

For each request:

1. The service searches Google Books.
2. It extracts book details and ISBN identifiers from the returned volumes.
3. It searches Open Library and Wikidata using the first listed author.
4. It returns the book data and best-effort author enrichment in one response.

Author-provider failures do not discard an otherwise valid book result. The current implementation is intentionally a lightweight prototype: provider responses are returned with minimal transformation, and author lookups run concurrently with a limit of five in-flight author lookups per request.

## Design Decisions and Lessons Learned

This project involved a few practical tradeoffs:

- **Use separate providers for separate strengths.** Google Books is the source for book results, while Open Library and Wikidata add author context. This keeps the main search focused and lets author enrichment remain optional.
- **Prefer partial results over total failure.** Author providers can be unavailable or incomplete, so their failures are logged and the book result is still returned. This makes the API more useful when external services are unreliable.
- **Add concurrency with a limit.** Author lookups originally ran one at a time, which made responses slower as more books were requested. Bounded concurrency improves latency while avoiding an uncontrolled burst of requests to public APIs.
- **Keep the response shape stable.** The service returns a consistent set of fields with fallback values when providers omit data. That makes the API easier for clients to consume even when upstream responses vary.
- **Test provider behavior without network calls.** Mocked responses make validation fast and deterministic, while also making it possible to test rate limits, empty results, input validation, and the concurrency limit.

The main lessons were that asynchronous code does not automatically make external I/O scalable, public APIs need explicit failure handling and rate-limit awareness, and a small concurrency limit can be a useful improvement without introducing a full caching or job-processing system.

## Requirements

- Python 3.10 or newer
- Internet access for Google Books, Open Library, and Wikidata requests

Dependencies are listed in `requirements.txt`.

Google Books allows public requests, but its quota can be exhausted. To use a Google Books API key, set it before starting the server:

```sh
export GOOGLE_BOOKS_API_KEY="your-api-key"
```

## Setup

Create and activate a virtual environment:

```sh
python -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```sh
python -m pip install -r requirements.txt
```

Start the development server:

```sh
uvicorn main:app --host 127.0.0.1 --port 8080 --reload
```

The interactive API documentation is available at:

```text
http://127.0.0.1:8080/docs
```

## API

### `GET /search_books`

Search for books by title, free-text query, or ISBN.

#### Query parameters

| Parameter | Required | Default | Description |
| --- | --- | --- | --- |
| `query` | Yes | None | A book title, search phrase, or 10/13-digit ISBN. |
| `maxResults` | No | `5` | Number of Google Books results to request. Must be between `1` and `40`. |

Examples:

```sh
curl "http://127.0.0.1:8080/search_books?query=harry%20potter"
```

```sh
curl "http://127.0.0.1:8080/search_books?query=0743273567"
```

For a 10- or 13-digit query, the service sends an ISBN-specific query to Google Books.

#### Response shape

```json
{
  "books": [
    {
      "title": "The Great Gatsby",
      "authors": ["F. Scott Fitzgerald"],
      "published_date": "1925-04-10",
      "description": "Book description",
      "page_count": 180,
      "categories": ["Fiction"],
      "thumbnail": "https://books.google.com/thumbnail-url",
      "language": "en",
      "publisher": "Publisher name",
      "average_rating": 4.0,
      "ratings_count": 100,
      "preview_link": "https://books.google.com/preview-link",
      "info_link": "https://books.google.com/info-link",
      "canonical_volume_link": "https://books.google.com/canonical-link",
      "isbn_10": "0743273567",
      "isbn_13": "9780743273565",
      "author_info": {
        "open_library": [],
        "wikidata": []
      }
    }
  ]
}
```

Some fields use fallback values or `null` when the upstream provider does not supply them.

#### Status codes

- `200`: Results returned.
- `404`: No books matched the query.
- `422`: Missing, blank, or invalid query parameters.
- `502`: Google Books is unavailable or returned an upstream HTTP error.
- `503`: Google Books rate limit or quota was reached. Configure `GOOGLE_BOOKS_API_KEY` or try again later.
- `500`: Unexpected processing error.

## Testing

Tests use mocked provider responses, so they do not require network access or external API credentials.

```sh
.venv/bin/pytest -q
```

## Project Files

- `main.py`: FastAPI application and provider integration.
- `test_main.py`: API contract and validation tests.
- `requirements.txt`: Runtime and test dependencies.
- `.gitignore`: Local environment and generated-file exclusions.

## External APIs

- [Google Books API](https://developers.google.com/books)
- [Open Library API](https://openlibrary.org/developers/api)
- [Wikidata API](https://www.wikidata.org/w/api.php)
