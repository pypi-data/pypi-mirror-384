from src.broadie.prompts import BASE_INSTRUCTIONS


class TestPrompts:
    """Unit tests for prompts module."""

    def test_base_instructions_exists(self):
        """Test that BASE_INSTRUCTIONS constant exists."""
        assert BASE_INSTRUCTIONS is not None
        assert isinstance(BASE_INSTRUCTIONS, str)

    def test_base_instructions_not_empty(self):
        """Test that BASE_INSTRUCTIONS is not empty."""
        assert len(BASE_INSTRUCTIONS.strip()) > 0

    def test_base_instructions_contains_core_sections(self):
        """Test that BASE_INSTRUCTIONS contains expected sections."""
        required_sections = [
            "CORE BEHAVIOR",
            "RESPONSE RULES",
        ]

        for section in required_sections:
            assert section in BASE_INSTRUCTIONS, f"Missing section: {section}"

    def test_base_instructions_contains_behavioral_rules(self):
        """Test that BASE_INSTRUCTIONS contains key behavioral rules."""
        behavioral_keywords = [
            "autonomous agent",
            "TODO list",
            "strict_mode",
        ]

        for keyword in behavioral_keywords:
            assert keyword in BASE_INSTRUCTIONS, f"Missing keyword: {keyword}"

    def test_base_instructions_contains_safety_guidelines(self):
        """Test that BASE_INSTRUCTIONS contains safety and ethical guidelines."""
        safety_keywords = [
            "privacy",
            "ethical guidelines",
            "harmful",
            "unsafe",
            "accuracy",
            "safety",
        ]

        for keyword in safety_keywords:
            assert keyword.lower() in BASE_INSTRUCTIONS.lower(), f"Missing safety keyword: {keyword}"

    def test_base_instructions_has_proper_structure(self):
        """Test that BASE_INSTRUCTIONS has proper markdown-like structure."""
        # Should have section headers with ---
        assert "--- CORE BEHAVIOR ---" in BASE_INSTRUCTIONS
        assert "--- RESPONSE RULES ---" in BASE_INSTRUCTIONS

    def test_base_instructions_numbered_rules(self):
        """Test that BASE_INSTRUCTIONS contains numbered rules."""
        # Should contain numbered lists
        assert "1." in BASE_INSTRUCTIONS
        assert "2." in BASE_INSTRUCTIONS
        assert "3." in BASE_INSTRUCTIONS

    def test_base_instructions_formatting_consistency(self):
        """Test that BASE_INSTRUCTIONS has consistent formatting."""
        lines = BASE_INSTRUCTIONS.split("\n")

        # Should start and end with proper formatting
        assert lines[0].strip() == ""  # First line should be empty
        # Check that it has a reasonable structure - non-empty content lines
        non_empty_lines = [line for line in lines if line.strip()]
        assert len(non_empty_lines) > 0  # Should have content

    def test_base_instructions_word_count(self):
        """Test that BASE_INSTRUCTIONS has reasonable length for a prompt."""
        word_count = len(BASE_INSTRUCTIONS.split())

        # Should be substantial but not excessively long
        assert word_count > 100, "BASE_INSTRUCTIONS seems too short"

    def test_base_instructions_line_count(self):
        """Test that BASE_INSTRUCTIONS has reasonable number of lines."""
        lines = [line for line in BASE_INSTRUCTIONS.split("\n") if line.strip()]

        # Should have multiple lines of content
        assert len(lines) > 10, "BASE_INSTRUCTIONS should have more content lines"
