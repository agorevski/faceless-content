"""
Main Pipeline - Full Production Workflow
Orchestrates all modules to create complete videos from scratch

Features:
- Automatic checkpointing for resume on failure
- Configuration validation before running
- Optional thumbnail and subtitle generation
- Multi-platform output support
- TikTok engagement optimization (hooks, hashtags, posting schedule)
"""

import argparse
import json
import os
import sys
from datetime import datetime

from faceless.utils.logging import get_logger, setup_logging

# Add pipeline directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

logger = get_logger(__name__)

from env_config import PATHS, validate_config
from image_generator import generate_from_script as generate_images
from script_enhancer import enhance_script
from story_scraper import fetch_and_process_stories, story_to_script
from tts_generator import generate_from_script as generate_audio
from video_assembler import assemble_from_script, create_tiktok_cuts

# Import TikTok engagement modules
try:
    from content_metadata import generate_content_metadata, save_metadata

    ENGAGEMENT_MODULES_AVAILABLE = True
except ImportError:
    ENGAGEMENT_MODULES_AVAILABLE = False


# =============================================================================
# CHECKPOINTING SYSTEM
# =============================================================================


def get_checkpoint_path(niche: str, script_name: str) -> str:
    """Get path to checkpoint file for a script."""
    checkpoint_dir = os.path.join(PATHS[niche]["output"], ".checkpoints")
    os.makedirs(checkpoint_dir, exist_ok=True)
    return os.path.join(checkpoint_dir, f"{script_name}_checkpoint.json")


def load_checkpoint(checkpoint_path: str) -> dict:
    """Load checkpoint data if it exists."""
    if os.path.exists(checkpoint_path):
        with open(checkpoint_path, encoding="utf-8") as f:
            return json.load(f)
    return {
        "completed_steps": [],
        "last_updated": None,
        "images_done": False,
        "audio_done": False,
        "videos_done": {},
    }


def save_checkpoint(checkpoint_path: str, checkpoint: dict):
    """Save checkpoint data."""
    checkpoint["last_updated"] = datetime.now().isoformat()
    with open(checkpoint_path, "w", encoding="utf-8") as f:
        json.dump(checkpoint, f, indent=2)


def clear_checkpoint(checkpoint_path: str):
    """Remove checkpoint file after successful completion."""
    if os.path.exists(checkpoint_path):
        os.remove(checkpoint_path)


# =============================================================================
# MAIN PIPELINE
# =============================================================================


