"""
Pydantic models for the Faceless Content Pipeline.

This module defines all the data models used throughout the application,
providing validation, serialization, and type safety.

Models are organized into:
- Content Models: Scene, Script, VisualStyle
- Job Models: Job, JobResult, Checkpoint
- Asset Models: GeneratedImage, GeneratedAudio, GeneratedVideo
"""

from datetime import datetime
from pathlib import Path
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator, model_validator

from faceless.core.enums import JobStatus, Niche, Platform, Voice

# =============================================================================
# Visual Style Models
# =============================================================================


class RecurringElement(BaseModel):
    """A visual element that appears consistently across scenes."""

    name: str = Field(..., description="Name of the recurring element")
    description: str = Field(..., description="Detailed visual description")


class VisualStyle(BaseModel):
    """
    Visual style configuration for maintaining artistic consistency.

    This is used to ensure all generated images in a video share
    a cohesive visual language.
    """

    environment: str = Field(
        default="",
        description="Consistent setting/environment description",
    )
    color_mood: str = Field(
        default="",
        description="Color palette and emotional tone",
    )
    texture: str = Field(
        default="",
        description="Surface and material details",
    )
    recurring_elements: dict[str, str] = Field(
        default_factory=dict,
        description="Named visual elements with descriptions",
    )

    def to_prompt_suffix(self) -> str:
        """Convert visual style to a prompt suffix for image generation."""
        parts = []
        if self.environment:
            parts.append(f"Setting: {self.environment}")
        if self.color_mood:
            parts.append(f"Color mood: {self.color_mood}")
        if self.texture:
            parts.append(f"Textures: {self.texture}")
        return " | ".join(parts)


# =============================================================================
# Scene and Script Models
# =============================================================================


class Scene(BaseModel):
    """
    A single scene within a video script.

    Each scene represents one segment of the final video with
    its own narration and generated image.
    """

    scene_number: int = Field(..., ge=1, description="Scene sequence number")
    narration: str = Field(..., min_length=1, description="Text to be spoken")
    image_prompt: str = Field(..., min_length=1, description="Image generation prompt")
    duration_estimate: float = Field(
        default=10.0,
        ge=0.1,
        description="Estimated duration in seconds",
    )

    # Generated asset paths (populated during pipeline execution)
    image_path: Path | None = Field(default=None, description="Path to generated image")
    audio_path: Path | None = Field(default=None, description="Path to generated audio")
    video_path: Path | None = Field(default=None, description="Path to scene video")

    @field_validator("narration", "image_prompt")
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        """Strip leading/trailing whitespace from text fields."""
        return v.strip()

    @property
    def word_count(self) -> int:
        """Number of words in the narration."""
        return len(self.narration.split())

    @property
    def estimated_duration_from_words(self) -> float:
        """Estimate duration based on word count (~150 words/minute)."""
        return self.word_count / 2.5  # 150 words per minute = 2.5 words per second


