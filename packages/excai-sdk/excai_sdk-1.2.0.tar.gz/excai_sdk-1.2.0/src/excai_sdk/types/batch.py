# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional
from typing_extensions import Literal

from .._models import BaseModel
from .chat.metadata import Metadata

__all__ = [
    "Batch",
    "Errors",
    "ErrorsData",
    "RequestCounts",
    "Usage",
    "UsageInputTokensDetails",
    "UsageOutputTokensDetails",
]


class ErrorsData(BaseModel):
    code: Optional[str] = None
    """An error code identifying the error type."""

    line: Optional[int] = None
    """The line number of the input file where the error occurred, if applicable."""

    message: Optional[str] = None
    """A human-readable message providing more details about the error."""

    param: Optional[str] = None
    """The name of the parameter that caused the error, if applicable."""


class Errors(BaseModel):
    data: Optional[List[ErrorsData]] = None

    object: Optional[str] = None
    """The object type, which is always `list`."""


class RequestCounts(BaseModel):
    completed: int
    """Number of requests that have been completed successfully."""

    failed: int
    """Number of requests that have failed."""

    total: int
    """Total number of requests in the batch."""


class UsageInputTokensDetails(BaseModel):
    cached_tokens: int
    """The number of tokens that were retrieved from the cache.

    [More on prompt caching](https://main.excai.ai/docs/guides/prompt-caching).
    """


class UsageOutputTokensDetails(BaseModel):
    reasoning_tokens: int
    """The number of reasoning tokens."""


class Usage(BaseModel):
    input_tokens: int
    """The number of input tokens."""

    input_tokens_details: UsageInputTokensDetails
    """A detailed breakdown of the input tokens."""

    output_tokens: int
    """The number of output tokens."""

    output_tokens_details: UsageOutputTokensDetails
    """A detailed breakdown of the output tokens."""

    total_tokens: int
    """The total number of tokens used."""


class Batch(BaseModel):
    id: str

    completion_window: str
    """The time frame within which the batch should be processed."""

    created_at: int
    """The Unix timestamp (in seconds) for when the batch was created."""

    endpoint: str
    """The EXCai API endpoint used by the batch."""

    input_file_id: str
    """The ID of the input file for the batch."""

    object: Literal["batch"]
    """The object type, which is always `batch`."""

    status: Literal[
        "validating", "failed", "in_progress", "finalizing", "completed", "expired", "cancelling", "cancelled"
    ]
    """The current status of the batch."""

    cancelled_at: Optional[int] = None
    """The Unix timestamp (in seconds) for when the batch was cancelled."""

    cancelling_at: Optional[int] = None
    """The Unix timestamp (in seconds) for when the batch started cancelling."""

    completed_at: Optional[int] = None
    """The Unix timestamp (in seconds) for when the batch was completed."""

    error_file_id: Optional[str] = None
    """The ID of the file containing the outputs of requests with errors."""

    errors: Optional[Errors] = None

    expired_at: Optional[int] = None
    """The Unix timestamp (in seconds) for when the batch expired."""

    expires_at: Optional[int] = None
    """The Unix timestamp (in seconds) for when the batch will expire."""

    failed_at: Optional[int] = None
    """The Unix timestamp (in seconds) for when the batch failed."""

    finalizing_at: Optional[int] = None
    """The Unix timestamp (in seconds) for when the batch started finalizing."""

    in_progress_at: Optional[int] = None
    """The Unix timestamp (in seconds) for when the batch started processing."""

    metadata: Optional[Metadata] = None
    """Set of 16 key-value pairs that can be attached to an object.

    This can be useful for storing additional information about the object in a
    structured format, and querying for objects via API or the dashboard.

    Keys are strings with a maximum length of 64 characters. Values are strings with
    a maximum length of 512 characters.
    """

    model: Optional[str] = None
    """Model ID used to process the batch, like `gpt-5-2025-08-07`.

    EXCai offers a wide range of models with different capabilities, performance
    characteristics, and price points. Refer to the
    [model guide](https://main.excai.ai/docs/models) to browse and compare available
    models.
    """

    output_file_id: Optional[str] = None
    """The ID of the file containing the outputs of successfully executed requests."""

    request_counts: Optional[RequestCounts] = None
    """The request counts for different statuses within the batch."""

    usage: Optional[Usage] = None
    """
    Represents token usage details including input tokens, output tokens, a
    breakdown of output tokens, and the total tokens used. Only populated on batches
    created after September 7, 2025.
    """
