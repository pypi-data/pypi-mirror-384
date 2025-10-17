from typing import Any, cast

from arcade_tdk.errors import RetryableToolError, ToolExecutionError

from arcade_hubspot.enums import HubspotDefaultDealStage
from arcade_hubspot.exceptions import NotFoundError
from arcade_hubspot.http_client import HubspotHttpClient
from arcade_hubspot.models.crm_api_models import (
    HubSpotPipeline,
    HubSpotPipelinesResponse,
    HubSpotPipelineStage,
)
from arcade_hubspot.models.tool_models import (
    DealPipelineData,
    DealPipelineRef,
    DealPipelinesResponse,
    DealPipelineStagesResponse,
    DealStageRef,
    PipelineStageData,
)
from arcade_hubspot.utils.gui_url_builder import build_deal_pipeline_gui_url


async def fetch_deal_pipelines(http_client: HubspotHttpClient) -> HubSpotPipelinesResponse:
    """Fetch deal pipelines from HubSpot via HTTP client."""
    return await http_client.list_deal_pipelines()


def _map_stage(stage: HubSpotPipelineStage) -> PipelineStageData:
    return cast(
        PipelineStageData,
        {
            "id": stage.get("id", ""),
            "label": stage.get("label", ""),
            "display_order": stage.get("displayOrder"),
            "archived": stage.get("archived"),
        },
    )


def _map_pipeline(p: HubSpotPipeline, portal_id: str | None = None) -> DealPipelineData:
    stages: list[HubSpotPipelineStage] = p.get("stages") or []

    pipeline_data = {
        "id": p.get("id", ""),
        "label": p.get("label", ""),
        "display_order": p.get("displayOrder"),
        "archived": p.get("archived"),
        "stages": [_map_stage(s) for s in stages],
    }

    if portal_id and p.get("id"):
        pipeline_data["pipeline_gui_url"] = build_deal_pipeline_gui_url(portal_id, str(p.get("id")))

    return cast(DealPipelineData, pipeline_data)


def create_pipelines_response(
    api_data: HubSpotPipelinesResponse,
    search: str | None = None,
    portal_id: str | None = None,
) -> DealPipelinesResponse:
    """Map and filter pipelines, returning at most 30 items."""
    results: list[HubSpotPipeline] = api_data["results"]
    mapped = [_map_pipeline(p, portal_id) for p in results]

    if search:
        needle = search.lower()
        mapped = [
            p
            for p in mapped
            if needle in (p.get("label") or "").lower() or needle in (p.get("id") or "").lower()
        ]

    return {"pipelines": mapped[:30]}


async def fetch_pipeline_stages(
    http_client: HubspotHttpClient, pipeline_id: str, portal_id: str | None = None
) -> DealPipelineStagesResponse:
    """Fetch a single pipeline and map its stages."""
    p = await http_client.get_deal_pipeline(pipeline_id)
    mapped = _map_pipeline(p, portal_id)

    response_data: dict[str, Any] = {
        "pipeline_id": mapped["id"],
        "label": mapped["label"],
        "stages": mapped["stages"],
    }

    if "pipeline_gui_url" in mapped:
        response_data["pipeline_gui_url"] = mapped["pipeline_gui_url"]

    return cast(DealPipelineStagesResponse, response_data)


async def validate_pipeline_and_select_stage(
    http_client: HubspotHttpClient,
    pipeline_id: str,
    deal_stage: str | None,
) -> tuple[str, DealPipelineRef, DealStageRef | None]:
    """Validate pipeline existence and stage; return a valid stage id.

    Raises ToolExecutionError if pipeline is not found.
    Raises RetryableToolError if stage is invalid for the pipeline.
    Valid options are provided in additional_prompt_content.
    """
    pid = pipeline_id or "default"
    try:
        pipeline = await http_client.get_deal_pipeline(pid)
    except NotFoundError:
        raise ToolExecutionError(
            message="Invalid pipeline id",
            developer_message=(
                "Pipeline not found. Provide a valid pipeline id (e.g., 'default' or a "
                "pipeline GUID)."
            ),
        )

    valid_stage_ids = [s.get("id", "") for s in (pipeline.get("stages") or [])]
    pipeline_ref: DealPipelineRef = cast(
        DealPipelineRef,
        {"id": pid, "label": pipeline.get("label")},
    )
    # Prepare stage lookup from pipeline stages
    stage_list: list[HubSpotPipelineStage] = pipeline.get("stages") or []
    stage_id_to_label = {str(s.get("id", "")): s.get("label") for s in stage_list}

    is_default = pid == "default"
    default_valid_stages = {s.value for s in HubspotDefaultDealStage}
    if deal_stage:
        if is_default:
            if deal_stage not in valid_stage_ids:
                additional = "\n".join([
                    "The stage id must be one of:",
                    ", ".join(sorted([sid for sid in valid_stage_ids if sid])),
                ])
                raise RetryableToolError(
                    message="Invalid deal stage for the selected pipeline",
                    developer_message=(
                        f"dealstage '{deal_stage}' is invalid for pipeline '{pid}'. "
                        "Valid stages listed in additional_prompt_content."
                    ),
                    additional_prompt_content=additional,
                )
        else:
            # Non-default: must be an integer id, or accept a default stage string
            if not (str(deal_stage).isdigit() or str(deal_stage) in default_valid_stages):
                raise ToolExecutionError(
                    message=("deal_stage must be a numeric id for non-default pipeline"),
                    developer_message=(
                        "Provide an integer stage id when using a non-default pipeline"
                    ),
                )

    # Auto-pick first stage if not provided (for any pipeline with stages)
    if not deal_stage and valid_stage_ids:
        first_id = valid_stage_ids[0]
        picked_stage_ref = cast(
            DealStageRef,
            {"id": first_id, "label": stage_id_to_label.get(first_id)},
        )
        return first_id, pipeline_ref, picked_stage_ref

    if deal_stage:
        deal_stage_str = str(deal_stage)
        stage_ref: DealStageRef | None = None
        label_val = stage_id_to_label.get(deal_stage_str)
        if label_val is None and deal_stage_str in default_valid_stages:
            label_val = deal_stage_str
        if label_val is not None:
            stage_ref = cast(
                DealStageRef,
                {
                    "id": deal_stage_str,
                    "label": label_val,
                },
            )
        return deal_stage_str, pipeline_ref, stage_ref

    additional = "\n".join([
        "The stage id must be one of:",
        ", ".join(sorted([sid for sid in valid_stage_ids if sid])),
    ])
    raise RetryableToolError(
        message="Invalid deal stage for the selected pipeline",
        developer_message=(
            f"dealstage '{deal_stage}' is invalid for pipeline '{pid}'. "
            "Valid stages listed in additional_prompt_content."
        ),
        additional_prompt_content=additional,
    )
