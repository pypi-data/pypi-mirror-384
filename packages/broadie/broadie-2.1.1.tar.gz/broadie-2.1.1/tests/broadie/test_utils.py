"""Unit tests for utility functions."""

from src.broadie.utils import slugify


class TestSlugify:
    """Tests for slugify function."""

    def test_slugify_lowercase(self):
        """Test slugify converts to lowercase."""
        assert slugify("FileManagerAgent") == "filemanageragent"

    def test_slugify_with_spaces(self):
        """Test slugify handles spaces."""
        assert slugify("File Manager Agent") == "file-manager-agent"

    def test_slugify_camelcase(self):
        """Test slugify handles CamelCase."""
        result = slugify("FileManagerAgent")
        assert result == "filemanageragent"

    def test_slugify_special_characters(self):
        """Test slugify removes special characters."""
        assert slugify("File@Manager#Agent!") == "file-manager-agent"

    def test_slugify_leading_trailing_spaces(self):
        """Test slugify strips leading/trailing spaces."""
        assert slugify("  File Manager  ") == "file-manager"

    def test_slugify_multiple_dashes(self):
        """Test slugify consolidates multiple dashes."""
        assert slugify("File---Manager") == "file-manager"

    def test_slugify_numbers(self):
        """Test slugify preserves numbers."""
        assert slugify("Agent123") == "agent123"

    def test_slugify_empty_string(self):
        """Test slugify handles empty strings."""
        result = slugify("")
        # Should return a UUID since empty string results in empty slug
        assert len(result) > 0

    def test_slugify_unicode(self):
        """Test slugify handles unicode characters."""
        result = slugify("Agént Mañager")
        # Non-ASCII characters should be removed/replaced
        assert "ag" in result.lower()

    def test_slugify_only_special_chars(self):
        """Test slugify handles string with only special characters."""
        result = slugify("@#$%^&*()")
        # Should return a UUID since all chars are removed
        assert len(result) > 0


class TestSlugifyAgentNames:
    """Test slugify with actual agent names used in examples."""

    def test_slugify_file_manager_agent(self):
        """Test the FileManagerAgent example name."""
        assert slugify("FileManagerAgent") == "filemanageragent"

    def test_slugify_threat_intel_agent(self):
        """Test the ThreatIntelAgent example name."""
        assert slugify("ThreatIntelAgent") == "threatintelagent"

    def test_slugify_research_agent(self):
        """Test a typical research agent name."""
        assert slugify("ResearchAgent") == "researchagent"

    def test_slugify_code_review_agent(self):
        """Test a multi-word agent name."""
        assert slugify("Code Review Agent") == "code-review-agent"

    def test_slugify_with_version(self):
        """Test agent name with version number."""
        assert slugify("Agent v2.0") == "agent-v2-0"
