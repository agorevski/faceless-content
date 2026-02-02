"""
Unit tests for settings module.

Tests cover:
- AzureOpenAISettings validation
- ElevenLabsSettings configuration
- RedditSettings configuration
- Main Settings class and methods
"""

from pathlib import Path

from faceless.core.enums import Niche, Voice


class TestAzureOpenAISettings:
    """Tests for AzureOpenAISettings."""

    def test_default_values(self) -> None:
        """Test default values are set correctly."""
        from faceless.config.settings import AzureOpenAISettings

        # Use _env_file=None to prevent loading from .env
        settings = AzureOpenAISettings(_env_file=None)
        assert settings.endpoint == ""
        assert settings.api_key == ""
        assert settings.image_deployment == "gpt-image-1"
        assert settings.chat_deployment == "gpt-4o"
        assert settings.tts_deployment == "gpt-4o-mini-tts"

    def test_endpoint_validation_adds_trailing_slash(self) -> None:
        """Test endpoint gets trailing slash added."""
        from faceless.config.settings import AzureOpenAISettings

        settings = AzureOpenAISettings(endpoint="https://test.openai.azure.com")
        assert settings.endpoint == "https://test.openai.azure.com/"

    def test_endpoint_validation_preserves_trailing_slash(self) -> None:
        """Test endpoint with trailing slash is preserved."""
        from faceless.config.settings import AzureOpenAISettings

        settings = AzureOpenAISettings(endpoint="https://test.openai.azure.com/")
        assert settings.endpoint == "https://test.openai.azure.com/"

    def test_endpoint_validation_empty_string(self) -> None:
        """Test empty endpoint is handled."""
        from faceless.config.settings import AzureOpenAISettings

        settings = AzureOpenAISettings(endpoint="")
        assert settings.endpoint == ""

    def test_is_configured_true(self) -> None:
        """Test is_configured returns True when both endpoint and key set."""
        from faceless.config.settings import AzureOpenAISettings

        settings = AzureOpenAISettings(
            endpoint="https://test.openai.azure.com/",
            AZURE_OPENAI_API_KEY="test-key",
        )
        assert settings.is_configured is True

    def test_is_configured_false_no_endpoint(self) -> None:
        """Test is_configured returns False when endpoint missing."""
        from faceless.config.settings import AzureOpenAISettings

        # Use _env_file=None to prevent loading from .env
        settings = AzureOpenAISettings(_env_file=None, AZURE_OPENAI_API_KEY="test-key")
        assert settings.is_configured is False

    def test_is_configured_false_no_key(self) -> None:
        """Test is_configured returns False when key missing."""
        from faceless.config.settings import AzureOpenAISettings

        # Use _env_file=None to prevent loading from .env
        settings = AzureOpenAISettings(
            _env_file=None, endpoint="https://test.openai.azure.com/"
        )
        assert settings.is_configured is False


class TestElevenLabsSettings:
    """Tests for ElevenLabsSettings."""

    def test_default_values(self) -> None:
        """Test default values."""
        from faceless.config.settings import ElevenLabsSettings

        settings = ElevenLabsSettings()
        assert settings.api_key == ""
        assert settings.voice_id_scary == ""
        assert settings.voice_id_finance == ""
        assert settings.voice_id_luxury == ""

    def test_is_configured_true(self) -> None:
        """Test is_configured when API key set."""
        from faceless.config.settings import ElevenLabsSettings

        settings = ElevenLabsSettings(api_key="test-key")
        assert settings.is_configured is True

    def test_is_configured_false(self) -> None:
        """Test is_configured when API key missing."""
        from faceless.config.settings import ElevenLabsSettings

        settings = ElevenLabsSettings()
        assert settings.is_configured is False

    def test_get_voice_id_scary(self) -> None:
        """Test getting voice ID for scary niche."""
        from faceless.config.settings import ElevenLabsSettings

        settings = ElevenLabsSettings(voice_id_scary="scary-voice-id")
        assert settings.get_voice_id(Niche.SCARY_STORIES) == "scary-voice-id"

    def test_get_voice_id_finance(self) -> None:
        """Test getting voice ID for finance niche."""
        from faceless.config.settings import ElevenLabsSettings

        settings = ElevenLabsSettings(voice_id_finance="finance-voice-id")
        assert settings.get_voice_id(Niche.FINANCE) == "finance-voice-id"

    def test_get_voice_id_luxury(self) -> None:
        """Test getting voice ID for luxury niche."""
        from faceless.config.settings import ElevenLabsSettings

        settings = ElevenLabsSettings(voice_id_luxury="luxury-voice-id")
        assert settings.get_voice_id(Niche.LUXURY) == "luxury-voice-id"


