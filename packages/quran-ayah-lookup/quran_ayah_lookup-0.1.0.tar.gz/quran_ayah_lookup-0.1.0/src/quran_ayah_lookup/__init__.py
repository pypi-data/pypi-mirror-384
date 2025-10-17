"""
Quran Ayah Lookup Package

A Python package for looking up Quranic ayahs by their number or Arabic text.
Uses Quran corpus from Tanzil.net. Arabic only, no translations supported.

Author: Sayed Mahmoud
Email: foss-support@sayedmahmoud266.website
"""



# Import core functionality
from .models import QuranVerse, QuranChapter, QuranDatabase, FuzzySearchResult, MultiAyahMatch
from .text_utils import normalize_arabic_text
from .loader import initialize_quran_database, get_quran_database
from importlib.metadata import version


__version__ = version("quran-ayah-lookup")
__author__ = "Sayed Mahmoud"
__email__ = "foss-support@sayedmahmoud266.website"

print(f"Quran Ayah Lookup version {__version__} initialized.")

# Initialize the Quran database when package is imported
_quran_db = initialize_quran_database()

# Public API exports
__all__ = [
    'QuranVerse',
    'QuranChapter',
    'QuranDatabase',
    'FuzzySearchResult',
    'MultiAyahMatch',
    'normalize_arabic_text',
    'get_quran_database',
    'get_verse',
    'get_surah',
    'search_text',
    'fuzzy_search',
    'search_sliding_window',
    'smart_search',
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


def search_sliding_window(query: str, threshold: float = 80.0, normalized: bool = True,
                          max_results: int = None) -> list:
    """
    Search for verses using a sliding window approach that can match multiple ayahs.
    
    This function uses vectorized fuzzy matching with a sliding window to find text
    that may span multiple ayahs. It's particularly useful for finding longer passages
    or quotes that cross ayah boundaries.
    
    Args:
        query (str): Arabic text to search for (can span multiple ayahs)
        threshold (float): Minimum similarity score (0.0-100.0, default: 80.0)
        normalized (bool): Whether to search in normalized text (default: True)
        max_results (int, optional): Maximum number of results to return
        
    Returns:
        List[MultiAyahMatch]: List of matches sorted by similarity score, each potentially
                             spanning multiple ayahs
        
    Examples:
        >>> # Search for text spanning multiple ayahs
        >>> results = search_sliding_window(
        ...     "الرحمن علم القران خلق الانسان علمه البيان",
        ...     threshold=80
        ... )
        >>> for match in results:
        ...     print(f"Found in: {match.get_reference()}")
        ...     print(f"Similarity: {match.similarity:.1f}")
        ...     print(f"Matched text: {match.matched_text}")
        
        >>> # Search across surah boundaries
        >>> results = search_sliding_window(
        ...     "بسم الله الرحمن الرحيم الم نشرح لك صدرك",
        ...     threshold=85
        ... )
    """
    from .text_utils import sliding_window_multi_ayah_search
    
    all_verses = get_quran_database().get_all_verses()
    return sliding_window_multi_ayah_search(query, all_verses, threshold, normalized, max_results)


def smart_search(query: str, threshold: float = 0.7, sliding_threshold: float = 80.0,
                normalized: bool = True, max_results: int = None) -> dict:
    """
    Intelligent search that tries multiple search methods in order of precision.
    
    This function cascades through different search methods:
    1. First tries exact text search (search_text)
    2. If no results, tries fuzzy search (fuzzy_search)
    3. If still no results, tries sliding window search (search_sliding_window)
    4. Returns empty results if all methods fail
    
    Args:
        query (str): Arabic text to search for
        threshold (float): Minimum similarity score for fuzzy search (0.0-1.0, default: 0.7)
        sliding_threshold (float): Minimum similarity score for sliding window (0.0-100.0, default: 80.0)
        normalized (bool): Whether to search in normalized text (default: True)
        max_results (int, optional): Maximum number of results to return for each method
        
    Returns:
        dict: Dictionary containing:
            - 'method': The search method that returned results ('exact', 'fuzzy', 'sliding_window', or 'none')
            - 'results': List of results (QuranVerse, FuzzySearchResult, or MultiAyahMatch objects)
            - 'count': Number of results found
        
    Examples:
        >>> # Smart search will find the best matching method
        >>> result = smart_search("الرحمن الرحيم")
        >>> print(f"Found {result['count']} results using {result['method']} search")
        >>> for item in result['results']:
        ...     print(item)
        
        >>> # Works with exact matches, fuzzy matches, or multi-ayah matches
        >>> result = smart_search("الرحمن علم القران خلق الانسان")
        >>> if result['method'] == 'sliding_window':
        ...     print("Found multi-ayah match!")
    """
    # Handle empty or whitespace-only queries
    if not query or not query.strip():
        return {
            'method': 'none',
            'results': [],
            'count': 0
        }
    
    # Try exact text search first
    results = search_text(query, normalized=normalized)
    if results:
        limited_results = results[:max_results] if max_results else results
        return {
            'method': 'exact',
            'results': limited_results,
            'count': len(limited_results)
        }
    
    # Try fuzzy search if exact search failed
    fuzzy_results = fuzzy_search(query, threshold=threshold, normalized=normalized, max_results=max_results)
    if fuzzy_results:
        return {
            'method': 'fuzzy',
            'results': fuzzy_results,
            'count': len(fuzzy_results)
        }
    
    # Try sliding window search if fuzzy search failed
    sliding_results = search_sliding_window(query, threshold=sliding_threshold, 
                                           normalized=normalized, max_results=max_results)
    if sliding_results:
        return {
            'method': 'sliding_window',
            'results': sliding_results,
            'count': len(sliding_results)
        }
    
    # No results found with any method
    return {
        'method': 'none',
        'results': [],
        'count': 0
    }