# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional
from typing_extensions import Literal

from pydantic import Field as FieldInfo

from .._models import BaseModel
from .audit_log_actor_user import AuditLogActorUser
from .audit_log_event_type import AuditLogEventType

__all__ = [
    "OrganizationListAuditLogsResponse",
    "Data",
    "DataActor",
    "DataActorAPIKey",
    "DataActorAPIKeyServiceAccount",
    "DataActorSession",
    "DataAPIKeyCreated",
    "DataAPIKeyCreatedData",
    "DataAPIKeyDeleted",
    "DataAPIKeyUpdated",
    "DataAPIKeyUpdatedChangesRequested",
    "DataCertificateCreated",
    "DataCertificateDeleted",
    "DataCertificateUpdated",
    "DataCertificatesActivated",
    "DataCertificatesActivatedCertificate",
    "DataCertificatesDeactivated",
    "DataCertificatesDeactivatedCertificate",
    "DataCheckpointPermissionCreated",
    "DataCheckpointPermissionCreatedData",
    "DataCheckpointPermissionDeleted",
    "DataExternalKeyRegistered",
    "DataExternalKeyRemoved",
    "DataGroupCreated",
    "DataGroupCreatedData",
    "DataGroupDeleted",
    "DataGroupUpdated",
    "DataGroupUpdatedChangesRequested",
    "DataInviteAccepted",
    "DataInviteDeleted",
    "DataInviteSent",
    "DataInviteSentData",
    "DataIPAllowlistConfigActivated",
    "DataIPAllowlistConfigActivatedConfig",
    "DataIPAllowlistConfigDeactivated",
    "DataIPAllowlistConfigDeactivatedConfig",
    "DataIPAllowlistCreated",
    "DataIPAllowlistDeleted",
    "DataIPAllowlistUpdated",
    "DataLoginFailed",
    "DataLogoutFailed",
    "DataOrganizationUpdated",
    "DataOrganizationUpdatedChangesRequested",
    "DataProject",
    "DataProjectArchived",
    "DataProjectCreated",
    "DataProjectCreatedData",
    "DataProjectDeleted",
    "DataProjectUpdated",
    "DataProjectUpdatedChangesRequested",
    "DataRateLimitDeleted",
    "DataRateLimitUpdated",
    "DataRateLimitUpdatedChangesRequested",
    "DataRoleAssignmentCreated",
    "DataRoleAssignmentDeleted",
    "DataRoleCreated",
    "DataRoleDeleted",
    "DataRoleUpdated",
    "DataRoleUpdatedChangesRequested",
    "DataScimDisabled",
    "DataScimEnabled",
    "DataServiceAccountCreated",
    "DataServiceAccountCreatedData",
    "DataServiceAccountDeleted",
    "DataServiceAccountUpdated",
    "DataServiceAccountUpdatedChangesRequested",
    "DataUserAdded",
    "DataUserAddedData",
    "DataUserDeleted",
    "DataUserUpdated",
    "DataUserUpdatedChangesRequested",
]


class DataActorAPIKeyServiceAccount(BaseModel):
    id: Optional[str] = None
    """The service account id."""


class DataActorAPIKey(BaseModel):
    id: Optional[str] = None
    """The tracking id of the API key."""

    service_account: Optional[DataActorAPIKeyServiceAccount] = None
    """The service account that performed the audit logged action."""

    type: Optional[Literal["user", "service_account"]] = None
    """The type of API key. Can be either `user` or `service_account`."""

    user: Optional[AuditLogActorUser] = None
    """The user who performed the audit logged action."""


class DataActorSession(BaseModel):
    ip_address: Optional[str] = None
    """The IP address from which the action was performed."""

    user: Optional[AuditLogActorUser] = None
    """The user who performed the audit logged action."""


class DataActor(BaseModel):
    api_key: Optional[DataActorAPIKey] = None
    """The API Key used to perform the audit logged action."""

    session: Optional[DataActorSession] = None
    """The session in which the audit logged action was performed."""

    type: Optional[Literal["session", "api_key"]] = None
    """The type of actor. Is either `session` or `api_key`."""


class DataAPIKeyCreatedData(BaseModel):
    scopes: Optional[List[str]] = None
    """A list of scopes allowed for the API key, e.g. `["api.model.request"]`"""