class TestRedditSettings:
    """Tests for RedditSettings."""

    def test_default_values(self) -> None:
        """Test default values."""
        from faceless.config.settings import RedditSettings

        settings = RedditSettings()
        assert settings.client_id == ""
        assert settings.client_secret == ""
        assert settings.user_agent == "FacelessContent/1.0"

    def test_is_configured_true(self) -> None:
        """Test is_configured when both credentials set."""
        from faceless.config.settings import RedditSettings

        settings = RedditSettings(client_id="id", client_secret="secret")
        assert settings.is_configured is True

    def test_is_configured_false_no_id(self) -> None:
        """Test is_configured when client_id missing."""
        from faceless.config.settings import RedditSettings

        settings = RedditSettings(client_secret="secret")
        assert settings.is_configured is False

    def test_is_configured_false_no_secret(self) -> None:
        """Test is_configured when client_secret missing."""
        from faceless.config.settings import RedditSettings

        settings = RedditSettings(client_id="id")
        assert settings.is_configured is False


class TestSettings:
    """Tests for main Settings class."""

    def test_default_values(self) -> None:
        """Test default settings values."""
        from faceless.config.settings import Settings

        # Use _env_file=None to prevent loading from .env
        settings = Settings(_env_file=None)
        assert settings.log_level == "INFO"
        assert settings.log_json_format is False
        assert settings.debug is False
        assert settings.output_base_dir == Path("output")
        assert settings.max_concurrent_requests == 5
        assert settings.request_timeout == 120
        assert settings.enable_retry is True
        assert settings.max_retries == 3
        assert settings.enable_checkpointing is True

    def test_get_voice_settings_scary(self) -> None:
        """Test getting voice settings for scary niche."""
        from faceless.config.settings import Settings

        settings = Settings()
        voice, speed = settings.get_voice_settings(Niche.SCARY_STORIES)
        assert voice == Voice.ONYX
        assert speed == 0.9

    def test_get_voice_settings_finance(self) -> None:
        """Test getting voice settings for finance niche."""
        from faceless.config.settings import Settings

        settings = Settings()
        voice, speed = settings.get_voice_settings(Niche.FINANCE)
        assert voice == Voice.ONYX
        assert speed == 1.0

    def test_get_voice_settings_luxury(self) -> None:
        """Test getting voice settings for luxury niche."""
        from faceless.config.settings import Settings

        settings = Settings()
        voice, speed = settings.get_voice_settings(Niche.LUXURY)
        assert voice == Voice.NOVA
        assert speed == 0.95

    def test_get_output_dir(self) -> None:
        """Test getting output directory for niche."""
        from faceless.config.settings import Settings

        settings = Settings(output_base_dir=Path("/tmp/output"))
        path = settings.get_output_dir(Niche.SCARY_STORIES)
        assert path == Path("/tmp/output/scary-stories")

    def test_get_scripts_dir(self) -> None:
        """Test getting scripts directory."""
        from faceless.config.settings import Settings

        settings = Settings(output_base_dir=Path("/tmp/output"))
        path = settings.get_scripts_dir(Niche.FINANCE)
        assert path == Path("/tmp/output/finance/scripts")

    def test_get_images_dir(self) -> None:
        """Test getting images directory."""
        from faceless.config.settings import Settings

        settings = Settings(output_base_dir=Path("/tmp/output"))
        path = settings.get_images_dir(Niche.LUXURY)
        assert path == Path("/tmp/output/luxury/images")

    def test_get_audio_dir(self) -> None:
        """Test getting audio directory."""
        from faceless.config.settings import Settings

        settings = Settings(output_base_dir=Path("/tmp/output"))
        path = settings.get_audio_dir(Niche.SCARY_STORIES)
        assert path == Path("/tmp/output/scary-stories/audio")

    def test_get_videos_dir(self) -> None:
        """Test getting videos directory."""
        from faceless.config.settings import Settings

        settings = Settings(output_base_dir=Path("/tmp/output"))
        path = settings.get_videos_dir(Niche.FINANCE)
        assert path == Path("/tmp/output/finance/videos")

    def test_get_final_output_dir(self) -> None:
        """Test getting final output directory."""
        from faceless.config.settings import Settings

        settings = Settings(output_base_dir=Path("/tmp/output"))
        path = settings.get_final_output_dir(Niche.LUXURY)
        assert path == Path("/tmp/output/luxury/final")

    def test_get_checkpoints_dir(self) -> None:
        """Test getting checkpoints directory."""
        from faceless.config.settings import Settings

        settings = Settings(output_base_dir=Path("/tmp/output"))
        path = settings.get_checkpoints_dir(Niche.SCARY_STORIES)
        assert path == Path("/tmp/output/scary-stories/.checkpoints")

    def test_get_music_dir(self) -> None:
        """Test getting music directory."""
        from faceless.config.settings import Settings

        settings = Settings(shared_dir=Path("/tmp/shared"))
        path = settings.get_music_dir()
        assert path == Path("/tmp/shared/music")

    def test_get_prompts_dir(self) -> None:
        """Test getting prompts directory."""
        from faceless.config.settings import Settings

        settings = Settings(shared_dir=Path("/tmp/shared"))
        path = settings.get_prompts_dir()
        assert path == Path("/tmp/shared/prompts")

    def test_get_templates_dir(self) -> None:
        """Test getting templates directory."""
        from faceless.config.settings import Settings

        settings = Settings(shared_dir=Path("/tmp/shared"))
        path = settings.get_templates_dir()
        assert path == Path("/tmp/shared/templates")

    def test_is_production_true(self) -> None:
        """Test is_production returns True when not debug and json logging."""
        from faceless.config.settings import Settings

        settings = Settings(debug=False, log_json_format=True)
        assert settings.is_production is True

    def test_is_production_false_debug(self) -> None:
        """Test is_production returns False when debug enabled."""
        from faceless.config.settings import Settings

        settings = Settings(debug=True, log_json_format=True)
        assert settings.is_production is False

    def test_is_production_false_no_json(self) -> None:
        """Test is_production returns False when json logging disabled."""
        from faceless.config.settings import Settings

        settings = Settings(debug=False, log_json_format=False)
        assert settings.is_production is False

    def test_ensure_directories_single_niche(self, tmp_path: Path) -> None:
        """Test ensure_directories creates directories for single niche."""
        from faceless.config.settings import Settings

        settings = Settings(
            output_base_dir=tmp_path / "output",
            shared_dir=tmp_path / "shared",
        )
        settings.ensure_directories(Niche.SCARY_STORIES)

        assert (tmp_path / "output" / "scary-stories" / "scripts").exists()
        assert (tmp_path / "output" / "scary-stories" / "images").exists()
        assert (tmp_path / "output" / "scary-stories" / "audio").exists()
        assert (tmp_path / "output" / "scary-stories" / "videos").exists()
        assert (tmp_path / "output" / "scary-stories" / "final").exists()
        assert (tmp_path / "output" / "scary-stories" / ".checkpoints").exists()
        assert (tmp_path / "shared" / "music").exists()

    def test_ensure_directories_all_niches(self, tmp_path: Path) -> None:
        """Test ensure_directories creates directories for all niches."""
        from faceless.config.settings import Settings

        settings = Settings(
            output_base_dir=tmp_path / "output",
            shared_dir=tmp_path / "shared",
        )
        settings.ensure_directories()

        for niche in Niche:
            assert (tmp_path / "output" / niche.value / "scripts").exists()

    def test_ensure_directories_no_checkpoints_when_disabled(
        self, tmp_path: Path
    ) -> None:
        """Test checkpoints dir not created when disabled."""
        from faceless.config.settings import Settings

        settings = Settings(
            output_base_dir=tmp_path / "output",
            shared_dir=tmp_path / "shared",
            enable_checkpointing=False,
        )
        settings.ensure_directories(Niche.FINANCE)

        assert not (tmp_path / "output" / "finance" / ".checkpoints").exists()


