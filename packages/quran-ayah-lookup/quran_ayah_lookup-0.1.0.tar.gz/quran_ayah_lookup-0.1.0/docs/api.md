# API Reference

## Overview

This document provides detailed API reference for the Quran Ayah Lookup package with O(1) performance.

## Quick Reference

```python
import quran_ayah_lookup as qal

# O(1) Direct access
db = qal.get_quran_database()
verse = db[surah][ayah]

# Convenience functions  
verse = qal.get_verse(surah, ayah)
surah = qal.get_surah(surah_number)
results = qal.search_text(query)

# Fuzzy search
results = qal.fuzzy_search(query, threshold=0.7)

# Multi-ayah sliding window search
results = qal.search_sliding_window(query, threshold=80.0)

# Smart search (auto-selects best method)
result = qal.smart_search(query)
```

## Core Functions

### get_verse(surah_number: int, ayah_number: int) → QuranVerse

Get a specific verse by surah and ayah number.

```python
verse = qal.get_verse(3, 35)  # Al-Imran, verse 35
```

**Parameters:**
- `surah_number` (int): Surah number (1-114)
- `ayah_number` (int): Ayah number (0 for Basmala, 1+ for regular ayahs)

**Returns:** `QuranVerse` object

**Raises:** `ValueError` if verse not found

### get_surah(surah_number: int) → QuranChapter

Get a surah/chapter with O(1) verse access.

```python
surah = qal.get_surah(3)  # Get Al-Imran
verse = surah[35]         # O(1) access to verse 35
```

**Parameters:**
- `surah_number` (int): Surah number (1-114)

**Returns:** `QuranChapter` object

**Raises:** `ValueError` if surah not found

### search_text(query: str, normalized: bool = True) → List[QuranVerse]

Search for verses containing the query text (exact substring matching).

```python
results = qal.search_text("الله", normalized=True)
```

**Parameters:**
- `query` (str): Arabic text to search for
- `normalized` (bool): Search in normalized text (default: True)

**Returns:** List of matching `QuranVerse` objects

### fuzzy_search(query: str, threshold: float = 0.7, normalized: bool = True, max_results: int = None) → List[FuzzySearchResult]

Perform fuzzy search with partial text matching across all verses. This allows finding verses that contain similar text even if not exact matches.

```python
# Find partial ayah matches
results = qal.fuzzy_search("كذلك يجتبيك ربك ويعلمك", threshold=0.8)

# Find repeated phrases
results = qal.fuzzy_search("فبأي الاء ربكما تكذبان")

# Control similarity threshold
high_precision = qal.fuzzy_search("بسم الله", threshold=0.95)
more_results = qal.fuzzy_search("بسم الله", threshold=0.7)
```

**Parameters:**
- `query` (str): Arabic text to search for
- `threshold` (float): Minimum similarity score (0.0-1.0, default: 0.7)
- `normalized` (bool): Search in normalized text (default: True)
- `max_results` (int, optional): Maximum number of results to return

**Returns:** List of `FuzzySearchResult` objects sorted by similarity score

**Features:**
- **Partial text matching**: Finds verses containing part of the query text
- **Multiple results**: Returns all matches above the similarity threshold
- **Word-level positions**: Tracks exact word ranges of matches
- **Configurable precision**: Adjust threshold for stricter or looser matching
- **Similarity scoring**: Results ranked by relevance (0.0-1.0)

### search_sliding_window(query: str, threshold: float = 80.0, normalized: bool = True, max_results: int = None) → List[MultiAyahMatch]

Search for text that spans multiple consecutive ayahs using a sliding window algorithm with vectorized fuzzy matching.

```python
# Search for text spanning multiple ayahs
query = "الرحمن علم القران خلق الانسان علمه البيان"
results = qal.search_sliding_window(query, threshold=80.0)

# Cross-surah search
results = qal.search_sliding_window("بسم الله الرحمن الرحيم الحمد لله رب العالمين")

# Adjust precision
high_precision = qal.search_sliding_window(query, threshold=90.0)
more_matches = qal.search_sliding_window(query, threshold=75.0)
```

**Parameters:**
- `query` (str): Arabic text to search for (can span multiple ayahs)
- `threshold` (float): Minimum similarity score (0.0-100.0, default: 80.0)
- `normalized` (bool): Search in normalized text (default: True)
- `max_results` (int, optional): Maximum number of results to return

