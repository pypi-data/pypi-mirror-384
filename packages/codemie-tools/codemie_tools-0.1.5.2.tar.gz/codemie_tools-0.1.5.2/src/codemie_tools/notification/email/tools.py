import smtplib
import socket
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List, Type, Optional

from pydantic import BaseModel, Field

from codemie_tools.base.codemie_tool import CodeMieTool
from codemie_tools.notification.email.models import EmailToolConfig
from codemie_tools.notification.email.tools_vars import EMAIL_TOOL


class EmailToolInput(BaseModel):
    recipient_emails: List[str] = Field(..., description="A list of recipient email addresses")
    subject: str = Field(..., description="The email subject")
    body: str = Field(..., description="The body of the email (can include HTML formatting)")
    cc_emails: Optional[List[str]] = Field(
        default=None, description="A list of cc (carbon copy) email addresses"
    )
    bcc_emails: Optional[List[str]] = Field(
        default=None, description="A list of bcc (blind carbon copy) email addresses"
    )
    from_email: Optional[str] = Field(
        default=None,
        description="Sender email address. If not specified, the configured SMTP username will be used as the sender.",
    )
    timeout: Optional[float] = Field(
        default=30.0,
        description="Timeout in seconds for the SMTP operations (connection, sending). Default is 30 seconds.",
    )


class EmailTool(CodeMieTool):
    config: EmailToolConfig
    name: str = EMAIL_TOOL.name
    description: str = "Use this tool when you need to send an email notification via SMTP. Supports TO, CC, BCC, and custom FROM address."
    args_schema: Type[BaseModel] = EmailToolInput

    def execute(
        self,
        recipient_emails: List[str],
        subject: str,
        body: str,
        cc_emails: Optional[List[str]] = None,
        bcc_emails: Optional[List[str]] = None,
        from_email: Optional[str] = None,
        timeout: Optional[float] = 30.0,
    ) -> str:
        """
        Send an email via SMTP with a configurable timeout.

        Args:
            recipient_emails: List of recipient email addresses
            subject: Email subject
            body: Email body content (can include HTML)
            cc_emails: Optional list of CC email addresses
            bcc_emails: Optional list of BCC email addresses
            from_email: Optional sender email address (overrides config if provided)
            timeout: Optional timeout in seconds for SMTP operations (default: 30 seconds)

        Returns:
            Confirmation message on success
        """

        try:
            host, port = self.config.url.split(":")
        except Exception:
            raise ValueError(
                "Please provide valid SMTP url."
            )

        from_email = from_email if from_email else self.config.smtp_username

        if not from_email or not host or not port or not self.config.smtp_password:
            raise ValueError(
                "Please provide valid SMTP configuration before using the tool. "
            )

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = from_email
            msg["To"] = ", ".join(recipient_emails)
            if cc_emails:
                msg["Cc"] = ", ".join(cc_emails)
            # BCC is handled in sendmail recipients but not added as a header

            part = MIMEText(body, "html")
            msg.attach(part)

            with smtplib.SMTP(host, int(port), timeout=timeout) as server:
                server.starttls()
                server.login(self.config.smtp_username, self.config.smtp_password)
                # Combine all recipients for sendmail (to, cc, bcc)
                all_recipients_emails = (
                    recipient_emails
                    + (cc_emails if cc_emails else [])
                    + (bcc_emails if bcc_emails else [])
                )
                # Use the from_email if provided, otherwise use the configured SMTP username
                sender = from_email if from_email else self.config.smtp_username
                server.sendmail(sender, all_recipients_emails, msg.as_string())
                server.quit()

            # Don't expose BCC recipients in the success message
            visible_recipients = recipient_emails + (cc_emails if cc_emails else [])
            bcc_count = len(bcc_emails) if bcc_emails else 0
            bcc_suffix = 's' if bcc_count != 1 else ''
            bcc_message = (
                f" and {bcc_count} BCC recipient{bcc_suffix}"
                if bcc_count > 0
                else ""
            )
            return f"Email sent successfully to {', '.join(visible_recipients)}{bcc_message}"
        except smtplib.SMTPServerDisconnected as e:
            return f"Failed to send email due to server disconnection (possibly timeout): {e}"
        except socket.timeout as e:
            return f"Failed to send email due to timeout ({timeout}s): {e}"
        except Exception as e:
            return f"Failed to send email: {e}"

    def _healthcheck(self):
        """
        Check if the SMTP connection can be established.

        Returns:
            Nothing if successful, raises an exception on failure that will be caught by the parent class.
        """
        try:
            host, port = self.config.url.split(":")
            # Use a default timeout of 10 seconds for healthcheck
            with smtplib.SMTP(host, int(port), timeout=10.0) as server:
                server.starttls()
                server.login(self.config.smtp_username, self.config.smtp_password)
                server.noop()
                server.quit()
        except smtplib.SMTPResponseException as e:
            # Specific handling for SMTP response exceptions
            error_message = f"SMTP Code: {e.smtp_code}, Message: {e.smtp_error.decode() if isinstance(e.smtp_error, bytes) else e.smtp_error}"
            raise smtplib.SMTPException(error_message)