class TestGetSettings:
    """Tests for get_settings and reload_settings functions."""

    def test_get_settings_returns_settings(self) -> None:
        """Test get_settings returns Settings instance."""
        from faceless.config.settings import Settings, get_settings, reload_settings

        # Clear cache first
        reload_settings()
        settings = get_settings()
        assert isinstance(settings, Settings)

    def test_get_settings_is_cached(self) -> None:
        """Test get_settings returns cached instance."""
        from faceless.config.settings import get_settings, reload_settings

        reload_settings()
        settings1 = get_settings()
        settings2 = get_settings()
        assert settings1 is settings2

    def test_reload_settings_clears_cache(self) -> None:
        """Test reload_settings creates new instance."""
        from faceless.config.settings import get_settings, reload_settings

        settings1 = get_settings()
        settings2 = reload_settings()
        # After reload, should be new instance
        assert settings2 is not settings1


class TestOutputSettingsDict:
    """Tests for get_output_settings_dict function."""

    def test_youtube_settings(self) -> None:
        """Test getting YouTube output settings."""
        from faceless.config.settings import get_output_settings_dict

        settings = get_output_settings_dict("youtube")
        assert settings["resolution"] == "1920x1080"
        assert settings["fps"] == 30
        assert settings["format"] == "mp4"
        assert settings["codec"] == "libx264"

    def test_tiktok_settings(self) -> None:
        """Test getting TikTok output settings."""
        from faceless.config.settings import get_output_settings_dict

        settings = get_output_settings_dict("tiktok")
        assert settings["resolution"] == "1080x1920"
        assert settings["fps"] == 30
        assert settings["format"] == "mp4"
        assert settings["codec"] == "libx264"

    def test_unknown_platform_raises_error(self) -> None:
        """Test unknown platform raises ValueError."""
        import pytest

        from faceless.config.settings import get_output_settings_dict

        with pytest.raises(ValueError) as exc_info:
            get_output_settings_dict("instagram")

        assert "Unknown platform" in str(exc_info.value)


