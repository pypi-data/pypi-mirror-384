"""
Tests for fuzzy search functionality
"""
import pytest
from quran_ayah_lookup import fuzzy_search, get_quran_database
from quran_ayah_lookup.models import FuzzySearchResult
from quran_ayah_lookup.text_utils import fuzzy_substring_search, fuzzy_search_text


def test_fuzzy_substring_search_basic():
    """Test basic fuzzy substring search functionality."""
    query = "كذلك يجتبيك ربك ويعلمك"
    text = "وكذلك يجتبيك ربك ويعلمك من تأويل الأحاديث ويتم نعمته عليك"
    
    result = fuzzy_substring_search(query, text, threshold=0.7)
    
    assert result is not None
    assert result["similarity"] >= 0.7
    assert result["start_word"] >= 0
    assert result["end_word"] > result["start_word"]
    assert "matched_text" in result
    assert len(result["matched_text"]) > 0


def test_fuzzy_substring_search_no_match():
    """Test fuzzy substring search with no match above threshold."""
    query = "completely different text"
    text = "وكذلك يجتبيك ربك ويعلمك من تأويل الأحاديث"
    
    result = fuzzy_substring_search(query, text, threshold=0.9)
    
    assert result is None


def test_fuzzy_substring_search_exact_match():
    """Test fuzzy substring search with exact match."""
    query = "يجتبيك ربك ويعلمك"
    text = "وكذلك يجتبيك ربك ويعلمك من تأويل الأحاديث"
    
    result = fuzzy_substring_search(query, text, threshold=0.7)
    
    assert result is not None
    assert result["similarity"] >= 0.95  # Should be very high for exact substring


def test_fuzzy_search_partial_ayah_detection():
    """Test fuzzy search for partial ayah detection with the provided example."""
    # This is the example from the user's request
    query = "كذلك يجتبيك ربك ويعلمك من تأويل الأحاديث ويتم نعمته عليك وعلى ءال يعقوب"
    
    results = fuzzy_search(query, threshold=0.9)
    
    assert len(results) >= 1, "Should find at least one match"
    
    # Check the best result
    best_result = results[0]
    assert isinstance(best_result, FuzzySearchResult)
    assert best_result.similarity >= 0.9
    assert best_result.verse.surah_number == 12  # Should match Surah Yusuf
    assert best_result.verse.ayah_number == 6
    
    # Check that word positions are reasonable
    assert best_result.start_word >= 0
    assert best_result.end_word > best_result.start_word
    assert best_result.end_word <= 15  # Should be reasonable range


def test_fuzzy_search_repeated_phrases():
    """Test fuzzy search for repeated phrases across multiple verses."""
    # Test the repeated phrase from Surah Ar-Rahman
    query = "فبأي الاء ربكما تكذبان"
    
    results = fuzzy_search(query, threshold=0.8)
    
    assert len(results) > 20, "Should find many matches for this repeated phrase"
    
    # All results should be from Surah Ar-Rahman (55)
    surah_numbers = {result.verse.surah_number for result in results}
    assert 55 in surah_numbers, "Should find matches in Surah Ar-Rahman"
    
    # Check that all results have reasonable similarity
    for result in results:
        assert result.similarity >= 0.8
        assert isinstance(result, FuzzySearchResult)


def test_fuzzy_search_another_repeated_phrase():
    """Test fuzzy search for another repeated phrase."""
    query = "ومن اظلم ممن افترى على الله كذبا"
    
    results = fuzzy_search(query, threshold=0.8)
    
    assert len(results) >= 5, "Should find multiple matches for this phrase"
    
    # Check that all results have reasonable similarity
    for result in results:
        assert result.similarity >= 0.8
        assert isinstance(result, FuzzySearchResult)
        assert result.verse.surah_number >= 1
        assert result.verse.surah_number <= 114


