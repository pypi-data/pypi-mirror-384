from typing import Annotated

from arcade_tdk import ToolContext, tool
from arcade_tdk.auth import Hubspot

from arcade_hubspot.http_client.http_client import HubspotHttpClient
from arcade_hubspot.models.tool_models import DealPipelinesResponse, DealPipelineStagesResponse
from arcade_hubspot.tool_utils import pipeline_utils, shared_utils


@tool(
    requires_auth=Hubspot(
        scopes=[
            "oauth",
            "crm.objects.deals.read",  # /crm/v3/pipelines/deals
        ]
    )
)
async def get_deal_pipelines(
    context: ToolContext,
    search: Annotated[
        str | None,
        "Optional case-insensitive search string to filter pipelines by id or label",
    ] = None,
) -> Annotated[DealPipelinesResponse, "List up to 30 deal pipelines with their stages"]:
    """
    List HubSpot deal pipelines with their stages, optionally filtered by a search string.

    Recommended to be used before creating a new deal.

    For example updating the stage of a deal without changing the pipeline.
    """
    auth_token = shared_utils.get_auth_token_or_raise(context)

    http_client = HubspotHttpClient(auth_token=auth_token)

    token_info = await http_client.get_current_user_info()
    portal_id = str(token_info["hub_id"]) if token_info.get("hub_id") else None

    api_data = await pipeline_utils.fetch_deal_pipelines(http_client)
    response = pipeline_utils.create_pipelines_response(api_data, search, portal_id)
    return response


@tool(
    requires_auth=Hubspot(
        scopes=[
            "oauth",
            "crm.objects.deals.read",  # /crm/v3/pipelines/deals/{pipelineId}
        ]
    )
)
async def get_deal_pipeline_stages(
    context: ToolContext,
    pipeline_id: Annotated[str, "The pipeline id (e.g., 'default' or a pipeline GUID)"],
) -> Annotated[DealPipelineStagesResponse, "List stages for a specific deal pipeline"]:
    """
    List stages for a specific HubSpot deal pipeline.

    Useful to get the stage IDs for a specific pipeline.
    """
    auth_token = shared_utils.get_auth_token_or_raise(context)

    http_client = HubspotHttpClient(auth_token=auth_token)

    # Get portal_id for GUI URLs
    token_info = await http_client.get_current_user_info()
    portal_id = str(token_info["hub_id"]) if token_info.get("hub_id") else None

    normalized_pid = shared_utils.normalize_and_validate_pipeline_id(pipeline_id)
    response = await pipeline_utils.fetch_pipeline_stages(http_client, normalized_pid, portal_id)
    return response
