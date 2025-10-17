"""Comprehensive helper functions for HTTP client operations."""

import json
from datetime import datetime, timedelta
from typing import Any

import httpx
from arcade_tdk.errors import ToolExecutionError

from arcade_hubspot.enums import HubspotAssociationType
from arcade_hubspot.exceptions import HubspotToolExecutionError, NotFoundError


def build_error_context(
    *,
    method: str,
    url: str,
    endpoint: str,
    api_version: str,
    base_url: str,
) -> dict[str, str]:
    """Create a compact context dictionary to enrich error messages."""
    resource_hint = None
    try:
        parts = endpoint.split("/")
        if parts and parts[0] == "objects" and len(parts) > 1:
            resource_hint = f"object:{parts[1]}"
        elif parts and parts[0] == "pipelines" and len(parts) > 1:
            resource_hint = f"pipeline:{parts[1]}"
    except Exception:
        resource_hint = None

    context: dict[str, str] = {
        "method": method,
        "url": url,
        "endpoint": endpoint,
        "api_version": api_version,
        "base_url": base_url,
    }
    if resource_hint:
        context["resource_hint"] = resource_hint
    return context


def raise_for_status(
    response: httpx.Response,
    *,
    request_context: dict[str, str] | None = None,
) -> None:
    """Raise appropriate exceptions based on HTTP status codes."""
    if response.status_code < 300:
        return

    minimal_hint: dict[str, str] = {}
    if request_context:
        endpoint_hint = request_context.get("endpoint")
        resource_hint = request_context.get("resource_hint")
        if endpoint_hint:
            minimal_hint["endpoint"] = endpoint_hint
        if resource_hint:
            minimal_hint["resource_hint"] = resource_hint

    try:
        data = response.json()
        error_message = data.get("message", "Unknown error")
        errors_json = json.dumps(data.get("errors", []))
        category = data.get("category")
        correlation_id = data.get("correlationId")
        if category:
            minimal_hint["category"] = str(category)
        if correlation_id:
            minimal_hint["correlationId"] = str(correlation_id)

        developer_message: str | None = errors_json
        if minimal_hint:
            developer_message = f"{errors_json} | hint: {json.dumps(minimal_hint)}"
    except Exception:
        error_message = response.text or f"HTTP {response.status_code}"
        developer_message = f"hint: {json.dumps(minimal_hint)}" if minimal_hint else None

    if response.status_code == 404:
        raise NotFoundError(error_message, developer_message)

    raise HubspotToolExecutionError(error_message, developer_message)


def build_associations(
    activity_type: str,
    contact_ids: list[str] | None = None,
    company_ids: list[str] | None = None,
    deal_ids: list[str] | None = None,
    require_association: bool = True,
) -> list[dict[str, Any]] | None:
    """
    Build association structure for activity creation using static association type IDs.
    This is kept for backward compatibility but should be replaced with dynamic version.

    Args:
        activity_type: Type of activity (NOTE, CALL, EMAIL, etc.)
        contact_ids: List of contact IDs to associate
        company_ids: List of company IDs to associate
        deal_ids: List of deal IDs to associate
        require_association: If True, raises error when no associations provided

    Returns:
        List of association dictionaries or None

    Raises:
        ToolExecutionError: If require_association=True and no associations provided
    """
    _validate_associations_required(require_association, contact_ids, company_ids, deal_ids)

    associations = []
    associations.extend(_build_contact_associations(activity_type, contact_ids))
    associations.extend(_build_company_associations(activity_type, company_ids))
    associations.extend(_build_deal_associations(activity_type, deal_ids))

    return associations if associations else None


def _validate_associations_required(
    require_association: bool,
    contact_ids: list[str] | None,
    company_ids: list[str] | None,
    deal_ids: list[str] | None,
) -> None:
    """Validate that at least one association is provided if required."""
    if require_association and not any([contact_ids, company_ids, deal_ids]):
        raise ToolExecutionError(
            message="At least one association is required",
            developer_message=(
                "Provide at least one of: associate_to_contact_id, "
                "associate_to_company_id, or associate_to_deal_id. "
                "Activities must be associated with at least one CRM record."
            ),
        )


