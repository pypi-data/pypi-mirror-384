"""Helper functions for activity tools."""

from typing import Any, cast

from arcade_hubspot.enums import HubspotActivityType, HubspotObject
from arcade_hubspot.models.tool_models import (
    CreateCallActivityResponse,
    CreateCommunicationActivityResponse,
    CreateEmailActivityResponse,
    CreateMeetingActivityResponse,
    CreateNoteActivityResponse,
)


def activity_type_to_object(activity_type: HubspotActivityType) -> HubspotObject:
    """Map activity type enum to HubSpot object enum."""
    mapping: dict[HubspotActivityType, HubspotObject] = {
        HubspotActivityType.CALL: HubspotObject.CALL,
        HubspotActivityType.EMAIL: HubspotObject.EMAIL,
        HubspotActivityType.NOTE: HubspotObject.NOTE,
        HubspotActivityType.MEETING: HubspotObject.MEETING,
        HubspotActivityType.TASK: HubspotObject.TASK,
        HubspotActivityType.COMMUNICATION: HubspotObject.COMMUNICATION,
    }
    return mapping[activity_type]


def truncate_string(text: str | None, max_len: int = 100) -> str | None:
    """Truncate a string to max length, adding [...] if truncated."""
    if not text or not isinstance(text, str):
        return text
    if len(text) <= max_len:
        return text
    return text[:max_len] + "[...]"


def create_note_response(resp: dict[str, Any]) -> CreateNoteActivityResponse:
    """Create a note activity response from API response."""
    props = resp.get("properties", {})
    activity_id = resp.get("id") or props.get("hs_object_id")

    response = {
        "id": activity_id,
        "object_type": HubspotObject.NOTE.value,
        "body_preview": props.get("hs_note_body"),
        "owner_id": props.get("hubspot_owner_id"),
        "timestamp": props.get("hs_timestamp"),
    }

    return cast(CreateNoteActivityResponse, response)


def create_call_response(resp: dict[str, Any]) -> CreateCallActivityResponse:
    """Create a call activity response from API response."""
    props = resp.get("properties", {})
    activity_id = resp.get("id") or props.get("hs_object_id")

    response = {
        "id": activity_id,
        "object_type": HubspotObject.CALL.value,
        "title": props.get("hs_call_title"),
        "direction": props.get("hs_call_direction"),
        "status": props.get("hs_call_status"),
        "summary": props.get("hs_call_summary"),
        "owner_id": props.get("hubspot_owner_id"),
        "timestamp": props.get("hs_timestamp"),
    }

    return cast(CreateCallActivityResponse, response)


def create_email_response(resp: dict[str, Any]) -> CreateEmailActivityResponse:
    """Create an email activity response from API response."""
    props = resp.get("properties", {})
    activity_id = resp.get("id") or props.get("hs_object_id")

    response = {
        "id": activity_id,
        "object_type": HubspotObject.EMAIL.value,
        "subject": props.get("hs_email_subject"),
        "status": props.get("hs_email_status"),
        "owner_id": props.get("hubspot_owner_id"),
        "timestamp": props.get("hs_timestamp"),
    }

    return cast(CreateEmailActivityResponse, response)


def create_meeting_response(resp: dict[str, Any]) -> CreateMeetingActivityResponse:
    """Create a meeting activity response from API response."""
    props = resp.get("properties", {})
    activity_id = resp.get("id") or props.get("hs_object_id")

    response = {
        "id": activity_id,
        "object_type": HubspotObject.MEETING.value,
        "title": props.get("hs_meeting_title"),
        "start_time": props.get("hs_meeting_start_time"),
        "end_time": props.get("hs_meeting_end_time"),
        "location": props.get("hs_meeting_location"),
        "outcome": props.get("hs_meeting_outcome"),
        "owner_id": props.get("hubspot_owner_id"),
    }

    return cast(CreateMeetingActivityResponse, response)


def create_communication_response(resp: dict[str, Any]) -> CreateCommunicationActivityResponse:
    """Create a communication activity response from API response."""
    props = resp.get("properties", {})
    activity_id = resp.get("id") or props.get("hs_object_id")

    response = {
        "id": activity_id,
        "object_type": HubspotObject.COMMUNICATION.value,
        "channel": props.get("hs_communication_channel_type"),
        "body_preview": props.get("hs_body_preview"),
        "owner_id": props.get("hubspot_owner_id"),
        "timestamp": props.get("hs_timestamp"),
    }

    return cast(CreateCommunicationActivityResponse, response)


async def find_association_type_id(
    http_client: Any,
    from_object: HubspotObject,
    to_object: HubspotObject,
) -> str:
    """Find the appropriate association type ID between two HubSpot objects.

    Prioritizes HUBSPOT_DEFINED associations, falls back to first available.
    Raises ToolExecutionError if no association types found.
    """
    from arcade_tdk.errors import ToolExecutionError

    types = await http_client.get_association_types(
        from_object=from_object,
        to_object=to_object,
    )

    association_type_id: str | None = None
    if types:
        # First try to find a HUBSPOT_DEFINED association
        for t in types:
            if str(t.get("category")) == "HUBSPOT_DEFINED" and t.get("typeId"):
                association_type_id = str(t["typeId"])
                break
        # Fall back to first available type if no HUBSPOT_DEFINED found
        if not association_type_id and types[0].get("typeId"):
            association_type_id = str(types[0]["typeId"])

    if not association_type_id:
        raise ToolExecutionError(
            message="Unable to determine association type",
            developer_message=(
                f"No association types found between {from_object.value} and {to_object.value}"
            ),
        )

    return association_type_id
