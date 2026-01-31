"""
Quick script to finish video assembly from existing assets
"""

import os
import sys
import subprocess

# Paths
BASE = r"C:\Users\kat_l\clawd\faceless-content\scary-stories"
IMAGES = os.path.join(BASE, "images")
AUDIO = os.path.join(BASE, "audio")
VIDEOS = os.path.join(BASE, "videos")
OUTPUT = os.path.join(BASE, "output")

os.makedirs(OUTPUT, exist_ok=True)


def get_audio_duration(audio_path):
    """Get duration of audio file"""
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        audio_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return float(result.stdout.strip())


def create_segment(i):
    """Create a single video segment"""
    image = os.path.join(IMAGES, f"stairs-in-the-woods_script_{i:03d}.png")
    audio = os.path.join(AUDIO, f"stairs-in-the-woods_script_{i:03d}.mp3")
    output = os.path.join(VIDEOS, f"stairs-in-the-woods_script_{i:03d}.mp4")

    if os.path.exists(output):
        print(f"   Segment {i} already exists, skipping")
        return output

    if not os.path.exists(image) or not os.path.exists(audio):
        print(f"   Missing assets for segment {i}")
        return None

    duration = get_audio_duration(audio)
    fps = 30

    # Simple scaling without Ken Burns (faster)
    cmd = [
        "ffmpeg",
        "-y",
        "-loop",
        "1",
        "-i",
        image,
        "-i",
        audio,
        "-vf",
        "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2",
        "-c:v",
        "libx264",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-shortest",
        "-pix_fmt",
        "yuv420p",
        output,
    ]

    print(f"   Creating segment {i}...")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"   Error: {result.stderr[:200]}")
        return None

    print(f"   ✅ Created segment {i}")
    return output


def concatenate_all():
    """Concatenate all segments"""
    segments = []
    for i in range(1, 8):
        seg = os.path.join(VIDEOS, f"stairs-in-the-woods_script_{i:03d}.mp4")
        if os.path.exists(seg):
            segments.append(seg)

    if len(segments) != 7:
        print(f"   Only {len(segments)} segments found, expected 7")
        return None

    # Create concat file
    list_file = os.path.join(VIDEOS, "concat_list.txt")
    with open(list_file, "w") as f:
        for seg in segments:
            safe_path = seg.replace("\\", "/")
            f.write(f"file '{safe_path}'\n")

    output = os.path.join(OUTPUT, "stairs-in-the-woods_youtube.mp4")

    cmd = [
        "ffmpeg",
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        list_file,
        "-c",
        "copy",
        output,
    ]

    print("   Concatenating all segments...")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"   Error: {result.stderr[:200]}")
        return None

    print(f"   ✅ Final video: {output}")
    return output


if __name__ == "__main__":
    print("=" * 60)
    print("Finishing video assembly...")
    print("=" * 60)

    # Create any missing segments
    print("\n📹 Creating missing segments...")
    for i in range(1, 8):
        create_segment(i)

    # Concatenate
    print("\n🎬 Concatenating final video...")
    final = concatenate_all()

    if final:
        size = os.path.getsize(final) / (1024 * 1024)
        print(f"\n✅ DONE! Final video: {final}")
        print(f"   Size: {size:.1f} MB")
    else:
        print("\n❌ Failed to create final video")
