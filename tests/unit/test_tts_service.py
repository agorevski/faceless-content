"""
Unit tests for TTSService.

Tests cover:
- Audio generation for scenes
- Audio generation for scripts
- Checkpoint support
- Audio duration retrieval
- Scene duration updates
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from faceless.core.enums import JobStatus, Niche, Voice
from faceless.core.exceptions import TTSGenerationError
from faceless.core.models import Checkpoint, Scene, Script


class TestTTSService:
    """Tests for TTSService."""

    @pytest.fixture
    def mock_settings(self):
        """Mock settings."""
        with patch("faceless.services.tts_service.get_settings") as mock:
            settings = MagicMock()
            settings.get_voice_settings.return_value = (Voice.ONYX, 0.9)
            settings.get_audio_dir.return_value = Path("/tmp/audio")
            settings.ffprobe_path = "ffprobe"
            settings.max_concurrent_tts = 5
            mock.return_value = settings
            yield settings

    @pytest.fixture
    def mock_client(self):
        """Mock Azure OpenAI client."""
        client = MagicMock()
        client.save_audio = MagicMock()
        return client

    @pytest.fixture
    def tts_service(self, mock_settings, mock_client):
        """Create TTS service with mocked client."""
        with patch("faceless.services.tts_service.AzureOpenAIClient"):
            from faceless.services.tts_service import TTSService

            service = TTSService(client=mock_client)
            return service

    @pytest.fixture
    def sample_scene(self) -> Scene:
        """Create sample scene."""
        return Scene(
            scene_number=1,
            narration="This is a test narration for audio generation.",
            image_prompt="Test prompt",
            duration_estimate=10.0,
        )

    @pytest.fixture
    def sample_script(self, sample_scene) -> Script:
        """Create sample script."""
        return Script(
            title="Test Script",
            niche=Niche.SCARY_STORIES,
            scenes=[sample_scene],
        )

    def test_init_with_client(self, mock_settings, mock_client) -> None:
        """Test service initialization with provided client."""
        from faceless.services.tts_service import TTSService

        service = TTSService(client=mock_client)
        assert service._client == mock_client

    def test_init_without_client(self, mock_settings) -> None:
        """Test service initialization creates client."""
        with patch(
            "faceless.services.tts_service.AzureOpenAIClient"
        ) as mock_client_class:
            from faceless.services.tts_service import TTSService

            TTSService()
            mock_client_class.assert_called_once()

    def test_generate_for_scene_success(
        self, tts_service, mock_client, sample_scene, tmp_path: Path
    ) -> None:
        """Test successful audio generation for scene."""
        output_dir = tmp_path / "audio"
        output_dir.mkdir()

        result = tts_service.generate_for_scene(
            scene=sample_scene,
            niche=Niche.SCARY_STORIES,
            output_dir=output_dir,
        )

        expected_path = output_dir / "scene_01.mp3"
        assert result == expected_path
        assert sample_scene.audio_path == expected_path
        mock_client.save_audio.assert_called_once()

    def test_generate_for_scene_with_voice_override(
        self, tts_service, mock_client, sample_scene, tmp_path: Path
    ) -> None:
        """Test audio generation with voice override."""
        output_dir = tmp_path / "audio"
        output_dir.mkdir()

        tts_service.generate_for_scene(
            scene=sample_scene,
            niche=Niche.SCARY_STORIES,
            output_dir=output_dir,
            voice=Voice.NOVA,
            speed=1.2,
        )

        mock_client.save_audio.assert_called_once()
        call_kwargs = mock_client.save_audio.call_args[1]
        assert call_kwargs["voice"] == Voice.NOVA
        assert call_kwargs["speed"] == 1.2

    def test_generate_for_scene_error(
        self, tts_service, mock_client, sample_scene, tmp_path: Path
    ) -> None:
        """Test audio generation error handling."""
        mock_client.save_audio.side_effect = Exception("API Error")
        output_dir = tmp_path / "audio"
        output_dir.mkdir()

        with pytest.raises(TTSGenerationError) as exc_info:
            tts_service.generate_for_scene(
                scene=sample_scene,
                niche=Niche.SCARY_STORIES,
                output_dir=output_dir,
            )

        assert "scene 1" in str(exc_info.value).lower()

    def test_generate_for_script_success(
        self, tts_service, mock_client, mock_settings, sample_script, tmp_path: Path
    ) -> None:
        """Test audio generation for entire script."""
        mock_settings.get_audio_dir.return_value = tmp_path / "audio"

        results = tts_service.generate_for_script(script=sample_script)

        assert len(results) == 1
        mock_client.save_audio.assert_called_once()

    def test_generate_for_script_with_checkpoint_skip(
        self, tts_service, mock_client, mock_settings, sample_script, tmp_path: Path
    ) -> None:
        """Test script generation skips completed scenes."""
        from uuid import uuid4

        audio_dir = tmp_path / "audio" / sample_script.safe_title
        audio_dir.mkdir(parents=True)
        mock_settings.get_audio_dir.return_value = tmp_path / "audio"

        # Create existing audio file
        existing_audio = audio_dir / "scene_01.mp3"
        existing_audio.write_bytes(b"audio")

        checkpoint = Checkpoint(
            job_id=uuid4(),
            script_path=Path("/test/script.json"),
            status=JobStatus.GENERATING_AUDIO,
        )
        checkpoint.mark_audio_done(1)

        results = tts_service.generate_for_script(
            script=sample_script,
            checkpoint=checkpoint,
        )

        assert len(results) == 1
        # Should not call save_audio since scene was skipped
        mock_client.save_audio.assert_not_called()

    def test_generate_for_script_continues_on_error(
        self, tts_service, mock_client, mock_settings, tmp_path: Path
    ) -> None:
        """Test script generation continues after scene error."""
        scenes = [
            Scene(scene_number=1, narration="First scene", image_prompt="Test"),
            Scene(scene_number=2, narration="Second scene", image_prompt="Test"),
        ]
        script = Script(title="Test", niche=Niche.FINANCE, scenes=scenes)

        mock_settings.get_audio_dir.return_value = tmp_path / "audio"

        # Fail on first, succeed on second
        mock_client.save_audio.side_effect = [
            Exception("Failed"),
            None,
        ]

        results = tts_service.generate_for_script(script=script)

        # Second scene should succeed
        assert len(results) == 1
        assert mock_client.save_audio.call_count == 2

    def test_generate_for_script_updates_checkpoint(
        self, tts_service, mock_client, mock_settings, sample_script, tmp_path: Path
    ) -> None:
        """Test checkpoint is updated after successful generation."""
        from uuid import uuid4

        mock_settings.get_audio_dir.return_value = tmp_path / "audio"

        checkpoint = Checkpoint(
            job_id=uuid4(),
            script_path=Path("/test/script.json"),
            status=JobStatus.GENERATING_AUDIO,
        )

        tts_service.generate_for_script(
            script=sample_script,
            checkpoint=checkpoint,
        )

        assert checkpoint.is_audio_done(1)

    def test_get_audio_duration_success(self, tts_service, tmp_path: Path) -> None:
        """Test successful audio duration retrieval."""
        audio_path = tmp_path / "audio.mp3"
        audio_path.write_bytes(b"audio")

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="15.5\n", stderr="")

            result = tts_service.get_audio_duration(audio_path)

            assert result == 15.5

    def test_get_audio_duration_error(self, tts_service, tmp_path: Path) -> None:
        """Test audio duration retrieval error."""
        audio_path = tmp_path / "audio.mp3"

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = Exception("ffprobe error")

            result = tts_service.get_audio_duration(audio_path)

            assert result == 0.0

    def test_update_scene_durations(self, tts_service, tmp_path: Path) -> None:
        """Test updating scene durations from audio."""
        audio_path = tmp_path / "scene_01.mp3"
        audio_path.write_bytes(b"audio")

        scene = Scene(
            scene_number=1,
            narration="Test",
            image_prompt="Test",
            duration_estimate=10.0,
        )
        scene.audio_path = audio_path

        script = Script(
            title="Test",
            niche=Niche.SCARY_STORIES,
            scenes=[scene],
        )

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="25.0\n", stderr="")

            tts_service.update_scene_durations(script)

            assert scene.duration_estimate == 25.0

    def test_update_scene_durations_skips_missing_audio(self, tts_service) -> None:
        """Test duration update skips scenes without audio."""
        scene = Scene(
            scene_number=1,
            narration="Test",
            image_prompt="Test",
            duration_estimate=10.0,
        )
        # No audio_path set

        script = Script(
            title="Test",
            niche=Niche.SCARY_STORIES,
            scenes=[scene],
        )

        tts_service.update_scene_durations(script)

        # Duration should remain unchanged
        assert scene.duration_estimate == 10.0

    def test_update_scene_durations_skips_zero_duration(
        self, tts_service, tmp_path: Path
    ) -> None:
        """Test duration update skips when ffprobe returns 0."""
        audio_path = tmp_path / "scene_01.mp3"
        audio_path.write_bytes(b"audio")

        scene = Scene(
            scene_number=1,
            narration="Test",
            image_prompt="Test",
            duration_estimate=10.0,
        )
        scene.audio_path = audio_path

        script = Script(
            title="Test",
            niche=Niche.SCARY_STORIES,
            scenes=[scene],
        )

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="0.0\n", stderr="")

            tts_service.update_scene_durations(script)

            # Duration should remain unchanged when 0 returned
            assert scene.duration_estimate == 10.0
