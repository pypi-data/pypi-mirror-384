"""Main HubSpot HTTP client with all API methods."""

import asyncio
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Optional, cast

import httpx

from arcade_hubspot.constants import (
    HUBSPOT_BASE_URL,
    HUBSPOT_CRM_BASE_URL,
    HUBSPOT_MAX_CONCURRENT_REQUESTS,
)
from arcade_hubspot.enums import HubspotObject

if TYPE_CHECKING:
    from arcade_hubspot.enums import HubspotSortOrder
from arcade_hubspot.exceptions import HubspotToolExecutionError
from arcade_hubspot.http_client.client_helpers import (
    build_call_properties_and_associations,
    build_communication_properties_and_associations,
    build_email_properties_and_associations,
    build_error_context,
    build_meeting_properties_and_associations,
    build_note_properties_and_associations,
    raise_for_status,
)
from arcade_hubspot.http_client.list_helpers import build_search_request_data
from arcade_hubspot.models.crm_api_models import (
    HubSpotCreateCompanyResponse,
    HubSpotCreateContactResponse,
    HubSpotCreateDealResponse,
    HubSpotPipeline,
    HubSpotPipelinesResponse,
)
from arcade_hubspot.models.system_api_models import OAuthTokenResponse
from arcade_hubspot.properties import get_object_properties
from arcade_hubspot.utils.data_utils import (
    clean_api_response_to_tool_data,
    prepare_search_response,
    remove_none_values,
)


