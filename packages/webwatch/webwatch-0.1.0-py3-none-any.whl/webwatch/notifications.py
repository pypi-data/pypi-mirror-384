"""
Handles sending notifications.
"""

import os
import smtplib
from email.mime.text import MIMEText

from loguru import logger


def send_console_notification(message: str):
    """
    Prints a notification to the console.

    Args:
        message: The message to print.
    """
    logger.info(f"CONSOLE ALERT: {message}")


def send_email_notification(to_addr: str, subject: str, body: str):
    """
    Sends an email notification.
    Requires SMTP server configuration via environment variables.

    Args:
        to_addr: The recipient's email address.
        subject: The subject of the email.
        body: The body of the email.
    """
    from_addr: str | None = os.getenv("SMTP_FROM_EMAIL")
    smtp_server: str | None = os.getenv("SMTP_SERVER")
    smtp_port_str: str | None = os.getenv("SMTP_PORT")
    smtp_user: str | None = os.getenv("SMTP_USER")
    smtp_password: str | None = os.getenv("SMTP_PASSWORD")

    if not all([from_addr, smtp_server, smtp_port_str, smtp_user, smtp_password]):
        logger.warning(
            "SMTP environment variables not fully configured. Skipping email notification."
        )
        logger.warning(
            "Please set SMTP_FROM_EMAIL, SMTP_SERVER, SMTP_PORT, SMTP_USER, and SMTP_PASSWORD."
        )
        return

    try:
        smtp_port = int(smtp_port_str)
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = from_addr
        msg["To"] = to_addr

        with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
            server.login(smtp_user, smtp_password)
            server.sendmail(from_addr, [to_addr], msg.as_string())
            logger.info(f"Email notification sent to {to_addr}")

    except (ValueError, smtplib.SMTPException) as e:
        logger.error(f"Failed to send email notification: {e}")
