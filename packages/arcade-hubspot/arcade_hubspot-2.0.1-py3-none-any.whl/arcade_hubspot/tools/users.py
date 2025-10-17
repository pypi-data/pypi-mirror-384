"""HubSpot user management tools."""

from typing import Annotated, Any

from arcade_tdk import ToolContext, tool
from arcade_tdk.auth import Hubspot

from arcade_hubspot.http_client.http_client import HubspotHttpClient
from arcade_hubspot.tool_utils import shared_utils
from arcade_hubspot.utils.data_utils import remove_none_values


@tool(
    requires_auth=Hubspot(
        scopes=[
            "oauth",  # Required for authentication
            "crm.objects.owners.read",  # Required for /crm/v3/owners endpoint
        ]
    )
)
async def get_all_users(
    context: ToolContext,
) -> Annotated[
    dict[str, Any],
    "Get all users/owners in the HubSpot portal with their names, emails, IDs, and status.",
]:
    """
    Get all users/owners in the HubSpot portal.

    This tool retrieves a list of all users (owners) in your HubSpot portal,
    Useful for user management and assignment operations.

    Use this tool when needing information about ALL users in the HubSpot portal.
    """
    auth_token = shared_utils.get_auth_token_or_raise(context)

    http_client = HubspotHttpClient(auth_token=auth_token)
    owners_response = await http_client.get_all_owners()

    owners = owners_response.get("results", [])
    cleaned_owners = []

    for owner in owners:
        clean_owner = remove_none_values({
            "owner_id": owner.get("id"),
            "email": owner.get("email"),
            "first_name": owner.get("firstName"),
            "last_name": owner.get("lastName"),
            "user_id": owner.get("userId"),
            "created_at": owner.get("createdAt"),
            "updated_at": owner.get("updatedAt"),
            "archived": owner.get("archived", False),
        })
        if clean_owner:
            cleaned_owners.append(clean_owner)

    return {
        "users": cleaned_owners,
        "total_count": len(cleaned_owners),
    }


@tool(
    requires_auth=Hubspot(
        scopes=[
            "oauth",  # Required for authentication
            "crm.objects.owners.read",  # Required for /crm/v3/owners endpoint
        ]
    )
)
async def get_user_by_id(
    context: ToolContext,
    owner_id: Annotated[int, "The HubSpot owner/user ID to retrieve"],
) -> Annotated[
    dict[str, Any],
    "Get detailed information about a specific user/owner by their ID.",
]:
    """
    Get detailed information about a specific user/owner by their ID.

    This tool retrieves comprehensive information about a specific user
    in your HubSpot portal using their owner ID.
    """
    auth_token = shared_utils.get_auth_token_or_raise(context)

    http_client = HubspotHttpClient(auth_token=auth_token)
    owner_response = await http_client.get_owner_by_id(str(owner_id))

    clean_owner_data = remove_none_values({
        "owner_id": owner_response.get("id"),
        "email": owner_response.get("email"),
        "first_name": owner_response.get("firstName"),
        "last_name": owner_response.get("lastName"),
        "user_id": owner_response.get("userId"),
        "created_at": owner_response.get("createdAt"),
        "updated_at": owner_response.get("updatedAt"),
        "archived": owner_response.get("archived", False),
    })

    return clean_owner_data if isinstance(clean_owner_data, dict) else {"result": clean_owner_data}
