# Books API

This FastAPI application allows you to search for books (by title or ISBN) using the [Google Books API](https://developers.google.com/books) and fetch additional author information from [Open Library](https://openlibrary.org/) and [Wikidata](https://www.wikidata.org/). It provides a simple interface to retrieve book details such as title, authors, published date, and more, along with additional author information from external APIs.

## Features

- Search books by title or ISBN.
- Retrieve detailed book information, including title, author, description, publisher, ISBN, and more.
- Fetch author information from Open Library and Wikidata.
- RESTful API built with FastAPI.
- Easy to set up and run.

## Installation

1. Clone the repository:
   ```sh
   git clone https://github.com/radnunes/bookAPI.git
   cd bookAPI
   ```

2. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```

3. Run the FastAPI server using Uvicorn:
   ```sh
   uvicorn main:app --port 8080 --reload
   ```

4. Access the API by navigating to the following URL:
   ```http
   http://127.0.0.1:8080/docs
   ```

   The `/docs` endpoint provides an interactive Swagger UI to test the API endpoints.

## API Endpoints

### `GET /search_books`

Search for books by title or ISBN and return detailed information about the books and authors.

#### Parameters

- `query` (required): The search term (book title or ISBN).
- `maxResults` (optional, default: 5): The maximum number of results to return.

#### Example Request

```http
http://127.0.0.1:8080/search_books?query=harry%20potter
```

#### Example Response

```json
{
  "books": [
    {
      "title": "Harry Potter and the Sorcerer's Stone",
      "authors": ["J.K. Rowling"],
      "published_date": "1997-06-26",
      "description": "The first book in the Harry Potter series.",
      "page_count": 309,
      "categories": ["Fantasy"],
      "thumbnail": "http://example.com/thumbnail.jpg",
      "language": "en",
      "publisher": "Bloomsbury",
      "average_rating": 4.8,
      "ratings_count": 5000,
      "preview_link": "http://example.com/preview",
      "info_link": "http://example.com/info",
      "canonical_volume_link": "http://example.com/canonical",
      "isbn_10": "1234567890",
      "isbn_13": "9781234567890",
      "author_info": {
        "open_library": [...],
        "wikidata": [...]
      }
    }
  ]
}
```

### `GET /docs`

An auto-generated Swagger UI to interact with and test the API.

## Technologies Used

- **Python 3** – Main programming language.
- **FastAPI** – Web framework for building the API.
- **Requests** – HTTP library for making requests to external APIs.
- **Open Library API** – To fetch author information.
- **Wikidata API** – To fetch additional author data.
- **Uvicorn** – ASGI server to run the FastAPI application.

## Running Locally

To run the server locally, use the following command:
```sh
uvicorn main:app --port 8080 --reload
```

This will start the FastAPI server on `http://127.0.0.1:8080`. You can use the Swagger UI (`/docs`) or make direct requests to the endpoints.

## Contributing

Contributions are welcome! Feel free to fork the repository and submit a pull request with improvements or bug fixes.

## License

This project is open-source and available under the [MIT License](LICENSE).

---

This structure provides clear installation instructions, usage details, and an overview of the project’s features. Let me know if you want to adjust anything!
