import requests

from fastapi.testclient import TestClient

import main


client = TestClient(main.app)


class FakeResponse:
    def __init__(self, payload, status_code=200):
        self.payload = payload
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"status={self.status_code}")

    def json(self):
        return self.payload


def fake_get(url, *, params, timeout):
    assert timeout == main.REQUEST_TIMEOUT

    if url == main.GOOGLE_BOOKS_API_URL:
        return FakeResponse({
            "items": [{
                "volumeInfo": {
                    "title": "The Great Gatsby",
                    "authors": ["F. Scott Fitzgerald"],
                    "industryIdentifiers": [
                        {"type": "ISBN_10", "identifier": "0743273567"}
                    ]
                }
            }]
        })
    if url == main.OPEN_LIBRARY_AUTHOR_API:
        return FakeResponse({"docs": [{"name": "F. Scott Fitzgerald"}]})
    return FakeResponse({"search": [{"id": "Q9334", "label": "F. Scott Fitzgerald"}]})


def test_search_books(monkeypatch):
    monkeypatch.setattr(main.requests, "get", fake_get)

    response = client.get("/search_books", params={"query": "The Great Gatsby"})

    assert response.status_code == 200
    book = response.json()["books"][0]
    assert book["title"] == "The Great Gatsby"
    assert book["authors"] == ["F. Scott Fitzgerald"]
    assert "author_info" in book


def test_isbn_search_uses_isbn_query(monkeypatch):
    google_params = {}

    def fake_isbn_get(url, *, params, timeout):
        if url == main.GOOGLE_BOOKS_API_URL:
            google_params.update(params)
            return FakeResponse({"items": []})
        return FakeResponse({})

    monkeypatch.setattr(main.requests, "get", fake_isbn_get)

    response = client.get("/search_books", params={"query": "0743273567"})

    assert response.status_code == 404
    assert google_params["q"] == "isbn:0743273567"


def test_search_books_no_results(monkeypatch):
    def fake_empty_get(url, *, params, timeout):
        return FakeResponse({"items": []})

    monkeypatch.setattr(main.requests, "get", fake_empty_get)

    response = client.get("/search_books", params={"query": "No matching book"})

    assert response.status_code == 404
    assert response.json()["detail"] == "No books found."


def test_max_results_is_bounded():
    response = client.get("/search_books", params={"query": "books", "maxResults": 41})

    assert response.status_code == 422


def test_google_books_rate_limit_returns_service_unavailable(monkeypatch):
    def fake_rate_limited_get(url, *, params, timeout):
        response = requests.Response()
        response.status_code = 429
        response.url = url
        raise requests.HTTPError(response=response)

    monkeypatch.setattr(main.requests, "get", fake_rate_limited_get)

    response = client.get("/search_books", params={"query": "Maps of Meaning"})

    assert response.status_code == 503
    assert "rate limit" in response.json()["detail"]