class DataAPIKeyCreated(BaseModel):
    id: Optional[str] = None
    """The tracking ID of the API key."""

    data: Optional[DataAPIKeyCreatedData] = None
    """The payload used to create the API key."""


class DataAPIKeyDeleted(BaseModel):
    id: Optional[str] = None
    """The tracking ID of the API key."""


class DataAPIKeyUpdatedChangesRequested(BaseModel):
    scopes: Optional[List[str]] = None
    """A list of scopes allowed for the API key, e.g. `["api.model.request"]`"""


class DataAPIKeyUpdated(BaseModel):
    id: Optional[str] = None
    """The tracking ID of the API key."""

    changes_requested: Optional[DataAPIKeyUpdatedChangesRequested] = None
    """The payload used to update the API key."""


class DataCertificateCreated(BaseModel):
    id: Optional[str] = None
    """The certificate ID."""

    name: Optional[str] = None
    """The name of the certificate."""


class DataCertificateDeleted(BaseModel):
    id: Optional[str] = None
    """The certificate ID."""

    certificate: Optional[str] = None
    """The certificate content in PEM format."""

    name: Optional[str] = None
    """The name of the certificate."""


class DataCertificateUpdated(BaseModel):
    id: Optional[str] = None
    """The certificate ID."""

    name: Optional[str] = None
    """The name of the certificate."""


class DataCertificatesActivatedCertificate(BaseModel):
    id: Optional[str] = None
    """The certificate ID."""

    name: Optional[str] = None
    """The name of the certificate."""


class DataCertificatesActivated(BaseModel):
    certificates: Optional[List[DataCertificatesActivatedCertificate]] = None


class DataCertificatesDeactivatedCertificate(BaseModel):
    id: Optional[str] = None
    """The certificate ID."""

    name: Optional[str] = None
    """The name of the certificate."""


class DataCertificatesDeactivated(BaseModel):
    certificates: Optional[List[DataCertificatesDeactivatedCertificate]] = None


class DataCheckpointPermissionCreatedData(BaseModel):
    fine_tuned_model_checkpoint: Optional[str] = None
    """The ID of the fine-tuned model checkpoint."""

    project_id: Optional[str] = None
    """The ID of the project that the checkpoint permission was created for."""


class DataCheckpointPermissionCreated(BaseModel):
    id: Optional[str] = None
    """The ID of the checkpoint permission."""

    data: Optional[DataCheckpointPermissionCreatedData] = None
    """The payload used to create the checkpoint permission."""


class DataCheckpointPermissionDeleted(BaseModel):
    id: Optional[str] = None
    """The ID of the checkpoint permission."""


class DataExternalKeyRegistered(BaseModel):
    id: Optional[str] = None
    """The ID of the external key configuration."""

    data: Optional[object] = None
    """The configuration for the external key."""


class DataExternalKeyRemoved(BaseModel):
    id: Optional[str] = None
    """The ID of the external key configuration."""


class DataGroupCreatedData(BaseModel):
    group_name: Optional[str] = None
    """The group name."""


class DataGroupCreated(BaseModel):
    id: Optional[str] = None
    """The ID of the group."""

    data: Optional[DataGroupCreatedData] = None
    """Information about the created group."""


class DataGroupDeleted(BaseModel):
    id: Optional[str] = None
    """The ID of the group."""


class DataGroupUpdatedChangesRequested(BaseModel):
    group_name: Optional[str] = None
    """The updated group name."""


class DataGroupUpdated(BaseModel):
    id: Optional[str] = None
    """The ID of the group."""

    changes_requested: Optional[DataGroupUpdatedChangesRequested] = None
    """The payload used to update the group."""


class DataInviteAccepted(BaseModel):
    id: Optional[str] = None
    """The ID of the invite."""


class DataInviteDeleted(BaseModel):
    id: Optional[str] = None
    """The ID of the invite."""


class DataInviteSentData(BaseModel):
    email: Optional[str] = None
    """The email invited to the organization."""

    role: Optional[str] = None
    """The role the email was invited to be. Is either `owner` or `member`."""


class DataInviteSent(BaseModel):
    id: Optional[str] = None
    """The ID of the invite."""

    data: Optional[DataInviteSentData] = None
    """The payload used to create the invite."""


class DataIPAllowlistConfigActivatedConfig(BaseModel):
    id: Optional[str] = None
    """The ID of the IP allowlist configuration."""

    name: Optional[str] = None
    """The name of the IP allowlist configuration."""


