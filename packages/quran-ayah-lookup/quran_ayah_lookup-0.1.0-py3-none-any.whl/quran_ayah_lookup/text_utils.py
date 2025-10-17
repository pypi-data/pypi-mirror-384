"""
Text processing utilities for Arabic Quran text normalization.
"""
import re


# Arabic diacritics and special signs to be removed
ARABIC_DIACRITICS = [
    # Basic diacritics (tashkeel)
    '\u064B',  # FATHATAN (ً)
    '\u064C',  # DAMMATAN (ٌ)
    '\u064D',  # KASRATAN (ٍ)
    '\u064E',  # FATHA (َ)
    '\u064F',  # DAMMA (ُ)
    '\u0650',  # KASRA (ِ)
    '\u0651',  # SHADDA (ّ)
    '\u0652',  # SUKUN (ْ)
    
    # Maddah and other signs
    '\u0653',  # MADDAH ABOVE (ٓ)
    '\u0654',  # HAMZA ABOVE (ٔ)
    '\u0655',  # HAMZA BELOW (ٕ)
    '\u0656',  # SUBSCRIPT ALEF (ٖ)
    '\u0657',  # INVERTED DAMMA (ٗ)
    '\u0658',  # MARK NOON GHUNNA (٘)
    '\u0659',  # ZWARAKAY (ٙ)
    '\u065A',  # VOWEL SIGN SMALL V ABOVE (ٚ)
    '\u065B',  # VOWEL SIGN INVERTED SMALL V ABOVE (ٛ)
    '\u065C',  # VOWEL SIGN DOT BELOW (ٜ)
    '\u065D',  # REVERSED DAMMA (ٝ)
    '\u065E',  # FATHA WITH TWO DOTS (ٞ)
    '\u065F',  # WAVY HAMZA BELOW (ٟ)
    
    # Extended Arabic diacritics
    '\u0670',  # SUPERSCRIPT ALEF (ٰ)
    '\u06D6',  # SMALL HIGH LIGATURE SAD WITH LAM WITH ALEF MAKSURA (ۖ)
    '\u06D7',  # SMALL HIGH LIGATURE QAF WITH LAM WITH ALEF MAKSURA (ۗ)
    '\u06D8',  # SMALL HIGH MEEM INITIAL FORM (ۘ)
    '\u06D9',  # SMALL HIGH LAM ALEF (ۙ)
    '\u06DA',  # SMALL HIGH JEEM (ۚ)
    '\u06DB',  # SMALL HIGH THREE DOTS (ۛ)
    '\u06DC',  # SMALL HIGH SEEN (ۜ)
    '\u06DF',  # SMALL HIGH ROUNDED ZERO (۟)
    '\u06E0',  # SMALL HIGH UPRIGHT RECTANGULAR ZERO (۠)
    '\u06E1',  # SMALL HIGH DOTLESS HEAD OF KHAH (ۡ)
    '\u06E2',  # SMALL HIGH MEEM ISOLATED FORM (ۢ)
    '\u06E3',  # SMALL LOW SEEN (ۣ)
    '\u06E4',  # SMALL HIGH MADDA (ۤ)
    '\u06E5',  # SMALL WAW (ۥ)
    '\u06E6',  # SMALL YEH (ۦ)
    '\u06E7',  # SMALL HIGH YEH (ۧ)
    '\u06E8',  # SMALL HIGH NOON (ۨ)
    '\u06E9',  # PLACE OF SAJDAH (۩)
    '\u06EA',  # EMPTY CENTRE LOW STOP (۪)
    '\u06EB',  # EMPTY CENTRE HIGH STOP (۫)
    '\u06EC',  # ROUNDED HIGH STOP WITH FILLED CENTRE (۬)
    '\u06ED',  # SMALL LOW MEEM (ۭ)
    
    # Quranic annotation signs
    '\u06E9',  # PLACE OF SAJDAH (۩)
    '\u08F0',  # OPEN FATHATAN (ࣰ)
    '\u08F1',  # OPEN DAMMATAN (ࣱ)
    '\u08F2',  # OPEN KASRATAN (ࣲ)
    '\u08F3',  # SMALL HIGH WAW (ࣳ)
    '\u08F4',  # FATHA WITH RING (ࣴ)
    '\u08F5',  # FATHA WITH DOT ABOVE (ࣵ)
    '\u08F6',  # KASRA WITH DOT BELOW (ࣶ)
    '\u08F7',  # LEFT ARROWHEAD ABOVE (ࣷ)
    '\u08F8',  # RIGHT ARROWHEAD ABOVE (ࣸ)
    '\u08F9',  # LEFT ARROWHEAD BELOW (ࣹ)
    '\u08FA',  # RIGHT ARROWHEAD BELOW (ࣺ)
    '\u08FB',  # DOUBLE RIGHT ARROWHEAD ABOVE (ࣻ)
    '\u08FC',  # DOUBLE RIGHT ARROWHEAD ABOVE WITH DOT (ࣼ)
    '\u08FD',  # RIGHT ARROWHEAD ABOVE WITH DOT (ࣽ)
    '\u08FE',  # DAMMA WITH DOT (ࣾ)
    '\u08FF',  # MARK SIDEWAYS NOON GHUNNA (ࣿ)
]

