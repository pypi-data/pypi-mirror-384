"""Tests for configuration management."""

import json
from commitlm.config.settings import Settings, GeminiConfig, HuggingFaceConfig


class TestSettings:
    """Test Settings class."""

    def test_settings_creation(self, sample_config):
        """Test creating settings from dict."""
        settings = Settings(**sample_config)
        assert settings.provider == "gemini"
        assert settings.model == "gemini-2.5-flash"
        assert settings.commit_message_enabled is True
        assert settings.doc_generation_enabled is True

    def test_settings_default_values(self):
        """Test settings with default values."""
        settings = Settings(provider="gemini", model="gemini-2.5-flash")
        assert settings.fallback_to_local is False
        assert settings.commit_message_enabled is False
        assert settings.doc_generation_enabled is False

    def test_gemini_config(self):
        """Test Gemini configuration."""
        config = GeminiConfig(model="gemini-2.5-flash", api_key="test-key")
        assert config.model == "gemini-2.5-flash"
        assert config.api_key == "test-key"
        assert config.max_tokens == 1024
        assert config.temperature == 0.4

    def test_huggingface_config(self):
        """Test HuggingFace configuration."""
        config = HuggingFaceConfig(model="qwen2.5-coder-1.5b")
        assert config.model == "qwen2.5-coder-1.5b"
        assert config.device == "auto"
        assert config.memory_optimization is True

    def test_settings_save_load(self, temp_dir, sample_config):
        """Test saving and loading settings."""
        config_path = temp_dir / ".commitlm-config.json"

        # Save settings
        with open(config_path, "w") as f:
            json.dump(sample_config, f)

        # Load settings
        with open(config_path, "r") as f:
            loaded_config = json.load(f)

        settings = Settings(**loaded_config)
        assert settings.provider == sample_config["provider"]
        assert settings.model == sample_config["model"]