class Script(BaseModel):
    """
    A complete video script with metadata and scenes.

    This is the primary data structure for content that flows
    through the pipeline.
    """

    title: str = Field(..., min_length=1, max_length=200, description="Video title")
    niche: Niche = Field(..., description="Content niche category")
    scenes: list[Scene] = Field(..., min_length=1, description="List of scenes")

    # Source metadata
    source: str = Field(default="", description="Content source (e.g., r/nosleep)")
    author: str = Field(default="", description="Original author")
    url: str = Field(default="", description="Source URL")

    # Visual consistency
    visual_style: VisualStyle | None = Field(
        default=None,
        description="Visual style for consistent imagery",
    )

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)
    enhanced_at: datetime | None = Field(default=None)

    # Generated output paths
    output_paths: dict[str, Path] = Field(
        default_factory=dict,
        description="Paths to final outputs by platform",
    )

    @field_validator("title")
    @classmethod
    def clean_title(cls, v: str) -> str:
        """Clean and normalize the title."""
        return v.strip()

    @model_validator(mode="after")
    def validate_scene_numbers(self) -> "Script":
        """Ensure scene numbers are sequential starting from 1."""
        for i, scene in enumerate(self.scenes, 1):
            if scene.scene_number != i:
                # Auto-fix scene numbers
                scene.scene_number = i
        return self

    @property
    def total_duration(self) -> float:
        """Total estimated duration in seconds."""
        return sum(scene.duration_estimate for scene in self.scenes)

    @property
    def total_words(self) -> int:
        """Total word count across all scenes."""
        return sum(scene.word_count for scene in self.scenes)

    @property
    def safe_title(self) -> str:
        """Filename-safe version of the title."""
        import re

        safe = re.sub(r"[^\w\s-]", "", self.title[:50])
        safe = re.sub(r"[-\s]+", "-", safe).strip("-")
        return safe.lower()

    def get_scene(self, scene_number: int) -> Scene | None:
        """Get a scene by its number."""
        for scene in self.scenes:
            if scene.scene_number == scene_number:
                return scene
        return None

    def to_json_file(self, path: Path) -> None:
        """Save script to a JSON file."""
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.model_dump_json(indent=2))

    @classmethod
    def from_json_file(cls, path: Path) -> "Script":
        """Load script from a JSON file."""
        with open(path, encoding="utf-8") as f:
            import json

            data = json.load(f)
        return cls.model_validate(data)


# =============================================================================
# Job Models
# =============================================================================


class JobConfig(BaseModel):
    """Configuration for a content generation job."""

    niche: Niche = Field(..., description="Content niche")
    platforms: list[Platform] = Field(
        default=[Platform.YOUTUBE, Platform.TIKTOK],
        description="Target platforms",
    )
    enhance_script: bool = Field(
        default=False,
        description="Whether to enhance script with GPT",
    )
    generate_thumbnails: bool = Field(
        default=True,
        description="Whether to generate thumbnails",
    )
    generate_subtitles: bool = Field(
        default=True,
        description="Whether to generate subtitles",
    )
    burn_subtitles: bool = Field(
        default=False,
        description="Whether to burn subtitles into video",
    )
    music_path: Path | None = Field(
        default=None,
        description="Background music file path",
    )


class JobResult(BaseModel):
    """Results from a completed job."""

    success: bool = Field(..., description="Whether job completed successfully")
    script_path: Path | None = Field(default=None)
    video_paths: dict[str, Path] = Field(default_factory=dict)
    thumbnail_paths: list[Path] = Field(default_factory=list)
    subtitle_paths: dict[str, Path] = Field(default_factory=dict)
    errors: list[str] = Field(default_factory=list)
    duration_seconds: float = Field(default=0.0)


