"""
CLI commands for the Faceless Content Pipeline.

This module defines all CLI commands using Typer.
"""

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from faceless import __version__
from faceless.config import get_settings
from faceless.core.enums import Niche, Platform
from faceless.utils.logging import setup_logging

# Create the main app
app = typer.Typer(
    name="faceless",
    help="AI-powered content production pipeline for faceless videos.",
    add_completion=False,
    no_args_is_help=True,
)

console = Console()

# =============================================================================
# Type Aliases for CLI Arguments
# =============================================================================

NicheArg = Annotated[
    Niche,
    typer.Argument(
        help="Content niche (scary-stories, finance, luxury)",
    ),
]

PlatformOption = Annotated[
    list[Platform],
    typer.Option(
        "--platform",
        "-p",
        help="Target platform(s)",
    ),
]

CountOption = Annotated[
    int,
    typer.Option(
        "--count",
        "-c",
        help="Number of videos to generate",
        min=1,
        max=10,
    ),
]

# =============================================================================
# Callbacks
# =============================================================================


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        console.print(f"[bold blue]Faceless Content Pipeline[/] v{__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Annotated[
        bool,
        typer.Option(
            "--version",
            "-v",
            help="Show version and exit",
            callback=version_callback,
            is_eager=True,
        ),
    ] = False,
    debug: Annotated[
        bool,
        typer.Option(
            "--debug",
            help="Enable debug logging",
        ),
    ] = False,
) -> None:
    """
    Faceless Content Pipeline - AI-powered video production.

    Generate engaging short-form videos with AI-generated images,
    text-to-speech narration, and automated video assembly.
    """
    # Setup logging based on debug flag
    settings = get_settings()
    log_level = "DEBUG" if debug else settings.log_level
    setup_logging(level=log_level, json_format=settings.log_json_format)


# =============================================================================
# Generate Command
# =============================================================================


@app.command()
def generate(
    niche: NicheArg,
    count: CountOption = 1,
    platform: PlatformOption = None,
    script: Annotated[
        Path | None,
        typer.Option(
            "--script",
            "-s",
            help="Path to existing script file",
            exists=True,
            file_okay=True,
            dir_okay=False,
        ),
    ] = None,
    skip_fetch: Annotated[
        bool,
        typer.Option(
            "--skip-fetch",
            help="Skip fetching new stories, use existing scripts",
        ),
    ] = False,
    enhance: Annotated[
        bool,
        typer.Option(
            "--enhance",
            "-e",
            help="Enhance scripts with GPT for better engagement",
        ),
    ] = False,
    thumbnails: Annotated[
        bool,
        typer.Option(
            "--thumbnails",
            "-t",
            help="Generate thumbnail variants",
        ),
    ] = True,
    subtitles: Annotated[
        bool,
        typer.Option(
            "--subtitles",
            help="Generate subtitle files",
        ),
    ] = True,
    music: Annotated[
        Path | None,
        typer.Option(
            "--music",
            "-m",
            help="Path to background music file",
            exists=True,
            file_okay=True,
        ),
    ] = None,
) -> None:
    """
    Generate faceless video content.

    This command runs the full pipeline: fetch content, generate images,
    create audio, and assemble final videos.

    Examples:

        # Generate 1 scary story video for all platforms
        faceless generate scary-stories

        # Generate 3 finance videos for YouTube only
        faceless generate finance -c 3 -p youtube

        # Process a specific script with enhancement
        faceless generate scary-stories -s path/to/script.json --enhance
    """
    if platform is None:
        platform = [Platform.YOUTUBE, Platform.TIKTOK]
    console.print(
        Panel.fit(
            f"[bold blue]Generating {count} {niche.display_name} video(s)[/]\n"
            f"Platforms: {', '.join(p.display_name for p in platform)}",
            title="🎬 Faceless Content Pipeline",
        )
    )

    # Ensure output directories exist
    settings = get_settings()
    settings.ensure_directories(niche)

    console.print(f"\n[dim]Output directory: {settings.get_output_dir(niche)}[/]")

    # TODO: Implement pipeline orchestration
    console.print("\n[yellow]⚠️  Pipeline orchestration not yet implemented[/]")
    console.print("[dim]The new service layer is being developed...[/]")

    # Show what would be done
    table = Table(title="Pipeline Steps")
    table.add_column("Step", style="cyan")
    table.add_column("Status", style="green")

    steps = [
        ("Fetch/Load Scripts", "pending"),
        (
            "Enhance Scripts" if enhance else "Skip Enhancement",
            "pending" if enhance else "skipped",
        ),
        ("Generate Images", "pending"),
        ("Generate Audio", "pending"),
        ("Assemble Videos", "pending"),
        (
            "Generate Thumbnails" if thumbnails else "Skip Thumbnails",
            "pending" if thumbnails else "skipped",
        ),
        (
            "Generate Subtitles" if subtitles else "Skip Subtitles",
            "pending" if subtitles else "skipped",
        ),
    ]

    for step, status in steps:
        table.add_row(
            step, f"[{'yellow' if status == 'pending' else 'dim'}]{status}[/]"
        )

    console.print(table)


# =============================================================================
# Validate Command
# =============================================================================


