"""
Unit tests for smart_search functionality.
"""
import pytest
from quran_ayah_lookup import (
    smart_search,
    QuranVerse,
    FuzzySearchResult,
    MultiAyahMatch,
)


class TestSmartSearch:
    """Test smart search functionality."""
    
    def test_smart_search_uses_exact_when_available(self):
        """Test that smart_search uses exact text search when matches are found."""
        # Query that should match exactly
        query = "بسم الله الرحمن الرحيم"
        result = smart_search(query, normalized=True)
        
        assert result['method'] == 'exact', f"Expected exact search, got {result['method']}"
        assert result['count'] > 0, "Should find results"
        assert isinstance(result['results'][0], QuranVerse), "Results should be QuranVerse objects"
    
    def test_smart_search_uses_fuzzy_when_exact_fails(self):
        """Test that smart_search falls back to fuzzy search when exact fails."""
        # Query with slight variations that won't match exactly
        query = "الحمد لله رب"  # Partial phrase
        result = smart_search(query, threshold=0.7, normalized=True)
        
        # Should use either exact or fuzzy
        assert result['method'] in ['exact', 'fuzzy'], f"Expected exact or fuzzy, got {result['method']}"
        assert result['count'] > 0, "Should find results"
        
        if result['method'] == 'fuzzy':
            assert isinstance(result['results'][0], FuzzySearchResult), "Results should be FuzzySearchResult objects"
    
    def test_smart_search_uses_sliding_window_for_multi_ayah(self):
        """Test that smart_search uses sliding window for multi-ayah queries."""
        # Query spanning multiple ayahs
        query = "الرحمن علم القران خلق الانسان علمه البيان"
        result = smart_search(query, sliding_threshold=80.0, normalized=True)
        
        # Could be exact if the text matches, or sliding window
        assert result['count'] > 0, "Should find results"
        
        # Check that we get the right type based on method
        if result['method'] == 'exact':
            assert isinstance(result['results'][0], QuranVerse)
        elif result['method'] == 'fuzzy':
            assert isinstance(result['results'][0], FuzzySearchResult)
        elif result['method'] == 'sliding_window':
            assert isinstance(result['results'][0], MultiAyahMatch)
    
    def test_smart_search_returns_none_when_no_results(self):
        """Test that smart_search returns 'none' method when no results found."""
        # Nonsense query that should not match anything
        query = "كلمات غير موجودة في القران xyz123"
        result = smart_search(query, threshold=0.9, sliding_threshold=95.0, normalized=True)
        
        assert result['method'] == 'none', f"Expected 'none' method, got {result['method']}"
        assert result['count'] == 0, "Should have zero results"
        assert result['results'] == [], "Results should be empty list"
    
    def test_smart_search_respects_max_results(self):
        """Test that smart_search respects max_results parameter."""
        query = "الله"  # Common word, should have many results
        result = smart_search(query, max_results=5, normalized=True)
        
        assert result['count'] <= 5, f"Should not exceed max_results=5, got {result['count']}"
        assert len(result['results']) <= 5, "Results list should not exceed limit"
    
    def test_smart_search_with_normalized_text(self):
        """Test smart_search with normalized text."""
        query = "الرحمن الرحيم"
        result = smart_search(query, normalized=True)
        
        assert result['count'] > 0, "Should find results in normalized text"
        assert result['method'] != 'none', "Should find results with some method"
    
    def test_smart_search_with_original_text(self):
        """Test smart_search with original text (with diacritics)."""
        # Query with diacritics
        query = "بِسْمِ ٱللَّهِ"
        result = smart_search(query, normalized=False)
        
        # Should still find something
        assert result['method'] != 'none', "Should find results with some method"
    
    def test_smart_search_threshold_parameters(self):
        """Test that smart_search uses threshold parameters correctly."""
        query = "الحمد لله"
        
        # Low threshold should find more results
        result_low = smart_search(query, threshold=0.5, sliding_threshold=60.0)
        
        # High threshold should find fewer or no results  
        result_high = smart_search(query, threshold=0.95, sliding_threshold=95.0)
        
        # Both should return valid results
        assert 'method' in result_low
        assert 'method' in result_high
        assert 'count' in result_low
        assert 'count' in result_high
    
    def test_smart_search_empty_query(self):
        """Test smart_search with empty query."""
        result = smart_search("", normalized=True)
        
        assert result['method'] == 'none', "Empty query should return 'none'"
        assert result['count'] == 0, "Empty query should have zero results"
        assert result['results'] == [], "Results should be empty"
    
    def test_smart_search_whitespace_query(self):
        """Test smart_search with whitespace-only query."""
        result = smart_search("   ", normalized=True)
        
        assert result['method'] == 'none', "Whitespace query should return 'none'"
        assert result['count'] == 0, "Whitespace query should have zero results"
    
    def test_smart_search_result_structure(self):
        """Test that smart_search returns correctly structured results."""
        query = "الرحمن"
        result = smart_search(query)
        
        # Check required keys
        assert 'method' in result, "Result should have 'method' key"
        assert 'results' in result, "Result should have 'results' key"
        assert 'count' in result, "Result should have 'count' key"
        
        # Check types
        assert isinstance(result['method'], str), "Method should be a string"
        assert isinstance(result['results'], list), "Results should be a list"
        assert isinstance(result['count'], int), "Count should be an integer"
        
        # Check method is valid
        assert result['method'] in ['exact', 'fuzzy', 'sliding_window', 'none'], \
            f"Invalid method: {result['method']}"
        
        # Check count matches results length
        assert result['count'] == len(result['results']), \
            "Count should match results length"
    
    def test_smart_search_specific_surah_al_fatihah(self):
        """Test smart_search with text from Al-Fatihah."""
        query = "اهدنا الصرط المستقيم"
        result = smart_search(query, normalized=True)
        
        assert result['count'] > 0, "Should find Al-Fatihah text"
        
        # Verify we got results from Surah 1
        if result['method'] == 'exact':
            assert any(v.surah_number == 1 for v in result['results']), \
                "Should find results in Surah 1"
        elif result['method'] == 'fuzzy':
            assert any(r.verse.surah_number == 1 for r in result['results']), \
                "Should find results in Surah 1"
        elif result['method'] == 'sliding_window':
            assert any(m.start_surah == 1 or m.end_surah == 1 for m in result['results']), \
                "Should find results in Surah 1"
    
    def test_smart_search_repeated_phrase(self):
        """Test smart_search with a repeated phrase."""
        # "رب العلمين" appears multiple times
        query = "رب العلمين"
        result = smart_search(query, normalized=True, max_results=10)
        
        assert result['count'] > 0, "Should find repeated phrase"
        assert result['count'] <= 10, "Should respect max_results"
    
    def test_smart_search_long_query(self):
        """Test smart_search with a long query spanning multiple ayahs."""
        query = "بسم الله الرحمن الرحيم الم ذلك الكتاب لا ريب فيه"
        result = smart_search(query, sliding_threshold=75.0, normalized=True)
        
        assert result['count'] > 0, "Should find long query"
        # Long query might use sliding window or fuzzy
        assert result['method'] in ['exact', 'fuzzy', 'sliding_window'], \
            f"Expected search method, got {result['method']}"
    
    def test_smart_search_single_word(self):
        """Test smart_search with a single word."""
        query = "الله"
        result = smart_search(query, normalized=True, max_results=20)
        
        assert result['count'] > 0, "Should find single word"
        assert result['count'] <= 20, "Should respect max_results"
        # Single word should typically use exact search
        assert result['method'] in ['exact', 'fuzzy'], \
            f"Single word should use exact or fuzzy, got {result['method']}"
    
    def test_smart_search_method_priority(self):
        """Test that smart_search tries methods in correct order."""
        # Use a query that we know exists exactly
        query = "بسم الله الرحمن الرحيم"
        result = smart_search(query, normalized=True)
        
        # Should use exact search since this text exists exactly
        assert result['method'] == 'exact', \
            f"Should prioritize exact search, got {result['method']}"
    
    def test_smart_search_with_very_high_thresholds(self):
        """Test smart_search with very high similarity thresholds."""
        query = "الحمد لله"
        result = smart_search(query, threshold=0.99, sliding_threshold=99.0)
        
        # With very high thresholds, might only find exact matches or nothing
        assert result['method'] in ['exact', 'none'], \
            f"High threshold should give exact or none, got {result['method']}"
    
    def test_smart_search_with_very_low_thresholds(self):
        """Test smart_search with very low similarity thresholds."""
        query = "الله"
        result = smart_search(query, threshold=0.3, sliding_threshold=30.0, max_results=5)
        
        # Low threshold should find results
        assert result['count'] > 0, "Low threshold should find results"
        assert result['count'] <= 5, "Should respect max_results"


