"""
Story Scraper Module

⚠️ NOTE: Partially replaced by faceless.services.research_service and
faceless.services.trending_service. Consider using those for new code.

Fetches content from various free sources for video scripts
"""

import json
import os
import re
from datetime import datetime
from typing import Optional

import requests
from env_config import PATHS
from faceless.utils.logging import get_logger

logger = get_logger(__name__)


def clean_text(text: str) -> str:
    """Clean and normalize text from web sources."""
    # Remove markdown formatting
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"\*(.+?)\*", r"\1", text)
    text = re.sub(r"\_\_(.+?)\_\_", r"\1", text)
    text = re.sub(r"\_(.+?)\_", r"\1", text)
    text = re.sub(r"\~\~(.+?)\~\~", r"\1", text)

    # Remove links
    text = re.sub(r"\[(.+?)\]\(.+?\)", r"\1", text)

    # Remove extra whitespace
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r" {2,}", " ", text)

    # Remove Reddit-specific formatting
    text = re.sub(r"\^(.+)", r"\1", text)  # Superscript
    text = re.sub(r"&amp;", "&", text)
    text = re.sub(r"&lt;", "<", text)
    text = re.sub(r"&gt;", ">", text)

    return text.strip()


def fetch_reddit_stories(
    subreddit: str = "nosleep",
    limit: int = 10,
    time_filter: str = "month",
    min_score: int = 100,
) -> list:
    """
    Fetch top stories from a subreddit.

    Args:
        subreddit: Name of the subreddit
        limit: Maximum number of posts to fetch
        time_filter: "hour", "day", "week", "month", "year", "all"
        min_score: Minimum upvote score

    Returns:
        List of story dicts with title, content, author, score, url
    """

    url = f"https://www.reddit.com/r/{subreddit}/top.json"
    params = {
        "limit": limit * 2,  # Fetch more to filter by score
        "t": time_filter,
    }
    headers = {"User-Agent": "FacelessContent/1.0 (Educational Project)"}

    logger.info("Fetching stories from subreddit", subreddit=subreddit)

    try:
        response = requests.get(url, params=params, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()

        stories = []
        for post in data["data"]["children"]:
            post_data = post["data"]

            # Skip if below minimum score
            if post_data.get("score", 0) < min_score:
                continue

            # Skip if no text content
            if not post_data.get("selftext"):
                continue

            story = {
                "title": post_data.get("title", ""),
                "content": clean_text(post_data.get("selftext", "")),
                "author": post_data.get("author", "[deleted]"),
                "score": post_data.get("score", 0),
                "url": f"https://reddit.com{post_data.get('permalink', '')}",
                "source": f"r/{subreddit}",
                "fetched_at": datetime.now().isoformat(),
            }

            stories.append(story)

            if len(stories) >= limit:
                break

        logger.info("Found stories", count=len(stories), subreddit=subreddit)
        return stories

    except requests.exceptions.RequestException as e:
        logger.error("Failed to fetch stories", subreddit=subreddit, error=str(e))
        return []


def fetch_creepypasta(limit: int = 10) -> list:
    """
    Fetch stories from Creepypasta Wiki API.

    Note: This is a simplified version. The actual implementation
    would need to scrape the wiki pages.

    Args:
        limit: Maximum number of stories to fetch

    Returns:
        List of story dicts
    """

    # Creepypasta doesn't have a public API, so we'll use Reddit's
    # creepypasta subreddit as an alternative
    return fetch_reddit_stories("creepypasta", limit=limit)


def save_story(story: dict, niche: str, filename: str = None) -> str:
    """
    Save a story to the scripts directory as JSON.

    Args:
        story: Story dict from fetch functions
        niche: One of "scary-stories", "finance", "luxury"
        filename: Optional custom filename

    Returns:
        Path to the saved file
    """

    if not filename:
        # Create filename from title
        safe_title = re.sub(r"[^\w\s-]", "", story["title"][:50])
        safe_title = re.sub(r"[-\s]+", "-", safe_title).strip("-")
        filename = f"{safe_title.lower()}.json"

    output_dir = PATHS[niche]["scripts"]
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, filename)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(story, f, indent=2, ensure_ascii=False)

    logger.info("Story saved", path=output_path)
    return output_path


def story_to_script(
    story: dict,
    niche: str,
    max_scenes: int = 10,
    words_per_scene: int = 150,
) -> dict:
    """
    Convert a raw story into a video script with scenes.

    Each scene has:
    - narration: Text to be spoken
    - image_prompt: Description for AI image generation

    Args:
        story: Story dict
        niche: One of "scary-stories", "finance", "luxury"
        max_scenes: Maximum number of scenes
        words_per_scene: Target words per scene

    Returns:
        Script dict ready for video production
    """

    content = story["content"]
    title = story["title"]

    # Split into paragraphs
    paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]

    # Merge short paragraphs, split long ones
    scenes = []
    current_text = ""

    for para in paragraphs:
        current_text += " " + para if current_text else para

        word_count = len(current_text.split())
        if word_count >= words_per_scene:
            scenes.append(current_text.strip())
            current_text = ""

            if len(scenes) >= max_scenes:
                break

    # Don't forget the last bit
    if current_text and len(scenes) < max_scenes:
        scenes.append(current_text.strip())

    # Generate image prompts based on niche
    script = {
        "title": title,
        "source": story.get("source", ""),
        "author": story.get("author", ""),
        "url": story.get("url", ""),
        "niche": niche,
        "created_at": datetime.now().isoformat(),
        "scenes": [],
    }

    for i, narration in enumerate(scenes, 1):
        # Generate contextual image prompt
        image_prompt = generate_image_prompt(narration, niche, i, len(scenes))

        script["scenes"].append(
            {
                "scene_number": i,
                "narration": narration,
                "image_prompt": image_prompt,
                "duration_estimate": len(narration.split())
                / 2.5,  # ~150 words per minute
            }
        )

    return script