@app.command()
def validate(
    test_connections: Annotated[
        bool,
        typer.Option(
            "--test-connections",
            "-t",
            help="Test actual API connectivity",
        ),
    ] = False,
    niche: Annotated[
        Niche | None,
        typer.Option(
            "--niche",
            "-n",
            help="Validate for a specific niche",
        ),
    ] = None,
) -> None:
    """
    Validate configuration and API connections.

    Checks that all required settings are configured and optionally
    tests actual API connectivity.

    Examples:

        # Validate configuration
        faceless validate

        # Test API connections
        faceless validate --test-connections
    """
    console.print(
        Panel.fit(
            "[bold]Configuration Validation[/]",
            title="🔍 Checking Configuration",
        )
    )

    settings = get_settings()

    # Create results table
    table = Table(title="Configuration Status")
    table.add_column("Setting", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Details")

    # Check Azure OpenAI
    azure_ok = settings.azure_openai.is_configured
    table.add_row(
        "Azure OpenAI",
        "[green]✓[/]" if azure_ok else "[red]✗[/]",
        "Configured" if azure_ok else "Missing endpoint or API key",
    )

    # Check ElevenLabs (optional)
    if settings.use_elevenlabs:
        eleven_ok = settings.elevenlabs.is_configured
        table.add_row(
            "ElevenLabs",
            "[green]✓[/]" if eleven_ok else "[red]✗[/]",
            "Configured" if eleven_ok else "Missing API key",
        )
    else:
        table.add_row(
            "ElevenLabs",
            "[dim]–[/]",
            "Not enabled (using Azure TTS)",
        )

    # Check FFmpeg
    import subprocess

    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            timeout=5,
        )
        ffmpeg_ok = result.returncode == 0
    except Exception:
        ffmpeg_ok = False

    table.add_row(
        "FFmpeg",
        "[green]✓[/]" if ffmpeg_ok else "[red]✗[/]",
        "Installed" if ffmpeg_ok else "Not found in PATH",
    )

    console.print(table)

    # Test connections if requested
    if test_connections:
        console.print("\n[bold]Testing API Connections...[/]")

        if azure_ok:
            from faceless.clients.azure_openai import AzureOpenAIClient

            try:
                client = AzureOpenAIClient()
                if client.test_connection():
                    console.print("[green]✓[/] Azure OpenAI: Connected")
                else:
                    console.print("[red]✗[/] Azure OpenAI: Connection failed")
            except Exception as e:
                console.print(f"[red]✗[/] Azure OpenAI: {e}")

    # Summary
    all_ok = azure_ok and ffmpeg_ok
    if all_ok:
        console.print("\n[green]✓ Configuration is valid![/]")
        raise typer.Exit(0)
    else:
        console.print(
            "\n[red]✗ Configuration has issues. Fix them before running the pipeline.[/]"
        )
        raise typer.Exit(1)


# =============================================================================
# Init Command
# =============================================================================


@app.command()
def init(
    niche: Annotated[
        Niche | None,
        typer.Option(
            "--niche",
            "-n",
            help="Initialize directories for a specific niche only",
        ),
    ] = None,
) -> None:
    """
    Initialize project directories.

    Creates all required output directories for the specified niche
    or all niches if none specified.
    """
    settings = get_settings()
    settings.ensure_directories(niche)

    if niche:
        console.print(f"[green]✓[/] Created directories for {niche.display_name}")
        console.print(f"  [dim]{settings.get_output_dir(niche)}[/]")
    else:
        console.print("[green]✓[/] Created directories for all niches:")
        for n in Niche:
            console.print(f"  [dim]{settings.get_output_dir(n)}[/]")


# =============================================================================
# Info Command
# =============================================================================


@app.command()
def info() -> None:
    """
    Show information about the pipeline configuration.

    Displays current settings and paths.
    """
    settings = get_settings()

    console.print(
        Panel.fit(
            f"[bold blue]Faceless Content Pipeline[/] v{__version__}",
            title="ℹ️  Pipeline Info",
        )
    )

    # Settings table
    table = Table(title="Current Settings")
    table.add_column("Setting", style="cyan")
    table.add_column("Value")

    table.add_row("Log Level", settings.log_level)
    table.add_row("Debug Mode", "Yes" if settings.debug else "No")
    table.add_row("Output Directory", str(settings.output_base_dir))
    table.add_row("Max Concurrent Requests", str(settings.max_concurrent_requests))
    table.add_row("Request Timeout", f"{settings.request_timeout}s")
    table.add_row("Retry Enabled", "Yes" if settings.enable_retry else "No")
    table.add_row("Max Retries", str(settings.max_retries))
    table.add_row(
        "Checkpointing", "Enabled" if settings.enable_checkpointing else "Disabled"
    )
    table.add_row(
        "TTS Provider", "ElevenLabs" if settings.use_elevenlabs else "Azure OpenAI"
    )

    console.print(table)

    # Voice settings
    voice_table = Table(title="Voice Settings by Niche")
    voice_table.add_column("Niche", style="cyan")
    voice_table.add_column("Voice")
    voice_table.add_column("Speed")

    for niche in Niche:
        voice, speed = settings.get_voice_settings(niche)
        voice_table.add_row(niche.display_name, voice.value, str(speed))

    console.print(voice_table)


if __name__ == "__main__":
    app()
