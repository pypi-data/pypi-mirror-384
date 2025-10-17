from typing import Annotated, Any

from arcade_tdk import ToolContext, tool
from arcade_tdk.auth import Hubspot

from arcade_hubspot.http_client.http_client import HubspotHttpClient
from arcade_hubspot.models.tool_models import DetailedUserData
from arcade_hubspot.tool_utils import shared_utils
from arcade_hubspot.utils.data_utils import remove_none_values
from arcade_hubspot.utils.gui_url_builder import build_user_profile_gui_url


@tool(
    requires_auth=Hubspot(
        scopes=[
            "oauth",  # Required for /oauth/v1/access-tokens endpoint
            "crm.objects.owners.read",  # Required for /crm/v3/users endpoint
        ]
    )
)
async def who_am_i(
    context: ToolContext,
) -> Annotated[
    dict[str, Any],
    "Get current user information.",
]:
    """
    Get current user information from HubSpot.

    This is typically the first tool called to understand the current user context.

    Use this tool when needing information about the current user basic HubSpot information.
    and the associated HubSpot portal.
    """
    auth_token = shared_utils.get_auth_token_or_raise(context)

    http_client = HubspotHttpClient(auth_token=auth_token)

    token_info = await http_client.get_current_user_info()

    user_info = await http_client.get_user_by_id(str(token_info["user_id"]))

    portal_id = str(token_info["hub_id"]) if token_info.get("hub_id") else None
    profile_gui_url = build_user_profile_gui_url(portal_id) if portal_id else None

    user_response = DetailedUserData(
        user_id=token_info["user_id"],
        email=token_info["user"],
        first_name=user_info.get("firstName"),
        last_name=user_info.get("lastName"),
        owner_id=user_info.get("id"),
        hub_id=token_info.get("hub_id"),
        hub_domain=token_info["hub_domain"],
        app_id=str(token_info["app_id"]) if token_info.get("app_id") is not None else None,
        expires_in=None,
        user_id_including_portal=token_info.get("user_id_including_portal"),
        my_profile_gui_url=profile_gui_url,
    )

    result = remove_none_values(dict(user_response))
    return result if isinstance(result, dict) else {"result": result}


@tool()
async def toolkit_enviroment_guidance(
    context: ToolContext,
) -> Annotated[
    dict[str, Any],
    "List of guidance.",
]:
    """
    Get guidance and considerations for using the HubSpot toolkit effectively.

    This tool provides important context and best practices for working with HubSpot tools.
    Based on all available HubSpot toolkit tools, some suggestions may apply to tools that are not
    available in the current agent's configuration.
    """
    return {
        "considerations": [
            (
                "The following considerations are based on all available HubSpot toolkit tools. "
                "Be aware that the current agent may not have all tools available."
            ),
            (
                "For getting current user profile information, including HubSpot environment "
                "data like ID, use the 'who am I' tool."
            ),
            (
                "Deals can have either the default HubSpot pipeline or a custom one with custom "
                "stages. When setting a deal stage, either when creating a new one or updating "
                "the deal's stage, it is important to use a tool to get pipeline information "
                "if available."
            ),
            (
                "Search by keywords tools search by keywords in many properties. Those properties "
                "depend on the object type."
            ),
            (
                "Tools that require some kind of ID as parameters indicate that for using those "
                "fields, it is necessary to already have the mapping between the object and its "
                "ID in context."
            ),
            (
                "Listing tools are useful when no extra context is given for the search or the "
                "user wants to verify the latest updated items."
            ),
            (
                "When creating an engagement activity object, it should have the current user as "
                "owner if not informed otherwise."
            ),
            (
                "When creating an engagement activity object, it must be associated with at least "
                "one of the following: contact, deal, or company. Otherwise, finding the activity "
                "in HubSpot's GUI won't be trivial."
            ),
            (
                "In HubSpot there are custom and default association types. Currently, this "
                "toolkit only supports default associations."
            ),
            (
                "Currently, for deals and engagement, no association data is returned in tools' "
                "responses."
            ),
        ]
    }
