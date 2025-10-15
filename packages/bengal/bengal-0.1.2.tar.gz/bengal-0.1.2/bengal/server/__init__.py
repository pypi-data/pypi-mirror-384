"""
Development server for Bengal SSG.

Provides a local HTTP server with file watching and automatic rebuilds
for a smooth development experience.

Components:
- DevServer: Main development server with HTTP serving and file watching
- BuildHandler: File system event handler for triggering rebuilds
- LiveReloadMixin: Server-Sent Events (SSE) for browser hot reload
- RequestHandler: Custom HTTP request handler with beautiful logging
- ResourceManager: Graceful cleanup of server resources on shutdown
- PIDManager: Process tracking and stale process recovery

Features:
- Automatic incremental rebuilds on file changes
- Beautiful, minimal request logging
- Custom 404 error pages
- Graceful shutdown handling (Ctrl+C, SIGTERM)
- Stale process detection and cleanup
- Automatic port fallback if port is in use
- Optional browser auto-open

Usage:
    from bengal.server import DevServer
    from bengal.core import Site

    site = Site.from_config()
    server = DevServer(
        site,
        host="localhost",
        port=5173,
        watch=True,
        auto_port=True,
        open_browser=True
    )
    server.start()

The server watches for changes in:
- content/ - Markdown content files
- assets/ - CSS, JS, images
- templates/ - Jinja2 templates
- data/ - YAML/JSON data files
- themes/ - Theme files
- bengal.toml - Configuration file
"""

from bengal.server.dev_server import DevServer

__all__ = ["DevServer"]