class DataIPAllowlistConfigActivated(BaseModel):
    configs: Optional[List[DataIPAllowlistConfigActivatedConfig]] = None
    """The configurations that were activated."""


class DataIPAllowlistConfigDeactivatedConfig(BaseModel):
    id: Optional[str] = None
    """The ID of the IP allowlist configuration."""

    name: Optional[str] = None
    """The name of the IP allowlist configuration."""


class DataIPAllowlistConfigDeactivated(BaseModel):
    configs: Optional[List[DataIPAllowlistConfigDeactivatedConfig]] = None
    """The configurations that were deactivated."""


class DataIPAllowlistCreated(BaseModel):
    id: Optional[str] = None
    """The ID of the IP allowlist configuration."""

    allowed_ips: Optional[List[str]] = None
    """The IP addresses or CIDR ranges included in the configuration."""

    name: Optional[str] = None
    """The name of the IP allowlist configuration."""


class DataIPAllowlistDeleted(BaseModel):
    id: Optional[str] = None
    """The ID of the IP allowlist configuration."""

    allowed_ips: Optional[List[str]] = None
    """The IP addresses or CIDR ranges that were in the configuration."""

    name: Optional[str] = None
    """The name of the IP allowlist configuration."""


class DataIPAllowlistUpdated(BaseModel):
    id: Optional[str] = None
    """The ID of the IP allowlist configuration."""

    allowed_ips: Optional[List[str]] = None
    """The updated set of IP addresses or CIDR ranges in the configuration."""


class DataLoginFailed(BaseModel):
    error_code: Optional[str] = None
    """The error code of the failure."""

    error_message: Optional[str] = None
    """The error message of the failure."""


class DataLogoutFailed(BaseModel):
    error_code: Optional[str] = None
    """The error code of the failure."""

    error_message: Optional[str] = None
    """The error message of the failure."""


class DataOrganizationUpdatedChangesRequested(BaseModel):
    api_call_logging: Optional[str] = None
    """How your organization logs data from supported API calls.

    One of `disabled`, `enabled_per_call`, `enabled_for_all_projects`, or
    `enabled_for_selected_projects`
    """

    api_call_logging_project_ids: Optional[str] = None
    """
    The list of project ids if api_call_logging is set to
    `enabled_for_selected_projects`
    """

    description: Optional[str] = None
    """The organization description."""

    name: Optional[str] = None
    """The organization name."""

    threads_ui_visibility: Optional[str] = None
    """
    Visibility of the threads page which shows messages created with the Assistants
    API and Playground. One of `ANY_ROLE`, `OWNERS`, or `NONE`.
    """

    title: Optional[str] = None
    """The organization title."""

    usage_dashboard_visibility: Optional[str] = None
    """
    Visibility of the usage dashboard which shows activity and costs for your
    organization. One of `ANY_ROLE` or `OWNERS`.
    """


class DataOrganizationUpdated(BaseModel):
    id: Optional[str] = None
    """The organization ID."""

    changes_requested: Optional[DataOrganizationUpdatedChangesRequested] = None
    """The payload used to update the organization settings."""


class DataProject(BaseModel):
    id: Optional[str] = None
    """The project ID."""

    name: Optional[str] = None
    """The project title."""


class DataProjectArchived(BaseModel):
    id: Optional[str] = None
    """The project ID."""


class DataProjectCreatedData(BaseModel):
    name: Optional[str] = None
    """The project name."""

    title: Optional[str] = None
    """The title of the project as seen on the dashboard."""


class DataProjectCreated(BaseModel):
    id: Optional[str] = None
    """The project ID."""

    data: Optional[DataProjectCreatedData] = None
    """The payload used to create the project."""


class DataProjectDeleted(BaseModel):
    id: Optional[str] = None
    """The project ID."""


class DataProjectUpdatedChangesRequested(BaseModel):
    title: Optional[str] = None
    """The title of the project as seen on the dashboard."""


class DataProjectUpdated(BaseModel):
    id: Optional[str] = None
    """The project ID."""

    changes_requested: Optional[DataProjectUpdatedChangesRequested] = None
    """The payload used to update the project."""


class DataRateLimitDeleted(BaseModel):
    id: Optional[str] = None
    """The rate limit ID"""


