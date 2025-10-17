import re
from datetime import datetime, timezone

from arcade_tdk import ToolContext
from arcade_tdk.errors import ToolExecutionError

from arcade_hubspot.http_client.http_client import HubspotHttpClient


def get_auth_token_or_raise(context: ToolContext) -> str:
    """Return auth token or raise a standardized error if missing/empty."""
    token = context.get_auth_token_or_empty()
    if not token:
        raise ToolExecutionError(
            message="Authentication token is required",
            developer_message="HubSpot authentication token was not provided or is empty",
        )
    return token


async def get_current_hubspot_user_id(context: ToolContext) -> str:
    """Get the current HubSpot user ID from the authentication token.

    Returns:
        str: The current user's HubSpot user ID

    Raises:
        ToolExecutionError: If authentication token is missing or API call fails
    """
    auth_token = get_auth_token_or_raise(context)
    http_client = HubspotHttpClient(auth_token=auth_token)

    token_info = await http_client.get_current_user_info()
    user_id = token_info.get("user_id")

    if not user_id:
        raise ToolExecutionError(
            message="Unable to retrieve user ID from token",
            developer_message="HubSpot token info did not contain user_id field",
        )

    return str(user_id)


def to_epoch_millis(date_str: str) -> str:
    """Convert date/datetime string to epoch milliseconds string as required by HubSpot.

    Supports formats:
    - YYYY-MM-DD (date only, assumes UTC midnight)
    - YYYY-MM-DDTHH:MM:SS (ISO datetime format)
    - YYYY-MM-DD HH:MM:SS (space-separated datetime)

    Raises:
        ValueError: if the date_str is not in a recognized format
    """
    # Try different date formats
    formats = [
        "%Y-%m-%dT%H:%M:%S",  # ISO format with T separator
        "%Y-%m-%d %H:%M:%S",  # Space-separated datetime
        "%Y-%m-%d",  # Date only
    ]

    dt = None
    for fmt in formats:
        try:
            dt = datetime.strptime(date_str, fmt).replace(tzinfo=timezone.utc)
            break
        except ValueError:
            continue

    if dt is None:
        # Try using fromisoformat as a fallback for more complex ISO formats
        try:
            # Remove timezone info if present and parse
            date_str_clean = date_str.split("+")[0].split("Z")[0]
            dt = datetime.fromisoformat(date_str_clean).replace(tzinfo=timezone.utc)
        except ValueError:
            raise ValueError(f"Date string '{date_str}' is not in a recognized format")

    return str(int(dt.timestamp() * 1000))


_NUMERIC_ID_REGEX = re.compile(r"^\d{1,32}$")


def normalize_and_validate_pipeline_id(pipeline_id: str | None) -> str:
    """Normalize and validate pipeline id to be 'default' or a numeric id.

    Raises:
        ToolExecutionError: if not 'default' or numeric.
    """
    pid = (pipeline_id or "default").strip()
    if pid == "default":
        return pid
    if _NUMERIC_ID_REGEX.match(pid):
        return pid
    raise ToolExecutionError(
        message="Invalid pipeline id format",
        developer_message=("pipeline_id must be 'default' or a numeric id"),
    )
