"""Tests for health check endpoints."""


def test_root_health_endpoint(client):
    """Test the root health endpoint returns healthy status."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "book-translator"


def test_api_health_endpoint(client):
    """Test the API health endpoint."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


def test_home_page_loads(client):
    """Test that the home page renders successfully."""
    response = client.get("/")
    assert response.status_code == 200
    assert "Book Translator" in response.text
    assert "Upload Document" in response.text