class DataRateLimitUpdatedChangesRequested(BaseModel):
    batch_1_day_max_input_tokens: Optional[int] = None
    """The maximum batch input tokens per day. Only relevant for certain models."""

    max_audio_megabytes_per_1_minute: Optional[int] = None
    """The maximum audio megabytes per minute. Only relevant for certain models."""

    max_images_per_1_minute: Optional[int] = None
    """The maximum images per minute. Only relevant for certain models."""

    max_requests_per_1_day: Optional[int] = None
    """The maximum requests per day. Only relevant for certain models."""

    max_requests_per_1_minute: Optional[int] = None
    """The maximum requests per minute."""

    max_tokens_per_1_minute: Optional[int] = None
    """The maximum tokens per minute."""


class DataRateLimitUpdated(BaseModel):
    id: Optional[str] = None
    """The rate limit ID"""

    changes_requested: Optional[DataRateLimitUpdatedChangesRequested] = None
    """The payload used to update the rate limits."""


class DataRoleAssignmentCreated(BaseModel):
    id: Optional[str] = None
    """The identifier of the role assignment."""

    principal_id: Optional[str] = None
    """The principal (user or group) that received the role."""

    principal_type: Optional[str] = None
    """The type of principal (user or group) that received the role."""

    resource_id: Optional[str] = None
    """The resource the role assignment is scoped to."""

    resource_type: Optional[str] = None
    """The type of resource the role assignment is scoped to."""


class DataRoleAssignmentDeleted(BaseModel):
    id: Optional[str] = None
    """The identifier of the role assignment."""

    principal_id: Optional[str] = None
    """The principal (user or group) that had the role removed."""

    principal_type: Optional[str] = None
    """The type of principal (user or group) that had the role removed."""

    resource_id: Optional[str] = None
    """The resource the role assignment was scoped to."""

    resource_type: Optional[str] = None
    """The type of resource the role assignment was scoped to."""


class DataRoleCreated(BaseModel):
    id: Optional[str] = None
    """The role ID."""

    permissions: Optional[List[str]] = None
    """The permissions granted by the role."""

    resource_id: Optional[str] = None
    """The resource the role is scoped to."""

    resource_type: Optional[str] = None
    """The type of resource the role belongs to."""

    role_name: Optional[str] = None
    """The name of the role."""


class DataRoleDeleted(BaseModel):
    id: Optional[str] = None
    """The role ID."""


class DataRoleUpdatedChangesRequested(BaseModel):
    description: Optional[str] = None
    """The updated role description, when provided."""

    metadata: Optional[object] = None
    """Additional metadata stored on the role."""

    permissions_added: Optional[List[str]] = None
    """The permissions added to the role."""

    permissions_removed: Optional[List[str]] = None
    """The permissions removed from the role."""

    resource_id: Optional[str] = None
    """The resource the role is scoped to."""

    resource_type: Optional[str] = None
    """The type of resource the role belongs to."""

    role_name: Optional[str] = None
    """The updated role name, when provided."""


class DataRoleUpdated(BaseModel):
    id: Optional[str] = None
    """The role ID."""

    changes_requested: Optional[DataRoleUpdatedChangesRequested] = None
    """The payload used to update the role."""


class DataScimDisabled(BaseModel):
    id: Optional[str] = None
    """The ID of the SCIM was disabled for."""


class DataScimEnabled(BaseModel):
    id: Optional[str] = None
    """The ID of the SCIM was enabled for."""


class DataServiceAccountCreatedData(BaseModel):
    role: Optional[str] = None
    """The role of the service account. Is either `owner` or `member`."""


class DataServiceAccountCreated(BaseModel):
    id: Optional[str] = None
    """The service account ID."""

    data: Optional[DataServiceAccountCreatedData] = None
    """The payload used to create the service account."""


class DataServiceAccountDeleted(BaseModel):
    id: Optional[str] = None
    """The service account ID."""


class DataServiceAccountUpdatedChangesRequested(BaseModel):
    role: Optional[str] = None
    """The role of the service account. Is either `owner` or `member`."""


class DataServiceAccountUpdated(BaseModel):
    id: Optional[str] = None
    """The service account ID."""

    changes_requested: Optional[DataServiceAccountUpdatedChangesRequested] = None
    """The payload used to updated the service account."""


class DataUserAddedData(BaseModel):
    role: Optional[str] = None
    """The role of the user. Is either `owner` or `member`."""


