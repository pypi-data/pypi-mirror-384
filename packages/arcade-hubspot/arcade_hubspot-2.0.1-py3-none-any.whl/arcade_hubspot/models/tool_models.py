"""TypedDict models for HubSpot tool responses and data structures."""

from typing import Any

from typing_extensions import TypedDict


class CurrentUserData(TypedDict):
    """Cleaned current user data model for tool responses."""

    user_id: int
    """Unique identifier for the current user in HubSpot."""

    email: str
    """Email address of the current user."""

    hub_id: int
    """HubSpot portal/hub identifier where the user belongs."""

    hub_domain: str
    """Domain name of the HubSpot portal."""


class DetailedUserData(TypedDict):
    """Detailed current user data model combining OAuth token and owner info."""

    user_id: int
    """Unique identifier for the current user in HubSpot."""

    email: str
    """Email address of the current user."""

    first_name: str | None
    """First name of the current user."""

    last_name: str | None
    """Last name of the current user."""

    owner_id: str | None
    """HubSpot owner identifier for the current user."""

    hub_id: int | None
    """HubSpot portal/hub identifier where the user belongs."""

    hub_domain: str
    """Domain name of the HubSpot portal."""

    app_id: str | None
    """Application identifier for the OAuth token."""

    expires_in: int | None
    """Token expiration time in seconds."""

    user_id_including_portal: int | None
    """Combined user and portal identifier."""

    my_profile_gui_url: str | None
    """Direct URL to view the user's profile in HubSpot interface."""


class ContactData(TypedDict):
    """Cleaned contact data model for tool responses."""

    id: str
    """Unique identifier for the contact in HubSpot."""

    object_type: str
    """Type of HubSpot object."""

    firstname: str | None
    """First name of the contact."""

    lastname: str | None
    """Last name of the contact."""

    email_address: str | None
    """Primary email address of the contact."""

    phone: str | None
    """Primary phone number of the contact."""

    mobilephone: str | None
    """Mobile phone number of the contact."""

    jobtitle: str | None
    """Job title or position of the contact."""

    lifecycle_stage: str | None
    """Current lifecycle stage of the contact."""

    lead_status: str | None
    """Current lead status of the contact."""

    owner_id: str | None
    """HubSpot owner/sales rep assigned to this contact."""

    datetime: str | None
    """Timestamp when the contact was created or last modified."""

    contact_gui_url: str | None
    """Direct URL to view this contact in HubSpot interface."""


class CompanyData(TypedDict):
    """Cleaned company data model for tool responses."""

    id: str
    """Unique identifier for the company in HubSpot."""

    object_type: str
    """Type of HubSpot object."""

    name: str | None
    """Company name or business name."""

    website: str | None
    """Company website URL."""

    phone: str | None
    """Primary phone number for the company."""

    employee_count: str | None
    """Number of employees at the company."""

    company_type: str | None
    """Type of company or business classification."""

    annual_revenue: dict | None
    """Annual revenue information with amount and currency."""

    lifecycle_stage: str | None
    """Current lifecycle stage of the company."""

    lead_status: str | None
    """Current lead status of the company."""

    owner_id: str | None
    """HubSpot owner/sales rep assigned to this company."""

    datetime: str | None
    """Timestamp when the company was created or last modified."""

    address: dict | None
    """Company address information including street, city, state, country."""

    company_gui_url: str | None
    """Direct URL to view this company in HubSpot interface."""


class DealData(TypedDict):
    """Cleaned deal data model for tool responses."""

    id: str
    """Unique identifier for the deal in HubSpot."""

    object_type: str
    """Type of HubSpot object."""

    deal_name: str | None
    """Name or title of the deal."""

    amount: str | None
    """Monetary value of the deal."""

    deal_stage: str | None
    """Current stage of the deal in the sales pipeline."""

    deal_type: str | None
    """Type of deal or business classification."""

    expected_close_date: str | None
    """Expected date when the deal will close."""

    pipeline: str | None
    """Sales pipeline this deal belongs to."""

    deal_owner: str | None
    """HubSpot owner/sales rep assigned to this deal."""

    priority_level: str | None
    """Priority level of the deal."""

    deal_description: str | None
    """Description or notes about the deal."""

    datetime: str | None
    """Timestamp when the deal was created or last modified."""

    deal_gui_url: str | None
    """Direct URL to view this deal in HubSpot interface."""