**Returns:** List of `MultiAyahMatch` objects sorted by similarity score (highest first)

**Features:**
- **Multi-ayah matching**: Finds text spanning consecutive verses
- **Vectorized performance**: Uses rapidfuzz.process.cdist for fast batch matching
- **Dynamic window sizing**: Adapts window size based on query length
- **Cross-surah support**: Can match text across surah boundaries
- **Optimized for long queries**: Uses stride for queries >30 words
- **Word-level positions**: Tracks exact word ranges across verses

### smart_search(query: str, threshold: float = 0.7, sliding_threshold: float = 80.0, normalized: bool = True, max_results: int = None) → dict

Intelligently search using cascading methods: exact text search → fuzzy search → sliding window search.

```python
# Automatic method selection
result = qal.smart_search("الرحمن الرحيم")
print(f"Used {result['method']} search")
print(f"Found {result['count']} results")

# Multi-ayah query (automatically uses sliding window)
result = qal.smart_search("الرحمن علم القران خلق الانسان")

# Custom thresholds
result = qal.smart_search(
    "الحمد لله",
    threshold=0.8,              # Fuzzy search threshold
    sliding_threshold=85.0,     # Sliding window threshold
    max_results=10
)

# Access results based on method used
if result['method'] == 'exact':
    for verse in result['results']:
        print(verse.text)
elif result['method'] == 'fuzzy':
    for match in result['results']:
        print(f"{match.verse.text} (score: {match.similarity})")
elif result['method'] == 'sliding_window':
    for match in result['results']:
        print(f"{match.get_reference()}: {match.similarity}%")
```

**Parameters:**
- `query` (str): Arabic text to search for
- `threshold` (float): Fuzzy search threshold (0.0-1.0, default: 0.7)
- `sliding_threshold` (float): Sliding window threshold (0.0-100.0, default: 80.0)
- `normalized` (bool): Search in normalized text (default: True)
- `max_results` (int, optional): Maximum number of results to return

**Returns:** Dictionary with:
- `method` (str): Which search method succeeded ('exact', 'fuzzy', 'sliding_window', or 'none')
- `results` (list): List of results (type depends on method)
- `count` (int): Number of results found

**Search Strategy:**
1. **Exact text search**: Tries `search_text()` first (fastest, most precise)
2. **Fuzzy search**: Falls back to `fuzzy_search()` if exact fails (handles variations)
3. **Sliding window**: Falls back to `search_sliding_window()` if fuzzy fails (multi-ayah)
4. **None**: Returns empty results if all methods fail

**Features:**
- **Automatic optimization**: Uses fastest applicable method
- **Consistent interface**: Single function for all search types
- **Method transparency**: Returns which method was used
- **Flexible configuration**: Separate thresholds for each method
- **Type-safe results**: Result type matches the method used

### get_surah_verses(surah_number: int) → List[QuranVerse]

Get all verses from a specific surah.

```python
verses = qal.get_surah_verses(1)  # All verses from Al-Fatihah
```

**Parameters:**
- `surah_number` (int): Surah number (1-114)

**Returns:** List of `QuranVerse` objects (including Basmala if present)

### normalize_arabic_text(text: str) → str

Normalize Arabic text by removing diacritics and normalizing Alif characters.

```python
normalized = qal.normalize_arabic_text("بِسْمِ ٱللَّهِ")
# Result: "بسم الله"
```

**Parameters:**
- `text` (str): Original Arabic text with diacritics

**Returns:** Normalized Arabic text without diacritics

### get_quran_database() → QuranDatabase

Get the main database instance (loaded automatically on import).

```python
db = qal.get_quran_database()
verse = db[3][35]  # Direct O(1) access
```

**Returns:** `QuranDatabase` object

## Data Models

### QuranVerse

Represents a single verse from the Quran.

```python
verse = qal.get_verse(1, 1)
print(f"Surah: {verse.surah_number}")
print(f"Ayah: {verse.ayah_number}")
print(f"Text: {verse.text}")
print(f"Normalized: {verse.text_normalized}")
print(f"Is Basmala: {verse.is_basmalah}")
```

**Attributes:**
- `surah_number` (int): Surah number (1-114)
- `ayah_number` (int): Ayah number (0 for Basmala, 1+ for regular ayahs)
- `text` (str): Original Arabic text with diacritics
- `text_normalized` (str): Normalized Arabic text without diacritics
- `is_basmalah` (bool): True if this is a Basmala verse

