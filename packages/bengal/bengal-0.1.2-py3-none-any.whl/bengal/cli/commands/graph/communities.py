"""Community detection command for discovering topical clusters."""

import json
from pathlib import Path

import click

from bengal.core.site import Site
from bengal.utils.logger import LogLevel, close_all_loggers, configure_logging


@click.command()
@click.option(
    "--min-size", "-m", default=2, type=int, help="Minimum community size to show (default: 2)"
)
@click.option(
    "--resolution",
    "-r",
    default=1.0,
    type=float,
    help="Resolution parameter (higher = more communities, default: 1.0)",
)
@click.option(
    "--top-n", "-n", default=10, type=int, help="Number of communities to show (default: 10)"
)
@click.option(
    "--format",
    "-f",
    type=click.Choice(["table", "json", "summary"]),
    default="table",
    help="Output format (default: table)",
)
@click.option("--seed", type=int, help="Random seed for reproducibility")
@click.option(
    "--config", type=click.Path(exists=True), help="Path to config file (default: bengal.toml)"
)
@click.argument("source", type=click.Path(exists=True), default=".")
def communities(
    min_size: int, resolution: float, top_n: int, format: str, seed: int, config: str, source: str
) -> None:
    """
    🔍 Discover topical communities in your content.

    Uses the Louvain algorithm to find natural clusters of related pages.
    Communities represent topic areas or content groups based on link structure.

    Use community detection to:
    - Discover hidden content structure
    - Organize content into logical groups
    - Identify topic clusters
    - Guide taxonomy creation

    Examples:
        # Show top 10 communities
        bengal communities

        # Show only large communities (10+ pages)
        bengal communities --min-size 10

        # Find more granular communities
        bengal communities --resolution 2.0

        # Export as JSON
        bengal communities --format json > communities.json
    """
    from bengal.analysis.knowledge_graph import KnowledgeGraph

    try:
        # Configure minimal logging
        configure_logging(level=LogLevel.WARNING)

        # Load site
        source_path = Path(source).resolve()

        if config:
            config_path = Path(config).resolve()
            site = Site.from_config(source_path, config_file=config_path)
        else:
            site = Site.from_config(source_path)

        # Discover content
        click.echo("🔍 Discovering site content...")
        from bengal.orchestration.content import ContentOrchestrator

        content_orch = ContentOrchestrator(site)
        content_orch.discover()

        # Build knowledge graph
        click.echo(f"📊 Building knowledge graph from {len(site.pages)} pages...")
        graph_obj = KnowledgeGraph(site)
        graph_obj.build()

        # Detect communities
        click.echo(f"🔍 Detecting communities (resolution={resolution})...")
        results = graph_obj.detect_communities(resolution=resolution, random_seed=seed)

        # Filter by minimum size
        communities_to_show = results.get_communities_above_size(min_size)

        # Sort by size
        communities_to_show.sort(key=lambda c: c.size, reverse=True)

        # Limit to top N
        communities_to_show = communities_to_show[:top_n]

        # Output based on format
        if format == "json":
            # Export as JSON
            data = {
                "total_communities": len(results.communities),
                "modularity": results.modularity,
                "iterations": results.iterations,
                "resolution": resolution,
                "communities": [],
            }

            for community in communities_to_show:
                # Get top pages by incoming links
                pages_with_refs = [
                    (page, graph_obj.incoming_refs.get(page, 0)) for page in community.pages
                ]
                pages_with_refs.sort(key=lambda x: x[1], reverse=True)

                data["communities"].append(
                    {
                        "id": community.id,
                        "size": community.size,
                        "pages": [
                            {
                                "title": page.title,
                                "url": getattr(page, "url_path", str(page.source_path)),
                                "incoming_refs": refs,
                            }
                            for page, refs in pages_with_refs[:5]  # Top 5 pages
                        ],
                    }
                )

            click.echo(json.dumps(data, indent=2))

        elif format == "summary":
            # Show summary stats
            click.echo("\n" + "=" * 60)
            click.echo("🔍 Community Detection Summary")
            click.echo("=" * 60)
            click.echo(f"Total communities found:  {len(results.communities)}")
            click.echo(f"Showing communities:      {len(communities_to_show)}")
            click.echo(f"Modularity score:         {results.modularity:.4f}")
            click.echo(f"Iterations:               {results.iterations}")
            click.echo(f"Resolution:               {resolution}")
            click.echo("")

            for i, community in enumerate(communities_to_show, 1):
                click.echo(f"\nCommunity {i} (ID: {community.id})")
                click.echo(f"  Size: {community.size} pages")

                # Show top pages
                pages_with_refs = [
                    (page, graph_obj.incoming_refs.get(page, 0)) for page in community.pages
                ]
                pages_with_refs.sort(key=lambda x: x[1], reverse=True)

                click.echo("  Top pages:")
                for page, refs in pages_with_refs[:3]:
                    click.echo(f"    • {page.title} ({refs} refs)")

        else:  # table format
            click.echo("\n" + "=" * 100)
            click.echo(f"🔍 Top {len(communities_to_show)} Communities")
            click.echo("=" * 100)
            click.echo(
                f"Found {len(results.communities)} communities • Modularity: {results.modularity:.4f} • Resolution: {resolution}"
            )
            click.echo("=" * 100)
            click.echo(f"{'ID':<5} {'Size':<6} {'Top Pages':<85}")
            click.echo("-" * 100)

            for community in communities_to_show:
                # Get top 3 pages by incoming links
                pages_with_refs = [
                    (page, graph_obj.incoming_refs.get(page, 0)) for page in community.pages
                ]
                pages_with_refs.sort(key=lambda x: x[1], reverse=True)

                top_page_titles = ", ".join(
                    [
                        page.title[:25] + "..." if len(page.title) > 25 else page.title
                        for page, _ in pages_with_refs[:3]
                    ]
                )

                if len(top_page_titles) > 83:
                    top_page_titles = top_page_titles[:80] + "..."

                click.echo(f"{community.id:<5} {community.size:<6} {top_page_titles:<85}")

            click.echo("=" * 100)
            click.echo("\n💡 Tip: Use --format json to export full data")
            click.echo("       Use --min-size to filter small communities")
            click.echo("       Use --resolution to control granularity\n")

        # Show insights
        if format != "json":
            click.echo("\n" + "=" * 60)
            click.echo("📊 Insights")
            click.echo("=" * 60)

            total_pages = sum(c.size for c in results.communities)
            avg_size = total_pages / len(results.communities) if results.communities else 0
            largest = max((c.size for c in results.communities), default=0)

            click.echo(f"• Average community size:     {avg_size:.1f} pages")
            click.echo(f"• Largest community:          {largest} pages")
            click.echo(f"• Communities >= {min_size} pages:      {len(communities_to_show)}")

            if results.modularity > 0.3:
                click.echo("• Modularity:                 High (good clustering)")
            elif results.modularity > 0.1:
                click.echo("• Modularity:                 Moderate (some structure)")
            else:
                click.echo("• Modularity:                 Low (weak structure)")

            click.echo("\n")

    except Exception as e:
        click.echo(click.style(f"❌ Error: {e}", fg="red", bold=True))
        raise click.Abort() from e
    finally:
        close_all_loggers()
