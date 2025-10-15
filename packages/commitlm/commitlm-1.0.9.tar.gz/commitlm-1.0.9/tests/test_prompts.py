"""Tests for prompt template system."""

from commitlm.config.prompts import (
    PromptManager,
    PromptTemplate,
    get_prompt_manager,
    render_documentation_prompt,
    render_commit_message_prompt,
    render_short_commit_message_prompt,
)


class TestPromptTemplate:
    """Test PromptTemplate class."""

    def test_template_creation(self):
        """Test creating a template."""
        template = PromptTemplate(
            name="test", template="Hello {{ name }}!", description="A test template"
        )
        assert template.name == "test"
        assert template.description == "A test template"

    def test_template_rendering(self):
        """Test rendering a template."""
        template = PromptTemplate(
            name="test",
            template="Hello {{ name }}!",
        )
        result = template.render(name="World")
        assert result == "Hello World!"

    def test_template_with_conditional(self):
        """Test template with conditional."""
        template = PromptTemplate(
            name="test",
            template="{% if show %}Hello {{ name }}!{% endif %}",
        )
        result = template.render(show=True, name="World")
        assert result == "Hello World!"

        result = template.render(show=False, name="World")
        assert result == ""


class TestPromptManager:
    """Test PromptManager class."""

    def test_manager_creation(self):
        """Test creating a prompt manager."""
        manager = PromptManager()
        templates = manager.list_templates()
        assert len(templates) > 0
        assert "documentation_generation" in templates
        assert "commit_message" in templates
        assert "short_commit_message" in templates

    def test_get_template(self):
        """Test getting a template."""
        manager = PromptManager()
        template = manager.get_template("commit_message")
        assert template is not None
        assert template.name == "commit_message"

    def test_register_custom_template(self):
        """Test registering a custom template."""
        manager = PromptManager()
        manager.register_template(
            "custom", "Custom template: {{ content }}", "A custom template"
        )
        template = manager.get_template("custom")
        assert template is not None
        result = template.render(content="test")
        assert result == "Custom template: test"

    def test_render_prompt(self):
        """Test rendering a prompt."""
        manager = PromptManager()
        result = manager.render_prompt("short_commit_message", diff_content="test diff")
        assert "test diff" in result
        assert "conventional commits" in result.lower()


class TestPromptHelpers:
    """Test prompt helper functions."""

    def test_render_documentation_prompt(self, sample_diff):
        """Test documentation prompt rendering."""
        result = render_documentation_prompt(sample_diff)
        assert sample_diff in result
        assert "Summary" in result
        assert "Changes" in result

    def test_render_documentation_prompt_with_max_tokens(self, sample_diff):
        """Test documentation prompt with max tokens."""
        result = render_documentation_prompt(sample_diff, max_tokens=512)
        assert "512 tokens" in result
        assert sample_diff in result

    def test_render_commit_message_prompt(self, sample_diff):
        """Test commit message prompt rendering."""
        result = render_commit_message_prompt(sample_diff)
        assert sample_diff in result
        assert "conventional commits" in result.lower()

    def test_render_short_commit_message_prompt(self, sample_diff):
        """Test short commit message prompt rendering."""
        result = render_short_commit_message_prompt(sample_diff)
        assert sample_diff in result
        assert "single-line" in result.lower()

    def test_get_prompt_manager_singleton(self):
        """Test that get_prompt_manager returns a singleton."""
        manager1 = get_prompt_manager()
        manager2 = get_prompt_manager()
        assert manager1 is manager2