### FuzzySearchResult

Represents a fuzzy search result with partial match information.

```python
results = qal.fuzzy_search("كذلك يجتبيك ربك ويعلمك")
for result in results:
    print(f"Verse: {result.verse.surah_number}:{result.verse.ayah_number}")
    print(f"Similarity: {result.similarity:.3f}")
    print(f"Words: {result.start_word}-{result.end_word}")
    print(f"Matched: {result.matched_text}")
    print(f"Query: {result.query_text}")
```

**Attributes:**
- `verse` (QuranVerse): The matched verse object
- `start_word` (int): Starting word index of the match (0-based)
- `end_word` (int): Ending word index of the match (exclusive)
- `similarity` (float): Similarity score (0.0-1.0)
- `matched_text` (str): The actual text segment that was matched
- `query_text` (str): The original query text used for matching

**Usage Examples:**
```python
# Find partial ayah matches
results = qal.fuzzy_search("ويعلمك من تأويل الأحاديث")
result = results[0]

# Get the exact words that matched
words = result.verse.text_normalized.split()
matched_segment = " ".join(words[result.start_word:result.end_word])
print(f"Matched segment: {matched_segment}")

# Access the full verse
print(f"Full verse: {result.verse.text}")
```

### MultiAyahMatch

Represents a match spanning multiple consecutive ayahs from sliding window search.

```python
results = qal.search_sliding_window("الرحمن علم القران خلق الانسان علمه البيان")
for match in results:
    print(f"Reference: {match.get_reference()}")
    print(f"Similarity: {match.similarity}%")
    print(f"Verses: {len(match.verses)}")
    print(f"Start: Surah {match.start_surah}:{match.start_ayah}, word {match.start_word}")
    print(f"End: Surah {match.end_surah}:{match.end_ayah}, word {match.end_word}")
    
    # Access all verses in the match
    for verse in match.verses:
        print(f"  {verse.text}")
```

**Attributes:**
- `verses` (List[QuranVerse]): List of consecutive verses in the match
- `start_surah` (int): Starting surah number
- `start_ayah` (int): Starting ayah number
- `start_word` (int): Starting word index (0-based)
- `end_surah` (int): Ending surah number
- `end_ayah` (int): Ending ayah number
- `end_word` (int): Ending word index (exclusive)
- `similarity` (float): Similarity score (0.0-100.0)

**Methods:**
- `get_reference()` → str: Get formatted reference string (e.g., "55:1-4" or "1:7-2:2")

**Usage Examples:**
```python
# Search across multiple ayahs
results = qal.search_sliding_window("بسم الله الرحمن الرحيم الحمد لله رب العالمين")
match = results[0]

# Get reference string
print(match.get_reference())  # "1:1-2" (Surah Al-Fatihah, ayahs 1-2)

# Access individual verses
for i, verse in enumerate(match.verses):
    print(f"Verse {i+1}: {verse.text}")

# Get word range information
total_words = match.end_word - match.start_word
print(f"Matched {total_words} words")

# Check if match crosses surah boundary
crosses_surah = match.start_surah != match.end_surah
```

### QuranChapter

Represents a Quran chapter (surah) with O(1) verse lookup.

```python
surah = qal.get_surah(2)  # Al-Baqarah

# O(1) operations
verse = surah[255]        # Get Ayat al-Kursi
has_verse = 255 in surah  # Check existence  
count = len(surah)        # Get verse count

# Methods
all_verses = surah.get_all_verses()
verse_count = surah.get_verse_count()
has_basmala = surah.has_basmala()
```

**Attributes:**
- `number` (int): Surah number (1-114)
- `ayahs` (Dict[int, QuranVerse]): Dictionary mapping ayah number to verse

**Methods:**
- `get_verse(ayah_number)` → QuranVerse: Get specific verse (O(1))
- `get_all_verses()` → List[QuranVerse]: Get all verses as ordered list
- `get_verse_count()` → int: Get total verse count
- `has_basmala()` → bool: Check if surah has Basmala (ayah 0)

**Special Methods:**
- `len(chapter)`: Get verse count
- `ayah_number in chapter`: Check if ayah exists (O(1))
- `chapter[ayah_number]`: Get verse directly (O(1))

### QuranDatabase

Main database containing all Quran chapters with O(1) lookup.

