"""
Image generation service for the Faceless Content Pipeline.

This service handles generating images for each scene in a script,
managing the Azure OpenAI client and saving results to disk.
"""

from pathlib import Path

from faceless.clients.azure_openai import AzureOpenAIClient
from faceless.config import get_settings
from faceless.core.enums import Niche, Platform
from faceless.core.exceptions import ImageGenerationError
from faceless.core.models import Checkpoint, Scene, Script
from faceless.utils.logging import LoggerMixin

class ImageService(LoggerMixin):
    """
    Service for generating images from scene prompts.

    Handles:
    - Image generation for each scene
    - Platform-specific sizing
    - Checkpointing for resume support
    - Visual style consistency

    Example:
        >>> service = ImageService()
        >>> service.generate_for_script(script, Platform.YOUTUBE)
    """

    def __init__(self, client: AzureOpenAIClient | None = None) -> None:
        """
        Initialize image service.

        Args:
            client: Optional Azure OpenAI client (creates one if not provided)
        """
        self._client = client or AzureOpenAIClient()
        self._settings = get_settings()

    def generate_for_scene(
        self,
        scene: Scene,
        niche: Niche,
        platform: Platform,
        output_dir: Path,
        visual_style_suffix: str = "",
    ) -> Path:
        """
        Generate an image for a single scene.

        Args:
            scene: Scene with image_prompt
            niche: Content niche for styling
            platform: Target platform for sizing
            output_dir: Directory to save images
            visual_style_suffix: Additional style prompt suffix

        Returns:
            Path to the generated image

        Raises:
            ImageGenerationError: On generation failure
        """
        # Build full prompt
        prompt = scene.image_prompt
        if visual_style_suffix:
            prompt = f"{prompt}. {visual_style_suffix}"

        # Generate filename
        filename = f"scene_{scene.scene_number:02d}_{platform.value}.png"
        output_path = output_dir / filename

        self.logger.info(
            "Generating image",
            scene_number=scene.scene_number,
            platform=platform.value,
            prompt_preview=prompt[:80],
        )

        try:
            self._client.save_image(
                prompt=prompt,
                output_path=output_path,
                platform=platform,
            )
            scene.image_path = output_path
            return output_path

        except Exception as e:
            raise ImageGenerationError(
                message=f"Failed to generate image for scene {scene.scene_number}",
                prompt=prompt,
                scene_number=scene.scene_number,
                api_error=str(e),
            ) from e

    def generate_for_script(
        self,
        script: Script,
        platform: Platform,
        checkpoint: Checkpoint | None = None,
    ) -> list[Path]:
        """
        Generate images for all scenes in a script.

        Args:
            script: Script with scenes
            platform: Target platform for sizing
            checkpoint: Optional checkpoint for resume support

        Returns:
            List of paths to generated images

        Raises:
            ImageGenerationError: If any scene fails
        """
        output_dir = self._settings.get_images_dir(script.niche) / script.safe_title
        output_dir.mkdir(parents=True, exist_ok=True)

        # Get visual style suffix if available
        style_suffix = ""
        if script.visual_style:
            style_suffix = script.visual_style.to_prompt_suffix()

        generated_paths: list[Path] = []
        errors: list[str] = []

        for scene in script.scenes:
            # Skip if already done (checkpoint support)
            if checkpoint and checkpoint.is_image_done(scene.scene_number):
                existing_path = output_dir / f"scene_{scene.scene_number:02d}_{platform.value}.png"
                if existing_path.exists():
                    self.logger.info(
                        "Skipping existing image",
                        scene_number=scene.scene_number,
                    )
                    scene.image_path = existing_path
                    generated_paths.append(existing_path)
                    continue

            try:
                path = self.generate_for_scene(
                    scene=scene,
                    niche=script.niche,
                    platform=platform,
                    output_dir=output_dir,
                    visual_style_suffix=style_suffix,
                )
                generated_paths.append(path)

                # Update checkpoint
                if checkpoint:
                    checkpoint.mark_image_done(scene.scene_number)

            except ImageGenerationError as e:
                self.logger.error(
                    "Scene image generation failed",
                    scene_number=scene.scene_number,
                    error=str(e),
                )
                errors.append(f"Scene {scene.scene_number}: {e}")
                # Continue with remaining scenes

        if errors:
            self.logger.warning(
                "Some images failed to generate",
                failed_count=len(errors),
                total_scenes=len(script.scenes),
            )

        return generated_paths

    def generate_for_all_platforms(
        self,
        script: Script,
        platforms: list[Platform],
        checkpoint: Checkpoint | None = None,
    ) -> dict[Platform, list[Path]]:
        """
        Generate images for a script across all platforms.

        Args:
            script: Script with scenes
            platforms: List of target platforms
            checkpoint: Optional checkpoint for resume support

        Returns:
            Dict mapping platform to list of image paths
        """
        results: dict[Platform, list[Path]] = {}

        for platform in platforms:
            self.logger.info(
                "Generating images for platform",
                platform=platform.value,
                scene_count=len(script.scenes),
            )

            paths = self.generate_for_script(
                script=script,
                platform=platform,
                checkpoint=checkpoint,
            )
            results[platform] = paths

        return results