class DataUserAdded(BaseModel):
    id: Optional[str] = None
    """The user ID."""

    data: Optional[DataUserAddedData] = None
    """The payload used to add the user to the project."""


class DataUserDeleted(BaseModel):
    id: Optional[str] = None
    """The user ID."""


class DataUserUpdatedChangesRequested(BaseModel):
    role: Optional[str] = None
    """The role of the user. Is either `owner` or `member`."""


class DataUserUpdated(BaseModel):
    id: Optional[str] = None
    """The project ID."""

    changes_requested: Optional[DataUserUpdatedChangesRequested] = None
    """The payload used to update the user."""


class Data(BaseModel):
    id: str
    """The ID of this log."""

    actor: DataActor
    """The actor who performed the audit logged action."""

    effective_at: int
    """The Unix timestamp (in seconds) of the event."""

    type: AuditLogEventType
    """The event type."""

    api_key_created: Optional[DataAPIKeyCreated] = FieldInfo(alias="api_key.created", default=None)
    """The details for events with this `type`."""

    api_key_deleted: Optional[DataAPIKeyDeleted] = FieldInfo(alias="api_key.deleted", default=None)
    """The details for events with this `type`."""

    api_key_updated: Optional[DataAPIKeyUpdated] = FieldInfo(alias="api_key.updated", default=None)
    """The details for events with this `type`."""

    certificate_created: Optional[DataCertificateCreated] = FieldInfo(alias="certificate.created", default=None)
    """The details for events with this `type`."""

    certificate_deleted: Optional[DataCertificateDeleted] = FieldInfo(alias="certificate.deleted", default=None)
    """The details for events with this `type`."""

    certificate_updated: Optional[DataCertificateUpdated] = FieldInfo(alias="certificate.updated", default=None)
    """The details for events with this `type`."""

    certificates_activated: Optional[DataCertificatesActivated] = FieldInfo(
        alias="certificates.activated", default=None
    )
    """The details for events with this `type`."""

    certificates_deactivated: Optional[DataCertificatesDeactivated] = FieldInfo(
        alias="certificates.deactivated", default=None
    )
    """The details for events with this `type`."""

    checkpoint_permission_created: Optional[DataCheckpointPermissionCreated] = FieldInfo(
        alias="checkpoint.permission.created", default=None
    )
    """
    The project and fine-tuned model checkpoint that the checkpoint permission was
    created for.
    """

    checkpoint_permission_deleted: Optional[DataCheckpointPermissionDeleted] = FieldInfo(
        alias="checkpoint.permission.deleted", default=None
    )
    """The details for events with this `type`."""

    external_key_registered: Optional[DataExternalKeyRegistered] = FieldInfo(
        alias="external_key.registered", default=None
    )
    """The details for events with this `type`."""

    external_key_removed: Optional[DataExternalKeyRemoved] = FieldInfo(alias="external_key.removed", default=None)
    """The details for events with this `type`."""

    group_created: Optional[DataGroupCreated] = FieldInfo(alias="group.created", default=None)
    """The details for events with this `type`."""

    group_deleted: Optional[DataGroupDeleted] = FieldInfo(alias="group.deleted", default=None)
    """The details for events with this `type`."""

    group_updated: Optional[DataGroupUpdated] = FieldInfo(alias="group.updated", default=None)
    """The details for events with this `type`."""

    invite_accepted: Optional[DataInviteAccepted] = FieldInfo(alias="invite.accepted", default=None)
    """The details for events with this `type`."""

    invite_deleted: Optional[DataInviteDeleted] = FieldInfo(alias="invite.deleted", default=None)
    """The details for events with this `type`."""

    invite_sent: Optional[DataInviteSent] = FieldInfo(alias="invite.sent", default=None)
    """The details for events with this `type`."""

    ip_allowlist_config_activated: Optional[DataIPAllowlistConfigActivated] = FieldInfo(
        alias="ip_allowlist.config.activated", default=None
    )
    """The details for events with this `type`."""

    ip_allowlist_config_deactivated: Optional[DataIPAllowlistConfigDeactivated] = FieldInfo(
        alias="ip_allowlist.config.deactivated", default=None
    )
    """The details for events with this `type`."""

    ip_allowlist_created: Optional[DataIPAllowlistCreated] = FieldInfo(alias="ip_allowlist.created", default=None)
    """The details for events with this `type`."""

    ip_allowlist_deleted: Optional[DataIPAllowlistDeleted] = FieldInfo(alias="ip_allowlist.deleted", default=None)
    """The details for events with this `type`."""

    ip_allowlist_updated: Optional[DataIPAllowlistUpdated] = FieldInfo(alias="ip_allowlist.updated", default=None)
    """The details for events with this `type`."""

    login_failed: Optional[DataLoginFailed] = FieldInfo(alias="login.failed", default=None)
    """The details for events with this `type`."""

    login_succeeded: Optional[object] = FieldInfo(alias="login.succeeded", default=None)
    """This event has no additional fields beyond the standard audit log attributes."""

    logout_failed: Optional[DataLogoutFailed] = FieldInfo(alias="logout.failed", default=None)
    """The details for events with this `type`."""

    logout_succeeded: Optional[object] = FieldInfo(alias="logout.succeeded", default=None)
    """This event has no additional fields beyond the standard audit log attributes."""

    organization_updated: Optional[DataOrganizationUpdated] = FieldInfo(alias="organization.updated", default=None)
    """The details for events with this `type`."""

    project: Optional[DataProject] = None
    """The project that the action was scoped to.

    Absent for actions not scoped to projects. Note that any admin actions taken via
    Admin API keys are associated with the default project.
    """

    project_archived: Optional[DataProjectArchived] = FieldInfo(alias="project.archived", default=None)
    """The details for events with this `type`."""

    project_created: Optional[DataProjectCreated] = FieldInfo(alias="project.created", default=None)
    """The details for events with this `type`."""

    project_deleted: Optional[DataProjectDeleted] = FieldInfo(alias="project.deleted", default=None)
    """The details for events with this `type`."""

    project_updated: Optional[DataProjectUpdated] = FieldInfo(alias="project.updated", default=None)
    """The details for events with this `type`."""

    rate_limit_deleted: Optional[DataRateLimitDeleted] = FieldInfo(alias="rate_limit.deleted", default=None)
    """The details for events with this `type`."""

    rate_limit_updated: Optional[DataRateLimitUpdated] = FieldInfo(alias="rate_limit.updated", default=None)
    """The details for events with this `type`."""

    role_assignment_created: Optional[DataRoleAssignmentCreated] = FieldInfo(
        alias="role.assignment.created", default=None
    )
    """The details for events with this `type`."""

    role_assignment_deleted: Optional[DataRoleAssignmentDeleted] = FieldInfo(
        alias="role.assignment.deleted", default=None
    )
    """The details for events with this `type`."""

    role_created: Optional[DataRoleCreated] = FieldInfo(alias="role.created", default=None)
    """The details for events with this `type`."""

    role_deleted: Optional[DataRoleDeleted] = FieldInfo(alias="role.deleted", default=None)
    """The details for events with this `type`."""

    role_updated: Optional[DataRoleUpdated] = FieldInfo(alias="role.updated", default=None)
    """The details for events with this `type`."""

    scim_disabled: Optional[DataScimDisabled] = FieldInfo(alias="scim.disabled", default=None)
    """The details for events with this `type`."""

    scim_enabled: Optional[DataScimEnabled] = FieldInfo(alias="scim.enabled", default=None)
    """The details for events with this `type`."""

    service_account_created: Optional[DataServiceAccountCreated] = FieldInfo(
        alias="service_account.created", default=None
    )
    """The details for events with this `type`."""

    service_account_deleted: Optional[DataServiceAccountDeleted] = FieldInfo(
        alias="service_account.deleted", default=None
    )
    """The details for events with this `type`."""

    service_account_updated: Optional[DataServiceAccountUpdated] = FieldInfo(
        alias="service_account.updated", default=None
    )
    """The details for events with this `type`."""

    user_added: Optional[DataUserAdded] = FieldInfo(alias="user.added", default=None)
    """The details for events with this `type`."""

    user_deleted: Optional[DataUserDeleted] = FieldInfo(alias="user.deleted", default=None)
    """The details for events with this `type`."""

    user_updated: Optional[DataUserUpdated] = FieldInfo(alias="user.updated", default=None)
    """The details for events with this `type`."""


class OrganizationListAuditLogsResponse(BaseModel):
    data: List[Data]

    first_id: str

    has_more: bool

    last_id: str

    object: Literal["list"]
