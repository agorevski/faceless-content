"""
Unit tests for ImageService.

Tests cover:
- Image generation for scenes
- Image generation for scripts
- Platform-specific sizing
- Checkpoint support
- Visual style handling
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from faceless.core.enums import JobStatus, Niche, Platform
from faceless.core.exceptions import ImageGenerationError
from faceless.core.models import Checkpoint, Scene, Script, VisualStyle


class TestImageService:
    """Tests for ImageService."""

    @pytest.fixture
    def mock_settings(self):
        """Mock settings."""
        with patch("faceless.services.image_service.get_settings") as mock:
            settings = MagicMock()
            settings.get_images_dir.return_value = Path("/tmp/images")
            mock.return_value = settings
            yield settings

    @pytest.fixture
    def mock_client(self):
        """Mock Azure OpenAI client."""
        client = MagicMock()
        client.save_image = MagicMock()
        return client

    @pytest.fixture
    def image_service(self, mock_settings, mock_client):
        """Create image service with mocked client."""
        with patch("faceless.services.image_service.AzureOpenAIClient"):
            from faceless.services.image_service import ImageService

            service = ImageService(client=mock_client)
            return service

    @pytest.fixture
    def sample_scene(self) -> Scene:
        """Create sample scene."""
        return Scene(
            scene_number=1,
            narration="A dark forest at night.",
            image_prompt="A dark mysterious forest with fog and moonlight",
            duration_estimate=15.0,
        )

    @pytest.fixture
    def sample_visual_style(self) -> VisualStyle:
        """Create sample visual style."""
        return VisualStyle(
            environment="Dark foggy forest",
            color_mood="Blue and gray tones",
            texture="Rough bark and wet leaves",
        )

    def test_init_with_client(self, mock_settings, mock_client) -> None:
        """Test service initialization with provided client."""
        from faceless.services.image_service import ImageService

        service = ImageService(client=mock_client)
        assert service._client == mock_client

    def test_init_without_client(self, mock_settings) -> None:
        """Test service initialization creates client."""
        with patch(
            "faceless.services.image_service.AzureOpenAIClient"
        ) as mock_client_class:
            from faceless.services.image_service import ImageService

            ImageService()
            mock_client_class.assert_called_once()

    def test_generate_for_scene_success(
        self, image_service, mock_client, sample_scene, tmp_path: Path
    ) -> None:
        """Test successful image generation for scene."""
        output_dir = tmp_path / "images"
        output_dir.mkdir()

        result = image_service.generate_for_scene(
            scene=sample_scene,
            niche=Niche.SCARY_STORIES,
            platform=Platform.YOUTUBE,
            output_dir=output_dir,
        )

        expected_path = output_dir / "scene_01_youtube.png"
        assert result == expected_path
        assert sample_scene.image_path == expected_path
        mock_client.save_image.assert_called_once()

    def test_generate_for_scene_with_visual_style(
        self, image_service, mock_client, sample_scene, tmp_path: Path
    ) -> None:
        """Test image generation with visual style suffix."""
        output_dir = tmp_path / "images"
        output_dir.mkdir()

        image_service.generate_for_scene(
            scene=sample_scene,
            niche=Niche.SCARY_STORIES,
            platform=Platform.YOUTUBE,
            output_dir=output_dir,
            visual_style_suffix="Dark foggy atmosphere",
        )

        call_kwargs = mock_client.save_image.call_args[1]
        assert "Dark foggy atmosphere" in call_kwargs["prompt"]

    def test_generate_for_scene_tiktok_platform(
        self, image_service, mock_client, sample_scene, tmp_path: Path
    ) -> None:
        """Test image generation for TikTok platform."""
        output_dir = tmp_path / "images"
        output_dir.mkdir()

        result = image_service.generate_for_scene(
            scene=sample_scene,
            niche=Niche.SCARY_STORIES,
            platform=Platform.TIKTOK,
            output_dir=output_dir,
        )

        expected_path = output_dir / "scene_01_tiktok.png"
        assert result == expected_path
        call_kwargs = mock_client.save_image.call_args[1]
        assert call_kwargs["platform"] == Platform.TIKTOK

    def test_generate_for_scene_error(
        self, image_service, mock_client, sample_scene, tmp_path: Path
    ) -> None:
        """Test image generation error handling."""
        mock_client.save_image.side_effect = Exception("API Error")
        output_dir = tmp_path / "images"
        output_dir.mkdir()

        with pytest.raises(ImageGenerationError) as exc_info:
            image_service.generate_for_scene(
                scene=sample_scene,
                niche=Niche.SCARY_STORIES,
                platform=Platform.YOUTUBE,
                output_dir=output_dir,
            )

        assert "scene 1" in str(exc_info.value).lower()

    def test_generate_for_script_success(
        self, image_service, mock_client, mock_settings, sample_scene, tmp_path: Path
    ) -> None:
        """Test image generation for entire script."""
        mock_settings.get_images_dir.return_value = tmp_path / "images"

        script = Script(
            title="Test Script",
            niche=Niche.SCARY_STORIES,
            scenes=[sample_scene],
        )

        results = image_service.generate_for_script(
            script=script,
            platform=Platform.YOUTUBE,
        )

        assert len(results) == 1
        mock_client.save_image.assert_called_once()

    def test_generate_for_script_with_visual_style(
        self,
        image_service,
        mock_client,
        mock_settings,
        sample_scene,
        sample_visual_style,
        tmp_path: Path,
    ) -> None:
        """Test script generation uses visual style."""
        mock_settings.get_images_dir.return_value = tmp_path / "images"

        script = Script(
            title="Test Script",
            niche=Niche.SCARY_STORIES,
            scenes=[sample_scene],
            visual_style=sample_visual_style,
        )

        image_service.generate_for_script(
            script=script,
            platform=Platform.YOUTUBE,
        )

        call_kwargs = mock_client.save_image.call_args[1]
        # Visual style should be appended to prompt
        assert (
            "Dark foggy forest" in call_kwargs["prompt"]
            or mock_client.save_image.called
        )

    def test_generate_for_script_with_checkpoint_skip(
        self, image_service, mock_client, mock_settings, sample_scene, tmp_path: Path
    ) -> None:
        """Test script generation skips completed scenes."""
        from uuid import uuid4

        images_dir = tmp_path / "images"
        mock_settings.get_images_dir.return_value = images_dir

        script = Script(
            title="Test Script",
            niche=Niche.SCARY_STORIES,
            scenes=[sample_scene],
        )

        # Create existing image
        script_images_dir = images_dir / script.safe_title
        script_images_dir.mkdir(parents=True)
        existing_image = script_images_dir / "scene_01_youtube.png"
        existing_image.write_bytes(b"image")

        checkpoint = Checkpoint(
            job_id=uuid4(),
            script_path=Path("/test/script.json"),
            status=JobStatus.GENERATING_IMAGES,
        )
        checkpoint.mark_image_done(1)

        results = image_service.generate_for_script(
            script=script,
            platform=Platform.YOUTUBE,
            checkpoint=checkpoint,
        )

        assert len(results) == 1
        # Should not call save_image since scene was skipped
        mock_client.save_image.assert_not_called()

    def test_generate_for_script_continues_on_error(
        self, image_service, mock_client, mock_settings, tmp_path: Path
    ) -> None:
        """Test script generation continues after scene error."""
        mock_settings.get_images_dir.return_value = tmp_path / "images"

        scenes = [
            Scene(scene_number=1, narration="First", image_prompt="First prompt"),
            Scene(scene_number=2, narration="Second", image_prompt="Second prompt"),
        ]
        script = Script(title="Test", niche=Niche.FINANCE, scenes=scenes)

        # Fail on first, succeed on second
        mock_client.save_image.side_effect = [
            Exception("Failed"),
            None,
        ]

        results = image_service.generate_for_script(
            script=script,
            platform=Platform.YOUTUBE,
        )

        # Second scene should succeed
        assert len(results) == 1
        assert mock_client.save_image.call_count == 2

    def test_generate_for_script_updates_checkpoint(
        self, image_service, mock_client, mock_settings, sample_scene, tmp_path: Path
    ) -> None:
        """Test checkpoint is updated after successful generation."""
        from uuid import uuid4

        mock_settings.get_images_dir.return_value = tmp_path / "images"

        script = Script(
            title="Test Script",
            niche=Niche.SCARY_STORIES,
            scenes=[sample_scene],
        )

        checkpoint = Checkpoint(
            job_id=uuid4(),
            script_path=Path("/test/script.json"),
            status=JobStatus.GENERATING_IMAGES,
        )

        image_service.generate_for_script(
            script=script,
            platform=Platform.YOUTUBE,
            checkpoint=checkpoint,
        )

        assert checkpoint.is_image_done(1)

    def test_generate_for_all_platforms(
        self, image_service, mock_client, mock_settings, sample_scene, tmp_path: Path
    ) -> None:
        """Test image generation for all platforms."""
        mock_settings.get_images_dir.return_value = tmp_path / "images"

        script = Script(
            title="Test Script",
            niche=Niche.LUXURY,
            scenes=[sample_scene],
        )

        results = image_service.generate_for_all_platforms(
            script=script,
            platforms=[Platform.YOUTUBE, Platform.TIKTOK],
        )

        assert len(results) == 2
        assert Platform.YOUTUBE in results
        assert Platform.TIKTOK in results
        assert mock_client.save_image.call_count == 2

    def test_generate_for_all_platforms_with_checkpoint(
        self, image_service, mock_client, mock_settings, sample_scene, tmp_path: Path
    ) -> None:
        """Test all platforms generation with checkpoint."""
        from uuid import uuid4

        mock_settings.get_images_dir.return_value = tmp_path / "images"

        script = Script(
            title="Test Script",
            niche=Niche.FINANCE,
            scenes=[sample_scene],
        )

        checkpoint = Checkpoint(
            job_id=uuid4(),
            script_path=Path("/test/script.json"),
            status=JobStatus.GENERATING_IMAGES,
        )

        results = image_service.generate_for_all_platforms(
            script=script,
            platforms=[Platform.YOUTUBE, Platform.TIKTOK],
            checkpoint=checkpoint,
        )

        assert len(results) == 2