def full_pipeline(
    niche: str,
    story_count: int = 1,
    platforms: list = None,
    skip_fetch: bool = False,
    script_path: str = None,
    add_music: bool = False,
    music_path: str = None,
    enhance: bool = False,
    generate_thumbs: bool = False,
    generate_subs: bool = False,
    burn_subs: bool = False,
    validate: bool = True,
    use_checkpoint: bool = True,
    generate_metadata: bool = True,
    series_name: str = None,
    tiktok_format: str = None,
) -> dict:
    """
    Run the complete content production pipeline.

    Args:
        niche: One of "scary-stories", "finance", "luxury"
        story_count: Number of stories to process
        platforms: List of platforms ["youtube", "tiktok"]
        skip_fetch: Skip fetching new stories, use existing scripts
        script_path: Path to a specific script to process
        add_music: Whether to add background music
        music_path: Path to background music file
        enhance: Whether to enhance scripts with GPT for better engagement
        generate_thumbs: Whether to generate thumbnail variants
        generate_subs: Whether to generate subtitle files
        burn_subs: Whether to burn subtitles into video
        validate: Whether to validate configuration first
        use_checkpoint: Whether to use checkpointing for resume
        generate_metadata: Whether to generate TikTok posting metadata
        series_name: Optional series name for recurring content
        tiktok_format: Optional TikTok format name (e.g., "pov_horror")

    Returns:
        Dict with paths to all created assets
    """

    if platforms is None:
        platforms = ["youtube", "tiktok"]

    setup_logging()

    logger.info(
        "Starting pipeline",
        niche=niche,
        platforms=platforms,
        series=series_name,
        format=tiktok_format,
        timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    )

    results = {
        "niche": niche,
        "platforms": platforms,
        "scripts": [],
        "videos": [],
        "errors": [],
    }

    # Step 1: Get scripts
    logger.info("Step 1: Getting scripts")

    script_paths = []

    if script_path:
        # Use provided script
        if os.path.exists(script_path):
            script_paths = [script_path]
            logger.info("Using provided script", path=script_path)
        else:
            logger.error("Script not found", path=script_path)
            return results
    elif skip_fetch:
        # Use existing scripts in directory
        script_dir = PATHS[niche]["scripts"]
        if os.path.exists(script_dir):
            script_paths = [
                os.path.join(script_dir, f)
                for f in os.listdir(script_dir)
                if f.endswith("_script.json")
            ][:story_count]
            logger.info("Found existing scripts", count=len(script_paths))
        else:
            logger.error("No scripts directory found")
            return results
    else:
        # Fetch new stories
        script_paths = fetch_and_process_stories(niche, count=story_count)

    results["scripts"] = script_paths

    if not script_paths:
        logger.error("No scripts to process")
        return results

    # Step 1.5: Enhance scripts (optional)
    if enhance:
        logger.info("Step 1.5: Enhancing scripts with GPT")
        enhanced_paths = []
        for sp in script_paths:
            try:
                enhanced_path = enhance_script(sp, niche)
                enhanced_paths.append(enhanced_path)
            except Exception as e:
                logger.warning(
                    "Enhancement failed, continuing with original",
                    script=sp,
                    error=str(e),
                )
                enhanced_paths.append(sp)
                results["errors"].append(f"Enhancement: {e}")
        script_paths = enhanced_paths

    # Process each script
    for script_path in script_paths:
        logger.info("Processing script", script=os.path.basename(script_path))

        try:
            # Step 2: Generate Images
            logger.info("Step 2: Generating images")

            for platform in platforms:
                logger.info("Generating images for platform", platform=platform)
                try:
                    image_paths = generate_images(script_path, niche, platform)
                    logger.info(
                        "Images generated",
                        platform=platform,
                        count=len([p for p in image_paths if p]),
                    )
                except Exception as e:
                    logger.error("Image generation failed", platform=platform, error=str(e))
                    results["errors"].append(f"Images ({platform}): {e}")

            # Step 3: Generate Audio
            logger.info("Step 3: Generating audio")

            try:
                audio_paths = generate_audio(script_path, niche)
                logger.info("Audio files generated", count=len([p for p in audio_paths if p]))
            except Exception as e:
                logger.error("Audio generation failed", error=str(e))
                results["errors"].append(f"Audio: {e}")
                continue

            # Step 4: Assemble Videos
            logger.info("Step 4: Assembling videos")

            for platform in platforms:
                logger.info("Assembling video for platform", platform=platform)
                try:
                    video_path = assemble_from_script(
                        script_path,
                        niche,
                        platform,
                        add_music=add_music,
                        music_path=music_path,
                    )

                    video_info = {
                        "platform": platform,
                        "path": video_path,
                        "script": script_path,
                    }

                    # Generate TikTok metadata for TikTok videos
                    if (
                        platform == "tiktok"
                        and generate_metadata
                        and ENGAGEMENT_MODULES_AVAILABLE
                    ):
                        try:
                            # Load script for title and duration info
                            with open(script_path, encoding="utf-8") as f:
                                script_data = json.load(f)

                            # Estimate duration from scenes
                            total_duration = sum(
                                scene.get("duration_estimate", 10)
                                for scene in script_data.get("scenes", [])
                            )

                            # Determine part number for series
                            part_number = None
                            if series_name:
                                existing_videos = [
                                    v
                                    for v in results["videos"]
                                    if v["platform"] == "tiktok"
                                ]
                                part_number = len(existing_videos) + 1

                            metadata = generate_content_metadata(
                                niche=niche,
                                title=script_data.get("title", "Untitled"),
                                video_duration=total_duration,
                                format_name=tiktok_format,
                                series_name=series_name,
                                part_number=part_number,
                            )

                            # Save metadata alongside video
                            metadata_path = video_path.replace(".mp4", "_metadata.json")
                            save_metadata(metadata, metadata_path)
                            video_info["metadata_path"] = metadata_path
                            video_info["hashtags"] = metadata["hashtag_string"]
                            video_info["optimal_posting_time"] = metadata[
                                "optimal_posting"
                            ]["formatted"]

                            logger.info(
                                "Metadata saved",
                                metadata_path=os.path.basename(metadata_path),
                                hashtags=metadata['hashtag_string'][:50],
                                best_posting_time=metadata['optimal_posting']['formatted'],
                            )

                        except Exception as e:
                            logger.warning("Metadata generation failed", error=str(e))

                    results["videos"].append(video_info)
                    logger.info("Video created", path=video_path)

                    # Create TikTok cuts if this is a long YouTube video
                    if platform == "youtube" and "tiktok" in platforms:
                        logger.info("Creating TikTok cuts")
                        tiktok_dir = os.path.join(PATHS[niche]["output"], "tiktok_cuts")
                        cuts = create_tiktok_cuts(video_path, tiktok_dir)
                        logger.info("TikTok segments created", count=len(cuts))

                except Exception as e:
                    logger.error("Video assembly failed", platform=platform, error=str(e))
                    results["errors"].append(f"Video ({platform}): {e}")

        except Exception as e:
            logger.error("Failed to process script", script=script_path, error=str(e))
            results["errors"].append(f"Script {script_path}: {e}")

    # Summary
    logger.info(
        "Pipeline complete",
        scripts_processed=len(script_paths),
        videos_created=len(results['videos']),
        error_count=len(results['errors']),
    )

    if results["videos"]:
        for video in results["videos"]:
            logger.info(
                "Created video",
                path=video['path'],
                optimal_posting_time=video.get('optimal_posting_time'),
            )

    if results["errors"]:
        for error in results["errors"]:
            logger.error("Error encountered", error=error)

    return results