class ContactSearchResponse(TypedDict):
    """Contact search response model for tool responses."""

    contacts: list[ContactData]
    """List of contacts matching the search criteria."""

    pagination: dict[str, Any]
    """Pagination information for navigating through results."""


class CompanySearchResponse(TypedDict):
    """Company search response model for tool responses."""

    companies: list[CompanyData]
    """List of companies matching the search criteria."""

    pagination: dict[str, Any]
    """Pagination information for navigating through results."""


class DealSearchResponse(TypedDict):
    """Deal search response model for tool responses."""

    deals: list[DealData]
    """List of deals matching the search criteria."""

    pagination: dict[str, Any]
    """Pagination information for navigating through results."""


class CreateContactResponse(TypedDict):
    """Response model for contact creation."""

    id: str
    """Unique identifier for the newly created contact."""

    object_type: str
    """Type of HubSpot object."""

    firstname: str | None
    """First name of the contact."""

    lastname: str | None
    """Last name of the contact."""

    email_address: str | None
    """Primary email address of the contact."""

    phone: str | None
    """Primary phone number of the contact."""

    mobilephone: str | None
    """Mobile phone number of the contact."""

    jobtitle: str | None
    """Job title or position of the contact."""

    contact_gui_url: str | None
    """Direct URL to view this contact in HubSpot interface."""


class CreateCompanyResponse(TypedDict):
    """Response model for company creation."""

    id: str
    """Unique identifier for the newly created company."""

    name: str | None
    """Company name or business name."""

    domain: str | None
    """Company domain name."""

    industry: str | None
    """Industry classification of the company."""

    city: str | None
    """City where the company is located."""

    state: str | None
    """State or province where the company is located."""

    country: str | None
    """Country where the company is located."""

    phone: str | None
    """Primary phone number for the company."""

    website: str | None
    """Company website URL."""

    created_at: str | None
    """Timestamp when the company was created."""

    company_gui_url: str | None
    """Direct URL to view this company in HubSpot interface."""


class DealPipelineRef(TypedDict):
    """Reference to a deal pipeline with identifier and label."""

    id: str
    """Unique identifier for the deal pipeline."""

    label: str | None
    """Human-readable name of the pipeline."""


class DealStageRef(TypedDict):
    """Reference to a deal stage with identifier and label."""

    id: str
    """Unique identifier for the deal stage."""

    label: str | None
    """Human-readable name of the stage."""


class CreateDealResponse(TypedDict):
    """Response model for deal creation."""

    id: str
    """Unique identifier for the newly created deal."""

    deal_name: str | None
    """Name or title of the deal."""

    amount: str | None
    """Monetary value of the deal."""

    deal_stage: DealStageRef | None
    """Current stage of the deal in the sales pipeline."""

    deal_type: str | None
    """Type of deal or business classification."""

    expected_close_date: str | None
    """Expected date when the deal will close."""

    pipeline: DealPipelineRef | None
    """Sales pipeline this deal belongs to."""

    deal_owner: str | None
    """HubSpot owner/sales rep assigned to this deal."""

    priority_level: str | None
    """Priority level of the deal."""

    deal_description: str | None
    """Description or notes about the deal."""

    created_at: str | None
    """Timestamp when the deal was created."""

    deal_gui_url: str | None
    """Direct URL to view this deal in HubSpot interface."""


class PipelineStageData(TypedDict):
    """Deal pipeline stage information."""

    id: str
    """Unique identifier for the pipeline stage."""

    label: str
    """Human-readable name of the stage."""

    display_order: int | None
    """Order in which this stage appears in the pipeline."""

    archived: bool | None
    """Whether this stage is archived or active."""


