"""Utility functions for building HubSpot GUI URLs."""


def build_record_gui_url(portal_id: str, object_type: str, object_id: str) -> str:
    """
    Build a HubSpot GUI URL for viewing a specific record.

    Args:
        portal_id: The HubSpot portal/account ID
        object_type: The type of object ('contact', 'company', 'deal', 'ticket')
        object_id: The unique ID of the object

    Returns:
        The complete GUI URL for the record

    Raises:
        ValueError: If object_type is not supported
    """
    object_type_map = {"contact": "1", "company": "2", "deal": "3", "ticket": "5"}

    if object_type.lower() not in object_type_map:
        supported_types = list(object_type_map.keys())
        raise ValueError(
            f"Unsupported object type: {object_type}. Supported types: {supported_types}"
        )

    inner_id = object_type_map[object_type.lower()]
    return f"https://app.hubspot.com/contacts/{portal_id}/record/0-{inner_id}/{object_id}"


def build_deal_gui_url(portal_id: str, deal_id: str) -> str:
    """
    Build a HubSpot GUI URL for viewing a specific deal.

    Args:
        portal_id: The HubSpot portal/account ID
        deal_id: The unique ID of the deal

    Returns:
        The complete GUI URL for the deal record
    """
    return build_record_gui_url(portal_id, "deal", deal_id)


def build_contact_gui_url(portal_id: str, contact_id: str) -> str:
    """
    Build a HubSpot GUI URL for viewing a specific contact.

    Args:
        portal_id: The HubSpot portal/account ID
        contact_id: The unique ID of the contact

    Returns:
        The complete GUI URL for the contact record
    """
    return build_record_gui_url(portal_id, "contact", contact_id)


def build_company_gui_url(portal_id: str, company_id: str) -> str:
    """
    Build a HubSpot GUI URL for viewing a specific company.

    Args:
        portal_id: The HubSpot portal/account ID
        company_id: The unique ID of the company

    Returns:
        The complete GUI URL for the company record
    """
    return build_record_gui_url(portal_id, "company", company_id)


def build_pipeline_gui_url(portal_id: str, pipeline_type: str, pipeline_id: str) -> str:
    """
    Build a HubSpot GUI URL for viewing a pipeline board.

    Args:
        portal_id: The HubSpot portal/account ID
        pipeline_type: The type of pipeline ('deals' or 'tickets')
        pipeline_id: The pipeline ID ('default' for default pipeline or GUID for custom)

    Returns:
        The complete GUI URL for the pipeline board

    Raises:
        ValueError: If pipeline_type is not supported
    """
    if pipeline_type.lower() not in ["deals", "tickets"]:
        raise ValueError(
            f"Unsupported pipeline type: {pipeline_type}. Supported types: ['deals', 'tickets']"
        )

    return f"https://app.hubspot.com/contacts/{portal_id}/{pipeline_type.lower()}/pipeline/{pipeline_id}/"


def build_deal_pipeline_gui_url(portal_id: str, pipeline_id: str) -> str:
    """
    Build a HubSpot GUI URL for viewing a deal pipeline board.

    Args:
        portal_id: The HubSpot portal/account ID
        pipeline_id: The pipeline ID ('default' for default pipeline or GUID for custom)

    Returns:
        The complete GUI URL for the deal pipeline board
    """
    return build_pipeline_gui_url(portal_id, "deals", pipeline_id)


def build_user_profile_gui_url(portal_id: str) -> str:
    """
    Build a HubSpot GUI URL for viewing the current user's profile.

    Args:
        portal_id: The HubSpot portal/account ID

    Returns:
        The complete GUI URL for the user's profile page
    """
    return f"https://app.hubspot.com/user-preferences/{portal_id}/profile"


def extract_portal_id_from_token_info(token_info: dict) -> str | None:
    """
    Extract portal ID from HubSpot token info response.

    Args:
        token_info: The token info dictionary from HubSpot API

    Returns:
        The portal ID as a string, or None if not found
    """
    hub_id = token_info.get("hub_id")
    return str(hub_id) if hub_id is not None else None
