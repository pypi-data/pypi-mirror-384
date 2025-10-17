"""Utility functions for deal operations."""

from typing import Any, cast

from arcade_tdk.errors import RetryableToolError

from arcade_hubspot.enums import HubspotDealPriority, HubspotDealType
from arcade_hubspot.http_client import HubspotHttpClient
from arcade_hubspot.models.crm_api_models import HubSpotCreateDealResponse
from arcade_hubspot.models.tool_models import (
    AssociationResult,
    CreateDealResponse,
    DealPipelineRef,
    DealStageRef,
)
from arcade_hubspot.tool_utils import shared_utils
from arcade_hubspot.utils.gui_url_builder import build_deal_gui_url


async def create_deal_record(
    http_client: HubspotHttpClient,
    deal_name: str,
    amount: float | None = None,
    deal_stage: str | None = None,
    deal_type: str | None = None,
    close_date: str | None = None,
    pipeline: str | None = None,
    deal_owner: str | None = None,
    priority: str | None = None,
    deal_description: str | None = None,
) -> HubSpotCreateDealResponse:
    """
    Create a deal record in HubSpot via the HTTP client.

    Args:
        http_client: HubSpot HTTP client
        deal_name: Deal name (required)
        amount: Deal amount/value
        deal_stage: Deal stage
        deal_type: Deal type (e.g., "New Business", "Existing Business")
        close_date: Expected close date (YYYY-MM-DD format)
        pipeline: Deal pipeline
        deal_owner: Deal owner user ID
        priority: Deal priority level
        deal_description: Deal description

    Returns:
        HubSpot API response with created deal information.
    """
    response = await http_client.create_deal(
        deal_name=deal_name,
        amount=amount,
        deal_stage=deal_stage,
        deal_type=deal_type,
        close_date=close_date,
        pipeline=pipeline,
        deal_owner=deal_owner,
        priority=priority,
        deal_description=deal_description,
    )
    return response


def create_deal_response(
    deal_data: HubSpotCreateDealResponse,
    pipeline_ref: DealPipelineRef | None = None,
    stage_ref: DealStageRef | None = None,
    portal_id: str | None = None,
) -> CreateDealResponse:
    """
    Create a standardized response for deal creation operations.

    Args:
        deal_data: Raw deal data from HubSpot API

    Returns:
        Cleaned deal response for tool output.
    """
    properties = deal_data.get("properties", {})
    pipeline_info: DealPipelineRef | None = None
    if pipeline_ref is not None:
        pipeline_info = pipeline_ref

    if stage_ref is None and properties.get("dealstage"):
        stage_id_value = properties.get("dealstage") or ""
        stage_ref = cast(DealStageRef, {"id": stage_id_value, "name": None})

    # Build GUI URL if portal_id is available
    deal_gui_url = None
    if portal_id and deal_data.get("id"):
        deal_gui_url = build_deal_gui_url(portal_id, str(deal_data.get("id")))

    # Build response data
    response_data: CreateDealResponse = {
        "id": str(deal_data.get("id", "")),
        "deal_name": properties.get("dealname"),
        "amount": properties.get("amount"),
        "deal_stage": stage_ref,
        "deal_type": properties.get("dealtype"),
        "expected_close_date": properties.get("closedate"),
        "pipeline": pipeline_info,
        "deal_owner": properties.get("hubspot_owner_id"),
        "priority_level": properties.get("hs_priority"),
        "deal_description": properties.get("description"),
        "created_at": deal_data.get("createdAt"),
        "deal_gui_url": deal_gui_url,
    }

    return response_data


async def update_deal_record(
    http_client: HubspotHttpClient,
    deal_id: str,
    properties: dict[str, Any],
) -> HubSpotCreateDealResponse:
    """
    Update a deal record in HubSpot via the HTTP client.

    Args:
        http_client: HubSpot HTTP client
        deal_id: Deal ID to update
        properties: Dictionary of properties to update

    Returns:
        HubSpot API response with updated deal information.
    """
    response = await http_client.update_deal(deal_id=deal_id, properties=properties)
    return response


async def get_deal_record(
    http_client: HubspotHttpClient,
    deal_id: str,
) -> HubSpotCreateDealResponse:
    """
    Get a deal record by ID from HubSpot via the HTTP client.

    Args:
        http_client: HubSpot HTTP client
        deal_id: Deal ID to retrieve

    Returns:
        HubSpot API response with deal information.
    """
    response = await http_client.get_deal(deal_id=deal_id)
    return response


