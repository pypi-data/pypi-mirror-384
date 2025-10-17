"""
Data models for Quran verses and related structures.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional


@dataclass
class QuranVerse:
    """
    Represents a single verse from the Quran.
    
    Attributes:
        surah_number (int): The surah number (1-114)
        ayah_number (int): The ayah number within the surah (0 for Basmala, 1+ for regular ayahs)
        text (str): The original Arabic text with all diacritics
        text_normalized (str): The normalized Arabic text without diacritics
        is_basmalah (bool): True if this is a Basmala verse (ayah_number = 0)
    """
    surah_number: int
    ayah_number: int
    text: str
    text_normalized: str
    is_basmalah: bool = False
    
    def __str__(self) -> str:
        verse_type = "Basmala" if self.is_basmalah else "Ayah"
        return f"{verse_type} {self.surah_number}:{self.ayah_number} - {self.text[:50]}..."
    
    def __repr__(self) -> str:
        return (f"QuranVerse(surah={self.surah_number}, ayah={self.ayah_number}, "
                f"text='{self.text[:30]}...', is_basmalah={self.is_basmalah})")


@dataclass
class FuzzySearchResult:
    """
    Represents a fuzzy search result with partial match information.
    
    Attributes:
        verse (QuranVerse): The matched verse
        start_word (int): Starting word index of the match (0-based)
        end_word (int): Ending word index of the match (exclusive)
        similarity (float): Similarity score (0.0-1.0)
        matched_text (str): The actual text segment that was matched
        query_text (str): The original query text used for matching
    """
    verse: 'QuranVerse'
    start_word: int
    end_word: int
    similarity: float
    matched_text: str
    query_text: str
    
    def __str__(self) -> str:
        verse_type = "Basmala" if self.verse.is_basmalah else "Ayah"
        return (f"{verse_type} {self.verse.surah_number}:{self.verse.ayah_number} "
                f"(similarity: {self.similarity:.3f}, words: {self.start_word}-{self.end_word}) - "
                f"{self.matched_text[:50]}...")
    
    def __repr__(self) -> str:
        return (f"FuzzySearchResult(verse={self.verse.surah_number}:{self.verse.ayah_number}, "
                f"similarity={self.similarity:.3f}, words={self.start_word}-{self.end_word})")


@dataclass
class MultiAyahMatch:
    """
    Represents a match that may span multiple ayahs using sliding window search.
    
    Attributes:
        verses (List[QuranVerse]): List of verses in the match (ordered)
        similarity (float): Similarity score (0.0-100.0)
        matched_text (str): The actual text segment that was matched
        query_text (str): The original query text used for matching
        start_surah (int): Starting surah number
        start_ayah (int): Starting ayah number
        start_word (int): Starting word index within the first ayah (0-based)
        end_surah (int): Ending surah number
        end_ayah (int): Ending ayah number
        end_word (int): Ending word index within the last ayah (exclusive)
    """
    verses: List['QuranVerse']
    similarity: float
    matched_text: str
    query_text: str
    start_surah: int
    start_ayah: int
    start_word: int
    end_surah: int
    end_ayah: int
    end_word: int
    
    def __str__(self) -> str:
        if len(self.verses) == 1:
            return (f"Surah {self.start_surah}:{self.start_ayah} "
                   f"(similarity: {self.similarity:.1f}, words: {self.start_word}-{self.end_word}) - "
                   f"{self.matched_text[:60]}...")
        else:
            return (f"Surah {self.start_surah}:{self.start_ayah} to {self.end_surah}:{self.end_ayah} "
                   f"(similarity: {self.similarity:.1f}, {len(self.verses)} ayahs) - "
                   f"{self.matched_text[:60]}...")
    
    def __repr__(self) -> str:
        return (f"MultiAyahMatch(start={self.start_surah}:{self.start_ayah}, "
                f"end={self.end_surah}:{self.end_ayah}, similarity={self.similarity:.1f})")
    
    def get_reference(self) -> str:
        """Get a human-readable reference string for this match."""
        if self.start_surah == self.end_surah and self.start_ayah == self.end_ayah:
            return f"{self.start_surah}:{self.start_ayah}"
        elif self.start_surah == self.end_surah:
            return f"{self.start_surah}:{self.start_ayah}-{self.end_ayah}"
        else:
            return f"{self.start_surah}:{self.start_ayah} - {self.end_surah}:{self.end_ayah}"


@dataclass
class QuranChapter:
    """
    Represents a Quran chapter (surah) with O(1) verse lookup.
    
    Attributes:
        number (int): The surah number (1-114)
        ayahs (Dict[int, QuranVerse]): Dictionary mapping ayah number to verse for O(1) lookup
    """
    number: int
    ayahs: Dict[int, QuranVerse] = field(default_factory=dict)
    
    def add_verse(self, verse: QuranVerse) -> None:
        """Add a verse to this chapter."""
        if verse.surah_number != self.number:
            raise ValueError(f"Verse surah number {verse.surah_number} doesn't match chapter number {self.number}")
        self.ayahs[verse.ayah_number] = verse
    
    def get_verse(self, ayah_number: int) -> QuranVerse:
        """Get a specific verse by ayah number (O(1) operation)."""
        if ayah_number not in self.ayahs:
            raise ValueError(f"Ayah {ayah_number} not found in surah {self.number}")
        return self.ayahs[ayah_number]
    
    def get_all_verses(self) -> List[QuranVerse]:
        """Get all verses in this chapter as a list, ordered by ayah number."""
        return [self.ayahs[ayah_num] for ayah_num in sorted(self.ayahs.keys())]
    
    def get_verse_count(self) -> int:
        """Get the total number of verses in this chapter."""
        return len(self.ayahs)
    
    def has_basmala(self) -> bool:
        """Check if this chapter has a Basmala (ayah 0)."""
        return 0 in self.ayahs and self.ayahs[0].is_basmalah
    
    def __len__(self) -> int:
        return len(self.ayahs)
    
    def __contains__(self, ayah_number: int) -> bool:
        return ayah_number in self.ayahs
    
    def __getitem__(self, ayah_number: int) -> QuranVerse:
        return self.get_verse(ayah_number)
    
    def __str__(self) -> str:
        return f"Surah {self.number} ({len(self.ayahs)} verses)"
    
    def __repr__(self) -> str:
        return f"QuranChapter(number={self.number}, verse_count={len(self.ayahs)})"


@dataclass
class QuranDatabase:
    """
    Contains all Quran chapters and provides efficient O(1) lookup functionality.
    
    Attributes:
        surahs (Dict[int, QuranChapter]): Dictionary mapping surah number to chapter for O(1) lookup
        total_verses (int): Total number of verses (including Basmalas)
        total_surahs (int): Total number of surahs (114)
    """
    surahs: Dict[int, QuranChapter] = field(default_factory=dict)
    total_verses: int = 0
    total_surahs: int = 114
    
    def add_verse(self, verse: QuranVerse) -> None:
        """Add a verse to the database, creating chapter if needed."""
        if verse.surah_number not in self.surahs:
            self.surahs[verse.surah_number] = QuranChapter(number=verse.surah_number)
        
        self.surahs[verse.surah_number].add_verse(verse)
        self.total_verses += 1
    
    def get_verse(self, surah_number: int, ayah_number: int) -> QuranVerse:
        """Get a specific verse by surah and ayah number (O(1) operation)."""
        if surah_number not in self.surahs:
            raise ValueError(f"Surah {surah_number} not found")
        return self.surahs[surah_number].get_verse(ayah_number)
    
    def get_surah(self, surah_number: int) -> QuranChapter:
        """Get a specific surah/chapter (O(1) operation)."""
        if surah_number not in self.surahs:
            raise ValueError(f"Surah {surah_number} not found")
        return self.surahs[surah_number]
    
    def get_surah_verses(self, surah_number: int) -> List[QuranVerse]:
        """Get all verses for a specific surah."""
        return self.get_surah(surah_number).get_all_verses()
    
    def get_all_verses(self) -> List[QuranVerse]:
        """Get all verses in the database as a list, ordered by surah and ayah number."""
        all_verses = []
        for surah_num in sorted(self.surahs.keys()):
            all_verses.extend(self.surahs[surah_num].get_all_verses())
        return all_verses
    
    def search_text(self, query: str, normalized: bool = True) -> List[QuranVerse]:
        """
        Search for verses containing the query text.
        
        Args:
            query: Text to search for
            normalized: Whether to search in normalized text (default: True)
        
        Returns:
            List of matching verses
        """
        results = []
        for surah in self.surahs.values():
            for verse in surah.get_all_verses():
                search_text = verse.text_normalized if normalized else verse.text
                if query in search_text:
                    results.append(verse)
        return results
    
    def fuzzy_search(self, query: str, threshold: float = 0.7, normalized: bool = True, 
                    max_results: Optional[int] = None) -> List['FuzzySearchResult']:
        """
        Perform fuzzy search with partial text matching across all verses.
        
        Args:
            query: Text to search for
            threshold: Minimum similarity score (0.0-1.0)
            normalized: Whether to search in normalized text (default: True)
            max_results: Maximum number of results to return (None for no limit)
        
        Returns:
            List of FuzzySearchResult objects sorted by similarity score
        """
        from .text_utils import fuzzy_search_text
        
        all_verses = self.get_all_verses()
        return fuzzy_search_text(query, all_verses, threshold, normalized, max_results)
    
    def get_surah_count(self) -> int:
        """Get the total number of surahs in the database."""
        return len(self.surahs)
    
    def __len__(self) -> int:
        return self.total_verses
    
    def __contains__(self, surah_number: int) -> bool:
        return surah_number in self.surahs
    
    def __getitem__(self, surah_number: int) -> QuranChapter:
        return self.get_surah(surah_number)
    
    def __str__(self) -> str:
        return f"Quran Database ({self.total_surahs} surahs, {self.total_verses} verses)"
    
    def __repr__(self) -> str:
        return f"QuranDatabase(surahs={self.get_surah_count()}, verses={self.total_verses})"
    
    @property
    def verses(self) -> List[QuranVerse]:
        """Backward compatibility property to get all verses as a list."""
        return self.get_all_verses()