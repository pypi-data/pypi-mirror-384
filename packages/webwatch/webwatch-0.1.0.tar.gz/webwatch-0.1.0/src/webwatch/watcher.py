"""
Core watcher logic for fetching, parsing, and comparing web content.
"""

import hashlib

import httpx
from loguru import logger
from lxml import html

from .notifications import send_console_notification, send_email_notification


class MismatchError(Exception):
    """Custom exception for content mismatch."""


class Watcher:
    """
    A class to watch a web page for changes.
    """

    def __init__(
        self,
        url: str,
        css_selector: str | None = None,
        xpath_selector: str | None = None,
        email_to: str | None = None,
    ):
        self.url = url
        self.css_selector = css_selector
        self.xpath_selector = xpath_selector or "//body"  # Default to body
        self.email_to = email_to
        self.last_hash: str | None = None

    def fetch_content(self) -> str:
        """
        Fetches the content from the URL.

        Returns:
            The HTML content of the page as a string.
        """
        try:
            with httpx.Client(follow_redirects=True) as client:
                response = client.get(self.url, headers={"User-Agent": "WebWatch-Bot/1.0"})
                response.raise_for_status()
                return response.text
        except httpx.RequestError as exc:
            logger.error(f"An error occurred while requesting {exc.request.url!r}.")
            raise
        except httpx.HTTPStatusError as exc:
            logger.error(
                f"Error response {exc.response.status_code} while requesting {exc.request.url!r}."
            )
            raise

    def extract_target(self, html_content: str) -> str | None:
        """
        Extracts the target part of the HTML content.

        Args:
            html_content: The full HTML content of the page.

        Returns:
            The string representation of the target element, or None if not found.
        """
        tree = html.fromstring(html_content)
        if self.css_selector:
            target = tree.cssselect(self.css_selector)
        else:
            target = tree.xpath(self.xpath_selector)

        if not target:
            logger.warning("Target element not found on the page.")
            return None

        # Convert all found elements to string and join them
        return "".join(
            [html.tostring(element, pretty_print=True).decode("utf-8") for element in target]
        )

    @staticmethod
    def hash_content(content: str) -> str:
        """
        Generates a SHA-256 hash of the content.

        Args:
            content: The content to hash.

        Returns:
            The hex digest of the hash.
        """
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def check(self):
        """
        Performs a single check of the web page.
        Raises MismatchError if the content has changed.
        """
        html_content = self.fetch_content()
        target_content = self.extract_target(html_content)

        if target_content is None:
            # If target is not found, we treat it as a change if it was previously found
            if self.last_hash is not None:
                raise MismatchError("Target element that was previously present is now missing.")
            return  # If it was never found, we just continue

        current_hash = self.hash_content(target_content)

        if self.last_hash is None:
            self.last_hash = current_hash
            return

        if self.last_hash != current_hash:
            raise MismatchError("Content has changed.")

    def notify_change(self):
        """
        Sends a notification about the change.
        """
        message = f"Change detected on {self.url}"
        send_console_notification(message)
        if self.email_to:
            send_email_notification(
                to_addr=self.email_to,
                subject="WebWatch Alert: Change Detected",
                body=f"A change was detected on the page: {self.url}\n"
                f"Please check the page for updates.",
            )
