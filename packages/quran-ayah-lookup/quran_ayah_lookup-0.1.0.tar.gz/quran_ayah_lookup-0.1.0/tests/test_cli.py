"""
Unit tests for the CLI module.
"""
import pytest
from click.testing import CliRunner
from quran_ayah_lookup.cli import cli


@pytest.fixture
def runner():
    """Fixture to create a CLI runner."""
    return CliRunner()


class TestVerseCommand:
    """Tests for the 'verse' command."""
    
    def test_get_verse_basic(self, runner):
        """Test basic verse retrieval."""
        result = runner.invoke(cli, ["verse", "1", "1"])
        assert result.exit_code == 0
        assert "Ayah 1:1" in result.output
        assert "بِسْمِ" in result.output
    
    def test_get_verse_basmala(self, runner):
        """Test Basmala retrieval (ayah 0)."""
        result = runner.invoke(cli, ["verse", "2", "0"])
        assert result.exit_code == 0
        assert "Basmala 2:0" in result.output
    
    def test_get_verse_normalized(self, runner):
        """Test verse with normalized flag."""
        result = runner.invoke(cli, ["verse", "1", "1", "--normalized"])
        assert result.exit_code == 0
        assert "Normalized:" in result.output
    
    def test_get_verse_original(self, runner):
        """Test verse with original flag."""
        result = runner.invoke(cli, ["verse", "1", "1", "--original"])
        assert result.exit_code == 0
        assert "Original:" in result.output
    
    def test_get_verse_invalid_surah(self, runner):
        """Test error handling for invalid surah."""
        result = runner.invoke(cli, ["verse", "115", "1"])
        assert result.exit_code == 1
        assert "Error:" in result.output
    
    def test_get_verse_invalid_ayah(self, runner):
        """Test error handling for invalid ayah."""
        result = runner.invoke(cli, ["verse", "1", "100"])
        assert result.exit_code == 1
        assert "Error:" in result.output


class TestSurahCommand:
    """Tests for the 'surah' command."""
    
    def test_get_surah_basic(self, runner):
        """Test basic surah information."""
        result = runner.invoke(cli, ["surah", "1"])
        assert result.exit_code == 0
        assert "Surah 1" in result.output
        assert "Total verses:" in result.output
    
    def test_get_surah_count(self, runner):
        """Test surah verse count."""
        result = runner.invoke(cli, ["surah", "1", "--count"])
        assert result.exit_code == 0
        assert "has" in result.output
        assert "verses" in result.output
    
    def test_get_surah_list(self, runner):
        """Test listing all verses in a surah."""
        result = runner.invoke(cli, ["surah", "1", "--list"])
        assert result.exit_code == 0
        assert "All Verses:" in result.output
        assert "Ayah 1:1" in result.output
    
    def test_get_surah_invalid(self, runner):
        """Test error handling for invalid surah."""
        result = runner.invoke(cli, ["surah", "115"])
        assert result.exit_code == 1
        assert "Error:" in result.output


class TestSearchCommand:
    """Tests for the 'search' command."""
    
    def test_search_basic(self, runner):
        """Test basic text search."""
        result = runner.invoke(cli, ["search", "الله"])
        assert result.exit_code == 0
        assert "Found" in result.output
        assert "verse(s)" in result.output
    
    def test_search_with_limit(self, runner):
        """Test search with result limit."""
        result = runner.invoke(cli, ["search", "الله", "--limit", "5"])
        assert result.exit_code == 0
        assert "Found" in result.output
    
    def test_search_no_results(self, runner):
        """Test search with no matches."""
        result = runner.invoke(cli, ["search", "xyz123abc"])
        assert result.exit_code == 0
        assert "No verses found" in result.output
    
    def test_search_original_text(self, runner):
        """Test search in original text."""
        result = runner.invoke(cli, ["search", "بِسْمِ", "--original"])
        assert result.exit_code == 0
        assert "Found" in result.output
    
    def test_search_normalized_text(self, runner):
        """Test search in normalized text."""
        result = runner.invoke(cli, ["search", "بسم", "--normalized"])
        assert result.exit_code == 0
        assert "Found" in result.output


