# Quick Start Guide

## Basic Usage

The Quran database loads automatically when you import the package:

```python
import quran_ayah_lookup as qal

# Database loads automatically on import
# ✓ Quran database loaded successfully:
#   - Total verses: 6348  
#   - Total surahs: 114
#   - Source: Tanzil.net
```

## O(1) Verse Lookup

### Direct Database Access (Fastest)

```python
# Get database instance
db = qal.get_quran_database()

# O(1) direct access: db[surah][ayah]
verse = db[3][35]  # Surah Al-Imran, Ayah 35
print(verse.text)  # Original Arabic with diacritics
print(verse.text_normalized)  # Normalized Arabic without diacritics
```

### Using Convenience Functions

```python
# Alternative syntax (also O(1))
verse = qal.get_verse(3, 35)  # Surah 3, Ayah 35
print(f"Surah: {verse.surah_number}, Ayah: {verse.ayah_number}")
print(f"Is Basmala: {verse.is_basmalah}")
```

## Working with Surahs/Chapters

### Get Entire Surah

```python
# Get a surah/chapter with O(1) verse access
surah = qal.get_surah(3)  # Al-Imran
print(f"Surah {surah.number} has {len(surah)} verses")

# Access verses within surah (O(1))
basmala = surah[0]        # Basmala (ayah 0)
first_ayah = surah[1]     # First regular ayah
verse_35 = surah[35]      # Any specific ayah

# Check if verse exists (O(1))
if 35 in surah:
    verse = surah[35]
    
# Get all verses as a list
all_verses = surah.get_all_verses()
print(f"Retrieved {len(all_verses)} verses")
```

### Surah Information

```python
surah = qal.get_surah(2)  # Al-Baqarah
print(f"Has Basmala: {surah.has_basmala()}")
print(f"Verse count: {surah.get_verse_count()}")

# At-Tawbah (special case - no Basmala)
tawbah = qal.get_surah(9)
print(f"At-Tawbah has Basmala: {tawbah.has_basmala()}")  # False
```

## Text Search

### Basic Arabic Text Search

```python
# Search across all verses
results = qal.search_text("الله")
print(f"Found {len(results)} verses containing 'الله'")

for verse in results[:5]:  # Show first 5 results
    print(f"Surah {verse.surah_number}:{verse.ayah_number} - {verse.text[:50]}...")
```

### Normalized vs Original Text Search

```python
# Search in normalized text (recommended - default)
results = qal.search_text("الله", normalized=True)

# Search in original text with diacritics
results = qal.search_text("ٱللَّهِ", normalized=False)
```

## Fuzzy Search

### Partial Ayah Detection

```python
# Find verses containing partial text (even if not exact match)
query = "كذلك يجتبيك ربك ويعلمك من تأويل الأحاديث"
results = qal.fuzzy_search(query, threshold=0.8)

print(f"Found {len(results)} fuzzy matches")
for result in results[:3]:
    print(f"Surah {result.verse.surah_number}:{result.verse.ayah_number}")
    print(f"Similarity: {result.similarity:.3f}")
    print(f"Words {result.start_word}-{result.end_word}: {result.matched_text[:60]}...")
```

### Finding Repeated Phrases

```python
# Find all occurrences of repeated phrases
repeated_phrase = "فبأي الاء ربكما تكذبان"  # From Surah Ar-Rahman
results = qal.fuzzy_search(repeated_phrase, threshold=0.9)

print(f"Found {len(results)} occurrences of this phrase:")
for result in results[:10]:
    print(f"  Surah {result.verse.surah_number}:{result.verse.ayah_number} (similarity: {result.similarity:.3f})")

# Another repeated phrase example
another_phrase = "ومن اظلم ممن افترى على الله كذبا"
results = qal.fuzzy_search(another_phrase, threshold=0.85)
print(f"Found {len(results)} matches for 'Who is more unjust' phrase")
```

### Configurable Similarity

