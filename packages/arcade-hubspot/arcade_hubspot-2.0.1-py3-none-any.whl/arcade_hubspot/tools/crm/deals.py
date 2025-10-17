from typing import Annotated, Any

from arcade_tdk import ToolContext, tool
from arcade_tdk.auth import Hubspot
from arcade_tdk.errors import ToolExecutionError

from arcade_hubspot.enums import (
    HubspotDealPriority,
    HubspotDealType,
    HubspotObject,
    HubspotSortOrder,
)
from arcade_hubspot.http_client.http_client import HubspotHttpClient
from arcade_hubspot.models.tool_models import AssociationResult, CreateDealResponse
from arcade_hubspot.tool_utils import deal_utils, pipeline_utils, shared_utils


@tool(
    requires_auth=Hubspot(
        scopes=[
            "oauth",
            "crm.objects.deals.read",  # /crm/v3/objects/deals/search
            "crm.objects.contacts.read",  # Associated contacts data
            "crm.objects.companies.read",  # Associated companies data
            "sales-email-read",  # Associated email data
        ],
    ),
)
async def get_deal_data_by_keywords(
    context: ToolContext,
    keywords: Annotated[
        str,
        "The keywords to search for deals. It will match against the deal name and description.",
    ],
    limit: Annotated[int, "The maximum number of deals to return. Defaults to 10. Max is 10."] = 10,
    next_page_token: Annotated[
        str | None,
        "The token to get the next page of results. "
        "Defaults to None (returns first page of results)",
    ] = None,
) -> Annotated[
    dict[str, Any],
    "Retrieve deal data with associated contacts, companies, calls, emails, "
    "meetings, notes, and tasks.",
]:
    """Retrieve deal data with associated contacts, companies, calls, emails,
    meetings, notes, and tasks.

    This tool will return up to 10 items of each associated object (contacts, companies, etc).
    """
    auth_token = shared_utils.get_auth_token_or_raise(context)

    http_client = HubspotHttpClient(auth_token=auth_token)

    token_info = await http_client.get_current_user_info()
    portal_id = str(token_info["hub_id"]) if token_info.get("hub_id") else None

    limit = min(limit, 10)
    result = await http_client.search_by_keywords(
        object_type=HubspotObject.DEAL,
        keywords=keywords,
        limit=limit,
        next_page_token=next_page_token,
        portal_id=portal_id,
        associations=[
            HubspotObject.CALL,
            HubspotObject.CONTACT,
            HubspotObject.COMPANY,
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
            "crm.objects.deals.write",  # Required to create deals
        ]
    )
)
async def create_deal(
    context: ToolContext,
    deal_name: Annotated[str, "The deal name (required)"],
    deal_amount: Annotated[float | None, "The deal amount/value"] = None,
    deal_stage: Annotated[str | None, "The deal stage"] = None,
    deal_type: Annotated[
        HubspotDealType | None,
        "The deal type.",
    ] = None,
    expected_close_date: Annotated[str | None, "Expected close date in YYYY-MM-DD format"] = None,
    pipeline_id: Annotated[
        str | None,
        "Pipeline id. Use 'default' for default pipeline or pass a pipeline id (integer)",
    ] = "default",
    deal_owner: Annotated[str | None, "The deal owner user ID"] = None,
    priority_level: Annotated[
        HubspotDealPriority | None,
        "Priority level.",
    ] = None,
    deal_description: Annotated[str | None, "The deal description"] = None,
) -> Annotated[CreateDealResponse, "Dictionary containing the created deal information"]:
    """
    Create a new deal in HubSpot.

    If pipeline_id is not provided, the default pipeline will be used.

    For custom pipelines, deal_stage must be a valid stage ID within
    the selected pipeline. If deal_stage is not specified,
    the first stage in the pipeline will be used automatically.

    It is recommended have already pipeline data available when
    planning to call this tool.
    """
    auth_token = shared_utils.get_auth_token_or_raise(context)

    http_client = HubspotHttpClient(auth_token=auth_token)

    token_info = await http_client.get_current_user_info()
    portal_id = str(token_info["hub_id"]) if token_info.get("hub_id") else None

    # If a stage is provided, ensure we have a valid pipeline_id (use default if not provided)
    effective_pipeline_id = pipeline_id or "default"
    if (deal_stage is not None and str(deal_stage).strip() != "") and (
        effective_pipeline_id.strip() == ""
    ):
        raise ToolExecutionError(
            message="pipeline_id is required when deal_stage is provided",
            developer_message="Provide pipeline_id along with deal_stage",
        )

    (
        normalized_deal_type,
        normalized_priority,
        closedate_ms,
        pipeline_value,
    ) = _normalize_deal_creation_inputs(
        deal_type=deal_type,
        priority_level=priority_level,
        expected_close_date=expected_close_date,
        pipeline_id=pipeline_id,
    )

    deal_stage, pipeline_ref, stage_ref = await pipeline_utils.validate_pipeline_and_select_stage(
        http_client=http_client,
        pipeline_id=pipeline_value,
        deal_stage=deal_stage,
    )

    deal_data = await deal_utils.create_deal_record(
        http_client=http_client,
        deal_name=deal_name,
        amount=deal_amount,
        deal_stage=deal_stage,
        deal_type=normalized_deal_type,
        close_date=closedate_ms,
        pipeline=pipeline_value,
        deal_owner=deal_owner,
        priority=normalized_priority,
        deal_description=deal_description,
    )

    created = deal_utils.create_deal_response(
        deal_data,
        pipeline_ref=pipeline_ref,
        stage_ref=stage_ref,
        portal_id=portal_id,
    )
    return created