class TestFuzzySearchCommand:
    """Tests for the 'fuzzy' command."""
    
    def test_fuzzy_search_basic(self, runner):
        """Test basic fuzzy search."""
        result = runner.invoke(cli, ["fuzzy", "بسم الله"])
        assert result.exit_code == 0
        assert "Found" in result.output
        assert "fuzzy match(es)" in result.output
    
    def test_fuzzy_search_with_threshold(self, runner):
        """Test fuzzy search with custom threshold."""
        result = runner.invoke(cli, ["fuzzy", "بسم الله", "--threshold", "0.9"])
        assert result.exit_code == 0
        assert "threshold: 0.9" in result.output
    
    def test_fuzzy_search_with_limit(self, runner):
        """Test fuzzy search with result limit."""
        result = runner.invoke(cli, ["fuzzy", "الله", "--limit", "3"])
        assert result.exit_code == 0
    
    def test_fuzzy_search_invalid_threshold_low(self, runner):
        """Test error handling for threshold below 0.0."""
        result = runner.invoke(cli, ["fuzzy", "الله", "--threshold", "-0.1"])
        assert result.exit_code == 1
        assert "Error:" in result.output
    
    def test_fuzzy_search_invalid_threshold_high(self, runner):
        """Test error handling for threshold above 1.0."""
        result = runner.invoke(cli, ["fuzzy", "الله", "--threshold", "1.5"])
        assert result.exit_code == 1
        assert "Error:" in result.output
    
    def test_fuzzy_search_similarity_display(self, runner):
        """Test that similarity scores are displayed."""
        result = runner.invoke(cli, ["fuzzy", "بسم الله", "--limit", "1"])
        assert result.exit_code == 0
        assert "Similarity:" in result.output
        assert "Words:" in result.output
        assert "Matched text:" in result.output


class TestListVersesCommand:
    """Tests for the 'list-verses' command."""
    
    def test_list_verses_basic(self, runner):
        """Test listing all verses in a surah."""
        result = runner.invoke(cli, ["list-verses", "1"])
        assert result.exit_code == 0
        assert "Surah 1" in result.output
        assert "verse(s):" in result.output
    
    def test_list_verses_invalid_surah(self, runner):
        """Test error handling for invalid surah."""
        result = runner.invoke(cli, ["list-verses", "115"])
        assert result.exit_code == 1
        assert "Error:" in result.output
    
    def test_list_verses_includes_basmala(self, runner):
        """Test that Basmala is included when present."""
        result = runner.invoke(cli, ["list-verses", "2"])
        assert result.exit_code == 0
        assert "Basmala 2:0" in result.output


class TestStatsCommand:
    """Tests for the 'stats' command."""
    
    def test_stats_display(self, runner):
        """Test database statistics display."""
        result = runner.invoke(cli, ["stats"])
        assert result.exit_code == 0
        assert "Quran Database Statistics" in result.output
        assert "Total surahs:" in result.output
        assert "Total verses:" in result.output
        assert "114" in result.output  # Number of surahs
        assert "Tanzil.net" in result.output


class TestVersionCommand:
    """Tests for the version command."""
    
    def test_version_display(self, runner):
        """Test version display."""
        result = runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert "version" in result.output.lower()


class TestHelpCommand:
    """Tests for the help command."""
    
    def test_main_help(self, runner):
        """Test main help display."""
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "Quran Ayah Lookup CLI" in result.output
        assert "verse" in result.output
        assert "surah" in result.output
        assert "search" in result.output
        assert "fuzzy" in result.output
    
    def test_verse_help(self, runner):
        """Test verse command help."""
        result = runner.invoke(cli, ["verse", "--help"])
        assert result.exit_code == 0
        assert "Get a specific verse" in result.output
    
    def test_search_help(self, runner):
        """Test search command help."""
        result = runner.invoke(cli, ["search", "--help"])
        assert result.exit_code == 0
        assert "Search for verses" in result.output


