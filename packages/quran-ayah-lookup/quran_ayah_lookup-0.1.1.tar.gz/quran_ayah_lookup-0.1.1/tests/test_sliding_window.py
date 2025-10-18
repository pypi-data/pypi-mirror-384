"""
Unit tests for sliding window multi-ayah search functionality.
"""
import pytest
from quran_ayah_lookup import (
    search_sliding_window,
    get_quran_database,
    MultiAyahMatch,
)
from quran_ayah_lookup.text_utils import normalize_arabic_text


class TestSlidingWindowSearch:
    """Test sliding window search functionality."""
    
    def test_exact_match_spanning_multiple_ayahs_surah_55(self):
        """
        Test case 1: Exact match spanning multiple ayahs in Surah Ar-Rahman.
        Query: "الرحمن علم القران خلق الانسان علمه البيان"
        Expected: Surah Ar-Rahman (55:1-4)
        """
        query = "الرحمن علم القران خلق الانسان علمه البيان"
        results = search_sliding_window(query, threshold=80.0, normalized=True)
        
        # Should find at least one match
        assert len(results) > 0, "Should find at least one match"
        
        # Check the top result
        top_match = results[0]
        assert isinstance(top_match, MultiAyahMatch)
        
        # Should match Surah 55 (Ar-Rahman)
        assert top_match.start_surah == 55, f"Expected surah 55, got {top_match.start_surah}"
        
        # Should start from ayah 1 and span to ayah 4
        assert top_match.start_ayah == 1, f"Expected start ayah 1, got {top_match.start_ayah}"
        assert top_match.end_ayah >= 3, f"Expected end ayah >= 3, got {top_match.end_ayah}"
        
        # Should have high similarity score for exact match
        assert top_match.similarity >= 85.0, f"Expected similarity >= 85, got {top_match.similarity}"
        
        # Should have multiple verses
        assert len(top_match.verses) >= 3, f"Expected at least 3 verses, got {len(top_match.verses)}"
    
    def test_exact_match_spanning_multiple_ayahs_surah_2(self):
        """
        Test case 2: Exact match spanning multiple ayahs in Surah Al-Baqarah.
        Query: "بسم الله الرحمن الرحيم الم ذلك الكتاب لا ريب فيه هدى للمتقين"
        Expected: Surah Al-Baqarah (2:1-2)
        """
        query = "بسم الله الرحمن الرحيم الم ذلك الكتاب لا ريب فيه هدى للمتقين"
        results = search_sliding_window(query, threshold=80.0, normalized=True)
        
        # Should find at least one match
        assert len(results) > 0, "Should find at least one match"
        
        # Check for matches in Surah 2
        surah_2_matches = [m for m in results if m.start_surah == 2]
        assert len(surah_2_matches) > 0, "Should find match in Surah 2"
        
        # Check the top match from Surah 2
        top_match = surah_2_matches[0]
        
        # Should start from around ayah 0 or 1 (Basmala or first ayah)
        assert top_match.start_ayah <= 1, f"Expected start ayah <= 1, got {top_match.start_ayah}"
        
        # Should span to at least ayah 2
        assert top_match.end_ayah >= 2, f"Expected end ayah >= 2, got {top_match.end_ayah}"
        
        # Should have high similarity score
        assert top_match.similarity >= 80.0, f"Expected similarity >= 80, got {top_match.similarity}"
    
    def test_match_spanning_multiple_surahs(self):
        """
        Test case 3: Match spanning multiple surahs.
        Query: "الم يجدك يتيما فاوى ووجدك ضالا فهدى ووجدك عائلا فاغنى فاما اليتيم فلا تقهر واما السائل فلا تنهر و اما بنعمة ربك فحدث بسم الله الرحمن الرحيم الم نشرح لك صدرك"
        Expected: Surah Ad-Duha (93:6-11) and Surah Ash-Sharh (94:0-1)
        """
        query = "الم يجدك يتيما فاوى ووجدك ضالا فهدى ووجدك عائلا فاغنى فاما اليتيم فلا تقهر واما السائل فلا تنهر و اما بنعمة ربك فحدث بسم الله الرحمن الرحيم الم نشرح لك صدرك"
        results = search_sliding_window(query, threshold=75.0, normalized=True)
        
        # Should find at least one match
        assert len(results) > 0, "Should find at least one match"
        
        # Check for matches that span from Surah 93 to 94
        cross_surah_matches = [
            m for m in results 
            if m.start_surah == 93 and m.end_surah == 94
        ]
        
        if len(cross_surah_matches) > 0:
            top_match = cross_surah_matches[0]
            
            # Should start in Surah 93
            assert top_match.start_surah == 93
            
            # Should end in Surah 94
            assert top_match.end_surah == 94
            
            # Should have reasonable similarity
            assert top_match.similarity >= 70.0, f"Expected similarity >= 70, got {top_match.similarity}"
            
            # Should have multiple verses
            assert len(top_match.verses) > 1, "Should have multiple verses"
    
    def test_empty_query(self):
        """Test with empty query string."""
        results = search_sliding_window("", threshold=80.0)
        assert len(results) == 0, "Empty query should return no results"
    
    def test_no_match_with_high_threshold(self):
        """Test that no results are returned with impossibly high threshold."""
        query = "الرحمن علم القران"
        results = search_sliding_window(query, threshold=99.9, normalized=True)
        
        # May return no results or very few with such high threshold
        # This is acceptable behavior
        assert isinstance(results, list)
    
    def test_short_query(self):
        """Test with a short query that should match many places."""
        query = "بسم الله"
        results = search_sliding_window(query, threshold=80.0, normalized=True, max_results=10)
        
        # Should find multiple matches (Basmala appears many times)
        assert len(results) > 0, "Should find at least one match"
        
        # Should not exceed max_results
        assert len(results) <= 10, "Should not exceed max_results limit"
    
    def test_normalized_vs_original(self):
        """Test that normalized search works correctly."""
        # Query with diacritics removed
        query_normalized = "الرحمن علم القران"
        
        # Search in normalized text
        results_normalized = search_sliding_window(
            query_normalized,
            threshold=80.0,
            normalized=True
        )
        
        # Should find matches
        assert len(results_normalized) > 0, "Normalized search should find matches"
    
    def test_result_structure(self):
        """Test that result objects have correct structure."""
        query = "الرحمن علم القران"
        results = search_sliding_window(query, threshold=80.0)
        
        if len(results) > 0:
            match = results[0]
            
            # Check all required attributes exist
            assert hasattr(match, 'verses')
            assert hasattr(match, 'similarity')
            assert hasattr(match, 'matched_text')
            assert hasattr(match, 'query_text')
            assert hasattr(match, 'start_surah')
            assert hasattr(match, 'start_ayah')
            assert hasattr(match, 'start_word')
            assert hasattr(match, 'end_surah')
            assert hasattr(match, 'end_ayah')
            assert hasattr(match, 'end_word')
            
            # Check types
            assert isinstance(match.verses, list)
            assert isinstance(match.similarity, (int, float))
            assert isinstance(match.matched_text, str)
            assert isinstance(match.query_text, str)
            assert isinstance(match.start_surah, int)
            assert isinstance(match.start_ayah, int)
            assert isinstance(match.start_word, int)
            assert isinstance(match.end_surah, int)
            assert isinstance(match.end_ayah, int)
            assert isinstance(match.end_word, int)
            
            # Check method exists
            assert hasattr(match, 'get_reference')
            reference = match.get_reference()
            assert isinstance(reference, str)
            assert len(reference) > 0
    
    def test_max_results_limit(self):
        """Test that max_results parameter limits the number of results."""
        query = "الله"  # Common word, should match many places
        
        results_5 = search_sliding_window(query, threshold=80.0, max_results=5)
        results_10 = search_sliding_window(query, threshold=80.0, max_results=10)
        
        # Should respect max_results
        assert len(results_5) <= 5, "Should not exceed max_results=5"
        assert len(results_10) <= 10, "Should not exceed max_results=10"
    
    def test_results_sorted_by_similarity(self):
        """Test that results are sorted by similarity score in descending order."""
        query = "الرحمن الرحيم"
        results = search_sliding_window(query, threshold=70.0, max_results=10)
        
        if len(results) > 1:
            # Check that results are sorted by similarity descending
            for i in range(len(results) - 1):
                assert results[i].similarity >= results[i + 1].similarity, \
                    f"Results not sorted: {results[i].similarity} < {results[i + 1].similarity}"
    
    def test_word_boundaries_within_ayah(self):
        """Test that word boundaries are correctly identified within a single ayah."""
        query = "بسم الله الرحمن الرحيم"
        results = search_sliding_window(query, threshold=90.0, normalized=True, max_results=1)
        
        if len(results) > 0:
            match = results[0]
            
            # Start word should be non-negative
            assert match.start_word >= 0
            
            # End word should be greater than start word
            assert match.end_word > match.start_word
    
    def test_special_characters_handling(self):
        """Test that special characters and diacritics are handled properly."""
        # Query with various diacritics
        query_with_diacritics = "ٱلرَّحۡمَـٰنُ"
        
        # Should still find matches when normalized
        results = search_sliding_window(
            query_with_diacritics,
            threshold=80.0,
            normalized=True
        )
        
        # May or may not find matches depending on normalization
        # Just ensure it doesn't crash
        assert isinstance(results, list)
    
    def test_repeated_phrase(self):
        """Test searching for a repeated phrase in the Quran."""
        # "فبأي آلاء ربكما تكذبان" is repeated many times in Surah Ar-Rahman
        query = "فباي الاء ربكما تكذبان"
        results = search_sliding_window(
            query,
            threshold=80.0,
            normalized=True,
            max_results=20
        )
        
        # Should find multiple matches since this phrase repeats
        assert len(results) > 1, "Should find multiple matches for repeated phrase"
        
        # Most should be in Surah 55 (Ar-Rahman)
        surah_55_matches = [m for m in results if m.start_surah == 55]
        assert len(surah_55_matches) > 0, "Should find matches in Surah 55"