def _normalize_deal_creation_inputs(
    deal_type: HubspotDealType | None,
    priority_level: HubspotDealPriority | None,
    expected_close_date: str | None,
    pipeline_id: str | None,
) -> tuple[str | None, str | None, str | None, str]:
    """Normalize enums, convert close date, and validate pipeline id."""
    return deal_utils.normalize_deal_creation_inputs(
        deal_type=deal_type,
        priority_level=priority_level,
        expected_close_date=expected_close_date,
        pipeline_id=pipeline_id,
    )


@tool(
    requires_auth=Hubspot(
        scopes=[
            "oauth",  # Required for authentication
            "crm.objects.deals.write",  # Required to update deals
            "crm.objects.deals.read",  # Required to read deal pipelines for enrichment
        ]
    )
)
async def update_deal_close_date(
    context: ToolContext,
    deal_id: Annotated[int, "The ID of the deal to update"],
    expected_close_date: Annotated[str, "New expected close date in YYYY-MM-DD format"],
) -> Annotated[CreateDealResponse, "Dictionary containing the updated deal information"]:
    """
    Update the expected close date of an existing deal in HubSpot.
    """
    auth_token = shared_utils.get_auth_token_or_raise(context)
    http_client = HubspotHttpClient(auth_token=auth_token)

    token_info = await http_client.get_current_user_info()
    portal_id = str(token_info["hub_id"]) if token_info.get("hub_id") else None

    closedate_ms = shared_utils.to_epoch_millis(expected_close_date)

    deal_data = await deal_utils.update_deal_record(
        http_client=http_client,
        deal_id=str(deal_id),
        properties={"closedate": closedate_ms},
    )

    # Enrich with pipeline and stage information
    pipeline_ref, stage_ref = await deal_utils.enrich_deal_with_pipeline_info(
        http_client=http_client,
        deal_data=deal_data,
    )

    updated = deal_utils.create_deal_response(deal_data, pipeline_ref, stage_ref, portal_id)
    return updated


@tool(
    requires_auth=Hubspot(
        scopes=[
            "oauth",  # Required for authentication
            "crm.objects.deals.write",  # Required to update deals
            "crm.objects.deals.read",  # Required to read deal pipelines for enrichment
        ]
    )
)
async def update_deal_stage(
    context: ToolContext,
    deal_id: Annotated[int, "The ID of the deal to update"],
    deal_stage: Annotated[str, "New deal stage ID"],
    current_pipeline_id: Annotated[
        str | None,
        "Current pipeline id for this deal, if already known (skips fetching the deal)",
    ] = None,
    allow_pipeline_change: Annotated[
        bool,
        "If true, allows changing the deal's pipeline when the stage belongs to another pipeline",
    ] = False,
) -> Annotated[CreateDealResponse, "The updated deal information"]:
    """
    Updates a deal's stage, validating against the current pipeline if provided
    or fetched using deal's pipeline property.

    Send current_pipeline_id to skip fetching the deal.
    If pipeline changes are allowed, updates the stage and HubSpot
    may move the deal to another pipeline.

    It is recommended have already pipeline data available when
    planning to call this tool.
    """
    auth_token = shared_utils.get_auth_token_or_raise(context)
    http_client = HubspotHttpClient(auth_token=auth_token)

    token_info = await http_client.get_current_user_info()
    portal_id = str(token_info["hub_id"]) if token_info.get("hub_id") else None

    # Resolve current pipeline id (provided or fetched)
    effective_pipeline_id = await deal_utils.resolve_current_pipeline_id(
        http_client=http_client,
        deal_id=str(deal_id),
        current_pipeline_id=(
            shared_utils.normalize_and_validate_pipeline_id(current_pipeline_id)
            if current_pipeline_id is not None and current_pipeline_id.strip() != ""
            else None
        ),
    )

    # Validate membership if pipeline change is not allowed
    if not allow_pipeline_change:
        await deal_utils.validate_stage_membership_or_retry(
            http_client=http_client,
            pipeline_id=effective_pipeline_id,
            deal_stage=deal_stage,
        )

    # Perform the update (if allow_pipeline_change=true, HubSpot may update pipeline automatically)
    deal_data = await deal_utils.update_deal_record(
        http_client=http_client,
        deal_id=str(deal_id),
        properties={"dealstage": deal_stage},
    )

    # Enrich with pipeline and stage information (reflects new pipeline if changed by HubSpot)
    pipeline_ref, stage_ref = await deal_utils.enrich_deal_with_pipeline_info(
        http_client=http_client,
        deal_data=deal_data,
    )

    updated = deal_utils.create_deal_response(deal_data, pipeline_ref, stage_ref, portal_id)
    return updated