# Quarter hizb and other special marks
QURAN_SPECIAL_MARKS = [
    '\u06DE',  # START OF RUB EL HIZB (۞)
    '\u060C',  # ARABIC COMMA (،)
    '\u061B',  # ARABIC SEMICOLON (؛)
    '\u061F',  # ARABIC QUESTION MARK (؟)
    '\u0640',  # ARABIC TATWEEL (ـ)
]

# Combine all characters to remove
ALL_DIACRITICS_AND_MARKS = ARABIC_DIACRITICS + QURAN_SPECIAL_MARKS


def normalize_arabic_text(text: str) -> str:
    """
    Normalize Arabic text by removing all diacritics, tashkeel, madd, 
    tajweed signs, sajdah signs, and quarter_hizb signs, and normalize
    Alif wasla to regular Alif.
    
    Args:
        text (str): Original Arabic text with diacritics
        
    Returns:
        str: Normalized Arabic text without diacritics
    """
    if not text:
        return text
    
    # Remove all diacritics and special marks
    normalized = text
    for mark in ALL_DIACRITICS_AND_MARKS:
        normalized = normalized.replace(mark, '')
    
    # Remove any remaining diacritics using Unicode categories
    # This catches any diacritics we might have missed
    normalized = re.sub(r'[\u064B-\u065F\u0670\u06D6-\u06ED\u08F0-\u08FF]', '', normalized)
    
    # Normalize Alif wasla (ٱ) to regular Alif (ا)
    normalized = normalized.replace('\u0671', '\u0627')  # ٱ → ا
    
    # Clean up extra whitespace
    normalized = ' '.join(normalized.split())
    
    return normalized


_BASMALA_CACHE = None

def extract_basmala() -> str:
    """
    Return the standard Basmala text as it appears in Al-Fatihah.
    
    Returns:
        str: The exact Basmala from the Quran text file
    """
    global _BASMALA_CACHE
    
    if _BASMALA_CACHE is None:
        # Load the exact Basmala from Al-Fatihah 1:1 in our data file
        # This ensures the diacritics match exactly with the file content
        import os
        from pathlib import Path
        
        # Get path to the data file
        current_dir = Path(__file__).parent
        data_file = current_dir / "resources" / "quran-uthmani_all.txt"
        
        try:
            with open(data_file, 'r', encoding='utf-8') as f:
                first_line = f.readline().strip()
                parts = first_line.split('|')
                if len(parts) == 3 and parts[0] == '1' and parts[1] == '1':
                    _BASMALA_CACHE = parts[2]  # Al-Fatihah 1:1 text
                else:
                    # Fallback if file format is unexpected
                    _BASMALA_CACHE = "بِسْمِ ٱللَّهِ ٱلرَّحْمَـٰنِ ٱلرَّحِيمِ"
        except FileNotFoundError:
            # Fallback if file not found
            _BASMALA_CACHE = "بِسْمِ ٱللَّهِ ٱلرَّحْمَـٰنِ ٱلرَّحِيمِ"
    
    return _BASMALA_CACHE


