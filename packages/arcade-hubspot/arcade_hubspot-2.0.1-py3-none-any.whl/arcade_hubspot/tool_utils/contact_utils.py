"""Utility functions for contact operations."""

from typing import Any

from arcade_hubspot.models.tool_models import CreateContactResponse
from arcade_hubspot.utils.gui_url_builder import build_contact_gui_url


def create_contact_response(
    contact_data: dict[str, Any], portal_id: str | None = None
) -> CreateContactResponse:
    """
    Create a standardized response for contact creation operations.

    Args:
        contact_data: Raw contact data from HubSpot API
        portal_id: HubSpot portal ID for GUI URL generation

    Returns:
        Cleaned contact response for tool output.
    """
    properties = contact_data.get("properties", {})

    # Build GUI URL if portal_id is available
    contact_gui_url = None
    if portal_id and contact_data.get("id"):
        contact_id = str(contact_data.get("id"))
        contact_gui_url = build_contact_gui_url(portal_id, contact_id)

    # Build response data
    response_data: CreateContactResponse = {
        "id": str(contact_data.get("id", "")),
        "object_type": contact_data.get("object_type", "contact"),
        "firstname": properties.get("firstname"),
        "lastname": properties.get("lastname"),
        "email_address": properties.get("email"),
        "phone": properties.get("phone"),
        "mobilephone": properties.get("mobilephone"),
        "jobtitle": properties.get("jobtitle"),
        "contact_gui_url": contact_gui_url,
    }

    return response_data