def test_fuzzy_search_with_different_thresholds():
    """Test fuzzy search with different similarity thresholds."""
    query = "بسم الله الرحمن الرحيم"
    
    # High threshold should return fewer results
    high_threshold_results = fuzzy_search(query, threshold=0.95)
    
    # Lower threshold should return more results
    low_threshold_results = fuzzy_search(query, threshold=0.7)
    
    assert len(low_threshold_results) >= len(high_threshold_results)
    
    # All high threshold results should also be in low threshold results
    high_verses = {(r.verse.surah_number, r.verse.ayah_number) for r in high_threshold_results}
    low_verses = {(r.verse.surah_number, r.verse.ayah_number) for r in low_threshold_results}
    
    assert high_verses.issubset(low_verses)


def test_fuzzy_search_max_results():
    """Test fuzzy search with max_results parameter."""
    query = "الله"
    
    # Test with limit
    limited_results = fuzzy_search(query, max_results=10)
    
    assert len(limited_results) <= 10
    
    # Test without limit should return more (if available)
    unlimited_results = fuzzy_search(query, max_results=None)
    
    assert len(unlimited_results) >= len(limited_results)


def test_fuzzy_search_normalized_vs_original():
    """Test fuzzy search with normalized vs original text."""
    # Use text with diacritics
    query = "بِسْمِ ٱللَّهِ ٱلرَّحْمَـٰنِ ٱلرَّحِيمِ"
    
    # Search in normalized text (should match Basmalas)
    normalized_results = fuzzy_search(query, normalized=True, threshold=0.8)
    
    # Search in original text (might be more strict)
    original_results = fuzzy_search(query, normalized=False, threshold=0.8)
    
    # Both should find results, but normalized might find more
    assert len(normalized_results) >= 1
    assert len(original_results) >= 1


def test_fuzzy_search_empty_query():
    """Test fuzzy search with empty query."""
    results = fuzzy_search("", threshold=0.7)
    
    assert len(results) == 0


def test_fuzzy_search_result_structure():
    """Test that FuzzySearchResult objects have correct structure."""
    query = "الحمد لله"
    results = fuzzy_search(query, threshold=0.7, max_results=5)
    
    for result in results:
        assert isinstance(result, FuzzySearchResult)
        
        # Check all required attributes exist
        assert hasattr(result, 'verse')
        assert hasattr(result, 'start_word')
        assert hasattr(result, 'end_word')
        assert hasattr(result, 'similarity')
        assert hasattr(result, 'matched_text')
        assert hasattr(result, 'query_text')
        
        # Check data types and ranges
        assert isinstance(result.start_word, int)
        assert isinstance(result.end_word, int)
        assert isinstance(result.similarity, float)
        assert 0.0 <= result.similarity <= 1.0
        assert result.start_word >= 0
        assert result.end_word > result.start_word
        assert len(result.matched_text) > 0
        assert len(result.query_text) > 0


def test_fuzzy_search_sorting():
    """Test that fuzzy search results are sorted by similarity."""
    query = "الرحمن الرحيم"
    results = fuzzy_search(query, threshold=0.6, max_results=20)
    
    if len(results) > 1:
        # Results should be sorted by similarity (descending)
        similarities = [result.similarity for result in results]
        assert similarities == sorted(similarities, reverse=True)


def test_fuzzy_search_database_integration():
    """Test that fuzzy search integrates properly with database."""
    db = get_quran_database()
    
    # Test database method directly
    query = "الصلاة"
    db_results = db.fuzzy_search(query, threshold=0.7, max_results=5)
    
    # Test convenience function
    api_results = fuzzy_search(query, threshold=0.7, max_results=5)
    
    # Should return same results
    assert len(db_results) == len(api_results)
    
    for db_result, api_result in zip(db_results, api_results):
        assert db_result.verse.surah_number == api_result.verse.surah_number
        assert db_result.verse.ayah_number == api_result.verse.ayah_number
        assert db_result.similarity == api_result.similarity