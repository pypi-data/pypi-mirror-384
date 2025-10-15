"""
The command line interface for the webwatch tool.
"""

import sys
import time

import click
from loguru import logger

from . import __version__
from .watcher import MismatchError, Watcher


@click.command(context_settings=dict(help_option_names=["-h", "--help"]))
@click.version_option(__version__, "-v", "--version", prog_name="webwatch")
@click.argument("url", type=str)
@click.option(
    "--period",
    "-p",
    type=int,
    default=60,
    show_default=True,
    help="Time period in seconds to check for changes.",
)
@click.option("--css", type=str, help="CSS selector to target a specific part of the page.")
@click.option("--xpath", type=str, help="XPath expression to target a specific part of the page.")
@click.option("--email", type=str, help="Email address to send notifications to.")
def main(url: str, period: int, css: str | None, xpath: str | None, email: str | None):
    """
    Watches a web page for changes in a target element.

    URL: The URL of the web page to watch.
    """
    # Configure logger
    logger.remove()
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>",
        level="INFO",
    )

    if css and xpath:
        logger.error("Please provide either a CSS selector or an XPath expression, not both.")
        sys.exit(1)

    try:
        watcher = Watcher(url=url, css_selector=css, xpath_selector=xpath, email_to=email)
        logger.info(f"Starting to watch {url} every {period} seconds.")
        logger.info("Initial check...")
        watcher.check()
        logger.info("Initial content fetched successfully. Monitoring for changes...")

        while True:
            time.sleep(period)
            watcher.check()
            logger.info("No changes detected. Continuing to watch.")

    except MismatchError:
        logger.warning("Target element has changed!")
        watcher.notify_change()
        logger.info("Notification sent. Exiting.")
        sys.exit(0)
    except (KeyboardInterrupt, SystemExit):
        logger.info("Stopping webwatch. Goodbye!")
        sys.exit(0)
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
