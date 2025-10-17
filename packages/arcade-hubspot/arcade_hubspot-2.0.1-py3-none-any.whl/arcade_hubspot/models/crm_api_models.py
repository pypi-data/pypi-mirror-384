"""API models for HubSpot CRM endpoints."""

from typing import Any, TypedDict


class HubSpotCrmProperties(TypedDict, total=False):
    """Raw CRM object properties from HubSpot API."""

    # Contact properties
    firstname: str | None
    lastname: str | None
    email: str | None
    phone: str | None
    mobilephone: str | None
    jobtitle: str | None
    lifecyclestage: str | None
    hs_lead_status: str | None
    hubspot_owner_id: str | None
    hs_timestamp: str | None

    # Company properties
    name: str | None
    website: str | None
    domain: str | None
    numberofemployees: str | None
    type: str | None
    annualrevenue: str | None
    hs_annual_revenue_currency_code: str | None
    address: str | None
    city: str | None
    state: str | None
    zip: str | None
    country: str | None
    linkedin_company_page: str | None

    # Deal properties
    dealname: str | None
    amount: str | None
    dealstage: str | None
    dealtype: str | None
    closedate: str | None
    pipeline: str | None
    hs_priority: str | None
    description: str | None

    # Common properties
    createdate: str | None
    hs_createdate: str | None
    lastmodifieddate: str | None
    hs_lastmodifieddate: str | None
    hs_object_id: str | None


class HubSpotCrmObject(TypedDict):
    """Raw CRM object from HubSpot API."""

    id: str
    properties: HubSpotCrmProperties
    createdAt: str
    updatedAt: str
    archived: bool


class HubSpotAssociation(TypedDict):
    """HubSpot object association data."""

    toObjectId: str
    associationCategory: str
    associationTypeId: int


class HubSpotAssociationsResponse(TypedDict):
    """Response from HubSpot associations API."""

    results: list[HubSpotAssociation]
    paging: dict[str, Any] | None


class HubSpotSearchResponse(TypedDict):
    """Response from HubSpot CRM search API."""

    total: int
    results: list[HubSpotCrmObject]
    paging: dict[str, Any] | None


class HubSpotBatchReadResponse(TypedDict):
    """Response from HubSpot batch read API."""

    status: str
    results: list[HubSpotCrmObject]
    startedAt: str
    completedAt: str


class HubSpotCreateContactRequest(TypedDict, total=False):
    """Request payload for creating a contact in HubSpot."""

    properties: HubSpotCrmProperties
    associations: list[dict[str, Any]] | None


class HubSpotCreateContactResponse(TypedDict):
    """Response from HubSpot contact creation API."""

    id: str
    properties: HubSpotCrmProperties
    createdAt: str
    updatedAt: str
    archived: bool


class HubSpotCreateCompanyRequest(TypedDict, total=False):
    """Request payload for creating a company in HubSpot."""

    properties: HubSpotCrmProperties


class HubSpotCreateCompanyResponse(TypedDict):
    """Response from HubSpot company creation API."""

    id: str
    properties: HubSpotCrmProperties
    createdAt: str
    updatedAt: str
    archived: bool


class HubSpotCreateDealRequest(TypedDict, total=False):
    """Request payload for creating a deal in HubSpot."""

    properties: HubSpotCrmProperties
    associations: list[dict[str, Any]] | None


class HubSpotCreateDealResponse(TypedDict):
    """Response from HubSpot deal creation API."""

    id: str
    properties: HubSpotCrmProperties
    createdAt: str
    updatedAt: str
    archived: bool


class HubSpotPipelineStage(TypedDict, total=False):
    """Raw HubSpot pipeline stage."""

    id: str
    label: str
    displayOrder: int
    archived: bool


class HubSpotPipeline(TypedDict, total=False):
    """Raw HubSpot pipeline."""

    id: str
    label: str
    displayOrder: int
    archived: bool
    stages: list[HubSpotPipelineStage]


class HubSpotPipelinesResponse(TypedDict):
    """Response from HubSpot pipelines list API."""

    results: list[HubSpotPipeline]