def is_basmala_present(text: str) -> bool:
    """
    Check if text starts with Basmala using normalized text comparison.
    This is more reliable than exact Unicode matching.
    
    Args:
        text (str): Arabic text to check
        
    Returns:
        bool: True if text starts with Basmala
    """
    # Normalize both the input text and the expected Basmala
    normalized_text = normalize_arabic_text(text.strip())
    normalized_basmala = get_normalized_basmala()
    
    return normalized_text.startswith(normalized_basmala)


def remove_basmala_from_text(text: str) -> str:
    """
    Remove Basmala from the beginning of text if present using normalized matching.
    
    Args:
        text (str): Arabic text that may start with Basmala
        
    Returns:
        str: Text with Basmala removed, or original text if no Basmala
    """
    text = text.strip()
    if not is_basmala_present(text):
        return text
    
    # Use the original Basmala from the file as reference
    original_basmala = extract_basmala()
    
    # Simple approach: if the text starts with the exact Basmala, remove it
    if text.startswith(original_basmala):
        return text[len(original_basmala):].strip()
    
    # Fallback: if normalized matching found Basmala but exact match fails,
    # try to find where the Basmala ends by looking for common patterns
    # The normalized Basmala should be: "بسم ٱلله ٱلرحمن ٱلرحيم"
    words = text.split()
    if len(words) >= 4:
        # Try to identify the 4 main words of Basmala and remove them
        normalized_words = [normalize_arabic_text(word) for word in words[:4]]
        expected = get_normalized_basmala().split()
        
        if len(normalized_words) >= len(expected):
            # Check if first N words match Basmala pattern
            match_count = 0
            for i, exp_word in enumerate(expected):
                if i < len(normalized_words) and normalized_words[i] == exp_word:
                    match_count += 1
                else:
                    break
            
            if match_count == len(expected):
                # Remove the matched words
                remaining_words = words[match_count:]
                return ' '.join(remaining_words)
    
    # If all else fails, return original text
    return text


def get_normalized_basmala() -> str:
    """
    Get the normalized version of Basmala (without diacritics).
    
    Returns:
        str: Normalized Basmala text
    """
    return normalize_arabic_text(extract_basmala())


def fuzzy_substring_search(query: str, text: str, window_size: int = None, 
                          threshold: float = 0.7) -> dict:
    """
    Perform fuzzy substring search within a single text using sliding window approach.
    
    Args:
        query (str): The text to search for
        text (str): The text to search within
        window_size (int, optional): Size of the sliding window. If None, uses query length + 3
        threshold (float): Minimum similarity score (0.0-1.0)
        
    Returns:
        dict: Match information with start_word, end_word, similarity, and matched_text
              Returns None if no match above threshold is found
    """
    from rapidfuzz import fuzz
    
    if not query.strip() or not text.strip():
        return None
    
    # Split into words
    text_words = text.split()
    query_words = query.split()
    q_len = len(query_words)
    
    if q_len == 0 or len(text_words) == 0:
        return None
    
    # Set window size with buffer
    if not window_size:
        window_size = max(q_len + 3, q_len * 2)  # Flexible window size
    
    best_score = 0
    best_range = (0, 0)
    best_matched_text = ""
    
    # Slide a window across the text
    max_start = max(0, len(text_words) - q_len + 1)
    for i in range(max_start):
        # Try different window sizes to find the best match
        for current_window in [q_len, min(window_size, len(text_words) - i)]:
            if i + current_window > len(text_words):
                continue
                
            segment = " ".join(text_words[i:i+current_window])
            
            # Use token_set_ratio for better Arabic text matching
            score = fuzz.token_set_ratio(query, segment) / 100.0
            
            if score > best_score:
                best_score = score
                best_range = (i, i + current_window)
                best_matched_text = segment
    
    # Also try token_sort_ratio for different matching approach
    for i in range(max_start):
        for current_window in [q_len, min(window_size, len(text_words) - i)]:
            if i + current_window > len(text_words):
                continue
                
            segment = " ".join(text_words[i:i+current_window])
            
            # Use token_sort_ratio as alternative
            score = fuzz.token_sort_ratio(query, segment) / 100.0
            
            if score > best_score:
                best_score = score
                best_range = (i, i + current_window)
                best_matched_text = segment
    
    if best_score < threshold:
        return None  # No good match found
    
    return {
        "start_word": best_range[0],
        "end_word": best_range[1],
        "similarity": round(best_score, 3),
        "matched_text": best_matched_text
    }


