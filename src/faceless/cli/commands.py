"""
CLI commands for the Faceless Content Pipeline.

This module defines all CLI commands using Typer.
"""

import json
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from faceless import __version__
from faceless.config import get_settings
from faceless.core.enums import Niche, Platform
from faceless.pipeline.orchestrator import Orchestrator
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
    list[Platform] | None,
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

    # Run the pipeline orchestrator
    orchestrator = Orchestrator()

    console.print("\n[bold]Starting pipeline...[/]\n")

    try:
        results = orchestrator.run(
            niche=niche,
            platforms=platform,
            count=count,
            script_path=script,
            enhance=enhance,
            thumbnails=thumbnails,
            subtitles=subtitles,
            music_path=music,
        )

        # Show results
        table = Table(title="Pipeline Results")
        table.add_column("Script", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Videos", style="blue")
        table.add_column("Duration", style="dim")

        for result in results:
            status = "[green]✓ Success[/]" if result.success else "[red]✗ Failed[/]"
            video_count = len(result.video_paths)
            duration = f"{result.duration_seconds:.1f}s"
            script_name = result.script_path.stem if result.script_path else "Unknown"

            table.add_row(script_name, status, str(video_count), duration)

            # Show errors if any
            if result.errors:
                for error in result.errors:
                    console.print(f"  [red]⚠️  {error}[/]")

        console.print(table)

        # Summary
        successful = sum(1 for r in results if r.success)
        failed = len(results) - successful

        if successful > 0:
            console.print(
                f"\n[green]✓ {successful} video(s) generated successfully![/]"
            )
        if failed > 0:
            console.print(f"[red]✗ {failed} video(s) failed[/]")

        # Show output locations
        if results and any(r.video_paths for r in results):
            console.print("\n[bold]Output files:[/]")
            for result in results:
                for plat, path in result.video_paths.items():
                    console.print(f"  [dim]{plat}:[/] {path}")

    except Exception as e:
        console.print(f"\n[red]✗ Pipeline failed: {e}[/]")
        if settings.debug:
            import traceback

            console.print(f"[dim]{traceback.format_exc()}[/]")
        raise typer.Exit(1) from None


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


# =============================================================================
# Research Command
# =============================================================================


@app.command()
def research(
    topic: Annotated[
        str,
        typer.Argument(
            help="Topic to research",
        ),
    ],
    niche: Annotated[
        Niche,
        typer.Option(
            "--niche",
            "-n",
            help="Content niche for context",
        ),
    ] = Niche.FINANCE,
    depth: Annotated[
        str,
        typer.Option(
            "--depth",
            "-d",
            help="Research depth: quick, standard, deep, investigative",
        ),
    ] = "standard",
    output: Annotated[
        Path | None,
        typer.Option(
            "--output",
            "-o",
            help="Save research to JSON file",
        ),
    ] = None,
    structure: Annotated[
        bool,
        typer.Option(
            "--structure",
            "-s",
            help="Generate content structure recommendation",
        ),
    ] = False,
) -> None:
    """
    Research a topic for content creation.

    Performs deep research on a topic using AI to gather facts,
    statistics, expert perspectives, and content recommendations.

    Examples:

        # Quick research on a topic
        faceless research "Why diamonds are expensive" -n finance -d quick

        # Deep research with structure recommendations
        faceless research "The history of Bitcoin" -n finance -d deep --structure

        # Save research to file
        faceless research "Scary hotel stories" -n scary-stories -o research.json
    """
    from faceless.services.research_service import DeepResearchService, ResearchDepth

    # Map depth string to enum
    depth_map = {
        "quick": ResearchDepth.QUICK,
        "standard": ResearchDepth.STANDARD,
        "deep": ResearchDepth.DEEP,
        "investigative": ResearchDepth.INVESTIGATIVE,
    }
    research_depth = depth_map.get(depth.lower(), ResearchDepth.STANDARD)

    console.print(
        Panel.fit(
            f"[bold blue]Researching:[/] {topic}\n"
            f"[dim]Niche: {niche.display_name} | Depth: {research_depth.value}[/]",
            title="🔬 Deep Research",
        )
    )

    try:
        service = DeepResearchService()

        with console.status("[bold green]Researching topic..."):
            result = service.research_topic(
                topic=topic,
                niche=niche,
                depth=research_depth,
            )

        # Display results
        console.print(
            f"\n[bold green]✓ Research Complete[/] (Confidence: {result.confidence_score:.0%})\n"
        )

        # Key findings
        if result.key_findings:
            console.print("[bold]📋 Key Findings:[/]")
            for i, finding in enumerate(result.key_findings[:5], 1):
                importance = (
                    "🔴"
                    if finding.importance >= 0.8
                    else "🟡" if finding.importance >= 0.5 else "⚪"
                )
                console.print(f"  {importance} {i}. {finding.content}")

        # Statistics
        if result.statistics:
            console.print("\n[bold]📊 Statistics:[/]")
            for stat in result.statistics[:3]:
                console.print(f"  • {stat.content}")

        # Suggested hook
        if result.suggested_hook:
            console.print(f'\n[bold]🎣 Suggested Hook:[/]\n  "{result.suggested_hook}"')

        # Why it matters
        if result.why_it_matters:
            console.print(
                f"\n[bold]💡 Why It Matters:[/]\n  {result.why_it_matters[:200]}..."
            )

        # Follow-up topics
        if result.follow_up_topics:
            console.print("\n[bold]🔗 Related Topics:[/]")
            for topic_name in result.follow_up_topics[:5]:
                console.print(f"  → {topic_name}")

        # Generate structure if requested
        if structure:
            console.print("\n[bold]📝 Content Structure:[/]")
            with console.status("[bold green]Generating structure..."):
                struct = service.generate_content_structure(result)

            if struct:
                if "hook" in struct:
                    console.print(f"  [cyan]Hook:[/] {struct['hook']}")
                if "sections" in struct:
                    for section in struct.get("sections", [])[:5]:
                        duration = section.get("duration_seconds", 60)
                        console.print(
                            f"  [cyan]{section.get('title', 'Section')}[/] ({duration}s)"
                        )
                if "cta" in struct:
                    console.print(f"  [cyan]CTA:[/] {struct['cta']}")

        # Save to file if requested
        if output:
            output_data = result.to_dict()
            if structure and struct:
                output_data["content_structure"] = struct
            output.write_text(json.dumps(output_data, indent=2, default=str))
            console.print(f"\n[green]✓ Saved research to {output}[/]")

    except Exception as e:
        console.print(f"\n[red]✗ Research failed: {e}[/]")
        raise typer.Exit(1) from None


# =============================================================================
# Quality Command
# =============================================================================


@app.command()
def quality(
    script_path: Annotated[
        Path,
        typer.Argument(
            help="Path to script JSON file to evaluate",
            exists=True,
            file_okay=True,
            dir_okay=False,
        ),
    ],
    strict: Annotated[
        bool,
        typer.Option(
            "--strict",
            help="Require all quality gates to pass",
        ),
    ] = False,
    improve_hooks: Annotated[
        bool,
        typer.Option(
            "--improve-hooks",
            "-i",
            help="Generate improved hook alternatives",
        ),
    ] = False,
    output: Annotated[
        Path | None,
        typer.Option(
            "--output",
            "-o",
            help="Save quality report to JSON file",
        ),
    ] = None,
) -> None:
    """
    Evaluate script quality before production.

    Analyzes a script for hook quality, retention potential,
    and engagement factors. Helps filter weak content before
    spending resources on generation.

    Examples:

        # Evaluate a script
        faceless quality scripts/my-script.json

        # Strict evaluation with hook suggestions
        faceless quality scripts/my-script.json --strict --improve-hooks

        # Save report to file
        faceless quality scripts/my-script.json -o quality-report.json
    """
    from faceless.core.models import Script
    from faceless.services.quality_service import QualityService

    console.print(
        Panel.fit(
            f"[bold blue]Evaluating:[/] {script_path.name}\n"
            f"[dim]Mode: {'Strict' if strict else 'Standard'}[/]",
            title="📊 Quality Evaluation",
        )
    )

    try:
        # Load script
        script = Script.from_json_file(script_path)
        console.print(f"[dim]Script: {script.title} ({len(script.scenes)} scenes)[/]\n")

        service = QualityService()

        with console.status("[bold green]Analyzing quality..."):
            result = service.evaluate_script(script, strict_mode=strict)

        # Display scores
        table = Table(title="Quality Scores")
        table.add_column("Metric", style="cyan")
        table.add_column("Score", justify="right")
        table.add_column("Status")

        def score_status(score: float, threshold: float = 7.0) -> str:
            if score >= 8.0:
                return "[green]Excellent[/]"
            elif score >= threshold:
                return "[green]Good[/]"
            elif score >= 5.0:
                return "[yellow]Fair[/]"
            else:
                return "[red]Poor[/]"

        table.add_row(
            "Overall",
            f"{result.overall_score:.1f}/10",
            score_status(result.overall_score, 6.5),
        )
        table.add_row(
            "Hook", f"{result.hook_score:.1f}/10", score_status(result.hook_score, 7.0)
        )
        table.add_row(
            "Narrative",
            f"{result.narrative_score:.1f}/10",
            score_status(result.narrative_score, 6.0),
        )
        table.add_row(
            "Engagement",
            f"{result.engagement_score:.1f}/10",
            score_status(result.engagement_score, 5.0),
        )
        table.add_row(
            "Information",
            f"{result.information_score:.1f}/10",
            score_status(result.information_score, 5.0),
        )

        console.print(table)

        # Quality gates
        console.print("\n[bold]Quality Gates:[/]")
        for gate in result.gates_passed:
            console.print(f"  [green]✓[/] {gate.value.replace('_', ' ').title()}")
        for gate in result.gates_failed:
            console.print(f"  [red]✗[/] {gate.value.replace('_', ' ').title()}")

        # Hook analysis
        if result.hook_analysis:
            console.print("\n[bold]🎣 Hook Analysis:[/]")
            console.print(f"  Type: {result.hook_analysis.hook_type}")
            console.print(
                f"  Attention Grab: {result.hook_analysis.attention_grab:.0%}"
            )
            console.print(f"  Curiosity Gap: {result.hook_analysis.curiosity_gap:.0%}")

        # Retention prediction
        if result.retention_analysis:
            console.print("\n[bold]📈 Retention Prediction:[/]")
            console.print(
                f"  30-second retention: {result.retention_analysis.predicted_retention_30s:.0%}"
            )
            console.print(
                f"  Completion rate: {result.retention_analysis.predicted_completion_rate:.0%}"
            )
            if result.retention_analysis.drop_off_risks:
                console.print("  [yellow]⚠️ Drop-off risks:[/]")
                for risk in result.retention_analysis.drop_off_risks[:3]:
                    console.print(f"    • {risk}")

        # Critical issues
        if result.critical_issues:
            console.print("\n[bold red]⚠️ Critical Issues:[/]")
            for issue in result.critical_issues:
                console.print(f"  • {issue}")

        # Improvements
        if result.improvements:
            console.print("\n[bold]💡 Suggested Improvements:[/]")
            for improvement in result.improvements[:5]:
                console.print(f"  • {improvement}")

        # Generate better hooks if requested
        if improve_hooks:
            console.print("\n[bold]🎣 Alternative Hooks:[/]")
            with console.status("[bold green]Generating hooks..."):
                hooks = service.generate_better_hooks(script, count=3)
            for i, hook in enumerate(hooks, 1):
                console.print(f'  {i}. "{hook}"')

        # Verdict
        if result.approved_for_production:
            console.print("\n[bold green]✓ APPROVED for production[/]")
        else:
            console.print("\n[bold red]✗ NOT APPROVED - improve before production[/]")

        # Save report if requested
        if output:
            output.write_text(json.dumps(result.to_dict(), indent=2, default=str))
            console.print(f"\n[green]✓ Saved report to {output}[/]")

        # Exit code based on approval
        if not result.approved_for_production:
            raise typer.Exit(1)

    except typer.Exit:
        raise
    except Exception as e:
        console.print(f"\n[red]✗ Quality evaluation failed: {e}[/]")
        raise typer.Exit(1) from None


# =============================================================================
# Trending Command
# =============================================================================


@app.command()
def trending(
    niche: Annotated[
        Niche,
        typer.Argument(
            help="Content niche to get trends for",
        ),
    ],
    count: Annotated[
        int,
        typer.Option(
            "--count",
            "-c",
            help="Number of trending topics to show",
            min=1,
            max=20,
        ),
    ] = 10,
    analyze: Annotated[
        str | None,
        typer.Option(
            "--analyze",
            "-a",
            help="Analyze a specific topic's potential",
        ),
    ] = None,
    output: Annotated[
        Path | None,
        typer.Option(
            "--output",
            "-o",
            help="Save trend report to JSON file",
        ),
    ] = None,
    calendar: Annotated[
        bool,
        typer.Option(
            "--calendar",
            help="Show content calendar suggestions",
        ),
    ] = False,
) -> None:
    """
    Discover trending topics for a niche.

    Finds hot topics from Reddit and AI suggestions,
    with viral potential scoring and timing recommendations.

    Examples:

        # Get trending topics for scary stories
        faceless trending scary-stories

        # Analyze a specific topic
        faceless trending finance --analyze "Why Gen Z is broke"

        # Get content calendar suggestions
        faceless trending luxury --calendar

        # Save full report
        faceless trending finance -o trends.json
    """
    from faceless.services.trending_service import TrendingService

    console.print(
        Panel.fit(
            f"[bold blue]Finding Trends for:[/] {niche.display_name}",
            title="📈 Trending Topics",
        )
    )

    try:
        service = TrendingService()

        # Analyze specific topic if requested
        if analyze:
            console.print(f"\n[bold]Analyzing:[/] {analyze}\n")

            with console.status("[bold green]Analyzing topic potential..."):
                topic = service.analyze_topic_potential(analyze, niche)

            # Display analysis
            table = Table(title="Topic Analysis")
            table.add_column("Metric", style="cyan")
            table.add_column("Value")

            table.add_row("Score", f"{topic.score:.0f}/100")
            table.add_row("Lifecycle", topic.lifecycle.value.title())
            table.add_row("Video Potential", f"{topic.video_potential:.0%}")
            table.add_row("Competition", topic.competition_level.title())
            table.add_row("Evergreen Potential", f"{topic.evergreen_potential:.0%}")

            console.print(table)

            if topic.suggested_angles:
                console.print("\n[bold]📐 Suggested Angles:[/]")
                for angle in topic.suggested_angles:
                    console.print(f"  → {angle}")

            # Timing recommendation
            timing = service.suggest_content_timing(topic)
            console.print(f"\n[bold]⏰ Timing:[/] {timing['recommendation']}")
            console.print(f"   Window: {timing['window']}")

            return

        # Get full trend report
        with console.status("[bold green]Discovering trends..."):
            report = service.get_trend_report(niche, max_topics_per_source=count)

        # Hot topics
        if report.hot_topics:
            console.print("\n[bold red]🔥 Hot Topics (Post Now!):[/]")
            for topic in report.hot_topics[:5]:
                score_color = (
                    "green"
                    if topic.score >= 80
                    else "yellow" if topic.score >= 60 else "white"
                )
                console.print(f"  [{score_color}]{topic.score:.0f}[/] {topic.title}")

        # Rising topics
        if report.rising_topics:
            console.print("\n[bold yellow]📈 Rising Topics:[/]")
            for topic in report.rising_topics[:5]:
                console.print(f"  ↑{topic.growth_rate:.0f}% {topic.title}")

        # Viral potential
        if report.viral_potential:
            console.print("\n[bold magenta]🚀 High Viral Potential:[/]")
            for topic in report.viral_potential[:3]:
                console.print(f"  {topic.video_potential:.0%} {topic.title}")

        # Evergreen topics
        if report.evergreen_topics:
            console.print("\n[bold green]🌲 Evergreen Topics:[/]")
            for topic in report.evergreen_topics[:3]:
                console.print(f"  • {topic.title}")

        # Top recommendation
        if report.top_recommendation:
            console.print(
                f"\n[bold]⭐ Top Recommendation:[/] {report.top_recommendation.title}"
            )

        # Content calendar
        if calendar and report.content_calendar_suggestions:
            console.print("\n[bold]📅 Content Calendar:[/]")
            for item in report.content_calendar_suggestions:
                console.print(f"  [{item['timing']}] {item['topic']}")
                console.print(f"    [dim]{item['reason']}[/]")

        # Save report if requested
        if output:
            output.write_text(json.dumps(report.to_dict(), indent=2, default=str))
            console.print(f"\n[green]✓ Saved report to {output}[/]")

    except Exception as e:
        console.print(f"\n[red]✗ Trend discovery failed: {e}[/]")
        raise typer.Exit(1) from None


if __name__ == "__main__":
    app()
