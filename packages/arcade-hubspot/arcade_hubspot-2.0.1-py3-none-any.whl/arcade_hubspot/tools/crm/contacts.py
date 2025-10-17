from typing import Annotated, Any

from arcade_tdk import ToolContext, tool
from arcade_tdk.auth import Hubspot

from arcade_hubspot.enums import HubspotObject, HubspotSortOrder
from arcade_hubspot.http_client.http_client import HubspotHttpClient
from arcade_hubspot.models.tool_models import CreateContactResponse
from arcade_hubspot.tool_utils import contact_utils, shared_utils


@tool(
    requires_auth=Hubspot(
        scopes=[
            "oauth",
            "crm.objects.contacts.read",  # /crm/v3/objects/contacts/search
        ],
    ),
)
async def get_contact_data_by_keywords(
    context: ToolContext,
    keywords: Annotated[
        str,
        "The keywords to search for contacts. It will match against the contact's "
        "first and last name, email addresses, phone numbers, and company name.",
    ],
    limit: Annotated[
        int, "The maximum number of contacts to return. Defaults to 10. Max is 100."
    ] = 10,
    next_page_token: Annotated[
        str | None,
        "The token to get the next page of results. "
        "Defaults to None (returns first page of results)",
    ] = None,
) -> Annotated[
    dict[str, Any],
    "Retrieve contact data with associated companies, deals, calls, "
    "emails, meetings, notes, and tasks.",
]:
    """
    Retrieve contact data with associated companies, deals, calls, emails,
    meetings, notes, and tasks.
    """
    auth_token = shared_utils.get_auth_token_or_raise(context)

    http_client = HubspotHttpClient(auth_token=auth_token)

    token_info = await http_client.get_current_user_info()
    portal_id = str(token_info["hub_id"]) if token_info.get("hub_id") else None

    limit = min(limit, 100)
    result = await http_client.search_by_keywords(
        object_type=HubspotObject.CONTACT,
        keywords=keywords,
        limit=limit,
        next_page_token=next_page_token,
        portal_id=portal_id,
        associations=[
            HubspotObject.CALL,
            HubspotObject.COMPANY,
            HubspotObject.DEAL,
            HubspotObject.EMAIL,
            HubspotObject.MEETING,
            HubspotObject.NOTE,
            HubspotObject.TASK,
        ],
    )
    return result if isinstance(result, dict) else {"result": result}


@tool(
    requires_auth=Hubspot(
        scopes=[
            "oauth",
            "crm.objects.contacts.write",  # /crm/v3/objects/contacts
        ],
    ),
)
async def create_contact(
    context: ToolContext,
    company_id: Annotated[int, "The ID of the company to create the contact for."],
    first_name: Annotated[str, "The first name of the contact."],
    last_name: Annotated[str | None, "The last name of the contact."] = None,
    email: Annotated[str | None, "The email address of the contact."] = None,
    phone: Annotated[str | None, "The phone number of the contact."] = None,
    mobile_phone: Annotated[str | None, "The mobile phone number of the contact."] = None,
    job_title: Annotated[str | None, "The job title of the contact."] = None,
) -> Annotated[CreateContactResponse, "Create a contact associated with a company."]:
    """Create a contact associated with a company."""
    auth_token = shared_utils.get_auth_token_or_raise(context)

    http_client = HubspotHttpClient(auth_token=auth_token)

    token_info = await http_client.get_current_user_info()
    portal_id = str(token_info["hub_id"]) if token_info.get("hub_id") else None

    response = await http_client.create_contact(
        company_id=str(company_id),
        first_name=first_name,
        last_name=last_name,
        email=email,
        phone=phone,
        mobile_phone=mobile_phone,
        job_title=job_title,
    )

    result = contact_utils.create_contact_response(dict(response), portal_id)
    return result


@tool(
    requires_auth=Hubspot(
        scopes=[
            "oauth",
            "crm.objects.contacts.read",  # /crm/v3/objects/contacts/search
        ],
    ),
)
async def list_contacts(
    context: ToolContext,
    limit: Annotated[
        int, "The maximum number of contacts to return. Defaults to 10. Max is 50."
    ] = 10,
    company_id: Annotated[
        int | None, "Filter contacts by company ID. Defaults to None (no filtering)."
    ] = None,
    deal_id: Annotated[
        int | None, "Filter contacts by deal ID. Defaults to None (no filtering)."
    ] = None,
    sort_order: Annotated[
        HubspotSortOrder, "Sort order for results. Defaults to LATEST_MODIFIED."
    ] = HubspotSortOrder.LATEST_MODIFIED,
    next_page_token: Annotated[
        str | None,
        "The token to get the next page of results. "
        "Defaults to None (returns first page of results)",
    ] = None,
) -> Annotated[
    dict[str, Any],
    "List contacts in the HubSpot portal.",
]:
    """List contacts with optional filtering by company ID or deal ID, with pagination support."""
    auth_token = shared_utils.get_auth_token_or_raise(context)
    http_client = HubspotHttpClient(auth_token=auth_token)

    token_info = await http_client.get_current_user_info()
    portal_id = str(token_info["hub_id"]) if token_info.get("hub_id") else None

    limit = min(limit, 50)

    result = await http_client.list_objects_with_filters(
        object_type=HubspotObject.CONTACT,
        limit=limit,
        company_id=str(company_id) if company_id is not None else None,
        deal_id=str(deal_id) if deal_id is not None else None,
        sort_order=sort_order,
        next_page_token=next_page_token,
        portal_id=portal_id,
    )

    return result if isinstance(result, dict) else {"result": result}
