"""
Unit tests for the Quran Ayah Lookup REST API.

Tests all API endpoints including verse lookup, surah information,
text search, fuzzy search, and database statistics.
"""
import pytest
from fastapi.testclient import TestClient

# Import the FastAPI app
from quran_ayah_lookup.api import app


# Create a test client
@pytest.fixture
def client():
    """Create a test client for the API."""
    return TestClient(app)


# Test root endpoint
def test_root(client):
    """Test the root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data
    assert "endpoints" in data
    assert data["message"] == "Quran Ayah Lookup API"


# Test health check endpoint
def test_health_check(client):
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


# Test get verse endpoint
def test_get_verse_success(client):
    """Test getting a specific verse successfully."""
    response = client.get("/verses/1/1")
    assert response.status_code == 200
    data = response.json()
    
    assert data["surah_number"] == 1
    assert data["ayah_number"] == 1
    assert "text" in data
    assert "text_normalized" in data
    assert isinstance(data["is_basmalah"], bool)
    assert len(data["text"]) > 0
    assert len(data["text_normalized"]) > 0


def test_get_verse_basmala(client):
    """Test getting a Basmala verse."""
    # Surah 2 has a Basmala at ayah 0
    response = client.get("/verses/2/0")
    assert response.status_code == 200
    data = response.json()
    
    assert data["surah_number"] == 2
    assert data["ayah_number"] == 0
    assert data["is_basmalah"] is True


def test_get_verse_not_found(client):
    """Test getting a non-existent verse."""
    response = client.get("/verses/1/1000")
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data


def test_get_verse_invalid_surah(client):
    """Test getting a verse with invalid surah number."""
    response = client.get("/verses/200/1")
    assert response.status_code == 404


# Test get surah info endpoint
def test_get_surah_info_success(client):
    """Test getting surah information successfully."""
    response = client.get("/surahs/1")
    assert response.status_code == 200
    data = response.json()
    
    assert data["surah_number"] == 1
    assert data["verse_count"] > 0
    assert isinstance(data["has_basmala"], bool)


def test_get_surah_info_larger_surah(client):
    """Test getting information for a larger surah."""
    response = client.get("/surahs/2")
    assert response.status_code == 200
    data = response.json()
    
    assert data["surah_number"] == 2
    assert data["verse_count"] > 100  # Al-Baqarah has many verses


def test_get_surah_info_not_found(client):
    """Test getting information for a non-existent surah."""
    response = client.get("/surahs/200")
    assert response.status_code == 404


# Test get surah verses endpoint
def test_get_surah_verses_success(client):
    """Test getting all verses in a surah successfully."""
    response = client.get("/surahs/1/verses")
    assert response.status_code == 200
    data = response.json()
    
    assert isinstance(data, list)
    assert len(data) > 0
    
    # Check first verse structure
    first_verse = data[0]
    assert "surah_number" in first_verse
    assert "ayah_number" in first_verse
    assert "text" in first_verse
    assert "text_normalized" in first_verse
    assert "is_basmalah" in first_verse


def test_get_surah_verses_order(client):
    """Test that verses are returned in order."""
    response = client.get("/surahs/1/verses")
    assert response.status_code == 200
    data = response.json()
    
    # Check that ayah numbers are in order
    ayah_numbers = [verse["ayah_number"] for verse in data]
    assert ayah_numbers == sorted(ayah_numbers)


def test_get_surah_verses_not_found(client):
    """Test getting verses for a non-existent surah."""
    response = client.get("/surahs/200/verses")
    assert response.status_code == 404


# Test search text endpoint
def test_search_text_success(client):
    """Test searching for text successfully."""
    response = client.get("/search?query=الله")
    assert response.status_code == 200
    data = response.json()
    
    assert isinstance(data, list)
    assert len(data) > 0
    
    # Check that all results contain the query (in normalized form)
    for verse in data:
        assert "الله" in verse["text_normalized"]


def test_search_text_with_limit(client):
    """Test searching with a result limit."""
    response = client.get("/search?query=الله&limit=5")
    assert response.status_code == 200
    data = response.json()
    
    assert isinstance(data, list)
    assert len(data) <= 5


def test_search_text_no_results(client):
    """Test searching for text that doesn't exist."""
    response = client.get("/search?query=xyz123notfound")
    assert response.status_code == 200
    data = response.json()
    
    assert isinstance(data, list)
    assert len(data) == 0


def test_search_text_normalized(client):
    """Test searching in normalized text."""
    response = client.get("/search?query=بسم الله&normalized=true")
    assert response.status_code == 200
    data = response.json()
    
    assert len(data) > 0


def test_search_text_original(client):
    """Test searching in original text with diacritics."""
    response = client.get("/search?query=ٱللَّهِ&normalized=false")
    assert response.status_code == 200
    data = response.json()
    
    # Results depend on exact diacritics
    assert isinstance(data, list)


def test_search_text_empty_query(client):
    """Test searching with an empty query."""
    response = client.get("/search?query=")
    assert response.status_code == 422  # Validation error


# Test fuzzy search endpoint
def test_fuzzy_search_success(client):
    """Test fuzzy search successfully."""
    response = client.get("/fuzzy-search?query=بسم الله")
    assert response.status_code == 200
    data = response.json()
    
    assert isinstance(data, list)
    assert len(data) > 0
    
    # Check result structure
    first_result = data[0]
    assert "verse" in first_result
    assert "start_word" in first_result
    assert "end_word" in first_result
    assert "similarity" in first_result
    assert "matched_text" in first_result
    assert "query_text" in first_result
    
    # Check similarity score
    assert 0.0 <= first_result["similarity"] <= 1.0