@dataclass
class HubspotHttpClient:
    """Main HubSpot HTTP client with all API methods."""

    auth_token: str
    base_url: str = HUBSPOT_BASE_URL
    max_concurrent_requests: int = HUBSPOT_MAX_CONCURRENT_REQUESTS
    _semaphore: asyncio.Semaphore | None = None

    def __post_init__(self) -> None:
        """Initialize the HTTP client."""
        self._semaphore = self._semaphore or asyncio.Semaphore(self.max_concurrent_requests)

    async def get(
        self,
        endpoint: str,
        params: dict | None = None,
        headers: dict | None = None,
        api_version: str = "v3",
        base_url_override: str | None = None,
    ) -> dict[str, Any]:
        """Execute GET request with standardized error handling."""
        headers = headers or {}
        headers["Authorization"] = f"Bearer {self.auth_token}"

        base_url = base_url_override or self.base_url
        url = f"{base_url}/{api_version}/{endpoint}"

        kwargs = {"url": url, "headers": headers}
        if isinstance(params, dict):
            kwargs["params"] = params

        async with self._semaphore, httpx.AsyncClient() as client:  # type: ignore[union-attr]
            response = await client.get(**kwargs)  # type: ignore[arg-type]
            raise_for_status(
                response,
                request_context=build_error_context(
                    method="GET",
                    url=url,
                    endpoint=endpoint,
                    api_version=api_version,
                    base_url=base_url,
                ),
            )

        return cast(dict[str, Any], response.json())

    async def post(
        self,
        endpoint: str,
        data: dict | None = None,
        json_data: dict | None = None,
        headers: dict | None = None,
        api_version: str = "v3",
        base_url_override: str | None = None,
    ) -> dict[str, Any]:
        """Execute POST request with standardized error handling."""
        headers = headers or {}
        headers["Authorization"] = f"Bearer {self.auth_token}"
        headers["Content-Type"] = "application/json"

        base_url = base_url_override or self.base_url
        url = f"{base_url}/{api_version}/{endpoint}"

        kwargs = {"url": url, "headers": headers}

        if data and json_data:
            raise ValueError("Cannot provide both data and json_data")

        if data:
            kwargs["data"] = data
        elif json_data:
            kwargs["json"] = json_data

        async with self._semaphore, httpx.AsyncClient() as client:  # type: ignore[union-attr]
            response = await client.post(**kwargs)  # type: ignore[arg-type]
            raise_for_status(
                response,
                request_context=build_error_context(
                    method="POST",
                    url=url,
                    endpoint=endpoint,
                    api_version=api_version,
                    base_url=base_url,
                ),
            )

        return cast(dict[str, Any], response.json())

    async def patch(
        self,
        endpoint: str,
        json_data: dict | None = None,
        headers: dict | None = None,
        api_version: str = "v3",
        base_url_override: str | None = None,
    ) -> dict[str, Any]:
        """Execute PATCH request with standardized error handling."""
        headers = headers or {}
        headers["Authorization"] = f"Bearer {self.auth_token}"
        headers["Content-Type"] = "application/json"

        base_url = base_url_override or self.base_url
        url = f"{base_url}/{api_version}/{endpoint}"

        kwargs = {"url": url, "headers": headers}

        if json_data:
            kwargs["json"] = json_data

        async with self._semaphore, httpx.AsyncClient() as client:  # type: ignore[union-attr]
            response = await client.patch(**kwargs)  # type: ignore[arg-type]
            raise_for_status(
                response,
                request_context=build_error_context(
                    method="PATCH",
                    url=url,
                    endpoint=endpoint,
                    api_version=api_version,
                    base_url=base_url,
                ),
            )

        return cast(dict[str, Any], response.json())

    async def put(
        self,
        endpoint: str,
        data: dict | None = None,
        json_data: dict | list | None = None,
        headers: dict | None = None,
        api_version: str = "v3",
        base_url_override: str | None = None,
    ) -> dict[str, Any]:
        """Execute PUT request with standardized error handling."""
        headers = headers or {}
        headers["Authorization"] = f"Bearer {self.auth_token}"
        headers["Content-Type"] = "application/json"

        base_url = base_url_override or self.base_url
        url = f"{base_url}/{api_version}/{endpoint}"

        kwargs = {"url": url, "headers": headers}
        if data and json_data:
            raise ValueError("Cannot provide both data and json_data")
        if data:
            kwargs["data"] = data
        elif json_data:
            kwargs["json"] = json_data

        async with self._semaphore, httpx.AsyncClient() as client:  # type: ignore[union-attr]
            response = await client.put(**kwargs)  # type: ignore[arg-type]
            raise_for_status(
                response,
                request_context=build_error_context(
                    method="PUT",
                    url=url,
                    endpoint=endpoint,
                    api_version=api_version,
                    base_url=base_url,
                ),
            )

        return cast(dict[str, Any], response.json())

    async def get_current_user_info(self) -> OAuthTokenResponse:
        """Get current user information from HubSpot OAuth API."""
        response = await self.get(
            f"access-tokens/{self.auth_token}",
            api_version="v1",
            base_url_override="https://api.hubapi.com/oauth",
        )

        return cast(
            OAuthTokenResponse,
            {
                "user_id": response.get("user_id") or response.get("id") or response.get("userId"),
                "user": response.get("user") or response.get("email") or response.get("userEmail"),
                "hub_id": response.get("hub_id")
                or response.get("hubId")
                or response.get("portalId"),
                "hub_domain": response.get("hub_domain")
                or response.get("hubDomain")
                or response.get("domain"),
                "scopes": response.get("scopes", []),
                "token": response.get("token") or self.auth_token,
                "app_id": response.get("app_id")
                or response.get("appId")
                or response.get("applicationId"),
                "expires_in": response.get("expires_in") or response.get("expiresIn"),
                "user_id_including_portal": response.get("user_id_including_portal")
                or response.get("userIdIncludingPortal"),
            },
        )

    async def get_all_owners(self) -> dict[str, Any]:
        """Get all owners/users in the HubSpot portal."""
        return await self.get(
            "owners",
            params={"archived": "false"},
            api_version="crm/v3",
        )

    async def get_owner_by_id(self, owner_id: str) -> dict[str, Any]:
        """Get a specific owner/user by their ID."""
        return await self.get(f"owners/{owner_id}", api_version="crm/v3")

    async def get_user_by_id(self, user_id: str) -> dict[str, Any]:
        """Get a specific user by their ID using the CRM Owners API."""
        return await self.get(
            f"owners/{user_id}",
            params={"idProperty": "userId", "archived": "false"},
            api_version="crm/v3",
        )

    async def get_engagement(self, engagement_id: str) -> dict[str, Any]:
        """Get engagement details by id (legacy v1)."""
        return await self.get(
            f"engagements/v1/engagements/{engagement_id}",
            base_url_override=HUBSPOT_BASE_URL,
        )

    async def get_object_by_id(
        self,
        object_type: HubspotObject,
        object_id: str,
        properties: list[str] | None = None,
    ) -> dict:
        """Get a single object by its ID."""
        endpoint = f"objects/{object_type.plural}/{object_id}"
        params = {}
        if properties:
            params["properties"] = properties

        response = await self.get(
            endpoint,
            params=params,
            base_url_override=HUBSPOT_CRM_BASE_URL,
        )
        return clean_api_response_to_tool_data(response, object_type)

    async def batch_get_objects(
        self,
        object_type: HubspotObject,
        object_ids: list[str],
        properties: list[str] | None = None,
    ) -> list[dict]:
        """Get multiple objects by their IDs in batch."""
        endpoint = f"objects/{object_type.plural}/batch/read"
        data: dict[str, Any] = {"inputs": [{"id": object_id} for object_id in object_ids]}
        if properties:
            data["properties"] = properties

        response = await self.post(
            endpoint,
            json_data=data,
            base_url_override=HUBSPOT_CRM_BASE_URL,
        )
        return [
            clean_api_response_to_tool_data(object_data, object_type)
            for object_data in response["results"]
        ]

    async def search_by_keywords(
        self,
        object_type: HubspotObject,
        keywords: str,
        limit: int = 10,
        next_page_token: str | None = None,
        associations: list[HubspotObject] | None = None,
        portal_id: str | None = None,
    ) -> dict:
        """Search for objects by keywords."""
        if not keywords:
            raise HubspotToolExecutionError("`keywords` must be a non-empty string")

        associations = associations or []

        endpoint = f"objects/{object_type.plural}/search"
        request_data = {
            "query": keywords,
            "limit": limit,
            "sorts": [{"propertyName": "hs_lastmodifieddate", "direction": "DESCENDING"}],
            "properties": get_object_properties(object_type),
        }

        if next_page_token:
            request_data["after"] = next_page_token

        data = prepare_search_response(
            api_data=await self.post(
                endpoint,
                json_data=request_data,
                base_url_override=HUBSPOT_CRM_BASE_URL,
            ),
            object_type=object_type,
            portal_id=portal_id,
        )

        association_tasks = []
        task_metadata = []

        for object_ in data[object_type.plural]:
            for association in associations:
                task = self.get_associated_objects(
                    parent_object=object_type,
                    parent_id=object_["id"],
                    associated_object=association,
                    limit=10,
                )
                association_tasks.append(task)
                task_metadata.append((object_, association))

        if association_tasks:
            results = await asyncio.gather(*association_tasks)

            for (object_, association), result in zip(task_metadata, results):
                if result:
                    object_[association.plural] = result

        return data

    async def list_objects(
        self,
        object_type: HubspotObject,
        *,
        limit: int = 10,
        after: str | None = None,
        properties: list[str] | None = None,
    ) -> dict[str, Any]:
        """List CRM objects of a given type with optional pagination."""
        endpoint = f"objects/{object_type.plural}"
        params: dict[str, Any] = {"limit": limit}
        if after:
            params["after"] = after
        if properties:
            params["properties"] = properties

        response = await self.get(
            endpoint,
            params=params,
            base_url_override=HUBSPOT_CRM_BASE_URL,
        )
        return response

    async def list_objects_with_filters(
        self,
        object_type: HubspotObject,
        *,
        limit: int = 10,
        contact_id: str | None = None,
        company_id: str | None = None,
        deal_id: str | None = None,
        sort_order: Optional["HubspotSortOrder"] = None,
        next_page_token: str | None = None,
        portal_id: str | None = None,
    ) -> dict[str, Any]:
        """List CRM objects with filtering and sorting support using search API."""
        endpoint = f"objects/{object_type.plural}/search"

        request_data = build_search_request_data(
            limit=limit,
            object_type=object_type,
            properties=get_object_properties(object_type),
            contact_id=contact_id,
            company_id=company_id,
            deal_id=deal_id,
            sort_order=sort_order,
            next_page_token=next_page_token,
        )

        api_response = await self.post(
            endpoint,
            json_data=request_data,
            base_url_override=HUBSPOT_CRM_BASE_URL,
        )

        return prepare_search_response(
            api_data=api_response,
            object_type=object_type,
            portal_id=portal_id,
        )

    async def create_object(
        self,
        object_type: HubspotObject,
        *,
        properties: dict[str, Any],
        associations: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Create a CRM object of a given type with provided properties."""
        endpoint = f"objects/{object_type.plural}"
        payload: dict[str, Any] = {"properties": remove_none_values(properties)}
        if associations:
            payload["associations"] = associations
        response = await self.post(
            endpoint,
            json_data=payload,
            base_url_override=HUBSPOT_CRM_BASE_URL,
        )
        return response

    async def create_contact(
        self,
        company_id: str,
        first_name: str,
        last_name: str | None = None,
        email: str | None = None,
        phone: str | None = None,
        mobile_phone: str | None = None,
        job_title: str | None = None,
    ) -> HubSpotCreateContactResponse:
        """Create a contact associated with a company."""
        request_data = {
            "associations": [
                {
                    "types": [
                        {
                            "associationCategory": "HUBSPOT_DEFINED",
                            "associationTypeId": "1",
                        }
                    ],
                    "to": {"id": company_id},
                },
            ],
            "properties": remove_none_values({
                "firstname": first_name,
                "lastname": last_name,
                "email": email,
                "phone": phone,
                "mobilephone": mobile_phone,
                "jobtitle": job_title,
            }),
        }
        endpoint = "objects/contacts"
        response = await self.post(
            endpoint,
            json_data=request_data,
            base_url_override=HUBSPOT_CRM_BASE_URL,
        )
        return cast(HubSpotCreateContactResponse, response)

    async def create_company(
        self,
        name: str,
        domain: str | None = None,
        industry: str | None = None,
        city: str | None = None,
        state: str | None = None,
        country: str | None = None,
        phone: str | None = None,
        website: str | None = None,
    ) -> HubSpotCreateCompanyResponse:
        """Create a company."""
        properties = remove_none_values({
            "name": name,
            "domain": domain,
            "industry": industry,
            "city": city,
            "state": state,
            "country": country,
            "phone": phone,
            "website": website,
        })
        endpoint = "objects/companies"
        response = await self.post(
            endpoint,
            json_data={"properties": properties},
            base_url_override=HUBSPOT_CRM_BASE_URL,
        )
        return cast(HubSpotCreateCompanyResponse, response)

    async def create_deal(
        self,
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
        """Create a deal."""
        properties = remove_none_values({
            "dealname": deal_name,
            "amount": str(amount) if amount is not None else None,
            "dealstage": deal_stage,
            "dealtype": deal_type,
            "closedate": close_date,
            "pipeline": pipeline,
            "hubspot_owner_id": deal_owner,
            "hs_priority": priority,
            "description": deal_description,
        })
        endpoint = "objects/deals"
        response = await self.post(
            endpoint,
            json_data={"properties": properties},
            base_url_override=HUBSPOT_CRM_BASE_URL,
        )
        return cast(HubSpotCreateDealResponse, response)

    async def update_deal(
        self,
        deal_id: str,
        properties: dict[str, Any],
    ) -> HubSpotCreateDealResponse:
        """Update a deal with the given properties."""
        endpoint = f"objects/deals/{deal_id}"
        response = await self.patch(
            endpoint,
            json_data={"properties": properties},
            base_url_override=HUBSPOT_CRM_BASE_URL,
        )
        return cast(HubSpotCreateDealResponse, response)

    async def get_deal(self, deal_id: str) -> HubSpotCreateDealResponse:
        """Get a deal by ID."""
        endpoint = f"objects/deals/{deal_id}"
        response = await self.get(
            endpoint,
            base_url_override=HUBSPOT_CRM_BASE_URL,
        )
        return cast(HubSpotCreateDealResponse, response)

    async def list_deal_pipelines(self) -> HubSpotPipelinesResponse:
        """List all deal pipelines."""
        endpoint = "pipelines/deals"
        response = await self.get(
            endpoint,
            base_url_override=HUBSPOT_CRM_BASE_URL,
        )
        return cast(HubSpotPipelinesResponse, response)

    async def get_deal_pipeline(self, pipeline_id: str) -> HubSpotPipeline:
        """Get a single deal pipeline by id (e.g., 'default' or a GUID)."""
        endpoint = f"pipelines/deals/{pipeline_id}"
        response = await self.get(
            endpoint,
            base_url_override=HUBSPOT_CRM_BASE_URL,
        )
        return cast(HubSpotPipeline, response)

    # Activity creation methods (v3)
    async def create_note(
        self,
        *,
        body: str,
        owner_id: str,
        timestamp: int | None = None,
        contact_ids: list[str] | None = None,
        company_ids: list[str] | None = None,
        deal_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        properties, associations = build_note_properties_and_associations(
            body=body,
            owner_id=owner_id,
            timestamp=timestamp,
            contact_ids=contact_ids,
            company_ids=company_ids,
            deal_ids=deal_ids,
        )

        return await self.create_object(
            object_type=HubspotObject.NOTE,
            properties=properties,
            associations=associations if associations else None,
        )

    async def create_call(
        self,
        *,
        title: str,
        owner_id: str,
        direction: str | None = None,
        summary: str | None = None,
        timestamp: int | None = None,
        duration: int | None = None,
        to_number: str | None = None,
        from_number: str | None = None,
        contact_ids: list[str] | None = None,
        company_ids: list[str] | None = None,
        deal_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        properties, associations = build_call_properties_and_associations(
            title=title,
            owner_id=owner_id,
            direction=direction,
            summary=summary,
            timestamp=timestamp,
            duration=duration,
            to_number=to_number,
            from_number=from_number,
            contact_ids=contact_ids,
            company_ids=company_ids,
            deal_ids=deal_ids,
        )

        return await self.create_object(
            object_type=HubspotObject.CALL,
            properties=properties,
            associations=associations,
        )

    async def create_email(
        self,
        *,
        subject: str,
        owner_id: str,
        direction: str = "EMAIL",
        status: str | None = None,
        timestamp: int | None = None,
        from_email: str | None = None,
        from_first_name: str | None = None,
        from_last_name: str | None = None,
        to_emails: list[dict[str, str]] | None = None,
        cc_emails: list[dict[str, str]] | None = None,
        bcc_emails: list[dict[str, str]] | None = None,
        body_text: str | None = None,
        body_html: str | None = None,
        contact_ids: list[str] | None = None,
        company_ids: list[str] | None = None,
        deal_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        properties, associations = build_email_properties_and_associations(
            subject=subject,
            owner_id=owner_id,
            direction=direction,
            status=status,
            timestamp=timestamp,
            from_email=from_email,
            from_first_name=from_first_name,
            from_last_name=from_last_name,
            to_emails=to_emails,
            cc_emails=cc_emails,
            bcc_emails=bcc_emails,
            body_text=body_text,
            body_html=body_html,
            contact_ids=contact_ids,
            company_ids=company_ids,
            deal_ids=deal_ids,
        )

        return await self.create_object(
            object_type=HubspotObject.EMAIL,
            properties=properties,
            associations=associations,
        )

    async def create_meeting(
        self,
        *,
        title: str,
        start_date: str,
        start_time: str,
        owner_id: str,
        duration: str | None = None,
        location: str | None = None,
        outcome: str | None = None,
        contact_ids: list[str] | None = None,
        company_ids: list[str] | None = None,
        deal_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        properties, associations = build_meeting_properties_and_associations(
            title=title,
            start_date=start_date,
            start_time=start_time,
            owner_id=owner_id,
            duration=duration,
            location=location,
            outcome=outcome,
            contact_ids=contact_ids,
            company_ids=company_ids,
            deal_ids=deal_ids,
        )

        return await self.create_object(
            object_type=HubspotObject.MEETING,
            properties=properties,
            associations=associations,
        )

    async def create_communication(
        self,
        *,
        channel: str,
        owner_id: str,
        logged_from: str | None = None,
        body_text: str | None = None,
        timestamp: int | None = None,
        contact_ids: list[str] | None = None,
        company_ids: list[str] | None = None,
        deal_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        properties, associations = build_communication_properties_and_associations(
            channel=channel,
            owner_id=owner_id,
            logged_from=logged_from,
            body_text=body_text,
            timestamp=timestamp,
            contact_ids=contact_ids,
            company_ids=company_ids,
            deal_ids=deal_ids,
        )
        return await self.create_object(
            object_type=HubspotObject.COMMUNICATION,
            properties=properties,
            associations=associations,
        )

    async def get_associated_objects(
        self,
        parent_object: HubspotObject,
        parent_id: str,
        associated_object: HubspotObject,
        limit: int = 10,
        after: str | None = None,
        properties: list[str] | None = None,
    ) -> list[dict]:
        """Get associated objects for a parent object."""
        endpoint = (
            f"objects/{parent_object.value}/{parent_id}/associations/{associated_object.value}"
        )
        params = {"limit": limit}
        if after:
            params["after"] = after  # type: ignore[assignment]

        response = await self.get(
            endpoint,
            params=params,
            api_version="v4",
            base_url_override=HUBSPOT_CRM_BASE_URL,
        )

        if not response["results"]:
            return []

        return await self.batch_get_objects(
            object_type=associated_object,
            object_ids=[object_data["toObjectId"] for object_data in response["results"]],
            properties=properties or get_object_properties(associated_object),
        )

    async def create_association(
        self,
        from_object: HubspotObject,
        from_id: str,
        to_object: HubspotObject,
        to_id: str,
        association_type_id: str,
    ) -> dict[str, Any]:
        """Create a default association between two objects using v4 API.

        Uses PUT to create default associations.

        Args:
            from_object: Source object type (e.g., HubspotObject.CALL)
            from_id: Source object ID
            to_object: Target object type (e.g., HubspotObject.DEAL)
            to_id: Target object ID
            association_type_id: The association type ID (as string) - ignored for default

        Returns:
            Response from HubSpot API
        """
        endpoint = (
            f"objects/{from_object.plural}/{from_id}/associations/"
            f"default/{to_object.plural}/{to_id}"
        )

        response = await self.put(
            endpoint,
            api_version="v4",
            base_url_override=HUBSPOT_CRM_BASE_URL,
        )
        return response

    async def associate_contact_with_deal(
        self,
        deal_id: str,
        contact_id: str,
    ) -> dict[str, Any]:
        """Associate a contact with a deal using default associations.

        Uses PUT to create default associations.

        Args:
            deal_id: The deal ID
            contact_id: The contact ID
        """
        endpoint = f"objects/deals/{deal_id}/associations/default/contacts/{contact_id}"

        return await self.put(
            endpoint,
            api_version="v4",
            base_url_override=HUBSPOT_CRM_BASE_URL,
        )
