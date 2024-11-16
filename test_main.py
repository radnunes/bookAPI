from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_search_books():
    query = "The Great Gatsby"
    response = client.get("/search", params={"query": query})
    assert response.status_code == 200  # Check if the request was successful
    data = response.json()
    assert "books" in data  # Verify that 'books' key is in the response
    assert len(data["books"]) > 0  # Ensure that at least one book is returned

    # Optionally, you can print the data for debugging
    print(data)

    # Check the structure of the first book
    book = data["books"][0]
    assert "title" in book
    assert "authors" in book
    assert "authors_info" in book

def test_search_books_no_results():
    query = "SomeRandomStringThatMatchesNoBooks"
    response = client.get("/search", params={"query": query})
    assert response.status_code == 200
    data = response.json()
    assert "books" in data
    assert len(data["books"]) == 0  # Expecting zero books