def _build_contact_associations(
    activity_type: str, contact_ids: list[str] | None
) -> list[dict[str, Any]]:
    """Build default contact associations for the given activity type."""
    if not contact_ids:
        return []

    return [
        {
            "to": {"id": contact_id},
            "types": [
                {
                    "associationCategory": "HUBSPOT_DEFINED",
                    "associationTypeId": HubspotAssociationType.ENGAGEMENT_TO_CONTACT.value,
                }
            ],
        }
        for contact_id in contact_ids
    ]


def _build_company_associations(
    activity_type: str, company_ids: list[str] | None
) -> list[dict[str, Any]]:
    """Build default company associations for the given activity type."""
    if not company_ids:
        return []

    return [
        {
            "to": {"id": company_id},
            "types": [
                {
                    "associationCategory": "HUBSPOT_DEFINED",
                    "associationTypeId": HubspotAssociationType.ENGAGEMENT_TO_COMPANY.value,
                }
            ],
        }
        for company_id in company_ids
    ]


def _build_deal_associations(
    activity_type: str, deal_ids: list[str] | None
) -> list[dict[str, Any]]:
    """Build default deal associations for the given activity type."""
    if not deal_ids:
        return []

    return [
        {
            "to": {"id": deal_id},
            "types": [
                {
                    "associationCategory": "HUBSPOT_DEFINED",
                    "associationTypeId": HubspotAssociationType.ENGAGEMENT_TO_DEAL.value,
                }
            ],
        }
        for deal_id in deal_ids
    ]