def fuzzy_search_text(query: str, verses: list, threshold: float = 0.7, 
                     normalized: bool = True, max_results: int = None) -> list:
    """
    Perform fuzzy search across multiple verses with partial text matching.
    
    Args:
        query (str): The text to search for
        verses (List[QuranVerse]): List of verses to search in
        threshold (float): Minimum similarity score (0.0-1.0)
        normalized (bool): Whether to search in normalized text (default: True)
        max_results (int, optional): Maximum number of results to return
        
    Returns:
        List[FuzzySearchResult]: List of fuzzy search results, sorted by similarity score
    """
    from .models import FuzzySearchResult
    
    if not query.strip():
        return []
    
    # Normalize query if needed
    search_query = normalize_arabic_text(query.strip()) if normalized else query.strip()
    results = []
    
    for verse in verses:
        # Choose which text to search in
        search_text = verse.text_normalized if normalized else verse.text
        
        # Perform fuzzy substring search
        match = fuzzy_substring_search(search_query, search_text, threshold=threshold)
        
        if match:
            # Create result object
            result = FuzzySearchResult(
                verse=verse,
                start_word=match["start_word"],
                end_word=match["end_word"],
                similarity=match["similarity"],
                matched_text=match["matched_text"],
                query_text=search_query
            )
            results.append(result)
    
    # Sort by similarity score (descending)
    results.sort(key=lambda x: x.similarity, reverse=True)
    
    # Limit results if specified
    if max_results and len(results) > max_results:
        results = results[:max_results]
    
    return results


