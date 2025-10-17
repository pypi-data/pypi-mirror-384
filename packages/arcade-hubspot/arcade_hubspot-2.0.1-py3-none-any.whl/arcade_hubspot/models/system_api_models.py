"""API models for HubSpot System/OAuth endpoints."""

from typing import TypedDict


class OAuthTokenResponse(TypedDict):
    """Raw response model for HubSpot OAuth token information."""

    user_id: int
    user: str  # email address
    hub_id: int
    hub_domain: str
    scopes: list[str]
    token: str
    app_id: int
    expires_in: int
    user_id_including_portal: int | None
