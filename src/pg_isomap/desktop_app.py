"""
Desktop application entry point using pywebview.

This creates a native window with embedded webview for the UI.
"""

import logging
import sys
import threading
import time

import uvicorn
import webview

from .app import PGIsomapApp
from .config import settings
from .web_api import WebAPI

logger = logging.getLogger(__name__)


class DesktopApp:
    """Desktop application with native window."""

    def __init__(self):
        self.pg_app: PGIsomapApp | None = None
        self.web_api: WebAPI | None = None
        self.server_thread: threading.Thread | None = None
        self.window: webview.Window | None = None

    def start_backend(self):
        """Start the backend server in a separate thread."""
        logger.info("Starting backend server...")

        # Create application
        self.pg_app = PGIsomapApp()

        # Start application
        if not self.pg_app.start():
            logger.error("Failed to start application")
            sys.exit(1)

        # Create web API
        self.web_api = WebAPI(self.pg_app)

        # Run server in thread
        def run_server():
            uvicorn.run(
                self.web_api.fastapi,
                host=settings.web_host,
                port=settings.web_port,
                log_level="info" if not settings.debug else "debug",
            )

        self.server_thread = threading.Thread(target=run_server, daemon=True)
        self.server_thread.start()

        # Give server time to start
        time.sleep(1)
        logger.info(f"Backend server running on http://{settings.web_host}:{settings.web_port}")

    def create_window(self):
        """Create the native window with webview."""
        logger.info("Creating application window...")

        # URL to load (local server)
        url = f"http://{settings.web_host}:{settings.web_port}"

        # Create window
        self.window = webview.create_window(
            title=f"{settings.app_name} v{settings.version}",
            url=url,
            width=1280,
            height=800,
            resizable=True,
            min_size=(800, 600),
        )

        logger.info("Application window created")

    def run(self):
        """Run the desktop application."""
        try:
            # Start backend server
            self.start_backend()

            # Create and show window
            self.create_window()

            # Start webview (blocking call)
            logger.info("Starting webview...")
            webview.start(debug=settings.debug)

            logger.info("Application window closed")

        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
        finally:
            # Cleanup
            if self.pg_app:
                self.pg_app.stop()
            logger.info("Application stopped")


def main():
    """Main entry point for desktop app."""
    # Setup logging
    logging.basicConfig(
        level=logging.DEBUG if settings.debug else logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
        ],
    )

    logger.info(f"Starting {settings.app_name} v{settings.version}")

    # Create and run desktop app
    app = DesktopApp()
    app.run()


if __name__ == "__main__":
    main()