class TestGetLegacyPaths:
    """Tests for get_legacy_paths function."""

    def test_returns_paths_for_all_niches(self) -> None:
        """Test legacy paths include all niches."""
        from faceless.config.settings import Settings, get_legacy_paths
        from faceless.core.enums import Niche

        settings = Settings(
            _env_file=None,
            output_base_dir=Path("/tmp/output"),
            shared_dir=Path("/tmp/shared"),
        )
        paths = get_legacy_paths(settings)

        # Check all niches are included
        for niche in Niche:
            assert niche.value in paths
            assert "scripts" in paths[niche.value]
            assert "images" in paths[niche.value]
            assert "audio" in paths[niche.value]
            assert "videos" in paths[niche.value]
            assert "output" in paths[niche.value]

    def test_includes_shared_paths(self) -> None:
        """Test legacy paths include shared resources."""
        from faceless.config.settings import Settings, get_legacy_paths

        settings = Settings(
            _env_file=None,
            output_base_dir=Path("/tmp/output"),
            shared_dir=Path("/tmp/shared"),
        )
        paths = get_legacy_paths(settings)

        assert "shared" in paths
        assert paths["shared"]["templates"] == str(Path("/tmp/shared/templates"))
        assert paths["shared"]["prompts"] == str(Path("/tmp/shared/prompts"))
        assert paths["shared"]["music"] == str(Path("/tmp/shared/music"))

    def test_uses_cached_settings_when_none(self) -> None:
        """Test get_legacy_paths uses cached settings when None passed."""
        from faceless.config.settings import get_legacy_paths, reload_settings

        reload_settings()
        paths = get_legacy_paths(None)

        assert "shared" in paths
        assert "scary-stories" in paths


