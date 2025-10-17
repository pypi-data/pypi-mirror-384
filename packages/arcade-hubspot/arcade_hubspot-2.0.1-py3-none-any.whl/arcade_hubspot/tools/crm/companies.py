from typing import Annotated, Any

from arcade_tdk import ToolContext, tool
from arcade_tdk.auth import Hubspot

from arcade_hubspot.enums import HubspotIndustryType, HubspotObject, HubspotSortOrder
from arcade_hubspot.http_client.http_client import HubspotHttpClient
from arcade_hubspot.models.tool_models import CreateCompanyResponse
from arcade_hubspot.tool_utils import company_utils, shared_utils


@tool(
    requires_auth=Hubspot(
        scopes=[
            "oauth",
            "crm.objects.companies.read",  # /crm/v3/objects/companies/search
            "crm.objects.contacts.read",  # Associated contacts data
            "crm.objects.deals.read",  # Associated deals data
            "sales-email-read",  # Associated email data
        ],
    ),
)
async def get_company_data_by_keywords(
    context: ToolContext,
    keywords: Annotated[
        str,
        "The keywords to search for companies. It will match against the company name, phone, "
        "and website.",
    ],
    limit: Annotated[
        int, "The maximum number of companies to return. Defaults to 10. Max is 10."
    ] = 10,
    next_page_token: Annotated[
        str | None,
        "The token to get the next page of results. "
        "Defaults to None (returns first page of results)",
    ] = None,
) -> Annotated[
    dict[str, Any],
    "Retrieve company data with associated contacts, deals, calls, emails, "
    "meetings, notes, and tasks.",
]:
    """Retrieve company data with associated contacts, deals, calls, emails,
    meetings, notes, and tasks.

    This tool will return up to 10 items of each associated object (contacts, leads, etc).
    """
    auth_token = shared_utils.get_auth_token_or_raise(context)

    http_client = HubspotHttpClient(auth_token=auth_token)

    token_info = await http_client.get_current_user_info()
    portal_id = str(token_info["hub_id"]) if token_info.get("hub_id") else None

    limit = min(limit, 10)
    result = await http_client.search_by_keywords(
        object_type=HubspotObject.COMPANY,
        keywords=keywords,
        limit=limit,
        next_page_token=next_page_token,
        portal_id=portal_id,
        associations=[
            HubspotObject.CALL,
            HubspotObject.CONTACT,
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
            "oauth",  # Required for authentication
            "crm.objects.companies.write",  # Required to create companies
        ]
    )
)
async def create_company(
    context: ToolContext,
    company_name: Annotated[str, "The company name (required)"],
    web_domain: Annotated[str | None, "The company web domain (e.g., example.com)"] = None,
    industry_type: Annotated[
        str | None,
        "The company industry type (case-insensitive).",
    ] = None,
    company_city: Annotated[str | None, "The company city location"] = None,
    company_state: Annotated[str | None, "The company state or province"] = None,
    company_country: Annotated[str | None, "The company country"] = None,
    phone_number: Annotated[str | None, "The company main phone number"] = None,
    website_url: Annotated[str | None, "The company website URL"] = None,
) -> Annotated[CreateCompanyResponse, "Dictionary containing the created company information"]:
    """
    Create a new company in HubSpot.

    Before calling this tool, use Hubspot.GetAvailableIndustryTypes to see valid values.
    """
    auth_token = shared_utils.get_auth_token_or_raise(context)

    http_client = HubspotHttpClient(auth_token=auth_token)

    token_info = await http_client.get_current_user_info()
    portal_id = str(token_info["hub_id"]) if token_info.get("hub_id") else None

    industry_value = company_utils.validate_and_normalize_industry_type(industry_type)
    company_data = await company_utils.create_company_record(
        http_client=http_client,
        name=company_name,
        domain=web_domain,
        industry=industry_value,
        city=company_city,
        state=company_state,
        country=company_country,
        phone=phone_number,
        website=website_url,
    )

    created = company_utils.create_company_response(company_data, portal_id)
    return created


@tool(
    requires_auth=Hubspot(
        scopes=[
            "oauth",
            "crm.objects.companies.read",  # /crm/v3/objects/companies
        ],
    ),
)
async def list_companies(
    context: ToolContext,
    limit: Annotated[
        int, "The maximum number of companies to return. Defaults to 10. Max is 50."
    ] = 10,
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
    "List companies with pagination support.",
]:
    """List companies with pagination support."""
    auth_token = shared_utils.get_auth_token_or_raise(context)
    http_client = HubspotHttpClient(auth_token=auth_token)

    token_info = await http_client.get_current_user_info()
    portal_id = str(token_info["hub_id"]) if token_info.get("hub_id") else None

    limit = min(limit, 50)

    result = await http_client.list_objects_with_filters(
        object_type=HubspotObject.COMPANY,
        limit=limit,
        sort_order=sort_order,
        next_page_token=next_page_token,
        portal_id=portal_id,
    )

    return result if isinstance(result, dict) else {"result": result}


@tool(requires_auth=Hubspot(scopes=["oauth"]))
async def get_available_industry_types(
    context: ToolContext,
) -> Annotated[
    list[str],
    "List of all available industry types for HubSpot companies.",
]:
    """Get all available industry types for HubSpot companies.

    Returns a sorted list of valid industry type values that can be used
    when creating companies.
    """
    return sorted([industry.value for industry in HubspotIndustryType])