def sliding_window_multi_ayah_search(query: str, verses: list, threshold: float = 80.0,
                                     normalized: bool = True, max_results: int = None) -> list:
    """
    Perform sliding window search across multiple ayahs using vectorized fuzzy matching.
    
    This function concatenates all verses into a continuous text stream and uses a sliding
    window approach with vectorized fuzzy matching to find text that may span multiple ayahs.
    
    Args:
        query (str): The text to search for
        verses (List[QuranVerse]): List of verses to search in (should be ordered)
        threshold (float): Minimum similarity score (0.0-100.0, default: 80.0)
        normalized (bool): Whether to search in normalized text (default: True)
        max_results (int, optional): Maximum number of results to return
        
    Returns:
        List[MultiAyahMatch]: List of multi-ayah matches, sorted by similarity score
        
    Examples:
        >>> # Search for text spanning multiple ayahs
        >>> db = get_quran_database()
        >>> all_verses = db.get_all_verses()
        >>> results = sliding_window_multi_ayah_search(
        ...     "الرحمن علم القران خلق الانسان علمه البيان",
        ...     all_verses,
        ...     threshold=80
        ... )
        >>> for match in results:
        ...     print(f"Found in: {match.get_reference()}")
        ...     print(f"Similarity: {match.similarity:.1f}")
    """
    from rapidfuzz import process, fuzz
    from .models import MultiAyahMatch
    
    if not query.strip() or not verses:
        return []
    
    # Normalize query if needed
    search_query = normalize_arabic_text(query.strip()) if normalized else query.strip()
    query_words = search_query.split()
    query_len = len(query_words)
    
    if query_len == 0:
        return []
    
    # Build a continuous text stream with verse boundaries tracked
    text_segments = []
    verse_map = []  # Maps each segment index to (verse, word_start, word_end)
    
    for verse in verses:
        verse_text = verse.text_normalized if normalized else verse.text
        verse_words = verse_text.split()
        
        # Store each word segment with verse metadata
        for word_idx, word in enumerate(verse_words):
            text_segments.append(word)
            verse_map.append((verse, word_idx, word_idx + 1))
    
    if not text_segments:
        return []
    
    # Create sliding windows with varying sizes
    # We'll try windows from query_len to query_len * 1.5 to catch matches with some extra words
    # Limit the number of window sizes to avoid excessive computation
    windows = []
    window_metadata = []  # Stores (start_idx, end_idx) in text_segments
    
    min_window = query_len
    max_window = min(int(query_len * 1.5), len(text_segments))
    
    # Limit number of window sizes for performance
    # For long queries, only try a few window sizes
    if query_len > 20:
        window_sizes = [query_len, max_window]
    else:
        window_sizes = range(min_window, max_window + 1)
    
    for window_size in window_sizes:
        # Skip if window size is too large
        if window_size > len(text_segments):
            continue
            
        # Create sliding windows with a stride for very long queries
        # For very long queries (>30 words), use stride of 2-3 to reduce number of windows
        stride = 1 if query_len <= 30 else min(3, query_len // 10)
        
        for start_idx in range(0, len(text_segments) - window_size + 1, stride):
            end_idx = start_idx + window_size
            window_text = " ".join(text_segments[start_idx:end_idx])
            windows.append(window_text)
            window_metadata.append((start_idx, end_idx))
    
    if not windows:
        return []
    
    # Vectorized fuzzy matching using rapidfuzz
    # Use partial_ratio for substring matching
    scores = process.cdist([search_query], windows, scorer=fuzz.partial_ratio)[0]
    
    # Create list of (index, score) tuples for items above threshold
    scored_items = [(i, float(scores[i])) for i in range(len(scores)) if scores[i] >= threshold]
    
    if not scored_items:
        return []
    
    # Sort by score descending
    scored_items.sort(key=lambda x: x[1], reverse=True)
    
    # Build results
    results = []
    seen_ranges = set()  # To avoid duplicate overlapping matches
    
    for idx, score in scored_items:
        start_idx, end_idx = window_metadata[idx]
        matched_text = windows[idx]
        
        # Get verse boundaries
        start_verse_info = verse_map[start_idx]
        end_verse_info = verse_map[end_idx - 1]
        
        start_verse = start_verse_info[0]
        start_word_in_verse = start_verse_info[1]
        end_verse = end_verse_info[0]
        end_word_in_verse = end_verse_info[2]
        
        # Create a range key to avoid duplicates
        range_key = (start_verse.surah_number, start_verse.ayah_number, 
                    start_word_in_verse, end_verse.surah_number, 
                    end_verse.ayah_number, end_word_in_verse)
        
        if range_key in seen_ranges:
            continue
        
        seen_ranges.add(range_key)
        
        # Collect all verses in this range
        matched_verses = []
        current_verse = None
        
        for seg_idx in range(start_idx, end_idx):
            verse_at_seg = verse_map[seg_idx][0]
            if current_verse is None or verse_at_seg != current_verse:
                matched_verses.append(verse_at_seg)
                current_verse = verse_at_seg
        
        # Create match result
        match = MultiAyahMatch(
            verses=matched_verses,
            similarity=score,
            matched_text=matched_text,
            query_text=search_query,
            start_surah=start_verse.surah_number,
            start_ayah=start_verse.ayah_number,
            start_word=start_word_in_verse,
            end_surah=end_verse.surah_number,
            end_ayah=end_verse.ayah_number,
            end_word=end_word_in_verse
        )
        results.append(match)
        
        # Limit results if specified
        if max_results and len(results) >= max_results:
            break
    
    return results