class TestGetLegacyVoiceSettings:
    """Tests for get_legacy_voice_settings function."""

    def test_returns_voice_settings_for_all_niches(self) -> None:
        """Test legacy voice settings include all niches."""
        from faceless.config.settings import Settings, get_legacy_voice_settings
        from faceless.core.enums import Niche

        settings = Settings(_env_file=None)
        voice_settings = get_legacy_voice_settings(settings)

        for niche in Niche:
            assert niche.value in voice_settings
            assert "openai_voice" in voice_settings[niche.value]
            assert "openai_speed" in voice_settings[niche.value]
            assert "elevenlabs_voice_id" in voice_settings[niche.value]

    def test_scary_stories_voice_settings(self) -> None:
        """Test scary stories voice settings."""
        from faceless.config.settings import Settings, get_legacy_voice_settings

        settings = Settings(_env_file=None)
        voice_settings = get_legacy_voice_settings(settings)

        assert voice_settings["scary-stories"]["openai_voice"] == "onyx"
        assert voice_settings["scary-stories"]["openai_speed"] == 0.9

    def test_uses_cached_settings_when_none(self) -> None:
        """Test get_legacy_voice_settings uses cached settings when None passed."""
        from faceless.config.settings import get_legacy_voice_settings, reload_settings

        reload_settings()
        voice_settings = get_legacy_voice_settings(None)

        assert "scary-stories" in voice_settings


class TestFFmpegPathValidators:
    """Tests for FFmpeg/FFprobe path validators."""

    def test_empty_ffmpeg_path_uses_default(self) -> None:
        """Test empty ffmpeg_path defaults to 'ffmpeg'."""
        from faceless.config.settings import Settings

        settings = Settings(_env_file=None, ffmpeg_path="")
        assert settings.ffmpeg_path == "ffmpeg"

    def test_empty_ffprobe_path_uses_default(self) -> None:
        """Test empty ffprobe_path defaults to 'ffprobe'."""
        from faceless.config.settings import Settings

        settings = Settings(_env_file=None, ffprobe_path="")
        assert settings.ffprobe_path == "ffprobe"

    def test_custom_ffmpeg_path_preserved(self) -> None:
        """Test custom ffmpeg_path is preserved."""
        from faceless.config.settings import Settings

        settings = Settings(_env_file=None, ffmpeg_path="/usr/local/bin/ffmpeg")
        assert settings.ffmpeg_path == "/usr/local/bin/ffmpeg"

    def test_custom_ffprobe_path_preserved(self) -> None:
        """Test custom ffprobe_path is preserved."""
        from faceless.config.settings import Settings

        settings = Settings(_env_file=None, ffprobe_path="/usr/local/bin/ffprobe")
        assert settings.ffprobe_path == "/usr/local/bin/ffprobe"