def generate_image_prompt(
    narration: str,
    niche: str,
    scene_num: int,
    total_scenes: int,
) -> str:
    """
    Generate an image prompt based on narration content.

    This is a simple keyword-based approach. For better results,
    you could use an LLM to analyze the narration.

    Args:
        narration: The scene's narration text
        niche: One of "scary-stories", "finance", "luxury"
        scene_num: Current scene number
        total_scenes: Total number of scenes

    Returns:
        Image generation prompt
    """

    # Extract key nouns/concepts (simple approach)
    words = narration.lower().split()

    # Niche-specific prompt templates
    if niche == "scary-stories":
        # Horror-themed prompts
        if scene_num == 1:
            base = "Establishing shot, ominous atmosphere"
        elif scene_num == total_scenes:
            base = "Climactic horror scene, tension peak"
        else:
            base = "Dark atmospheric scene"

        # Look for location keywords
        locations = [
            "house",
            "forest",
            "room",
            "door",
            "window",
            "stairs",
            "basement",
            "attic",
            "road",
            "car",
            "bedroom",
            "kitchen",
        ]
        found_location = next(
            (loc for loc in locations if loc in words), "shadowy environment"
        )

        # Look for creature/entity keywords
        entities = [
            "figure",
            "shadow",
            "creature",
            "man",
            "woman",
            "child",
            "eyes",
            "face",
            "hand",
            "thing",
        ]
        found_entity = next((ent for ent in entities if ent in words), None)

        prompt = f"{base}, {found_location}"
        if found_entity:
            prompt += f", mysterious {found_entity} partially visible"
        prompt += ", horror movie cinematography, volumetric fog, dramatic shadows"

    elif niche == "finance":
        # Finance-themed prompts
        concepts = [
            "money",
            "investing",
            "stocks",
            "bank",
            "wallet",
            "credit",
            "debt",
            "savings",
            "wealth",
            "budget",
        ]
        found_concept = next((c for c in concepts if c in words), "financial growth")

        prompt = f"Professional visualization of {found_concept}, modern minimalist style, charts and graphs subtle background, green and gold accents, business professional aesthetic"

    elif niche == "luxury":
        # Luxury-themed prompts
        items = [
            "car",
            "watch",
            "yacht",
            "mansion",
            "jet",
            "diamond",
            "gold",
            "champagne",
            "designer",
            "penthouse",
        ]
        found_item = next((item for item in items if item in words), "luxury lifestyle")

        prompt = f"Elegant {found_item}, ultra high-end luxury, cinematic lighting, rich textures, gold and black color scheme, aspirational lifestyle photography"

    else:
        prompt = f"Scene {scene_num}: {narration[:100]}"

    return prompt


def fetch_and_process_stories(
    niche: str,
    count: int = 5,
) -> list:
    """
    Fetch stories and convert them to production-ready scripts.

    Args:
        niche: One of "scary-stories", "finance", "luxury"
        count: Number of stories to fetch

    Returns:
        List of paths to saved script files
    """

    logger.info("Starting story fetch", niche=niche, count=count)

    # Different sources for different niches
    if niche == "scary-stories":
        stories = fetch_reddit_stories("nosleep", limit=count)
        if len(stories) < count:
            stories.extend(
                fetch_reddit_stories("LetsNotMeet", limit=count - len(stories))
            )
    elif niche == "finance":
        stories = fetch_reddit_stories("personalfinance", limit=count)
    elif niche == "luxury":
        stories = fetch_reddit_stories("luxury", limit=count)
    else:
        logger.warning("Unknown niche specified", niche=niche)
        return []

    script_paths = []
    for story in stories:
        # Convert to script
        script = story_to_script(story, niche)

        # Save script
        safe_title = re.sub(r"[^\w\s-]", "", story["title"][:50])
        safe_title = re.sub(r"[-\s]+", "-", safe_title).strip("-")
        filename = f"{safe_title.lower()}_script.json"

        output_dir = PATHS[niche]["scripts"]
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, filename)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(script, f, indent=2, ensure_ascii=False)

        logger.info("Script created", path=output_path, title=story["title"][:50])
        script_paths.append(output_path)

    return script_paths


# =============================================================================
# STANDALONE USAGE
# =============================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Fetch and process stories for video scripts"
    )
    parser.add_argument(
        "--niche", "-n", choices=["scary-stories", "finance", "luxury"], required=True
    )
    parser.add_argument(
        "--count", "-c", type=int, default=5, help="Number of stories to fetch"
    )
    parser.add_argument("--subreddit", "-s", help="Specific subreddit to fetch from")

    args = parser.parse_args()

    if args.subreddit:
        stories = fetch_reddit_stories(args.subreddit, limit=args.count)
        for story in stories:
            save_story(story, args.niche)
    else:
        fetch_and_process_stories(args.niche, args.count)