```python
# High precision search (strict matching)
precise_results = qal.fuzzy_search("الحمد لله رب العالمين", threshold=0.95)

# Lower precision (more matches, less strict)
broad_results = qal.fuzzy_search("الحمد لله رب العالمين", threshold=0.7)

print(f"Precise search: {len(precise_results)} results")
print(f"Broad search: {len(broad_results)} results")

# Limit number of results
top_results = qal.fuzzy_search("بسم الله", max_results=10)
```

### Advanced Fuzzy Search Features

```python
# Access detailed match information
results = qal.fuzzy_search("ويعلمك من تأويل الأحاديث")
for result in results[:2]:
    # Get the exact matched segment
    words = result.verse.text_normalized.split()
    matched_segment = " ".join(words[result.start_word:result.end_word])
    
    print(f"Query: {result.query_text}")
    print(f"Matched: {matched_segment}")
    print(f"Full verse: {result.verse.text}")
    print(f"Word positions: {result.start_word} to {result.end_word}")
    print("-" * 50)
```

## Multi-Ayah Sliding Window Search

### Searching Text Spanning Multiple Ayahs

```python
# Search for text that spans multiple consecutive ayahs
query = "الرحمن علم القران خلق الانسان علمه البيان"
results = qal.search_sliding_window(query, threshold=80.0)

print(f"Found {len(results)} multi-ayah matches")
for match in results[:3]:
    print(f"Reference: {match.get_reference()}")
    print(f"Similarity: {match.similarity:.1f}%")
    print(f"Spans {len(match.verses)} verses")
    
    # Show all verses in the match
    for verse in match.verses:
        print(f"  {verse.surah_number}:{verse.ayah_number} - {verse.text[:60]}...")
```

### Cross-Surah Matching

```python
# Find text that crosses surah boundaries
query = "بسم الله الرحمن الرحيم الحمد لله رب العالمين"
results = qal.search_sliding_window(query)

for match in results:
    if match.start_surah != match.end_surah:
        print(f"Cross-surah match: {match.get_reference()}")
        print(f"From Surah {match.start_surah} to Surah {match.end_surah}")
```

### Adjusting Precision

```python
# High precision (strict matching)
precise = qal.search_sliding_window(query, threshold=90.0)

# Lower precision (more matches)
broad = qal.search_sliding_window(query, threshold=75.0)

print(f"Precise search: {len(precise)} results")
print(f"Broad search: {len(broad)} results")
```

## Smart Search (Automatic Method Selection)

### Let the Package Choose the Best Method

```python
# Smart search automatically tries:
# 1. Exact text search (fastest)
# 2. Fuzzy search (if exact fails)
# 3. Sliding window (if fuzzy fails)

result = qal.smart_search("الرحمن الرحيم")
print(f"Used {result['method']} search")
print(f"Found {result['count']} results")

# Access results based on method
if result['method'] == 'exact':
    for verse in result['results']:
        print(f"{verse.surah_number}:{verse.ayah_number} - {verse.text}")
```

### Smart Search for Multi-Ayah Queries

```python
# Automatically uses sliding window for multi-ayah text
result = qal.smart_search("الرحمن علم القران خلق الانسان")

if result['method'] == 'sliding_window':
    print("Used sliding window search for multi-ayah query")
    for match in result['results']:
        print(f"{match.get_reference()}: {match.similarity}%")
```

### Custom Thresholds for Each Method

```python
# Configure thresholds for fuzzy and sliding window
result = qal.smart_search(
    "الحمد لله",
    threshold=0.8,              # Fuzzy search threshold (0.0-1.0)
    sliding_threshold=85.0,     # Sliding window threshold (0.0-100.0)
    max_results=10
)

# Check which method was used
methods = {
    'exact': 'Exact text match',
    'fuzzy': 'Fuzzy matching',
    'sliding_window': 'Multi-ayah sliding window',
    'none': 'No results found'
}
print(f"Method: {methods[result['method']]}")
```

## Text Normalization