def quick_generate(
    niche: str,
    title: str,
    content: str,
    platforms: list = None,
) -> dict:
    """
    Quick generate a video from provided text content.
    Useful for custom stories or content not from Reddit.

    Args:
        niche: One of "scary-stories", "finance", "luxury"
        title: Title for the content
        content: The actual text content
        platforms: List of platforms

    Returns:
        Dict with paths to created assets
    """

    if platforms is None:
        platforms = ["youtube", "tiktok"]

    # Create a story dict
    story = {
        "title": title,
        "content": content,
        "author": "Custom",
        "source": "Manual Input",
        "url": "",
    }

    # Convert to script
    script = story_to_script(story, niche)

    # Save script
    safe_title = title.lower().replace(" ", "-")[:30]
    filename = f"{safe_title}_script.json"
    output_path = os.path.join(PATHS[niche]["scripts"], filename)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(script, f, indent=2, ensure_ascii=False)

    # Run pipeline on this script
    return full_pipeline(
        niche=niche,
        script_path=output_path,
        platforms=platforms,
    )


# =============================================================================
# CLI INTERFACE
# =============================================================================


def main():
    parser = argparse.ArgumentParser(
        description="Faceless Content Production Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Fetch and produce 3 scary story videos
  python pipeline.py --niche scary-stories --count 3

  # Process existing scripts only (no fetching)
  python pipeline.py --niche finance --skip-fetch

  # Process a specific script file
  python pipeline.py --niche luxury --script path/to/script.json

  # YouTube only (no TikTok)
  python pipeline.py --niche scary-stories --platform youtube

  # Add background music
  python pipeline.py --niche scary-stories --music path/to/music.mp3

  # Enhance scripts with GPT for viral engagement
  python pipeline.py --niche scary-stories --script path/to/script.json --enhance

  # Generate thumbnails and subtitles
  python pipeline.py --niche finance --script path/to/script.json --thumbnails --subtitles

  # Validate configuration only
  python pipeline.py --niche scary-stories --validate-only
        """,
    )

    parser.add_argument(
        "--niche",
        "-n",
        choices=["scary-stories", "finance", "luxury"],
        required=True,
        help="Content niche to produce",
    )
    parser.add_argument(
        "--count",
        "-c",
        type=int,
        default=1,
        help="Number of stories to process (default: 1)",
    )
    parser.add_argument(
        "--platform",
        "-p",
        choices=["youtube", "tiktok", "both"],
        default="both",
        help="Target platform(s) (default: both)",
    )
    parser.add_argument(
        "--skip-fetch",
        action="store_true",
        help="Skip fetching new stories, use existing scripts",
    )
    parser.add_argument(
        "--script", "-s", help="Path to a specific script file to process"
    )
    parser.add_argument("--music", "-m", help="Path to background music file")
    parser.add_argument(
        "--enhance",
        "-e",
        action="store_true",
        help="Enhance scripts with GPT for better engagement",
    )
    parser.add_argument(
        "--thumbnails",
        "-t",
        action="store_true",
        help="Generate thumbnail variants for A/B testing",
    )
    parser.add_argument(
        "--subtitles",
        action="store_true",
        help="Generate subtitle files (SRT/VTT)",
    )
    parser.add_argument(
        "--burn-subs",
        action="store_true",
        help="Burn subtitles directly into the video",
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Only validate configuration, don't run pipeline",
    )
    parser.add_argument(
        "--no-validate",
        action="store_true",
        help="Skip configuration validation",
    )
    parser.add_argument(
        "--no-metadata",
        action="store_true",
        help="Skip TikTok metadata generation (hashtags, posting times)",
    )
    parser.add_argument(
        "--series",
        help="Series name for recurring content (e.g., '3AM Stories')",
    )
    parser.add_argument(
        "--format",
        choices=[
            "pov_horror",
            "green_screen_storytime",
            "rules_of_location",
            "creepy_text_messages",
            "split_screen_reaction",
            "ranking_viewer_stories",
            "financial_red_flags_dating",
            "things_that_scream_broke",
            "roast_my_spending",
            "money_hot_takes",
            "what_x_gets_you",
            "i_did_the_math",
            "guess_the_price",
            "rich_people_secrets",
            "pov_afford_anything",
            "luxury_asmr",
            "cheap_vs_expensive",
            "billionaire_day_in_life",
        ],
        help="TikTok content format to use",
    )

    args = parser.parse_args()

    # Validate only mode
    if args.validate_only:
        success = validate_config()
        sys.exit(0 if success else 1)

    # Determine platforms
    platforms = ["youtube", "tiktok"] if args.platform == "both" else [args.platform]

    # Run pipeline
    results = full_pipeline(
        niche=args.niche,
        story_count=args.count,
        platforms=platforms,
        skip_fetch=args.skip_fetch,
        script_path=args.script,
        add_music=bool(args.music),
        music_path=args.music,
        enhance=args.enhance,
        generate_thumbs=args.thumbnails,
        generate_subs=args.subtitles,
        burn_subs=args.burn_subs,
        validate=not args.no_validate,
        generate_metadata=not args.no_metadata,
        series_name=args.series,
        tiktok_format=args.format,
    )

    # Exit with error code if there were failures
    if results["errors"] and not results["videos"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