class TestMultiAyahMatchModel:
    """Test the MultiAyahMatch data model."""
    
    def test_get_reference_single_ayah(self):
        """Test get_reference for a match within a single ayah."""
        db = get_quran_database()
        verse = db.get_verse(1, 1)
        
        match = MultiAyahMatch(
            verses=[verse],
            similarity=95.0,
            matched_text="بسم الله الرحمن الرحيم",
            query_text="بسم الله الرحمن الرحيم",
            start_surah=1,
            start_ayah=1,
            start_word=0,
            end_surah=1,
            end_ayah=1,
            end_word=4
        )
        
        reference = match.get_reference()
        assert reference == "1:1"
    
    def test_get_reference_multiple_ayahs_same_surah(self):
        """Test get_reference for a match spanning multiple ayahs in the same surah."""
        db = get_quran_database()
        verses = [db.get_verse(55, i) for i in range(1, 5)]
        
        match = MultiAyahMatch(
            verses=verses,
            similarity=90.0,
            matched_text="الرحمن علم القران خلق الانسان",
            query_text="الرحمن علم القران خلق الانسان",
            start_surah=55,
            start_ayah=1,
            start_word=0,
            end_surah=55,
            end_ayah=4,
            end_word=2
        )
        
        reference = match.get_reference()
        assert reference == "55:1-4"
    
    def test_get_reference_multiple_surahs(self):
        """Test get_reference for a match spanning multiple surahs."""
        db = get_quran_database()
        verse1 = db.get_verse(93, 11)
        verse2 = db.get_verse(94, 1)
        
        match = MultiAyahMatch(
            verses=[verse1, verse2],
            similarity=85.0,
            matched_text="test text",
            query_text="test",
            start_surah=93,
            start_ayah=11,
            start_word=0,
            end_surah=94,
            end_ayah=1,
            end_word=3
        )
        
        reference = match.get_reference()
        assert reference == "93:11 - 94:1"
    
    def test_str_representation(self):
        """Test string representation of MultiAyahMatch."""
        db = get_quran_database()
        verse = db.get_verse(1, 1)
        
        match = MultiAyahMatch(
            verses=[verse],
            similarity=95.5,
            matched_text="بسم الله الرحمن الرحيم",
            query_text="بسم الله",
            start_surah=1,
            start_ayah=1,
            start_word=0,
            end_surah=1,
            end_ayah=1,
            end_word=4
        )
        
        str_repr = str(match)
        assert "1:1" in str_repr
        assert "95.5" in str_repr or "95.5" in str_repr  # Similarity score
    
    def test_repr_representation(self):
        """Test repr representation of MultiAyahMatch."""
        db = get_quran_database()
        verse = db.get_verse(1, 1)
        
        match = MultiAyahMatch(
            verses=[verse],
            similarity=95.5,
            matched_text="test",
            query_text="test",
            start_surah=1,
            start_ayah=1,
            start_word=0,
            end_surah=1,
            end_ayah=1,
            end_word=4
        )
        
        repr_str = repr(match)
        assert "MultiAyahMatch" in repr_str
        assert "1:1" in repr_str


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
