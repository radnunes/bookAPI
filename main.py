import asyncio
import logging
import os
import re

import requests

from fastapi import FastAPI, HTTPException, Query

#run the server with
#uvicorn main:app  --port 8080 --reload

#example query
#http://127.0.0.1:8080/search_books?query=harry%potter

app = FastAPI()

# Base URLs for API calls
GOOGLE_BOOKS_API_URL = "https://www.googleapis.com/books/v1/volumes"
OPEN_LIBRARY_AUTHOR_API = "https://openlibrary.org/search/authors.json"
WIKIDATA_SEARCH_URL = "https://www.wikidata.org/w/api.php"
REQUEST_TIMEOUT = 10
AUTHOR_LOOKUP_CONCURRENCY = 5
GOOGLE_BOOKS_API_KEY = os.getenv("GOOGLE_BOOKS_API_KEY")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

@app.get("/search_books")
async def search_books(query: str = Query(..., min_length=1), maxResults: int = Query(5, ge=1, le=40)):
    """Search for books by name and return detailed information about the books and authors, including ISBN."""
    try:
        query = query.strip()
        if not query:
            raise HTTPException(status_code=422, detail="Query must not be blank.")

        # Check if the query is an ISBN
        if re.match(r'^\d{10}$|^\d{13}$', query):
            # It's an ISBN, construct the query accordingly
            google_query = f'isbn:{query}'
        else:
            google_query = query


        google_params = {"q": google_query, "maxResults": maxResults}
        if GOOGLE_BOOKS_API_KEY:
            google_params["key"] = GOOGLE_BOOKS_API_KEY

        # Search for books on Google Books
        books = (await request_json(
            GOOGLE_BOOKS_API_URL,
            params=google_params
        )).get("items", [])

        if not books:
            raise HTTPException(status_code=404, detail="No books found.")

        book_data = []
        author_names = []
        for book in books:
            volume_info = book.get("volumeInfo", {})
            title = volume_info.get("title", "Unknown Title")
            authors = volume_info.get("authors", ["Unknown Author"])
            published_date = volume_info.get("publishedDate", "Unknown Date")
            description = volume_info.get("description", "No description available.")
            page_count = volume_info.get("pageCount", 0)
            categories = volume_info.get("categories", [])
            thumbnail = volume_info.get("imageLinks", {}).get("thumbnail", "")
            language = volume_info.get("language", "Unknown")
            publisher = volume_info.get("publisher", "Unknown Publisher")
            average_rating = volume_info.get("averageRating", "No rating")
            ratings_count = volume_info.get("ratingsCount", 0)
            preview_link = volume_info.get("previewLink", "")
            info_link = volume_info.get("infoLink", "")
            canonical_volume_link = volume_info.get("canonicalVolumeLink", "")

            # Extract ISBNs if available
            isbn_10, isbn_13 = None, None
            for identifier in volume_info.get("industryIdentifiers", []):
                if identifier.get("type") == "ISBN_10":
                    isbn_10 = identifier.get("identifier")
                elif identifier.get("type") == "ISBN_13":
                    isbn_13 = identifier.get("identifier")

            # Assuming the first author is the primary one
            author_name = authors[0] if authors else "Unknown Author"
            author_names.append(author_name)

            book_data.append({
                "title": title,
                "authors": authors,
                "published_date": published_date,
                "description": description,
                "page_count": page_count,
                "categories": categories,
                "thumbnail": thumbnail,
                "language": language,
                "publisher": publisher,
                "average_rating": average_rating,
                "ratings_count": ratings_count,
                "preview_link": preview_link,
                "info_link": info_link,
                "canonical_volume_link": canonical_volume_link,
                "isbn_10": isbn_10,
                "isbn_13": isbn_13,
                "author_info": None
            })

        author_semaphore = asyncio.Semaphore(AUTHOR_LOOKUP_CONCURRENCY)
        author_info = await asyncio.gather(*(
            fetch_author_info_limited(author_name, author_semaphore)
            for author_name in author_names
        ))
        for book, info in zip(book_data, author_info):
            book["author_info"] = info

        return {"books": book_data}

    except HTTPException:
        raise
    except requests.HTTPError as error:
        if error.response is not None and error.response.status_code == 429:
            logging.warning("Google Books rate limit or quota exceeded")
            raise HTTPException(
                status_code=503,
                detail="Google Books rate limit reached. Try again later or configure GOOGLE_BOOKS_API_KEY."
            )
        logging.exception("Google Books returned an HTTP error")
        raise HTTPException(status_code=502, detail="Book search provider returned an error.")
    except requests.RequestException:
        logging.exception("Google Books request failed")
        raise HTTPException(status_code=502, detail="Book search provider is unavailable.")
    except Exception:
        logging.exception("Error processing book search")
        raise HTTPException(status_code=500, detail="Unable to process book search.")


async def request_json(url: str, params: dict):
    response = await asyncio.to_thread(
        requests.get,
        url,
        params=params,
        timeout=REQUEST_TIMEOUT
    )
    response.raise_for_status()
    return response.json()


async def fetch_author_info_limited(author_name: str, semaphore: asyncio.Semaphore):
    async with semaphore:
        return await fetch_author_info(author_name)


async def fetch_author_info(author_name: str):
    """Fetch additional author information from Open Library and Wikidata."""
    author_info = {
        "open_library": [],
        "wikidata": []
    }

    try:
        open_library_data = await request_json(
            OPEN_LIBRARY_AUTHOR_API,
            params={"q": author_name}
        )

        for author in open_library_data.get("docs", []):
            author_info["open_library"].append(author)
    except Exception as e:
        logging.error(f"Failed to fetch from Open Library: {e}")

    try:
        query_params = {
            "action": "wbsearchentities",
            "search": author_name,
            "language": "en",
            "format": "json"
        }
        wikidata_data = await request_json(WIKIDATA_SEARCH_URL, params=query_params)

        for entity in wikidata_data.get("search", []):
            author_info["wikidata"].append(entity)
    except Exception as e:
        logging.error(f"Failed to fetch from Wikidata: {e}")

    return author_info
