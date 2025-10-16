# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict, Union
from typing_extensions import Literal, Required, TypedDict

__all__ = [
    "SessionCreateParams",
    "Workflow",
    "WorkflowTracing",
    "ChatkitConfiguration",
    "ChatkitConfigurationAutomaticThreadTitling",
    "ChatkitConfigurationFileUpload",
    "ChatkitConfigurationHistory",
    "ExpiresAfter",
    "RateLimits",
]


class SessionCreateParams(TypedDict, total=False):
    user: Required[str]
    """
    A free-form string that identifies your end user; ensures this Session can
    access other objects that have the same `user` scope.
    """

    workflow: Required[Workflow]
    """Workflow that powers the session."""

    chatkit_configuration: ChatkitConfiguration
    """Optional overrides for ChatKit runtime configuration features"""

    expires_after: ExpiresAfter
    """Optional override for session expiration timing in seconds from creation.

    Defaults to 10 minutes.
    """

    rate_limits: RateLimits
    """Optional override for per-minute request limits. When omitted, defaults to 10."""


class WorkflowTracing(TypedDict, total=False):
    enabled: bool
    """Whether tracing is enabled during the session. Defaults to true."""


class Workflow(TypedDict, total=False):
    id: Required[str]
    """Identifier for the workflow invoked by the session."""

    state_variables: Dict[str, Union[str, bool, float]]
    """State variables forwarded to the workflow.

    Keys may be up to 64 characters, values must be primitive types, and the map
    defaults to an empty object.
    """

    tracing: WorkflowTracing
    """Optional tracing overrides for the workflow invocation.

    When omitted, tracing is enabled by default.
    """

    version: str
    """Specific workflow version to run. Defaults to the latest deployed version."""


class ChatkitConfigurationAutomaticThreadTitling(TypedDict, total=False):
    enabled: bool
    """Enable automatic thread title generation. Defaults to true."""


class ChatkitConfigurationFileUpload(TypedDict, total=False):
    enabled: bool
    """Enable uploads for this session. Defaults to false."""

    max_file_size: int
    """Maximum size in megabytes for each uploaded file.

    Defaults to 512 MB, which is the maximum allowable size.
    """

    max_files: int
    """Maximum number of files that can be uploaded to the session. Defaults to 10."""


class ChatkitConfigurationHistory(TypedDict, total=False):
    enabled: bool
    """Enables chat users to access previous ChatKit threads. Defaults to true."""

    recent_threads: int
    """Number of recent ChatKit threads users have access to.

    Defaults to unlimited when unset.
    """


class ChatkitConfiguration(TypedDict, total=False):
    automatic_thread_titling: ChatkitConfigurationAutomaticThreadTitling
    """Configuration for automatic thread titling.

    When omitted, automatic thread titling is enabled by default.
    """

    file_upload: ChatkitConfigurationFileUpload
    """Configuration for upload enablement and limits.

    When omitted, uploads are disabled by default (max_files 10, max_file_size 512
    MB).
    """

    history: ChatkitConfigurationHistory
    """Configuration for chat history retention.

    When omitted, history is enabled by default with no limit on recent_threads
    (null).
    """


class ExpiresAfter(TypedDict, total=False):
    anchor: Required[Literal["created_at"]]
    """Base timestamp used to calculate expiration. Currently fixed to `created_at`."""

    seconds: Required[int]
    """Number of seconds after the anchor when the session expires."""


class RateLimits(TypedDict, total=False):
    max_requests_per_1_minute: int
    """Maximum number of requests allowed per minute for the session. Defaults to 10."""
