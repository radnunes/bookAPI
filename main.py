from fastapi import FastAPI, HTTPException
import requests
import logging
import re

#run the server with
#uvicorn main:app  --port 8080 --reload

#example query
#http://127.0.0.1:8080/search_books?query=harry%potter

app = FastAPI()

# Base URLs for API calls
GOOGLE_BOOKS_API_URL = "https://www.googleapis.com/books/v1/volumes"
OPEN_LIBRARY_AUTHOR_API = "https://openlibrary.org/search/authors.json"
WIKIDATA_SEARCH_URL = "https://www.wikidata.org/w/api.php"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

@app.get("/search_books")
async def search_books(query: str, maxResults: int = 5):
    """Search for books by name and return detailed information about the books and authors, including ISBN."""
    try:
        # Check if the query is an ISBN
        if re.match(r'^\d{10}$|^\d{13}$', query):
            # It's an ISBN, construct the query accordingly
            google_query = f'isbn:{query}'
        else:
            google_query = query


        # Search for books on Google Books
        response = requests.get(GOOGLE_BOOKS_API_URL, params={"q": query, "maxResults": maxResults})
        response.raise_for_status()  # Raise an error for bad responses
        books = response.json().get("items", [])

        if not books:
            raise HTTPException(status_code=404, detail="No books found.")

        book_data = []
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
            author_info = await fetch_author_info(author_name)

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
                "author_info": author_info
            })

        return {"books": book_data}

    except Exception as e:
        logging.error(f"Error occurred: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def fetch_author_info(author_name: str):
    """Fetch additional author information from Open Library and Wikidata."""
    author_info = {
        "open_library": [],
        "wikidata": []
    }

    # Fetch from Open Library
    try:
        response = requests.get(OPEN_LIBRARY_AUTHOR_API, params={"q": author_name})
        response.raise_for_status()
        open_library_data = response.json()

        # Collecting all potential authors with all available fields
        for author in open_library_data.get("docs", []):
            author_info["open_library"].append(author)  # Append the entire author object
    except Exception as e:
        logging.error(f"Failed to fetch from Open Library: {e}")

    # Fetch from Wikidata
    try:
        # Search for author on Wikidata
        query_params = {
            "action": "wbsearchentities",
            "search": author_name,
            "language": "en",
            "format": "json"
        }
        response = requests.get(WIKIDATA_SEARCH_URL, params=query_params)
        response.raise_for_status()
        wikidata_data = response.json()

        # Collecting all potential authors with all available fields
        for entity in wikidata_data.get("search", []):
            author_info["wikidata"].append(entity)  # Append the entire entity object
    except Exception as e:
        logging.error(f"Failed to fetch from Wikidata: {e}")

    return author_info
