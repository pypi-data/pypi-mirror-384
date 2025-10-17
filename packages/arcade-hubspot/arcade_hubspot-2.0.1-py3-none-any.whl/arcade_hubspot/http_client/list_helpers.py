"""Helper functions for list operations in HubSpot HTTP client."""

from typing import Any

from arcade_hubspot.enums import HubspotObject, HubspotSortOrder


def build_filter_groups(
    *,
    contact_id: str | None = None,
    company_id: str | None = None,
    deal_id: str | None = None,
) -> list[dict[str, Any]]:
    """
    Build HubSpot API filter groups for association-based filtering.

    Args:
        contact_id: Filter by associated contact ID
        company_id: Filter by associated company ID
        deal_id: Filter by associated deal ID

    Returns:
        List of filter group dictionaries for HubSpot Search API
    """
    filter_groups = []

    if contact_id:
        filter_groups.append({
            "filters": [
                {"propertyName": "associations.contact", "operator": "EQ", "value": contact_id}
            ]
        })

    if company_id:
        filter_groups.append({
            "filters": [
                {"propertyName": "associations.company", "operator": "EQ", "value": company_id}
            ]
        })

    if deal_id:
        filter_groups.append({
            "filters": [{"propertyName": "associations.deal", "operator": "EQ", "value": deal_id}]
        })

    return filter_groups


def get_sort_property_for_object(object_type: HubspotObject) -> str:
    """
    Get the appropriate property name for alphabetical sorting by object type.

    Args:
        object_type: The HubSpot object type

    Returns:
        Property name to use for alphabetical sorting
    """
    property_mapping = {
        HubspotObject.CONTACT: "firstname",
        HubspotObject.COMPANY: "name",
        HubspotObject.DEAL: "dealname",
    }
    return property_mapping.get(object_type, "name")


def build_sort_configuration(
    sort_order: HubspotSortOrder | None,
    object_type: HubspotObject,
) -> list[dict[str, str]]:
    """
    Build HubSpot API sort configuration based on sort order and object type.

    Args:
        sort_order: The desired sort order (None defaults to LATEST_MODIFIED)
        object_type: The HubSpot object type being sorted

    Returns:
        List of sort configuration dictionaries for HubSpot Search API
    """
    if sort_order == HubspotSortOrder.LATEST_MODIFIED or sort_order is None:
        return [{"propertyName": "hs_lastmodifieddate", "direction": "DESCENDING"}]
    elif sort_order == HubspotSortOrder.OLDEST_MODIFIED:
        return [{"propertyName": "hs_lastmodifieddate", "direction": "ASCENDING"}]
    elif sort_order == HubspotSortOrder.ALPHABETICAL:
        property_name = get_sort_property_for_object(object_type)
        return [{"propertyName": property_name, "direction": "ASCENDING"}]
    else:
        # Default fallback to latest modified
        return [{"propertyName": "hs_lastmodifieddate", "direction": "DESCENDING"}]


def build_search_request_data(
    *,
    limit: int,
    object_type: HubspotObject,
    properties: list[str],
    contact_id: str | None = None,
    company_id: str | None = None,
    deal_id: str | None = None,
    sort_order: HubspotSortOrder | None = None,
    next_page_token: str | None = None,
) -> dict[str, Any]:
    """
    Build complete search request data for HubSpot Search API.

    Args:
        limit: Maximum number of results to return
        object_type: The HubSpot object type to search
        properties: List of properties to include in results
        contact_id: Filter by associated contact ID
        company_id: Filter by associated company ID
        deal_id: Filter by associated deal ID
        sort_order: Sort order for results
        next_page_token: Pagination token for next page

    Returns:
        Complete request data dictionary for HubSpot Search API
    """
    request_data = {
        "limit": limit,
        "sorts": build_sort_configuration(sort_order, object_type),
        "properties": properties,
    }

    filter_groups = build_filter_groups(
        contact_id=contact_id,
        company_id=company_id,
        deal_id=deal_id,
    )

    if filter_groups:
        request_data["filterGroups"] = filter_groups

    if next_page_token:
        request_data["after"] = next_page_token

    return request_data