def normalize_deal_creation_inputs(
    deal_type: HubspotDealType | None | str | None,
    priority_level: HubspotDealPriority | None | str | None,
    expected_close_date: str | None,
    pipeline_id: str | None,
) -> tuple[str | None, str | None, str | None, str]:
    """Normalize enums/strings, convert close date, and validate pipeline id.

    Returns a tuple of (deal_type_value, priority_value, closedate_ms, pipeline_value).
    """
    # deal type
    if isinstance(deal_type, HubspotDealType):
        normalized_deal_type: str | None = deal_type.value
    elif isinstance(deal_type, str):
        normalized_deal_type = deal_type.lower()
    else:
        normalized_deal_type = None

    # priority
    if isinstance(priority_level, HubspotDealPriority):
        normalized_priority: str | None = priority_level.value
    elif isinstance(priority_level, str):
        normalized_priority = priority_level.lower()
    else:
        normalized_priority = None

    # close date
    closedate_ms = (
        shared_utils.to_epoch_millis(expected_close_date) if expected_close_date else None
    )

    # pipeline
    pipeline_value = shared_utils.normalize_and_validate_pipeline_id(pipeline_id)

    return normalized_deal_type, normalized_priority, closedate_ms, pipeline_value


async def resolve_current_pipeline_id(
    http_client: HubspotHttpClient,
    deal_id: str,
    current_pipeline_id: str | None,
) -> str:
    """Return the current pipeline id for a deal or the provided one.

    If current_pipeline_id is provided, it is returned. Otherwise the deal
    is fetched and its pipeline property is used, defaulting to "default".
    """
    if current_pipeline_id and current_pipeline_id.strip() != "":
        return current_pipeline_id
    deal = await get_deal_record(http_client=http_client, deal_id=deal_id)
    props = deal.get("properties", {})
    return cast(str, props.get("pipeline") or "default")


async def validate_stage_membership_or_retry(
    http_client: HubspotHttpClient,
    pipeline_id: str,
    deal_stage: str,
) -> None:
    """Ensure stage belongs to pipeline or raise a RetryableToolError.

    The error includes a list of valid stage ids and labels for guidance.
    """
    pipeline = await http_client.get_deal_pipeline(pipeline_id)
    stages = pipeline.get("stages", [])
    stage_ids = {str(s.get("id")) for s in stages}
    if str(deal_stage) in stage_ids:
        return
    options_lines = [f"{s.get('id')}: {s.get('label', '')}" for s in stages]
    options_str = "; ".join(options_lines)
    additional = (
        "Stage does not belong to the current pipeline. | "
        f"To proceed: call with current_pipeline_id='{pipeline_id}' and "
        "allow_pipeline_change=true to switch pipelines; or choose a valid stage from the "
        "current pipeline. | "
        f"Valid stages (id: label): {options_str}"
    )

    raise RetryableToolError(
        message="Stage does not belong to the current pipeline.",
        developer_message=(
            "dealstage is not in the current pipeline. Provide current_pipeline_id and "
            "allow_pipeline_change=true to proceed, or select a stage from the current pipeline."
        ),
        additional_prompt_content=additional,
    )


async def enrich_deal_with_pipeline_info(
    http_client: HubspotHttpClient,
    deal_data: HubSpotCreateDealResponse,
) -> tuple[DealPipelineRef | None, DealStageRef | None]:
    """
    Enrich deal data with pipeline and stage information.

    Args:
        http_client: HubSpot HTTP client
        deal_data: Deal data from HubSpot API

    Returns:
        Tuple of (pipeline_ref, stage_ref) with enriched information
    """
    properties = deal_data.get("properties", {})
    deal_stage = properties.get("dealstage")

    if not deal_stage:
        return None, None

    # First try to get pipeline from deal properties
    pipeline_id = properties.get("pipeline")

    # If no pipeline in deal, try default
    if not pipeline_id:
        pipeline_id = "default"

    try:
        # Get pipeline information to get stage names
        pipeline_data = await http_client.get_deal_pipeline(pipeline_id)

        # Create pipeline reference
        pipeline_ref = cast(
            DealPipelineRef,
            {
                "id": pipeline_id,
                "label": pipeline_data.get("label", ""),
            },
        )

        # Find stage information
        stages = pipeline_data.get("stages", [])
        stage_ref = None

        for stage in stages:
            if stage.get("id") == deal_stage:
                stage_ref = cast(
                    DealStageRef,
                    {
                        "id": deal_stage,
                        "label": stage.get("label", ""),
                    },
                )
                break

        # If not found in pipeline stages, create basic stage ref
        if stage_ref is None:
            stage_ref = cast(
                DealStageRef,
                {
                    "id": deal_stage,
                    "label": deal_stage,  # Use ID as label if not found
                },
            )

    except Exception:
        # If pipeline lookup fails, create basic references
        pipeline_ref = cast(
            DealPipelineRef,
            {
                "id": pipeline_id,
                "label": pipeline_id,
            },
        )

        stage_ref = cast(
            DealStageRef,
            {
                "id": deal_stage,
                "label": deal_stage,
            },
        )

    return pipeline_ref, stage_ref


async def associate_contact_with_deal(
    http_client: HubspotHttpClient,
    deal_id: str,
    contact_id: str,
) -> AssociationResult:
    """Associate a contact with a deal using the HubSpot API."""
    await http_client.associate_contact_with_deal(deal_id=deal_id, contact_id=contact_id)

    return cast(
        AssociationResult,
        {
            "success": True,
            "deal_id": deal_id,
            "contact_id": contact_id,
            "message": f"Successfully associated contact {contact_id} with deal {deal_id}",
        },
    )