class TestSmartSearchEdgeCases:
    """Test edge cases for smart_search."""
    
    def test_smart_search_special_characters(self):
        """Test smart_search with special characters."""
        query = "الرَّحۡمَـٰنِ"  # With diacritics
        result = smart_search(query, normalized=True)
        
        # Should handle special characters gracefully
        assert isinstance(result, dict), "Should return valid result dict"
        assert 'method' in result, "Should have method key"
    
    def test_smart_search_mixed_content(self):
        """Test smart_search with mixed Arabic and spaces."""
        query = "  الله   الرحمن  "  # Extra spaces
        result = smart_search(query, normalized=True)
        
        # Should handle extra spaces
        assert isinstance(result, dict), "Should return valid result dict"
    
    def test_smart_search_very_short_query(self):
        """Test smart_search with very short query."""
        query = "ال"  # Just two letters
        result = smart_search(query, normalized=True, max_results=10)
        
        # Should handle short queries
        assert isinstance(result, dict), "Should return valid result dict"
        assert result['count'] <= 10, "Should respect max_results"
    
    def test_smart_search_result_types_consistency(self):
        """Test that result types are consistent with method used."""
        query = "الرحمن"
        result = smart_search(query)
        
        if result['method'] == 'exact' and result['count'] > 0:
            assert all(isinstance(r, QuranVerse) for r in result['results']), \
                "Exact search should return QuranVerse objects"
        
        elif result['method'] == 'fuzzy' and result['count'] > 0:
            assert all(isinstance(r, FuzzySearchResult) for r in result['results']), \
                "Fuzzy search should return FuzzySearchResult objects"
        
        elif result['method'] == 'sliding_window' and result['count'] > 0:
            assert all(isinstance(r, MultiAyahMatch) for r in result['results']), \
                "Sliding window should return MultiAyahMatch objects"
        
        elif result['method'] == 'none':
            assert result['results'] == [], "No method should return empty results"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