```python
db = qal.get_quran_database()

# Direct access (fastest)
verse = db[3][35]  # O(1) lookup

# Information
print(f"Total verses: {len(db)}")
print(f"Total surahs: {db.total_surahs}")

# Check existence
if 3 in db:
    surah = db[3]
```

**Attributes:**
- `surahs` (Dict[int, QuranChapter]): Dictionary mapping surah number to chapter
- `total_verses` (int): Total number of verses (6,348 including Basmalas)
- `total_surahs` (int): Total number of surahs (114)

**Methods:**
- `get_verse(surah_number, ayah_number)` → QuranVerse: Get specific verse (O(1))
- `get_surah(surah_number)` → QuranChapter: Get specific surah (O(1))
- `get_all_verses()` → List[QuranVerse]: Get all verses as ordered list
- `search_text(query, normalized)` → List[QuranVerse]: Search for text

**Special Methods:**
- `len(db)`: Get total verse count
- `surah_number in db`: Check if surah exists (O(1))
- `db[surah_number]`: Get surah directly (O(1))

## Performance Reference

### O(1) Operations
All these operations complete in constant time regardless of database size:

- `db[surah][ayah]` - Direct verse access
- `surah[ayah]` - Verse access within surah  
- `ayah in surah` - Existence check
- `surah in db` - Surah existence check
- `len(surah)` - Verse count
- `len(db)` - Total verse count

### Performance Metrics
```
Operation           | Time (1000x) | Complexity
--------------------|---------------|------------
O(1) lookup         | 0.0006s      | O(1)
Linear search       | 0.5725s      | O(n)
Speedup             | 956x faster  | -
```

## Error Handling

### ValueError
Raised when verse or surah not found:

```python
try:
    verse = qal.get_verse(999, 1)  # Invalid surah
except ValueError as e:
    print(f"Error: {e}")

try:
    verse = surah[999]  # Invalid ayah
except ValueError as e:
    print(f"Error: {e}")
```

### Valid Ranges
- **Surah numbers**: 1-114
- **Ayah numbers**: 
  - 0 for Basmala (available in surahs 2-114 except 9)
  - 1+ for regular ayahs (varies by surah)

## Best Practices

### Performance Tips
1. **Use direct access**: `db[surah][ayah]` (fastest)
2. **Cache surah objects**: `surah = qal.get_surah(3); verse = surah[35]`
3. **Use normalized search**: Better matching results
4. **Check existence first**: `if ayah in surah:` before access

### Memory Considerations
1. **Database loads once**: 6,348 verses loaded at import
2. **Efficient storage**: Hashmap-based with minimal overhead
3. **Surah objects are lightweight**: Safe to cache and reuse
Raised when an invalid ayah number is provided for a given surah.

### SearchError

Raised when search operations fail.

## Constants

```python
TOTAL_SURAHS = 114
MIN_SURAH = 1
MAX_SURAH = 114
SUPPORTED_LANGUAGES = ['arabic', 'english']
SUPPORTED_TRANSLATIONS = ['english', 'urdu', 'french']
```

## Usage Examples

### Basic Search

```python
from quran_ayah_lookup import QuranLookup

quran = QuranLookup()

# Search for text
results = quran.search_text("الحمد لله")
for result in results:
    print(f"Found in {result.ayah.surah}:{result.ayah.ayah}")
    print(f"Score: {result.score}")
```

### Error Handling

```python
from quran_ayah_lookup import QuranLookup, InvalidSurahError

quran = QuranLookup()

try:
    ayah = quran.get_ayah(surah=115, ayah=1)  # Invalid surah
except InvalidSurahError as e:
    print(f"Error: {e}")
```

## Performance Notes

- Text searches are optimized using RapidFuzz for fast string matching
- Results are cached to improve repeated query performance
- Large result sets are paginated automatically

---

# REST API Reference

The package includes a REST API server that exposes all functionalities through HTTP endpoints with automatic OpenAPI/Swagger documentation.

## Starting the API Server

### Via CLI Command

```bash
# Start server on default host and port (127.0.0.1:8000)
qal serve

# Custom host and port
qal serve --host 0.0.0.0 --port 8080

# Development mode with auto-reload
qal serve --reload
```

### Via Python

```python
from quran_ayah_lookup.api import run_server

# Start server programmatically
run_server(host="127.0.0.1", port=8000, reload=False)
```

### Via Uvicorn Directly

```bash
uvicorn quran_ayah_lookup.api:app --host 127.0.0.1 --port 8000
```

