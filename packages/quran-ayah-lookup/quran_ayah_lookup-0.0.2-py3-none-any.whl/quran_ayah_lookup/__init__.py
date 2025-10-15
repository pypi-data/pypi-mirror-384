"""
Quran Ayah Lookup Package

A Python package for looking up Quranic ayahs by their number or Arabic text.
Uses Quran corpus from Tanzil.net. Arabic only, no translations supported.

Author: Sayed Mahmoud
Email: foss-support@sayedmahmoud266.website
"""

__version__ = "0.0.1"
__author__ = "Sayed Mahmoud"
__email__ = "foss-support@sayedmahmoud266.website"

# Import core functionality
from .models import QuranVerse, QuranChapter, QuranDatabase, FuzzySearchResult
from .text_utils import normalize_arabic_text
from .loader import initialize_quran_database, get_quran_database

# Initialize the Quran database when package is imported
_quran_db = initialize_quran_database()

# Public API exports
__all__ = [
    'QuranVerse',
    'QuranChapter',
    'QuranDatabase',
    'FuzzySearchResult',
    'normalize_arabic_text',
    'get_quran_database',
    'get_verse',
    'get_surah',
    'search_text',
    'fuzzy_search',
    'get_surah_verses',
]


# Convenience functions for easy access
def get_verse(surah_number: int, ayah_number: int) -> QuranVerse:
    """
    Get a specific verse by surah and ayah number.
    
    Args:
        surah_number (int): Surah number (1-114)
        ayah_number (int): Ayah number (0 for Basmala, 1+ for regular ayahs)
        
    Returns:
        QuranVerse: The requested verse
        
    Raises:
        ValueError: If verse not found
    """
    return get_quran_database().get_verse(surah_number, ayah_number)


def get_surah(surah_number: int) -> QuranChapter:
    """
    Get a specific surah/chapter with O(1) verse access.
    
    Args:
        surah_number (int): Surah number (1-114)
        
    Returns:
        QuranChapter: The requested surah chapter
        
    Raises:
        ValueError: If surah not found
        
    Examples:
        >>> surah = get_surah(3)  # Get Al-Imran
        >>> verse = surah[35]     # Get verse 35 (O(1) operation)
        >>> all_verses = surah.get_all_verses()  # Get all verses as list
    """
    return get_quran_database().get_surah(surah_number)


def search_text(query: str, normalized: bool = True) -> list:
    """
    Search for verses containing the query text.
    
    Args:
        query (str): Arabic text to search for
        normalized (bool): Whether to search in normalized text (default: True)
        
    Returns:
        List[QuranVerse]: List of matching verses
    """
    return get_quran_database().search_text(query, normalized)


def fuzzy_search(query: str, threshold: float = 0.7, normalized: bool = True, 
                max_results: int = None) -> list:
    """
    Perform fuzzy search with partial text matching across all verses.
    
    Args:
        query (str): Arabic text to search for
        threshold (float): Minimum similarity score (0.0-1.0, default: 0.7)
        normalized (bool): Whether to search in normalized text (default: True)
        max_results (int, optional): Maximum number of results to return
        
    Returns:
        List[FuzzySearchResult]: List of fuzzy search results sorted by similarity
        
    Examples:
        >>> results = fuzzy_search("كذلك يجتبيك ربك ويعلمك", threshold=0.8)
        >>> for result in results[:5]:
        ...     print(f"Similarity: {result.similarity:.3f}")
        ...     print(f"Match: {result.matched_text}")
        
        >>> # Search for repeated phrases
        >>> results = fuzzy_search("فبأي الاء ربكما تكذبان")
        >>> print(f"Found {len(results)} matches")
    """
    return get_quran_database().fuzzy_search(query, threshold, normalized, max_results)


def get_surah_verses(surah_number: int) -> list:
    """
    Get all verses for a specific surah.
    
    Args:
        surah_number (int): Surah number (1-114)
        
    Returns:
        List[QuranVerse]: All verses in the surah (including Basmala if present)
    """
    return get_quran_database().get_surah_verses(surah_number)