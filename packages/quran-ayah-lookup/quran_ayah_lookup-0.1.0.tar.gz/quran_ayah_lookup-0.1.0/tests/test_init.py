"""
Basic tests for package initialization and core functionality
"""
import pytest
from quran_ayah_lookup import __version__, __author__, __email__
from quran_ayah_lookup import get_verse, get_surah, search_text, get_surah_verses
from quran_ayah_lookup.models import QuranVerse, QuranChapter


def test_package_metadata():
    """Test that package metadata is correctly set."""
    assert __version__ is not None
    assert __author__ == "Sayed Mahmoud"
    assert __email__ == "foss-support@sayedmahmoud266.website"


def test_package_import():
    """Test that the package can be imported successfully."""
    import quran_ayah_lookup
    assert quran_ayah_lookup is not None


def test_package_has_all_attribute():
    """Test that __all__ attribute exists."""
    import quran_ayah_lookup
    assert hasattr(quran_ayah_lookup, '__all__')
    assert isinstance(quran_ayah_lookup.__all__, list)


def test_get_verse_al_fatihah():
    """Test getting verse from Al-Fatihah (no Basmala extraction)."""
    verse = get_verse(1, 1)
    assert isinstance(verse, QuranVerse)
    assert verse.surah_number == 1
    assert verse.ayah_number == 1
    assert verse.text.startswith("بِسْمِ")  # Starts with "Bismillah"
    assert len(verse.text) > 30  # Reasonable length for full Basmala
    assert not verse.is_basmalah


def test_get_basmala_from_other_surah():
    """Test getting Basmala from a surah other than Al-Fatihah and At-Tawbah."""
    # Try to get Basmala from Al-Baqarah (should be ayah 0)
    basmala = get_verse(2, 0)
    assert isinstance(basmala, QuranVerse)
    assert basmala.surah_number == 2
    assert basmala.ayah_number == 0
    assert basmala.is_basmalah
    # Check that it's the standard Basmala
    assert basmala.text.startswith("بِسْمِ")
    assert "ح" in basmala.text and "ي" in basmala.text and "م" in basmala.text  # Contains letters from "Raheem"
    assert len(basmala.text) > 30  # Reasonable length


def test_get_verse_after_basmala_extraction():
    """Test getting first verse after Basmala extraction."""
    verse = get_verse(2, 1)
    assert isinstance(verse, QuranVerse)
    assert verse.surah_number == 2
    assert verse.ayah_number == 1
    assert not verse.is_basmalah
    # Should contain "الٓمٓ" but not the full Basmala
    assert "الٓمٓ" in verse.text
    assert not verse.text.startswith("بِسْمِ ٱللَّهِ")


def test_at_tawbah_no_basmala():
    """Test that At-Tawbah (Surah 9) has no Basmala."""
    verse = get_verse(9, 1)
    assert isinstance(verse, QuranVerse)
    assert verse.surah_number == 9
    assert verse.ayah_number == 1
    assert not verse.is_basmalah
    # Check that it starts with the first word of At-Tawbah
    assert verse.text.startswith("بَرَا")  # First part of "Bara'atun"
    assert not verse.text.startswith("بِسْمِ")  # Should not start with Basmala
    
    # Try to get Basmala from At-Tawbah (should raise ValueError)
    with pytest.raises(ValueError):
        get_verse(9, 0)


def test_search_text():
    """Test text search functionality."""
    results = search_text("الله")
    assert isinstance(results, list)
    assert len(results) > 0
    assert all(isinstance(verse, QuranVerse) for verse in results)


def test_get_surah_verses():
    """Test getting all verses from a surah."""
    verses = get_surah_verses(1)  # Al-Fatihah
    assert isinstance(verses, list)
    assert len(verses) == 7  # Al-Fatihah has 7 verses
    assert all(isinstance(verse, QuranVerse) for verse in verses)
    assert all(verse.surah_number == 1 for verse in verses)


def test_get_surah_chapter():
    """Test getting a surah as QuranChapter object."""
    surah = get_surah(3)  # Al-Imran
    assert isinstance(surah, QuranChapter)
    assert surah.number == 3
    assert len(surah) > 0  # Should have verses
    
    # Test O(1) access
    verse_35 = surah[35]  # Get verse 35 directly
    assert isinstance(verse_35, QuranVerse)
    assert verse_35.surah_number == 3
    assert verse_35.ayah_number == 35
    
    # Test getting all verses
    all_verses = surah.get_all_verses()
    assert isinstance(all_verses, list)
    assert len(all_verses) == len(surah)
    
    # Test contains check
    assert 35 in surah
    assert 999 not in surah


def test_surah_with_basmala():
    """Test that surahs (except Al-Fatihah and At-Tawbah) have Basmala."""
    surah = get_surah(2)  # Al-Baqarah
    assert surah.has_basmala()
    
    # Get Basmala (ayah 0)
    basmala = surah[0]
    assert basmala.is_basmalah
    assert basmala.ayah_number == 0
    
    # Get first real ayah
    first_ayah = surah[1]
    assert not first_ayah.is_basmalah
    assert first_ayah.ayah_number == 1


def test_surah_without_basmala():
    """Test that At-Tawbah doesn't have Basmala."""
    surah = get_surah(9)  # At-Tawbah
    assert not surah.has_basmala()
    assert 0 not in surah  # No ayah 0 (Basmala)
    
    # First ayah should be 1
    first_ayah = surah[1]
    assert first_ayah.ayah_number == 1
    assert not first_ayah.is_basmalah


def test_database_o1_lookup():
    """Test O(1) lookup using database[surah][ayah] syntax."""
    from quran_ayah_lookup import get_quran_database
    
    db = get_quran_database()
    
    # Test db[surah][ayah] syntax
    verse = db[3][35]  # Surah 3, Ayah 35
    assert isinstance(verse, QuranVerse)
    assert verse.surah_number == 3
    assert verse.ayah_number == 35
    
    # Test surah exists
    assert 3 in db
    assert 999 not in db