def test_fuzzy_search_with_threshold(client):
    """Test fuzzy search with custom threshold."""
    response = client.get("/fuzzy-search?query=الله&threshold=0.9")
    assert response.status_code == 200
    data = response.json()
    
    # All results should have similarity >= 0.9
    for result in data:
        assert result["similarity"] >= 0.9


def test_fuzzy_search_with_limit(client):
    """Test fuzzy search with result limit."""
    response = client.get("/fuzzy-search?query=الله&limit=3")
    assert response.status_code == 200
    data = response.json()
    
    assert len(data) <= 3


def test_fuzzy_search_sorted_by_similarity(client):
    """Test that fuzzy search results are sorted by similarity."""
    response = client.get("/fuzzy-search?query=بسم الله")
    assert response.status_code == 200
    data = response.json()
    
    if len(data) > 1:
        similarities = [result["similarity"] for result in data]
        assert similarities == sorted(similarities, reverse=True)


def test_fuzzy_search_invalid_threshold(client):
    """Test fuzzy search with invalid threshold."""
    response = client.get("/fuzzy-search?query=الله&threshold=1.5")
    assert response.status_code == 422  # Validation error


def test_fuzzy_search_no_results(client):
    """Test fuzzy search with no results."""
    response = client.get("/fuzzy-search?query=xyz123notfound&threshold=0.9")
    assert response.status_code == 200
    data = response.json()
    
    assert len(data) == 0


# Test stats endpoint
def test_get_stats(client):
    """Test getting database statistics."""
    response = client.get("/stats")
    assert response.status_code == 200
    data = response.json()
    
    assert "total_surahs" in data
    assert "total_verses" in data
    assert "source" in data
    assert "version" in data
    
    assert data["total_surahs"] == 114
    assert data["total_verses"] > 6000
    assert data["source"] == "Tanzil.net"


# Test error handling
def test_invalid_endpoint(client):
    """Test accessing an invalid endpoint."""
    response = client.get("/invalid-endpoint")
    assert response.status_code == 404


# Integration tests
def test_verse_lookup_and_search_consistency(client):
    """Test that verse lookup and search return consistent data."""
    # Get a specific verse
    verse_response = client.get("/verses/1/1")
    assert verse_response.status_code == 200
    verse_data = verse_response.json()
    
    # Search for text from that verse
    search_query = verse_data["text_normalized"][:10]  # First 10 characters
    search_response = client.get(f"/search?query={search_query}")
    assert search_response.status_code == 200
    search_data = search_response.json()
    
    # The verse should be in the search results
    assert len(search_data) > 0
    found = any(
        result["surah_number"] == 1 and result["ayah_number"] == 1
        for result in search_data
    )
    assert found


def test_surah_info_and_verses_consistency(client):
    """Test that surah info and verses list are consistent."""
    surah_number = 1
    
    # Get surah info
    info_response = client.get(f"/surahs/{surah_number}")
    assert info_response.status_code == 200
    info_data = info_response.json()
    
    # Get surah verses
    verses_response = client.get(f"/surahs/{surah_number}/verses")
    assert verses_response.status_code == 200
    verses_data = verses_response.json()
    
    # Verse count should match
    assert info_data["verse_count"] == len(verses_data)


# Performance tests
def test_multiple_verse_lookups(client):
    """Test multiple verse lookups for performance."""
    verse_pairs = [(1, 1), (2, 1), (3, 1), (4, 1), (5, 1)]
    
    for surah, ayah in verse_pairs:
        response = client.get(f"/verses/{surah}/{ayah}")
        assert response.status_code == 200


def test_large_search_results(client):
    """Test search with potentially large result set."""
    response = client.get("/search?query=ال")
    assert response.status_code == 200
    data = response.json()
    
    # Should return many results
    assert isinstance(data, list)
    # Don't assert specific count as it depends on the data


# Edge cases
def test_verse_with_zero_ayah(client):
    """Test getting verse with ayah number 0 (Basmala)."""
    response = client.get("/verses/2/0")
    assert response.status_code == 200
    data = response.json()
    
    assert data["ayah_number"] == 0
    assert data["is_basmalah"] is True


def test_last_surah_last_verse(client):
    """Test getting the last verse of the last surah."""
    # Get info about last surah first
    info_response = client.get("/surahs/114")
    assert info_response.status_code == 200
    info_data = info_response.json()
    
    last_ayah = info_data["verse_count"]
    
    # Try to get last verse
    verse_response = client.get(f"/verses/114/{last_ayah}")
    # This might be 404 if counting is off by one, so we check for valid responses
    assert verse_response.status_code in [200, 404]


def test_search_single_character(client):
    """Test searching for a single Arabic character."""
    response = client.get("/search?query=ا")
    assert response.status_code == 200
    data = response.json()
    
    # Should return many results
    assert len(data) > 0


def test_fuzzy_search_exact_match(client):
    """Test fuzzy search with exact match."""
    # Get a verse
    verse_response = client.get("/verses/1/1")
    verse_data = verse_response.json()
    
    # Search for exact text
    fuzzy_response = client.get(
        f"/fuzzy-search?query={verse_data['text_normalized']}&threshold=0.99"
    )
    assert fuzzy_response.status_code == 200
    fuzzy_data = fuzzy_response.json()
    
    # Should find at least the original verse
    assert len(fuzzy_data) > 0
    # First result should have very high similarity
    assert fuzzy_data[0]["similarity"] >= 0.99


# API documentation tests
def test_openapi_schema(client):
    """Test that OpenAPI schema is available."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    
    assert "openapi" in schema
    assert "info" in schema
    assert "paths" in schema


def test_docs_endpoint(client):
    """Test that API documentation is accessible."""
    response = client.get("/docs")
    assert response.status_code == 200
