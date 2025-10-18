# Installation Guide

## Requirements

- Python 3.8 or higher
- pip package manager

## Installation Methods

### From PyPI (Recommended)

```bash
pip install quran-ayah-lookup
```

### From Source

1. Clone the repository:
```bash
git clone https://github.com/sayedmahmoud266/quran-ayah-lookup.git
cd quran-ayah-lookup
```

2. Install the package:
```bash
pip install -e .
```

### Development Installation

For development, install with development dependencies:

```bash
git clone https://github.com/sayedmahmoud266/quran-ayah-lookup.git
cd quran-ayah-lookup
pip install -e ".[dev]"
```

Or using requirements files:
```bash
pip install -r requirements-dev.txt
```

## Verification

Verify the installation:

```python
import quran_ayah_lookup as qal

# Check version
print(qal.__version__)

# Test database loading
db = qal.get_quran_database()
print(f"Database loaded: {len(db)} verses")

# Test O(1) lookup
verse = qal.get_verse(1, 1)  # Al-Fatihah, first verse
print(f"First verse: {verse.text[:30]}...")

# Test direct access
verse = db[2][255]  # Al-Baqarah, Ayat al-Kursi
print("O(1) access working!")
```

Expected output:
```
✓ Quran database loaded successfully:
  - Total verses: 6348
  - Total surahs: 114
  - Source: Tanzil.net
0.0.1
Database loaded: 6348 verses
First verse: بِسْمِ ٱللَّهِ ٱلرَّحْمَـٰنِ ٱلرَّحِيمِ...
O(1) access working!
```

## Performance Test

Test the O(1) lookup performance:

```python
import quran_ayah_lookup as qal
import time

db = qal.get_quran_database()

# Performance test
start = time.time()
for i in range(1000):
    verse = db[2][255]  # Al-Baqarah, Ayat al-Kursi
o1_time = time.time() - start

print(f"O(1) lookup (1000x): {o1_time:.4f}s")
print("Expected: ~0.0006s (956x faster than linear search!)")
```

## Troubleshooting

### Common Issues

1. **Permission Errors**: Use `pip install --user` if you encounter permission issues
2. **Python Version**: Ensure you're using Python 3.8 or higher  
3. **Virtual Environment**: Consider using a virtual environment for isolation
4. **Memory**: Package loads 6,348 verses at startup (~2MB memory usage)

### Virtual Environment Setup

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install quran-ayah-lookup
```

### Development Environment

For contributing or development:

```bash
git clone https://github.com/sayedmahmoud266/quran-ayah-lookup.git
cd quran-ayah-lookup
make setup-dev          # Complete development setup (init + install-deps-dev)
make test               # Run tests (should show 34/34 passing)
```

For individual commands, use:
```bash
make help               # Show all available commands
make init               # Initialize virtual environment
make install-deps-dev   # Install development dependencies  
make test-coverage      # Run tests with coverage report
make format             # Format code with black
make lint               # Lint code with flake8
make typecheck          # Type check with mypy
make check              # Run all checks
```