class DealPipelineData(TypedDict):
    """Deal pipeline information with stages."""

    id: str
    """Unique identifier for the deal pipeline."""

    label: str
    """Human-readable name of the pipeline."""

    display_order: int | None
    """Order in which this pipeline appears in the list."""

    archived: bool | None
    """Whether this pipeline is archived or active."""

    stages: list[PipelineStageData]
    """List of stages within this pipeline."""

    pipeline_gui_url: str | None
    """Direct URL to view this pipeline in HubSpot interface."""


class DealPipelinesResponse(TypedDict):
    """Response model for listing deal pipelines."""

    pipelines: list[DealPipelineData]
    """List of available deal pipelines with their stages."""


class DealPipelineStagesResponse(TypedDict):
    """Stages for a specific deal pipeline."""

    pipeline_id: str
    """Unique identifier for the deal pipeline."""

    label: str
    """Human-readable name of the pipeline."""

    stages: list[PipelineStageData]
    """List of stages within this pipeline."""

    pipeline_gui_url: str | None
    """Direct URL to view this pipeline in HubSpot interface."""


# Activity response models
class CreateNoteActivityResponse(TypedDict):
    """Response model for note activity creation."""

    id: str
    """Unique identifier for the created note activity."""

    object_type: str
    """Type of HubSpot object."""

    body_preview: str | None
    """Preview of the note content."""

    owner_id: str | None
    """HubSpot owner who created this note."""

    timestamp: str | None
    """Timestamp when the note was created."""


class CreateCallActivityResponse(TypedDict):
    """Response model for call activity creation."""

    id: str
    """Unique identifier for the created call activity."""

    object_type: str
    """Type of HubSpot object."""

    title: str | None
    """Title or subject of the call."""

    direction: str | None
    """Direction of the call."""

    status: str | None
    """Status of the call."""

    summary: str | None
    """Summary or notes about the call."""

    owner_id: str | None
    """HubSpot owner who created this call activity."""

    timestamp: str | None
    """Timestamp when the call activity was created."""


class CreateEmailActivityResponse(TypedDict):
    """Response model for email activity creation."""

    id: str
    """Unique identifier for the created email activity."""

    object_type: str
    """Type of HubSpot object."""

    subject: str | None
    """Subject line of the email."""

    status: str | None
    """Status of the email."""

    owner_id: str | None
    """HubSpot owner who created this email activity."""

    timestamp: str | None
    """Timestamp when the email activity was created."""


class CreateMeetingActivityResponse(TypedDict):
    """Response model for meeting activity creation."""

    id: str
    """Unique identifier for the created meeting activity."""

    object_type: str
    """Type of HubSpot object."""

    title: str | None
    """Title or subject of the meeting."""

    start_time: str | None
    """Scheduled start time of the meeting."""

    end_time: str | None
    """Scheduled end time of the meeting."""

    location: str | None
    """Location where the meeting took place."""

    outcome: str | None
    """Outcome or result of the meeting."""

    owner_id: str | None
    """HubSpot owner who created this meeting activity."""


class CreateCommunicationActivityResponse(TypedDict):
    """Response model for communication activity creation."""

    id: str
    """Unique identifier for the created communication activity."""

    object_type: str
    """Type of HubSpot object."""

    channel: str | None
    """Communication channel used."""

    body_preview: str | None
    """Preview of the communication content."""

    owner_id: str | None
    """HubSpot owner who created this communication activity."""

    timestamp: str | None
    """Timestamp when the communication activity was created."""


class ActivitySearchResponse(TypedDict):
    """Response model for listing activities by type or across types."""

    type: str | None
    """Type of activities in the results."""

    results: list[dict[str, Any]]
    """List of activity records matching the search criteria."""

    paging: dict[str, Any] | None
    """Pagination information for navigating through results."""


class AssociationResult(TypedDict):
    """Response model for association operations."""

    success: bool
    """Whether the association operation was successful."""

    deal_id: str
    """Unique identifier of the deal in the association."""

    contact_id: str
    """Unique identifier of the contact in the association."""

    message: str
    """Status message describing the result of the operation."""
