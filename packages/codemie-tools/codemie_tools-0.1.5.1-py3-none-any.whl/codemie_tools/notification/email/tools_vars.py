from codemie_tools.base.models import ToolMetadata
from codemie_tools.notification.email.models import EmailToolConfig

EMAIL_TOOL = ToolMetadata(
    name="Email",
    description="Use this tool when you need to send an email notification via SMTP. Supports TO, CC, BCC, and custom FROM address.",
    label="Email",
    user_description="""The purpose of the email tool is to send emails using SMTP protocol. 
    Before using it it is necessary to add a new integration for the tool providing your: 
    1. SMTP Server URL with port (e.g., smtp.gmail.com:587);
    2. SMTP Server User Name;
    3. SMTP Server User Password.

    Features:
    - Supports HTML content in email bodies
    - CC and BCC support for carbon copy and blind carbon copy recipients
    - Custom sender email address support (overrides the configured SMTP username)
    - Configurable timeout to prevent hanging on slow connections (defaults to 30 seconds)
    - Proper error handling for connection issues

    NOTE: Accounts with enabled MFA must use App Password instead of account password. App Password creation must be allowed by your organization policy.
    For example: support.google.com/mail/answer/185833
    """,
    settings_config=True,
    config_class=EmailToolConfig,
)