class TestREPLMode:
    """Tests for REPL mode."""
    
    def test_repl_verse_command(self, runner):
        """Test verse command in REPL mode."""
        result = runner.invoke(cli, [], input="verse 1 1\nexit\n")
        assert result.exit_code == 0
        assert "Interactive REPL Mode" in result.output
        assert "Ayah 1:1" in result.output
    
    def test_repl_surah_command(self, runner):
        """Test surah command in REPL mode."""
        result = runner.invoke(cli, [], input="surah 1\nexit\n")
        assert result.exit_code == 0
        assert "Surah 1" in result.output
        assert "Total verses:" in result.output
    
    def test_repl_search_command(self, runner):
        """Test search command in REPL mode."""
        result = runner.invoke(cli, [], input="search الله\nexit\n")
        assert result.exit_code == 0
        assert "Found" in result.output
    
    def test_repl_fuzzy_command(self, runner):
        """Test fuzzy command in REPL mode."""
        result = runner.invoke(cli, [], input="fuzzy بسم الله\nexit\n")
        assert result.exit_code == 0
        assert "Found" in result.output
    
    def test_repl_stats_command(self, runner):
        """Test stats command in REPL mode."""
        result = runner.invoke(cli, [], input="stats\nexit\n")
        assert result.exit_code == 0
        assert "Total surahs:" in result.output
    
    def test_repl_quit_command(self, runner):
        """Test quit command in REPL mode."""
        result = runner.invoke(cli, [], input="quit\n")
        assert result.exit_code == 0
        assert "Goodbye!" in result.output
    
    def test_repl_help_command(self, runner):
        """Test help command in REPL mode."""
        result = runner.invoke(cli, [], input="help\nexit\n")
        assert result.exit_code == 0
        assert "Commands:" in result.output
    
    def test_repl_invalid_command(self, runner):
        """Test invalid command in REPL mode."""
        result = runner.invoke(cli, [], input="invalid_cmd\nexit\n")
        assert result.exit_code == 0
        assert "Unknown command" in result.output
    
    def test_repl_empty_input(self, runner):
        """Test empty input in REPL mode."""
        result = runner.invoke(cli, [], input="\n\nexit\n")
        assert result.exit_code == 0
    
    def test_repl_error_handling(self, runner):
        """Test error handling in REPL mode."""
        result = runner.invoke(cli, [], input="verse 115 1\nexit\n")
        assert result.exit_code == 0
        assert "Error:" in result.output
        assert "Goodbye!" in result.output  # Should continue after error


class TestIntegration:
    """Integration tests for CLI."""
    
    def test_verse_to_search_workflow(self, runner):
        """Test workflow from verse lookup to search."""
        # Get a verse
        result1 = runner.invoke(cli, ["verse", "1", "1"])
        assert result1.exit_code == 0
        
        # Search for text from that verse
        result2 = runner.invoke(cli, ["search", "بسم"])
        assert result2.exit_code == 0
        assert "Found" in result2.output
    
    def test_surah_info_to_list_workflow(self, runner):
        """Test workflow from surah info to listing verses."""
        # Get surah info
        result1 = runner.invoke(cli, ["surah", "1"])
        assert result1.exit_code == 0
        
        # List all verses
        result2 = runner.invoke(cli, ["list-verses", "1"])
        assert result2.exit_code == 0
    
    def test_multiple_commands_in_sequence(self, runner):
        """Test multiple commands work correctly in sequence."""
        commands = [
            ["verse", "1", "1"],
            ["surah", "1"],
            ["search", "الله"],
            ["stats"],
        ]
        
        for cmd in commands:
            result = runner.invoke(cli, cmd)
            assert result.exit_code == 0