## Installation

The REST API requires additional dependencies:

```bash
# Install with API support
pip install "quran-ayah-lookup[api]"

# Or install dependencies separately
pip install fastapi uvicorn[standard]
```

## API Documentation

Once the server is running, access the interactive documentation at:
- **Swagger UI**: `http://127.0.0.1:8000/docs`
- **ReDoc**: `http://127.0.0.1:8000/redoc`
- **OpenAPI JSON**: `http://127.0.0.1:8000/openapi.json`

## API Endpoints

### Root Endpoint

**GET /**

Returns API information and available endpoints.

```bash
curl http://127.0.0.1:8000/
```

Response:
```json
{
  "message": "Quran Ayah Lookup API",
  "version": "0.0.1",
  "docs": "/docs",
  "source": "Tanzil.net",
  "endpoints": {
    "verses": "/verses/{surah_number}/{ayah_number}",
    "surah_info": "/surahs/{surah_number}",
    "surah_verses": "/surahs/{surah_number}/verses",
    "search": "/search",
    "fuzzy_search": "/fuzzy-search",
    "sliding_window": "/sliding-window",
    "smart_search": "/smart-search",
    "stats": "/stats"
  }
}
```

### Get Verse

**GET /verses/{surah_number}/{ayah_number}**

Get a specific verse with O(1) performance.

Parameters:
- `surah_number` (path, int): Surah number (1-114)
- `ayah_number` (path, int): Ayah number (0 for Basmala, 1+ for regular ayahs)

```bash
curl http://127.0.0.1:8000/verses/1/1
```

Response:
```json
{
  "surah_number": 1,
  "ayah_number": 1,
  "text": "بِسۡمِ ٱللَّهِ ٱلرَّحۡمَـٰنِ ٱلرَّحِیمِ",
  "text_normalized": "بسم الله الرحمن الرحيم",
  "is_basmalah": false
}
```

### Get Surah Information

**GET /surahs/{surah_number}**

Get information about a specific surah/chapter.

Parameters:
- `surah_number` (path, int): Surah number (1-114)

```bash
curl http://127.0.0.1:8000/surahs/1
```

Response:
```json
{
  "surah_number": 1,
  "verse_count": 7,
  "has_basmala": false
}
```

### Get Surah Verses

**GET /surahs/{surah_number}/verses**

Get all verses in a specific surah.

Parameters:
- `surah_number` (path, int): Surah number (1-114)

```bash
curl http://127.0.0.1:8000/surahs/1/verses
```

Response: Array of verse objects

### Search Text

**GET /search**

Search for verses containing specific text (exact substring matching).

Query Parameters:
- `query` (string, required): Arabic text to search for
- `normalized` (boolean, optional): Search in normalized text (default: true)
- `limit` (integer, optional): Maximum number of results

```bash
# URL-encoded query
curl "http://127.0.0.1:8000/search?query=%D8%A7%D9%84%D9%84%D9%87&limit=5"
```

Response: Array of verse objects matching the query

### Fuzzy Search

**GET /fuzzy-search**

Perform fuzzy search with partial text matching and similarity scoring.

Query Parameters:
- `query` (string, required): Arabic text to search for
- `threshold` (float, optional): Minimum similarity score 0.0-1.0 (default: 0.7)
- `normalized` (boolean, optional): Search in normalized text (default: true)
- `limit` (integer, optional): Maximum number of results

```bash
curl "http://127.0.0.1:8000/fuzzy-search?query=%D8%A8%D8%B3%D9%85%20%D8%A7%D9%84%D9%84%D9%87&threshold=0.8"
```

Response:
```json
[
  {
    "verse": {
      "surah_number": 1,
      "ayah_number": 1,
      "text": "بِسۡمِ ٱللَّهِ ٱلرَّحۡمَـٰنِ ٱلرَّحِیمِ",
      "text_normalized": "بسم الله الرحمن الرحيم",
      "is_basmalah": false
    },
    "start_word": 0,
    "end_word": 4,
    "similarity": 0.95,
    "matched_text": "بسم الله الرحمن الرحيم",
    "query_text": "بسم الله"
  }
]
```

### Sliding Window Search

**GET /sliding-window**

Search for text spanning multiple consecutive ayahs using vectorized fuzzy matching with sliding windows.

Query Parameters:
- `query` (string, required): Arabic text to search for (can span multiple ayahs)
- `threshold` (float, optional): Minimum similarity score 0.0-100.0 (default: 80.0)
- `normalized` (boolean, optional): Search in normalized text (default: true)
- `limit` (integer, optional): Maximum number of results

```bash
# Search for multi-ayah text
curl "http://127.0.0.1:8000/sliding-window?query=%D8%A7%D9%84%D8%B1%D8%AD%D9%85%D9%86%20%D8%B9%D9%84%D9%85%20%D8%A7%D9%84%D9%82%D8%B1%D8%A7%D9%86&threshold=80.0&limit=5"
```

Response:
```json
[
  {
    "start_surah": 55,
    "start_ayah": 1,
    "start_word": 0,
    "end_surah": 55,
    "end_ayah": 4,
    "end_word": 12,
    "similarity": 95.5,
    "reference": "55:1-4",
    "verse_count": 4,
    "verses": [
      {
        "surah_number": 55,
        "ayah_number": 1,
        "text": "ٱلرَّحۡمَـٰنُ",
        "text_normalized": "الرحمن",
        "is_basmalah": false
      },
      {
        "surah_number": 55,
        "ayah_number": 2,
        "text": "عَلَّمَ ٱلۡقُرۡءَانَ",
        "text_normalized": "علم القران",
        "is_basmalah": false
      }
    ]
  }
]
```

**Features:**
- Finds text spanning multiple consecutive verses
- Uses vectorized matching for performance
- Can match across surah boundaries
- Returns complete verse ranges with word positions

### Smart Search

**GET /smart-search**

Intelligently search using cascading methods: exact → fuzzy → sliding window. Automatically selects the best search method.

Query Parameters:
- `query` (string, required): Arabic text to search for
- `fuzzy_threshold` (float, optional): Fuzzy search threshold 0.0-1.0 (default: 0.7)
- `sliding_threshold` (float, optional): Sliding window threshold 0.0-100.0 (default: 80.0)
- `normalized` (boolean, optional): Search in normalized text (default: true)
- `limit` (integer, optional): Maximum number of results

```bash
# Let smart search choose the best method
curl "http://127.0.0.1:8000/smart-search?query=%D8%A7%D9%84%D8%B1%D8%AD%D9%85%D9%86%20%D8%A7%D9%84%D8%B1%D8%AD%D9%8A%D9%85"
```

Response:
```json
{
  "method": "exact",
  "count": 114,
  "exact_results": [
    {
      "surah_number": 1,
      "ayah_number": 1,
      "text": "بِسۡمِ ٱللَّهِ ٱلرَّحۡمَـٰنِ ٱلرَّحِیمِ",
      "text_normalized": "بسم الله الرحمن الرحيم",
      "is_basmalah": false
    }
  ],
  "fuzzy_results": null,
  "sliding_window_results": null
}
```

**Method Response Examples:**

When using exact search (method="exact"):
```json
{
  "method": "exact",
  "count": 5,
  "exact_results": [...],
  "fuzzy_results": null,
  "sliding_window_results": null
}
```

When using fuzzy search (method="fuzzy"):
```json
{
  "method": "fuzzy",
  "count": 3,
  "exact_results": null,
  "fuzzy_results": [
    {
      "verse": {...},
      "similarity": 0.85,
      "matched_text": "...",
      "start_word": 0,
      "end_word": 4
    }
  ],
  "sliding_window_results": null
}
```

When using sliding window (method="sliding_window"):
```json
{
  "method": "sliding_window",
  "count": 2,
  "exact_results": null,
  "fuzzy_results": null,
  "sliding_window_results": [
    {
      "start_surah": 55,
      "start_ayah": 1,
      "similarity": 92.5,
      "reference": "55:1-4",
      "verses": [...]
    }
  ]
}
```

When no results found (method="none"):
```json
{
  "method": "none",
  "count": 0,
  "exact_results": null,
  "fuzzy_results": null,
  "sliding_window_results": null
}
```

**Search Strategy:**
1. **Exact**: Tries exact text search first (fastest)
2. **Fuzzy**: Falls back to fuzzy search if no exact matches
3. **Sliding Window**: Falls back to multi-ayah search if fuzzy fails
4. **None**: Returns empty if all methods fail

**Features:**
- Automatic method selection for optimal results
- Single endpoint for all search types
- Transparent about which method was used
- Separate threshold controls for each method
- Type-safe results based on method

### Database Statistics

**GET /stats**

Get statistics about the Quran database.

```bash
curl http://127.0.0.1:8000/stats
```

Response:
```json
{
  "total_surahs": 114,
  "total_verses": 6348,
  "source": "Tanzil.net",
  "version": "0.0.1"
}
```

### Health Check

**GET /health**

Check if the API is running.

```bash
curl http://127.0.0.1:8000/health
```

Response:
```json
{
  "status": "healthy",
  "version": "0.0.1"
}
```

## Error Responses

All endpoints return appropriate HTTP status codes:
- `200 OK`: Success
- `404 Not Found`: Verse or surah not found
- `422 Unprocessable Entity`: Invalid parameters
- `500 Internal Server Error`: Server error

Error response format:
```json
{
  "detail": "Error message describing what went wrong"
}
```

## Usage Examples

### Python with requests

```python
import requests

# Get a verse
response = requests.get("http://127.0.0.1:8000/verses/1/1")
verse = response.json()
print(verse["text"])

# Search for text
response = requests.get(
    "http://127.0.0.1:8000/search",
    params={"query": "الله", "limit": 5}
)
results = response.json()
print(f"Found {len(results)} verses")

# Fuzzy search
response = requests.get(
    "http://127.0.0.1:8000/fuzzy-search",
    params={"query": "بسم الله", "threshold": 0.8}
)
fuzzy_results = response.json()
for result in fuzzy_results:
    print(f"Similarity: {result['similarity']}")

# Sliding window search (multi-ayah)
response = requests.get(
    "http://127.0.0.1:8000/sliding-window",
    params={
        "query": "الرحمن علم القران خلق الانسان",
        "threshold": 80.0,
        "limit": 5
    }
)
sliding_results = response.json()
for result in sliding_results:
    print(f"Reference: {result['reference']}, Similarity: {result['similarity']:.1f}%")

# Smart search (automatic method selection)
response = requests.get(
    "http://127.0.0.1:8000/smart-search",
    params={
        "query": "الرحمن الرحيم",
        "fuzzy_threshold": 0.8,
        "sliding_threshold": 85.0
    }
)
smart_result = response.json()
print(f"Used {smart_result['method']} search, found {smart_result['count']} results")

# Access results based on method
if smart_result['method'] == 'exact':
    for verse in smart_result['exact_results'][:3]:
        print(verse['text'])
elif smart_result['method'] == 'fuzzy':
    for match in smart_result['fuzzy_results'][:3]:
        print(f"Similarity: {match['similarity']}")
elif smart_result['method'] == 'sliding_window':
    for match in smart_result['sliding_window_results'][:3]:
        print(f"Reference: {match['reference']}")
```

### JavaScript/TypeScript

```javascript
// Fetch a verse
const response = await fetch('http://127.0.0.1:8000/verses/1/1');
const verse = await response.json();
console.log(verse.text);

// Search with parameters
const searchParams = new URLSearchParams({
  query: 'الله',
  limit: '5'
});
const searchResponse = await fetch(`http://127.0.0.1:8000/search?${searchParams}`);
const results = await searchResponse.json();

// Sliding window search
const slidingParams = new URLSearchParams({
  query: 'الرحمن علم القران خلق الانسان',
  threshold: '80.0',
  limit: '5'
});
const slidingResponse = await fetch(`http://127.0.0.1:8000/sliding-window?${slidingParams}`);
const slidingResults = await slidingResponse.json();
console.log(`Found ${slidingResults.length} multi-ayah matches`);

// Smart search
const smartParams = new URLSearchParams({
  query: 'الرحمن الرحيم',
  fuzzy_threshold: '0.8',
  sliding_threshold: '85.0'
});
const smartResponse = await fetch(`http://127.0.0.1:8000/smart-search?${smartParams}`);
const smartResult = await smartResponse.json();
console.log(`Used ${smartResult.method} search, found ${smartResult.count} results`);
```

## API Features

- ✅ **Automatic Documentation**: Swagger UI and ReDoc interfaces
- ✅ **Type Validation**: Pydantic models ensure data integrity
- ✅ **Error Handling**: Comprehensive error messages
- ✅ **CORS Ready**: Can be configured for web applications
- ✅ **Async Support**: Built on FastAPI for high performance
- ✅ **OpenAPI Standard**: Standard API specification format

## Version Information

For the latest API updates, check the [changelog](../CHANGELOG.md).