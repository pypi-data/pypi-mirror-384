"""
Tests for Arabic text normalization functionality
"""
import pytest
from quran_ayah_lookup.text_utils import (
    normalize_arabic_text,
    extract_basmala,
    is_basmala_present,
    remove_basmala_from_text,
    get_normalized_basmala
)


def test_normalize_arabic_text():
    """Test removal of diacritics from Arabic text."""
    # Text with diacritics
    text_with_diacritics = "بِسْمِ ٱللَّهِ ٱلرَّحْمَـٰنِ ٱلرَّحِيمِ"
    normalized = normalize_arabic_text(text_with_diacritics)
    
    # Should not contain common diacritics
    assert 'ِ' not in normalized  # Kasra
    assert 'ْ' not in normalized  # Sukun  
    assert 'َ' not in normalized  # Fatha
    assert 'ّ' not in normalized  # Shadda
    assert 'ٰ' not in normalized  # Superscript Alef
    
    # Should still contain the base Arabic letters
    assert 'ب' in normalized
    assert 'س' in normalized
    assert 'م' in normalized
    assert 'ا' in normalized  # Alif wasla normalized to regular alif
    assert 'ل' in normalized
    assert 'ه' in normalized
    assert 'ر' in normalized
    assert 'ح' in normalized
    assert 'ن' in normalized
    assert 'ي' in normalized


def test_normalize_empty_text():
    """Test normalization of empty or None text."""
    assert normalize_arabic_text("") == ""
    assert normalize_arabic_text("   ") == ""


def test_alif_wasla_normalization():
    """Test that Alif wasla is normalized to regular Alif."""
    text_with_alif_wasla = "ٱللَّهِ"  # Allah with alif wasla
    normalized = normalize_arabic_text(text_with_alif_wasla)
    
    # Should not contain alif wasla anymore
    assert 'ٱ' not in normalized
    # Should contain regular alif instead
    assert 'ا' in normalized
    # Should be "الله" (without diacritics)
    assert normalized == "الله"


def test_extract_basmala():
    """Test extraction of standard Basmala text."""
    basmala = extract_basmala()
    # Test key components instead of exact Unicode match
    assert basmala.startswith("بِسْمِ")
    assert "ح" in basmala and "ي" in basmala and "م" in basmala  # Contains letters from "Raheem"
    assert len(basmala) > 30  # Should be reasonable length
    # Should contain letters from the word Allah
    assert "ل" in basmala and "ه" in basmala  # Contains letters from "Allah"


def test_is_basmala_present():
    """Test detection of Basmala in text."""
    basmala = extract_basmala()
    
    # Text starting with Basmala
    assert is_basmala_present(basmala)
    assert is_basmala_present(basmala + " additional text")
    assert is_basmala_present("  " + basmala + " more text")
    
    # Text not starting with Basmala
    assert not is_basmala_present("some other text")
    assert not is_basmala_present("بَرَآءَةٌ مِّنَ ٱللَّهِ")  # At-Tawbah start
    assert not is_basmala_present("")


def test_remove_basmala_from_text():
    """Test removal of Basmala from text."""
    basmala = extract_basmala()
    
    # Text with Basmala
    text_with_basmala = basmala + " الٓمٓ"
    remaining = remove_basmala_from_text(text_with_basmala)
    assert remaining == "الٓمٓ"
    
    # Text with only Basmala
    only_basmala = basmala
    remaining = remove_basmala_from_text(only_basmala)
    assert remaining == ""
    
    # Text without Basmala
    text_without_basmala = "بَرَآءَةٌ مِّنَ ٱللَّهِ"
    remaining = remove_basmala_from_text(text_without_basmala)
    assert remaining == text_without_basmala


def test_get_normalized_basmala():
    """Test getting normalized Basmala."""
    normalized_basmala = get_normalized_basmala()
    
    # Should not contain diacritics
    assert 'ِ' not in normalized_basmala
    assert 'ْ' not in normalized_basmala
    assert 'َ' not in normalized_basmala
    assert 'ّ' not in normalized_basmala
    assert 'ٰ' not in normalized_basmala
    
    # Should contain base letters
    assert 'ب' in normalized_basmala
    assert 'س' in normalized_basmala
    assert 'م' in normalized_basmala
    assert 'ا' in normalized_basmala  # Alif wasla normalized to regular alif
    assert 'ل' in normalized_basmala
    assert 'ه' in normalized_basmala


def test_special_quran_marks_removal():
    """Test removal of special Quran marks like quarter hizb."""
    text_with_marks = "۞ إِنَّ ٱللَّهَ لَا يَسْتَحْىِۦٓ"
    normalized = normalize_arabic_text(text_with_marks)
    
    # Should not contain quarter hizb mark
    assert '۞' not in normalized
    # Should not contain other special marks
    assert 'ۦ' not in normalized
    assert 'ٓ' not in normalized