class Job(BaseModel):
    """
    A content generation job with status tracking.

    Jobs are the primary unit of work in the pipeline,
    tracking progress and results.
    """

    id: UUID = Field(default_factory=uuid4, description="Unique job identifier")
    config: JobConfig = Field(..., description="Job configuration")
    status: JobStatus = Field(default=JobStatus.PENDING)
    script: Script | None = Field(default=None)
    result: JobResult | None = Field(default=None)

    # Timing
    created_at: datetime = Field(default_factory=datetime.now)
    started_at: datetime | None = Field(default=None)
    completed_at: datetime | None = Field(default=None)

    # Error tracking
    error_message: str | None = Field(default=None)
    retry_count: int = Field(default=0)

    @property
    def duration(self) -> float | None:
        """Job duration in seconds, if completed."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None

    def start(self) -> None:
        """Mark job as started."""
        self.started_at = datetime.now()

    def complete(self, result: JobResult) -> None:
        """Mark job as completed with result."""
        self.completed_at = datetime.now()
        self.result = result
        self.status = JobStatus.COMPLETED if result.success else JobStatus.FAILED

    def fail(self, error: str) -> None:
        """Mark job as failed with error."""
        self.completed_at = datetime.now()
        self.status = JobStatus.FAILED
        self.error_message = error


# =============================================================================
# Checkpoint Model
# =============================================================================


class Checkpoint(BaseModel):
    """
    Checkpoint for resuming interrupted jobs.

    Stores the state of a job at a specific point in the pipeline,
    allowing for recovery after failures.
    """

    job_id: UUID = Field(..., description="ID of the associated job")
    script_path: Path = Field(..., description="Path to the script file")
    status: JobStatus = Field(..., description="Status when checkpoint was created")

    # Progress tracking
    completed_steps: list[str] = Field(default_factory=list)
    images_generated: list[int] = Field(
        default_factory=list,
        description="Scene numbers with generated images",
    )
    audio_generated: list[int] = Field(
        default_factory=list,
        description="Scene numbers with generated audio",
    )
    videos_generated: dict[str, list[int]] = Field(
        default_factory=dict,
        description="Platform -> scene numbers with videos",
    )

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    def update(self) -> None:
        """Update the timestamp."""
        self.updated_at = datetime.now()

    def mark_image_done(self, scene_number: int) -> None:
        """Mark an image as generated."""
        if scene_number not in self.images_generated:
            self.images_generated.append(scene_number)
            self.update()

    def mark_audio_done(self, scene_number: int) -> None:
        """Mark audio as generated."""
        if scene_number not in self.audio_generated:
            self.audio_generated.append(scene_number)
            self.update()

    def mark_video_done(self, platform: str, scene_number: int) -> None:
        """Mark a video segment as generated."""
        if platform not in self.videos_generated:
            self.videos_generated[platform] = []
        if scene_number not in self.videos_generated[platform]:
            self.videos_generated[platform].append(scene_number)
            self.update()

    def is_image_done(self, scene_number: int) -> bool:
        """Check if image is already generated."""
        return scene_number in self.images_generated

    def is_audio_done(self, scene_number: int) -> bool:
        """Check if audio is already generated."""
        return scene_number in self.audio_generated

    def is_video_done(self, platform: str, scene_number: int) -> bool:
        """Check if video segment is already generated."""
        return scene_number in self.videos_generated.get(platform, [])

    def save(self, path: Path) -> None:
        """Save checkpoint to file."""
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.model_dump_json(indent=2))

    @classmethod
    def load(cls, path: Path) -> "Checkpoint":
        """Load checkpoint from file."""
        with open(path, encoding="utf-8") as f:
            import json

            data = json.load(f)
        return cls.model_validate(data)


# =============================================================================
# Asset Models
# =============================================================================


class GeneratedImage(BaseModel):
    """Metadata for a generated image."""

    scene_number: int
    platform: Platform
    path: Path
    prompt: str
    enhanced_prompt: str | None = None
    generated_at: datetime = Field(default_factory=datetime.now)


class GeneratedAudio(BaseModel):
    """Metadata for generated audio."""

    scene_number: int
    path: Path
    text: str
    voice: Voice
    duration_seconds: float | None = None
    generated_at: datetime = Field(default_factory=datetime.now)


class GeneratedVideo(BaseModel):
    """Metadata for a generated video segment or final video."""

    platform: Platform
    path: Path
    duration_seconds: float
    resolution: tuple[int, int]
    is_final: bool = False
    generated_at: datetime = Field(default_factory=datetime.now)


class Thumbnail(BaseModel):
    """Metadata for a generated thumbnail."""

    path: Path
    concept: str
    prompt: str
    variant_number: int = 1
    generated_at: datetime = Field(default_factory=datetime.now)


class SubtitleFile(BaseModel):
    """Metadata for generated subtitles."""

    path: Path
    format: str  # "srt", "vtt", "json"
    word_count: int
    generated_at: datetime = Field(default_factory=datetime.now)