@tool(
    requires_auth=Hubspot(
        scopes=[
            "oauth",  # Required for authentication
            "crm.objects.deals.read",  # Required to read deals
        ]
    )
)
async def get_deal_by_id(
    context: ToolContext,
    deal_id: Annotated[int, "The ID of the deal to retrieve"],
) -> Annotated[CreateDealResponse, "Dictionary containing the deal information"]:
    """
    Retrieve a specific deal by its ID from HubSpot.
    """
    auth_token = shared_utils.get_auth_token_or_raise(context)
    http_client = HubspotHttpClient(auth_token=auth_token)

    token_info = await http_client.get_current_user_info()
    portal_id = str(token_info["hub_id"]) if token_info.get("hub_id") else None

    deal_data = await deal_utils.get_deal_record(
        http_client=http_client,
        deal_id=str(deal_id),
    )

    # Enrich with pipeline and stage information
    pipeline_ref, stage_ref = await deal_utils.enrich_deal_with_pipeline_info(
        http_client=http_client,
        deal_data=deal_data,
    )

    deal_response = deal_utils.create_deal_response(deal_data, pipeline_ref, stage_ref, portal_id)
    return deal_response


@tool(
    requires_auth=Hubspot(
        scopes=[
            "oauth",
            "crm.objects.deals.write",
            "crm.objects.deals.read",
            "crm.objects.contacts.write",
            "crm.objects.contacts.read",
        ]
    )
)
async def associate_contact_to_deal(
    context: ToolContext,
    deal_id: Annotated[int, "The ID of the deal to associate the contact with"],
    contact_id: Annotated[int, "The ID of the contact to associate with the deal"],
) -> Annotated[AssociationResult, "Dictionary containing the association result"]:
    """
    Associate a contact with an existing deal in HubSpot.
    """
    auth_token = shared_utils.get_auth_token_or_raise(context)
    http_client = HubspotHttpClient(auth_token=auth_token)

    association_result = await deal_utils.associate_contact_with_deal(
        http_client=http_client,
        deal_id=str(deal_id),
        contact_id=str(contact_id),
    )

    return association_result


@tool(
    requires_auth=Hubspot(
        scopes=[
            "oauth",
            "crm.objects.deals.read",  # /crm/v3/objects/deals/search
        ],
    ),
)
async def list_deals(
    context: ToolContext,
    limit: Annotated[int, "The maximum number of deals to return. Defaults to 10. Max is 50."] = 10,
    contact_id: Annotated[
        int | None, "Filter deals by contact ID. Defaults to None (no filtering)."
    ] = None,
    company_id: Annotated[
        int | None, "Filter deals by company ID. Defaults to None (no filtering)."
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
    "List deals with optional filtering by contact ID or company ID, with pagination support.",
]:
    """List deals with optional filtering by contact ID or company ID, with pagination support."""
    auth_token = shared_utils.get_auth_token_or_raise(context)
    http_client = HubspotHttpClient(auth_token=auth_token)

    token_info = await http_client.get_current_user_info()
    portal_id = str(token_info["hub_id"]) if token_info.get("hub_id") else None

    limit = min(limit, 50)

    result = await http_client.list_objects_with_filters(
        object_type=HubspotObject.DEAL,
        limit=limit,
        contact_id=str(contact_id) if contact_id is not None else None,
        company_id=str(company_id) if company_id is not None else None,
        sort_order=sort_order,
        next_page_token=next_page_token,
        portal_id=portal_id,
    )

    return result if isinstance(result, dict) else {"result": result}
