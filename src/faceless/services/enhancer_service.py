"""
Script enhancement service for the Faceless Content Pipeline.

This service uses GPT to enhance scripts for better engagement,
including improved narration, image prompts, and visual consistency.
"""

from typing import Any

from faceless.clients.azure_openai import AzureOpenAIClient
from faceless.config import get_settings
from faceless.core.enums import Niche
from faceless.core.models import Script, Scene, VisualStyle
from faceless.utils.logging import LoggerMixin

ENHANCE_SYSTEM_PROMPT = """You are an expert content creator for short-form videos.
Your task is to enhance scripts for maximum engagement while maintaining the original story.

Guidelines:
1. Improve narration for better flow and emotional impact
2. Enhance image prompts for more vivid, consistent visuals
3. Maintain the original story's essence
4. Keep scenes concise for short-form content
5. Add visual style consistency across scenes

Output format: Valid JSON matching the script structure."""

class EnhancerService(LoggerMixin):
    """
    Service for enhancing scripts with GPT.

    Improves scripts for better engagement:
    - Narration flow and emotional impact
    - Image prompt quality and consistency
    - Visual style coherence across scenes

    Example:
        >>> service = EnhancerService()
        >>> enhanced = service.enhance_script(script)
    """

    def __init__(self, client: AzureOpenAIClient | None = None) -> None:
        """
        Initialize enhancer service.

        Args:
            client: Optional Azure OpenAI client
        """
        self._client = client or AzureOpenAIClient()
        self._settings = get_settings()

    def enhance_script(
        self,
        script: Script,
        enhance_narration: bool = True,
        enhance_prompts: bool = True,
        add_visual_style: bool = True,
    ) -> Script:
        """
        Enhance a script using GPT.

        Args:
            script: Original script to enhance
            enhance_narration: Improve narration text
            enhance_prompts: Improve image prompts
            add_visual_style: Add/enhance visual style

        Returns:
            Enhanced script
        """
        self.logger.info(
            "Enhancing script",
            title=script.title,
            scene_count=len(script.scenes),
        )

        # Build enhancement prompt
        user_prompt = self._build_enhancement_prompt(
            script=script,
            enhance_narration=enhance_narration,
            enhance_prompts=enhance_prompts,
            add_visual_style=add_visual_style,
        )

        # Get enhanced content from GPT
        try:
            result = self._client.chat_json(
                system_prompt=ENHANCE_SYSTEM_PROMPT,
                user_prompt=user_prompt,
                temperature=0.7,
                max_tokens=4000,
            )

            # Update script with enhanced content
            enhanced_script = self._apply_enhancements(script, result)

            self.logger.info(
                "Script enhanced successfully",
                title=enhanced_script.title,
            )

            return enhanced_script

        except Exception as e:
            self.logger.error(
                "Script enhancement failed, returning original",
                error=str(e),
            )
            return script

    def _build_enhancement_prompt(
        self,
        script: Script,
        enhance_narration: bool,
        enhance_prompts: bool,
        add_visual_style: bool,
    ) -> str:
        """Build the enhancement prompt."""
        tasks = []
        if enhance_narration:
            tasks.append("Improve narration for better flow and emotional impact")
        if enhance_prompts:
            tasks.append("Enhance image prompts for more vivid, cinematic visuals")
        if add_visual_style:
            tasks.append("Add a visual_style object for consistency across scenes")

        scenes_json = [
            {
                "scene_number": s.scene_number,
                "narration": s.narration,
                "image_prompt": s.image_prompt,
            }
            for s in script.scenes
        ]

        return f"""Enhance this {script.niche.value} script.

Tasks:
{chr(10).join(f"- {t}" for t in tasks)}

Title: {script.title}
Niche: {script.niche.value}
Scenes: {scenes_json}

Return a JSON object with:
{{
    "title": "enhanced or original title",
    "visual_style": {{
        "environment": "consistent environment description",
        "color_mood": "color palette and mood",
        "texture": "surface and material details",
        "recurring_elements": {{"element_name": "description"}}
    }},
    "scenes": [
        {{
            "scene_number": 1,
            "narration": "enhanced narration",
            "image_prompt": "enhanced image prompt"
        }}
    ]
}}"""

    def _apply_enhancements(
        self,
        original: Script,
        enhancements: dict[str, Any],
    ) -> Script:
        """Apply enhancements to the original script."""
        # Update scenes
        enhanced_scenes = []
        enhancement_scenes = {s["scene_number"]: s for s in enhancements.get("scenes", [])}

        for scene in original.scenes:
            enhanced_data = enhancement_scenes.get(scene.scene_number, {})
            enhanced_scene = Scene(
                scene_number=scene.scene_number,
                narration=enhanced_data.get("narration", scene.narration),
                image_prompt=enhanced_data.get("image_prompt", scene.image_prompt),
                duration_estimate=scene.duration_estimate,
            )
            enhanced_scenes.append(enhanced_scene)

        # Create visual style if provided
        visual_style = None
        if "visual_style" in enhancements:
            vs = enhancements["visual_style"]
            visual_style = VisualStyle(
                environment=vs.get("environment", ""),
                color_mood=vs.get("color_mood", ""),
                texture=vs.get("texture", ""),
                recurring_elements=vs.get("recurring_elements", {}),
            )

        # Create enhanced script
        from datetime import datetime
        return Script(
            title=enhancements.get("title", original.title),
            niche=original.niche,
            scenes=enhanced_scenes,
            source=original.source,
            author=original.author,
            url=original.url,
            visual_style=visual_style or original.visual_style,
            created_at=original.created_at,
            enhanced_at=datetime.now(),
        )

    def generate_visual_style(
        self,
        script: Script,
    ) -> VisualStyle:
        """
        Generate a visual style for a script.

        Args:
            script: Script to generate style for

        Returns:
            Generated VisualStyle
        """
        prompt = f"""Create a visual style for this {script.niche.value} video:

Title: {script.title}
First scene: {script.scenes[0].narration[:200] if script.scenes else 'N/A'}

Return JSON with:
{{
    "environment": "consistent setting description",
    "color_mood": "color palette and emotional tone",
    "texture": "surface and material details",
    "recurring_elements": {{"name": "visual description"}}
}}"""

        try:
            result = self._client.chat_json(
                system_prompt="You are a visual designer for video content. Create cohesive visual styles.",
                user_prompt=prompt,
                temperature=0.7,
            )

            return VisualStyle(
                environment=result.get("environment", ""),
                color_mood=result.get("color_mood", ""),
                texture=result.get("texture", ""),
                recurring_elements=result.get("recurring_elements", {}),
            )

        except Exception as e:
            self.logger.warning(
                "Failed to generate visual style",
                error=str(e),
            )
            return VisualStyle()