def build_note_properties_and_associations(
    *,
    body: str,
    owner_id: str,
    timestamp: int | None = None,
    contact_ids: list[str] | None = None,
    company_ids: list[str] | None = None,
    deal_ids: list[str] | None = None,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Build properties and associations for note creation."""
    if not any([contact_ids, company_ids, deal_ids]):
        raise ToolExecutionError(
            message="At least one association is required",
            developer_message=(
                "Provide at least one of: associate_to_contact_id, "
                "associate_to_company_id, or associate_to_deal_id. "
                "Activities must be associated with at least one CRM record."
            ),
        )

    properties = {
        "hs_note_body": body,
        "hubspot_owner_id": owner_id,
        "hs_timestamp": timestamp,
    }

    associations = []

    if contact_ids:
        for contact_id in contact_ids:
            associations.append({
                "to": {"id": contact_id},
                "types": [
                    {
                        "associationCategory": "HUBSPOT_DEFINED",
                        "associationTypeId": HubspotAssociationType.NOTE_TO_CONTACT.value,
                    }
                ],
            })

    if company_ids:
        for company_id in company_ids:
            associations.append({
                "to": {"id": company_id},
                "types": [
                    {
                        "associationCategory": "HUBSPOT_DEFINED",
                        "associationTypeId": HubspotAssociationType.NOTE_TO_COMPANY.value,
                    }
                ],
            })

    if deal_ids:
        for deal_id in deal_ids:
            associations.append({
                "to": {"id": deal_id},
                "types": [
                    {
                        "associationCategory": "HUBSPOT_DEFINED",
                        "associationTypeId": HubspotAssociationType.NOTE_TO_DEAL.value,
                    }
                ],
            })

    return properties, associations or []


def build_email_properties_and_associations(
    *,
    subject: str,
    owner_id: str,
    direction: str = "EMAIL",
    status: str | None = None,
    timestamp: int | None = None,
    from_email: str | None = None,
    from_first_name: str | None = None,
    from_last_name: str | None = None,
    to_emails: list[dict[str, str]] | None = None,
    cc_emails: list[dict[str, str]] | None = None,
    bcc_emails: list[dict[str, str]] | None = None,
    body_text: str | None = None,
    body_html: str | None = None,
    contact_ids: list[str] | None = None,
    company_ids: list[str] | None = None,
    deal_ids: list[str] | None = None,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Build properties and associations for email creation."""
    properties = {}
    if subject:
        properties["hs_email_subject"] = subject
    if direction:
        properties["hs_email_direction"] = direction
    if status:
        properties["hs_email_status"] = status
    if owner_id:
        properties["hubspot_owner_id"] = owner_id
    if timestamp:
        properties["hs_timestamp"] = str(timestamp)
    if body_text:
        properties["hs_email_text"] = body_text
    if body_html:
        properties["hs_email_html"] = body_html

    if from_email or to_emails or cc_emails or bcc_emails:
        headers: dict[str, Any] = {}

        if from_email:
            headers["from"] = {
                "email": from_email,
                "firstName": from_first_name or "",
                "lastName": from_last_name or "",
            }

        headers["to"] = to_emails or []
        headers["cc"] = cc_emails or []
        headers["bcc"] = bcc_emails or []

        properties["hs_email_headers"] = json.dumps(headers)

    associations = build_associations(
        activity_type="EMAIL",
        contact_ids=contact_ids,
        company_ids=company_ids,
        deal_ids=deal_ids,
        require_association=True,
    )

    return properties, associations or []


def build_meeting_properties_and_associations(
    *,
    title: str,
    start_date: str,
    start_time: str,
    owner_id: str,
    duration: str | None = None,
    location: str | None = None,
    outcome: str | None = None,
    contact_ids: list[str] | None = None,
    company_ids: list[str] | None = None,
    deal_ids: list[str] | None = None,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Build properties and associations for meeting creation."""

    start_datetime_str = f"{start_date}T{start_time}"
    if len(start_time.split(":")) == 2:
        start_datetime_str += ":00"

    start_datetime = datetime.fromisoformat(start_datetime_str)
    start_timestamp = int(start_datetime.timestamp() * 1000)

    end_timestamp = None
    if duration and ":" in duration:
        try:
            hours, minutes = map(int, duration.split(":"))
            end_datetime = start_datetime + timedelta(hours=hours, minutes=minutes)
            end_timestamp = int(end_datetime.timestamp() * 1000)
        except ValueError:
            pass

    properties = {
        "hs_meeting_title": title,
        "hs_meeting_start_time": str(start_timestamp),
        "hs_timestamp": str(start_timestamp),
    }
    if end_timestamp:
        properties["hs_meeting_end_time"] = str(end_timestamp)
    if location:
        properties["hs_meeting_location"] = location
    if outcome:
        properties["hs_meeting_outcome"] = outcome
    if owner_id:
        properties["hubspot_owner_id"] = owner_id

    associations = build_associations(
        activity_type="MEETING",
        contact_ids=contact_ids,
        company_ids=company_ids,
        deal_ids=deal_ids,
        require_association=True,
    )

    return properties, associations or []


def build_call_properties_and_associations(
    *,
    title: str,
    owner_id: str,
    direction: str | None = None,
    summary: str | None = None,
    timestamp: int | None = None,
    duration: int | None = None,
    to_number: str | None = None,
    from_number: str | None = None,
    contact_ids: list[str] | None = None,
    company_ids: list[str] | None = None,
    deal_ids: list[str] | None = None,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Build properties and associations for call creation."""
    properties = {
        "hs_call_title": title,
        "hs_call_direction": direction,
        "hs_call_body": summary,
        "hubspot_owner_id": owner_id,
        "hs_timestamp": timestamp,
        "hs_call_duration": duration,
        "hs_call_to_number": to_number,
        "hs_call_from_number": from_number,
    }

    associations = build_associations(
        activity_type="CALL",
        contact_ids=contact_ids,
        company_ids=company_ids,
        deal_ids=deal_ids,
        require_association=True,
    )

    return properties, associations or []


def build_communication_properties_and_associations(
    *,
    channel: str,
    owner_id: str,
    logged_from: str | None = None,
    body_text: str | None = None,
    timestamp: int | None = None,
    contact_ids: list[str] | None = None,
    company_ids: list[str] | None = None,
    deal_ids: list[str] | None = None,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Build properties and associations for communication creation using static association IDs."""
    properties = {
        "hs_communication_channel_type": channel,
        "hs_communication_logged_from": logged_from or "CRM",
        "hubspot_owner_id": owner_id,
    }

    if body_text:
        properties["hs_communication_body"] = body_text
    if timestamp:
        properties["hs_timestamp"] = str(timestamp)

    associations = build_associations(
        activity_type="COMMUNICATION",
        contact_ids=contact_ids,
        company_ids=company_ids,
        deal_ids=deal_ids,
        require_association=True,
    )

    return properties, associations or []