### Arabic Text Processing

```python
# Normalize Arabic text (remove diacritics, normalize Alif)
original = "بِسْمِ ٱللَّهِ ٱلرَّحْمَـٰنِ ٱلرَّحِيمِ"
normalized = qal.normalize_arabic_text(original)
print(normalized)  # "بسم الله الرحمن الرحيم"
```

## Performance Examples

### Speed Comparison

```python
import time

# O(1) lookup timing
start = time.time()
for i in range(1000):
    verse = db[2][255]  # Al-Baqarah, Ayat al-Kursi
o1_time = time.time() - start

print(f"O(1) lookup (1000x): {o1_time:.4f}s")
# Result: ~0.0006s (956x faster than linear search!)
```

## Common Patterns

### Batch Operations

```python
# Get multiple verses efficiently
verses_to_fetch = [(1, 1), (2, 255), (3, 35), (9, 1)]
verses = [db[s][a] for s, a in verses_to_fetch]

# Process surah by surah
for surah_num in [1, 2, 3]:
    surah = qal.get_surah(surah_num)
    print(f"Processing {len(surah)} verses from surah {surah_num}")
```

### Error Handling

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

---

## REST API Usage

The package includes a REST API server for accessing all functionalities via HTTP endpoints.

### Starting the API Server

```bash
# Start server on default port (8000)
qal serve

# Custom port
qal serve --port 8080

# Make server publicly accessible
qal serve --host 0.0.0.0 --port 80

# Development mode with auto-reload
qal serve --reload
```

### Installation

Install API dependencies:

```bash
pip install "quran-ayah-lookup[api]"
```

Or install separately:

```bash
pip install fastapi uvicorn[standard]
```

### Accessing the API

Once started, the API is available at:
- **API Root**: `http://127.0.0.1:8000/`
- **Interactive Docs**: `http://127.0.0.1:8000/docs`
- **Alternative Docs**: `http://127.0.0.1:8000/redoc`

### Quick API Examples

#### Using cURL

```bash
# Get a verse
curl http://127.0.0.1:8000/verses/1/1

# Search for text (URL-encoded)
curl "http://127.0.0.1:8000/search?query=%D8%A7%D9%84%D9%84%D9%87&limit=5"

# Get database stats
curl http://127.0.0.1:8000/stats
```

#### Using Python requests

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
for result in response.json():
    print(f"Similarity: {result['similarity']:.2f}")

# Sliding window search
response = requests.get(
    "http://127.0.0.1:8000/sliding-window",
    params={"query": "الرحمن علم القران خلق الانسان", "threshold": 80.0}
)
for result in response.json():
    print(f"Reference: {result['reference']}, Similarity: {result['similarity']:.1f}%")

# Smart search (auto-selects method)
response = requests.get(
    "http://127.0.0.1:8000/smart-search",
    params={"query": "الرحمن الرحيم"}
)
data = response.json()
print(f"Used {data['method']} search, found {data['count']} results")
```

### Available Endpoints

- `GET /verses/{surah_number}/{ayah_number}` - Get specific verse
- `GET /surahs/{surah_number}` - Get surah information
- `GET /surahs/{surah_number}/verses` - Get all verses in surah
- `GET /search` - Search for verses containing text
- `GET /fuzzy-search` - Fuzzy search with similarity scoring
- `GET /sliding-window` - Multi-ayah sliding window search
- `GET /smart-search` - Smart search (auto-selects best method)
- `GET /stats` - Database statistics
- `GET /health` - Health check

For complete API documentation, see the [REST API Reference](api.md#rest-api-reference) or visit `/docs` when the server is running.

## Next Steps

1. Check out the [API Reference](api.md) for detailed documentation
2. Try the [REST API](api.md#rest-api-reference) for HTTP-based access
3. Read the [Contributing Guidelines](../CONTRIBUTING.md) if you want to contribute
4. Browse the source code on [GitHub](https://github.com/sayedmahmoud266/quran-ayah-lookup)