class TestElevenLabsVoiceIds:
    """Tests for all ElevenLabs voice ID getters."""

    def test_get_voice_id_all_niches(self) -> None:
        """Test getting voice ID for all niches."""
        from faceless.config.settings import ElevenLabsSettings
        from faceless.core.enums import Niche

        settings = ElevenLabsSettings(
            voice_id_scary="scary-id",
            voice_id_finance="finance-id",
            voice_id_luxury="luxury-id",
            voice_id_true_crime="crime-id",
            voice_id_psychology="psych-id",
            voice_id_history="history-id",
            voice_id_motivation="motiv-id",
            voice_id_space="space-id",
            voice_id_conspiracy="conspiracy-id",
            voice_id_animals="animals-id",
            voice_id_health="health-id",
            voice_id_relationships="rel-id",
            voice_id_tech="tech-id",
            voice_id_lifehacks="hacks-id",
            voice_id_mythology="myth-id",
            voice_id_unsolved="unsolved-id",
            voice_id_geography="geo-id",
            voice_id_ai_future="ai-id",
            voice_id_philosophy="phil-id",
            voice_id_books="books-id",
            voice_id_celebrity="celeb-id",
            voice_id_survival="surv-id",
            voice_id_sleep="sleep-id",
            voice_id_netflix="netflix-id",
            voice_id_mockumentary="mock-id",
        )

        # Test each niche has a voice ID
        assert settings.get_voice_id(Niche.SCARY_STORIES) == "scary-id"
        assert settings.get_voice_id(Niche.FINANCE) == "finance-id"
        assert settings.get_voice_id(Niche.LUXURY) == "luxury-id"
        assert settings.get_voice_id(Niche.TRUE_CRIME) == "crime-id"
        assert settings.get_voice_id(Niche.PSYCHOLOGY_FACTS) == "psych-id"
        assert settings.get_voice_id(Niche.HISTORY) == "history-id"
        assert settings.get_voice_id(Niche.MOTIVATION) == "motiv-id"
        assert settings.get_voice_id(Niche.SPACE_ASTRONOMY) == "space-id"
        assert settings.get_voice_id(Niche.CONSPIRACY_MYSTERIES) == "conspiracy-id"
        assert settings.get_voice_id(Niche.ANIMAL_FACTS) == "animals-id"
        assert settings.get_voice_id(Niche.HEALTH_WELLNESS) == "health-id"
        assert settings.get_voice_id(Niche.RELATIONSHIP_ADVICE) == "rel-id"
        assert settings.get_voice_id(Niche.TECH_GADGETS) == "tech-id"
        assert settings.get_voice_id(Niche.LIFE_HACKS) == "hacks-id"
        assert settings.get_voice_id(Niche.MYTHOLOGY_FOLKLORE) == "myth-id"
        assert settings.get_voice_id(Niche.UNSOLVED_MYSTERIES) == "unsolved-id"
        assert settings.get_voice_id(Niche.GEOGRAPHY_FACTS) == "geo-id"
        assert settings.get_voice_id(Niche.AI_FUTURE_TECH) == "ai-id"
        assert settings.get_voice_id(Niche.PHILOSOPHY) == "phil-id"
        assert settings.get_voice_id(Niche.BOOK_SUMMARIES) == "books-id"
        assert settings.get_voice_id(Niche.CELEBRITY_NET_WORTH) == "celeb-id"
        assert settings.get_voice_id(Niche.SURVIVAL_TIPS) == "surv-id"
        assert settings.get_voice_id(Niche.SLEEP_RELAXATION) == "sleep-id"
        assert settings.get_voice_id(Niche.NETFLIX_RECOMMENDATIONS) == "netflix-id"
        assert settings.get_voice_id(Niche.MOCKUMENTARY_HOWMADE) == "mock-id"


class TestAllNicheVoiceSettings:
    """Tests for voice settings for all niches."""

    def test_get_voice_settings_all_niches(self) -> None:
        """Test getting voice settings for all niches."""
        from faceless.config.settings import Settings
        from faceless.core.enums import Niche, Voice

        settings = Settings(_env_file=None)

        # Test all niches return valid settings
        for niche in Niche:
            voice, speed = settings.get_voice_settings(niche)
            assert isinstance(voice, Voice)
            assert isinstance(speed, float)
            assert 0.25 <= speed <= 4.0

    def test_voice_settings_specific_niches(self) -> None:
        """Test specific niche voice settings."""
        from faceless.config.settings import Settings
        from faceless.core.enums import Niche, Voice

        settings = Settings(_env_file=None)

        # Test several specific niches
        voice, speed = settings.get_voice_settings(Niche.MOTIVATION)
        assert voice == Voice.ECHO
        assert speed == 1.0

        voice, speed = settings.get_voice_settings(Niche.SLEEP_RELAXATION)
        assert voice == Voice.SHIMMER
        assert speed == 0.8

        voice, speed = settings.get_voice_settings(Niche.MYTHOLOGY_FOLKLORE)
        assert voice == Voice.FABLE
        assert speed == 0.9
