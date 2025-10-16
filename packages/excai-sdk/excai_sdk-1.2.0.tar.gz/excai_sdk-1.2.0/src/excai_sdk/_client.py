# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, Mapping
from typing_extensions import Self, override

import httpx

from . import _exceptions
from ._qs import Querystring
from ._types import (
    Omit,
    Timeout,
    NotGiven,
    Transport,
    ProxiesTypes,
    RequestOptions,
    not_given,
)
from ._utils import is_given, get_async_library
from ._version import __version__
from .resources import (
    audio,
    files,
    images,
    models,
    videos,
    batches,
    uploads,
    responses,
    assistants,
    embeddings,
    completions,
    moderations,
)
from ._streaming import Stream as Stream, AsyncStream as AsyncStream
from ._exceptions import ExcaiSDKError, APIStatusError
from ._base_client import (
    DEFAULT_MAX_RETRIES,
    SyncAPIClient,
    AsyncAPIClient,
)
from .resources.chat import chat
from .resources.evals import evals
from .resources.chatkit import chatkit
from .resources.threads import threads
from .resources.realtime import realtime
from .resources.containers import containers
from .resources.fine_tuning import fine_tuning
from .resources.organization import organization
from .resources.conversations import conversations
from .resources.vector_stores import vector_stores

__all__ = [
    "Timeout",
    "Transport",
    "ProxiesTypes",
    "RequestOptions",
    "ExcaiSDK",
    "AsyncExcaiSDK",
    "Client",
    "AsyncClient",
]


class ExcaiSDK(SyncAPIClient):
    assistants: assistants.AssistantsResource
    audio: audio.AudioResource
    batches: batches.BatchesResource
    chat: chat.ChatResource
    completions: completions.CompletionsResource
    containers: containers.ContainersResource
    conversations: conversations.ConversationsResource
    embeddings: embeddings.EmbeddingsResource
    evals: evals.EvalsResource
    files: files.FilesResource
    fine_tuning: fine_tuning.FineTuningResource
    images: images.ImagesResource
    models: models.ModelsResource
    moderations: moderations.ModerationsResource
    organization: organization.OrganizationResource
    realtime: realtime.RealtimeResource
    responses: responses.ResponsesResource
    threads: threads.ThreadsResource
    uploads: uploads.UploadsResource
    vector_stores: vector_stores.VectorStoresResource
    videos: videos.VideosResource
    chatkit: chatkit.ChatkitResource
    with_raw_response: ExcaiSDKWithRawResponse
    with_streaming_response: ExcaiSDKWithStreamedResponse

    # client options
    api_key: str

    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str | httpx.URL | None = None,
        timeout: float | Timeout | None | NotGiven = not_given,
        max_retries: int = DEFAULT_MAX_RETRIES,
        default_headers: Mapping[str, str] | None = None,
        default_query: Mapping[str, object] | None = None,
        # Configure a custom httpx client.
        # We provide a `DefaultHttpxClient` class that you can pass to retain the default values we use for `limits`, `timeout` & `follow_redirects`.
        # See the [httpx documentation](https://www.python-httpx.org/api/#client) for more details.
        http_client: httpx.Client | None = None,
        # Enable or disable schema validation for data returned by the API.
        # When enabled an error APIResponseValidationError is raised
        # if the API responds with invalid data for the expected schema.
        #
        # This parameter may be removed or changed in the future.
        # If you rely on this feature, please open a GitHub issue
        # outlining your use-case to help us decide if it should be
        # part of our public interface in the future.
        _strict_response_validation: bool = False,
    ) -> None:
        """Construct a new synchronous ExcaiSDK client instance.

        This automatically infers the `api_key` argument from the `EXCAI_API_KEY` environment variable if it is not provided.
        """
        if api_key is None:
            api_key = os.environ.get("EXCAI_API_KEY")
        if api_key is None:
            raise ExcaiSDKError(
                "The api_key client option must be set either by passing api_key to the client or by setting the EXCAI_API_KEY environment variable"
            )
        self.api_key = api_key

        if base_url is None:
            base_url = os.environ.get("EXCAI_SDK_BASE_URL")
        if base_url is None:
            base_url = f"https://api-main.excai.ai/api/v1"

        super().__init__(
            version=__version__,
            base_url=base_url,
            max_retries=max_retries,
            timeout=timeout,
            http_client=http_client,
            custom_headers=default_headers,
            custom_query=default_query,
            _strict_response_validation=_strict_response_validation,
        )

        self.assistants = assistants.AssistantsResource(self)
        self.audio = audio.AudioResource(self)
        self.batches = batches.BatchesResource(self)
        self.chat = chat.ChatResource(self)
        self.completions = completions.CompletionsResource(self)
        self.containers = containers.ContainersResource(self)
        self.conversations = conversations.ConversationsResource(self)
        self.embeddings = embeddings.EmbeddingsResource(self)
        self.evals = evals.EvalsResource(self)
        self.files = files.FilesResource(self)
        self.fine_tuning = fine_tuning.FineTuningResource(self)
        self.images = images.ImagesResource(self)
        self.models = models.ModelsResource(self)
        self.moderations = moderations.ModerationsResource(self)
        self.organization = organization.OrganizationResource(self)
        self.realtime = realtime.RealtimeResource(self)
        self.responses = responses.ResponsesResource(self)
        self.threads = threads.ThreadsResource(self)
        self.uploads = uploads.UploadsResource(self)
        self.vector_stores = vector_stores.VectorStoresResource(self)
        self.videos = videos.VideosResource(self)
        self.chatkit = chatkit.ChatkitResource(self)
        self.with_raw_response = ExcaiSDKWithRawResponse(self)
        self.with_streaming_response = ExcaiSDKWithStreamedResponse(self)

    @property
    @override
    def qs(self) -> Querystring:
        return Querystring(array_format="comma")

    @property
    @override
    def auth_headers(self) -> dict[str, str]:
        api_key = self.api_key
        return {"Authorization": f"Bearer {api_key}"}

    @property
    @override
    def default_headers(self) -> dict[str, str | Omit]:
        return {
            **super().default_headers,
            "X-Stainless-Async": "false",
            **self._custom_headers,
        }

    def copy(
        self,
        *,
        api_key: str | None = None,
        base_url: str | httpx.URL | None = None,
        timeout: float | Timeout | None | NotGiven = not_given,
        http_client: httpx.Client | None = None,
        max_retries: int | NotGiven = not_given,
        default_headers: Mapping[str, str] | None = None,
        set_default_headers: Mapping[str, str] | None = None,
        default_query: Mapping[str, object] | None = None,
        set_default_query: Mapping[str, object] | None = None,
        _extra_kwargs: Mapping[str, Any] = {},
    ) -> Self:
        """
        Create a new client instance re-using the same options given to the current client with optional overriding.
        """
        if default_headers is not None and set_default_headers is not None:
            raise ValueError("The `default_headers` and `set_default_headers` arguments are mutually exclusive")

        if default_query is not None and set_default_query is not None:
            raise ValueError("The `default_query` and `set_default_query` arguments are mutually exclusive")

        headers = self._custom_headers
        if default_headers is not None:
            headers = {**headers, **default_headers}
        elif set_default_headers is not None:
            headers = set_default_headers

        params = self._custom_query
        if default_query is not None:
            params = {**params, **default_query}
        elif set_default_query is not None:
            params = set_default_query

        http_client = http_client or self._client
        return self.__class__(
            api_key=api_key or self.api_key,
            base_url=base_url or self.base_url,
            timeout=self.timeout if isinstance(timeout, NotGiven) else timeout,
            http_client=http_client,
            max_retries=max_retries if is_given(max_retries) else self.max_retries,
            default_headers=headers,
            default_query=params,
            **_extra_kwargs,
        )

    # Alias for `copy` for nicer inline usage, e.g.
    # client.with_options(timeout=10).foo.create(...)
    with_options = copy

    @override
    def _make_status_error(
        self,
        err_msg: str,
        *,
        body: object,
        response: httpx.Response,
    ) -> APIStatusError:
        if response.status_code == 400:
            return _exceptions.BadRequestError(err_msg, response=response, body=body)

        if response.status_code == 401:
            return _exceptions.AuthenticationError(err_msg, response=response, body=body)

        if response.status_code == 403:
            return _exceptions.PermissionDeniedError(err_msg, response=response, body=body)

        if response.status_code == 404:
            return _exceptions.NotFoundError(err_msg, response=response, body=body)

        if response.status_code == 409:
            return _exceptions.ConflictError(err_msg, response=response, body=body)

        if response.status_code == 422:
            return _exceptions.UnprocessableEntityError(err_msg, response=response, body=body)

        if response.status_code == 429:
            return _exceptions.RateLimitError(err_msg, response=response, body=body)

        if response.status_code >= 500:
            return _exceptions.InternalServerError(err_msg, response=response, body=body)
        return APIStatusError(err_msg, response=response, body=body)


class AsyncExcaiSDK(AsyncAPIClient):
    assistants: assistants.AsyncAssistantsResource
    audio: audio.AsyncAudioResource
    batches: batches.AsyncBatchesResource
    chat: chat.AsyncChatResource
    completions: completions.AsyncCompletionsResource
    containers: containers.AsyncContainersResource
    conversations: conversations.AsyncConversationsResource
    embeddings: embeddings.AsyncEmbeddingsResource
    evals: evals.AsyncEvalsResource
    files: files.AsyncFilesResource
    fine_tuning: fine_tuning.AsyncFineTuningResource
    images: images.AsyncImagesResource
    models: models.AsyncModelsResource
    moderations: moderations.AsyncModerationsResource
    organization: organization.AsyncOrganizationResource
    realtime: realtime.AsyncRealtimeResource
    responses: responses.AsyncResponsesResource
    threads: threads.AsyncThreadsResource
    uploads: uploads.AsyncUploadsResource
    vector_stores: vector_stores.AsyncVectorStoresResource
    videos: videos.AsyncVideosResource
    chatkit: chatkit.AsyncChatkitResource
    with_raw_response: AsyncExcaiSDKWithRawResponse
    with_streaming_response: AsyncExcaiSDKWithStreamedResponse

    # client options
    api_key: str

    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str | httpx.URL | None = None,
        timeout: float | Timeout | None | NotGiven = not_given,
        max_retries: int = DEFAULT_MAX_RETRIES,
        default_headers: Mapping[str, str] | None = None,
        default_query: Mapping[str, object] | None = None,
        # Configure a custom httpx client.
        # We provide a `DefaultAsyncHttpxClient` class that you can pass to retain the default values we use for `limits`, `timeout` & `follow_redirects`.
        # See the [httpx documentation](https://www.python-httpx.org/api/#asyncclient) for more details.
        http_client: httpx.AsyncClient | None = None,
        # Enable or disable schema validation for data returned by the API.
        # When enabled an error APIResponseValidationError is raised
        # if the API responds with invalid data for the expected schema.
        #
        # This parameter may be removed or changed in the future.
        # If you rely on this feature, please open a GitHub issue
        # outlining your use-case to help us decide if it should be
        # part of our public interface in the future.
        _strict_response_validation: bool = False,
    ) -> None:
        """Construct a new async AsyncExcaiSDK client instance.

        This automatically infers the `api_key` argument from the `EXCAI_API_KEY` environment variable if it is not provided.
        """
        if api_key is None:
            api_key = os.environ.get("EXCAI_API_KEY")
        if api_key is None:
            raise ExcaiSDKError(
                "The api_key client option must be set either by passing api_key to the client or by setting the EXCAI_API_KEY environment variable"
            )
        self.api_key = api_key

        if base_url is None:
            base_url = os.environ.get("EXCAI_SDK_BASE_URL")
        if base_url is None:
            base_url = f"https://api-main.excai.ai/api/v1"

        super().__init__(
            version=__version__,
            base_url=base_url,
            max_retries=max_retries,
            timeout=timeout,
            http_client=http_client,
            custom_headers=default_headers,
            custom_query=default_query,
            _strict_response_validation=_strict_response_validation,
        )

        self.assistants = assistants.AsyncAssistantsResource(self)
        self.audio = audio.AsyncAudioResource(self)
        self.batches = batches.AsyncBatchesResource(self)
        self.chat = chat.AsyncChatResource(self)
        self.completions = completions.AsyncCompletionsResource(self)
        self.containers = containers.AsyncContainersResource(self)
        self.conversations = conversations.AsyncConversationsResource(self)
        self.embeddings = embeddings.AsyncEmbeddingsResource(self)
        self.evals = evals.AsyncEvalsResource(self)
        self.files = files.AsyncFilesResource(self)
        self.fine_tuning = fine_tuning.AsyncFineTuningResource(self)
        self.images = images.AsyncImagesResource(self)
        self.models = models.AsyncModelsResource(self)
        self.moderations = moderations.AsyncModerationsResource(self)
        self.organization = organization.AsyncOrganizationResource(self)
        self.realtime = realtime.AsyncRealtimeResource(self)
        self.responses = responses.AsyncResponsesResource(self)
        self.threads = threads.AsyncThreadsResource(self)
        self.uploads = uploads.AsyncUploadsResource(self)
        self.vector_stores = vector_stores.AsyncVectorStoresResource(self)
        self.videos = videos.AsyncVideosResource(self)
        self.chatkit = chatkit.AsyncChatkitResource(self)
        self.with_raw_response = AsyncExcaiSDKWithRawResponse(self)
        self.with_streaming_response = AsyncExcaiSDKWithStreamedResponse(self)

    @property
    @override
    def qs(self) -> Querystring:
        return Querystring(array_format="comma")

    @property
    @override
    def auth_headers(self) -> dict[str, str]:
        api_key = self.api_key
        return {"Authorization": f"Bearer {api_key}"}

    @property
    @override
    def default_headers(self) -> dict[str, str | Omit]:
        return {
            **super().default_headers,
            "X-Stainless-Async": f"async:{get_async_library()}",
            **self._custom_headers,
        }

    def copy(
        self,
        *,
        api_key: str | None = None,
        base_url: str | httpx.URL | None = None,
        timeout: float | Timeout | None | NotGiven = not_given,
        http_client: httpx.AsyncClient | None = None,
        max_retries: int | NotGiven = not_given,
        default_headers: Mapping[str, str] | None = None,
        set_default_headers: Mapping[str, str] | None = None,
        default_query: Mapping[str, object] | None = None,
        set_default_query: Mapping[str, object] | None = None,
        _extra_kwargs: Mapping[str, Any] = {},
    ) -> Self:
        """
        Create a new client instance re-using the same options given to the current client with optional overriding.
        """
        if default_headers is not None and set_default_headers is not None:
            raise ValueError("The `default_headers` and `set_default_headers` arguments are mutually exclusive")

        if default_query is not None and set_default_query is not None:
            raise ValueError("The `default_query` and `set_default_query` arguments are mutually exclusive")

        headers = self._custom_headers
        if default_headers is not None:
            headers = {**headers, **default_headers}
        elif set_default_headers is not None:
            headers = set_default_headers

        params = self._custom_query
        if default_query is not None:
            params = {**params, **default_query}
        elif set_default_query is not None:
            params = set_default_query

        http_client = http_client or self._client
        return self.__class__(
            api_key=api_key or self.api_key,
            base_url=base_url or self.base_url,
            timeout=self.timeout if isinstance(timeout, NotGiven) else timeout,
            http_client=http_client,
            max_retries=max_retries if is_given(max_retries) else self.max_retries,
            default_headers=headers,
            default_query=params,
            **_extra_kwargs,
        )

    # Alias for `copy` for nicer inline usage, e.g.
    # client.with_options(timeout=10).foo.create(...)
    with_options = copy

    @override
    def _make_status_error(
        self,
        err_msg: str,
        *,
        body: object,
        response: httpx.Response,
    ) -> APIStatusError:
        if response.status_code == 400:
            return _exceptions.BadRequestError(err_msg, response=response, body=body)

        if response.status_code == 401:
            return _exceptions.AuthenticationError(err_msg, response=response, body=body)

        if response.status_code == 403:
            return _exceptions.PermissionDeniedError(err_msg, response=response, body=body)

        if response.status_code == 404:
            return _exceptions.NotFoundError(err_msg, response=response, body=body)

        if response.status_code == 409:
            return _exceptions.ConflictError(err_msg, response=response, body=body)

        if response.status_code == 422:
            return _exceptions.UnprocessableEntityError(err_msg, response=response, body=body)

        if response.status_code == 429:
            return _exceptions.RateLimitError(err_msg, response=response, body=body)

        if response.status_code >= 500:
            return _exceptions.InternalServerError(err_msg, response=response, body=body)
        return APIStatusError(err_msg, response=response, body=body)


class ExcaiSDKWithRawResponse:
    def __init__(self, client: ExcaiSDK) -> None:
        self.assistants = assistants.AssistantsResourceWithRawResponse(client.assistants)
        self.audio = audio.AudioResourceWithRawResponse(client.audio)
        self.batches = batches.BatchesResourceWithRawResponse(client.batches)
        self.chat = chat.ChatResourceWithRawResponse(client.chat)
        self.completions = completions.CompletionsResourceWithRawResponse(client.completions)
        self.containers = containers.ContainersResourceWithRawResponse(client.containers)
        self.conversations = conversations.ConversationsResourceWithRawResponse(client.conversations)
        self.embeddings = embeddings.EmbeddingsResourceWithRawResponse(client.embeddings)
        self.evals = evals.EvalsResourceWithRawResponse(client.evals)
        self.files = files.FilesResourceWithRawResponse(client.files)
        self.fine_tuning = fine_tuning.FineTuningResourceWithRawResponse(client.fine_tuning)
        self.images = images.ImagesResourceWithRawResponse(client.images)
        self.models = models.ModelsResourceWithRawResponse(client.models)
        self.moderations = moderations.ModerationsResourceWithRawResponse(client.moderations)
        self.organization = organization.OrganizationResourceWithRawResponse(client.organization)
        self.realtime = realtime.RealtimeResourceWithRawResponse(client.realtime)
        self.responses = responses.ResponsesResourceWithRawResponse(client.responses)
        self.threads = threads.ThreadsResourceWithRawResponse(client.threads)
        self.uploads = uploads.UploadsResourceWithRawResponse(client.uploads)
        self.vector_stores = vector_stores.VectorStoresResourceWithRawResponse(client.vector_stores)
        self.videos = videos.VideosResourceWithRawResponse(client.videos)
        self.chatkit = chatkit.ChatkitResourceWithRawResponse(client.chatkit)


class AsyncExcaiSDKWithRawResponse:
    def __init__(self, client: AsyncExcaiSDK) -> None:
        self.assistants = assistants.AsyncAssistantsResourceWithRawResponse(client.assistants)
        self.audio = audio.AsyncAudioResourceWithRawResponse(client.audio)
        self.batches = batches.AsyncBatchesResourceWithRawResponse(client.batches)
        self.chat = chat.AsyncChatResourceWithRawResponse(client.chat)
        self.completions = completions.AsyncCompletionsResourceWithRawResponse(client.completions)
        self.containers = containers.AsyncContainersResourceWithRawResponse(client.containers)
        self.conversations = conversations.AsyncConversationsResourceWithRawResponse(client.conversations)
        self.embeddings = embeddings.AsyncEmbeddingsResourceWithRawResponse(client.embeddings)
        self.evals = evals.AsyncEvalsResourceWithRawResponse(client.evals)
        self.files = files.AsyncFilesResourceWithRawResponse(client.files)
        self.fine_tuning = fine_tuning.AsyncFineTuningResourceWithRawResponse(client.fine_tuning)
        self.images = images.AsyncImagesResourceWithRawResponse(client.images)
        self.models = models.AsyncModelsResourceWithRawResponse(client.models)
        self.moderations = moderations.AsyncModerationsResourceWithRawResponse(client.moderations)
        self.organization = organization.AsyncOrganizationResourceWithRawResponse(client.organization)
        self.realtime = realtime.AsyncRealtimeResourceWithRawResponse(client.realtime)
        self.responses = responses.AsyncResponsesResourceWithRawResponse(client.responses)
        self.threads = threads.AsyncThreadsResourceWithRawResponse(client.threads)
        self.uploads = uploads.AsyncUploadsResourceWithRawResponse(client.uploads)
        self.vector_stores = vector_stores.AsyncVectorStoresResourceWithRawResponse(client.vector_stores)
        self.videos = videos.AsyncVideosResourceWithRawResponse(client.videos)
        self.chatkit = chatkit.AsyncChatkitResourceWithRawResponse(client.chatkit)


class ExcaiSDKWithStreamedResponse:
    def __init__(self, client: ExcaiSDK) -> None:
        self.assistants = assistants.AssistantsResourceWithStreamingResponse(client.assistants)
        self.audio = audio.AudioResourceWithStreamingResponse(client.audio)
        self.batches = batches.BatchesResourceWithStreamingResponse(client.batches)
        self.chat = chat.ChatResourceWithStreamingResponse(client.chat)
        self.completions = completions.CompletionsResourceWithStreamingResponse(client.completions)
        self.containers = containers.ContainersResourceWithStreamingResponse(client.containers)
        self.conversations = conversations.ConversationsResourceWithStreamingResponse(client.conversations)
        self.embeddings = embeddings.EmbeddingsResourceWithStreamingResponse(client.embeddings)
        self.evals = evals.EvalsResourceWithStreamingResponse(client.evals)
        self.files = files.FilesResourceWithStreamingResponse(client.files)
        self.fine_tuning = fine_tuning.FineTuningResourceWithStreamingResponse(client.fine_tuning)
        self.images = images.ImagesResourceWithStreamingResponse(client.images)
        self.models = models.ModelsResourceWithStreamingResponse(client.models)
        self.moderations = moderations.ModerationsResourceWithStreamingResponse(client.moderations)
        self.organization = organization.OrganizationResourceWithStreamingResponse(client.organization)
        self.realtime = realtime.RealtimeResourceWithStreamingResponse(client.realtime)
        self.responses = responses.ResponsesResourceWithStreamingResponse(client.responses)
        self.threads = threads.ThreadsResourceWithStreamingResponse(client.threads)
        self.uploads = uploads.UploadsResourceWithStreamingResponse(client.uploads)
        self.vector_stores = vector_stores.VectorStoresResourceWithStreamingResponse(client.vector_stores)
        self.videos = videos.VideosResourceWithStreamingResponse(client.videos)
        self.chatkit = chatkit.ChatkitResourceWithStreamingResponse(client.chatkit)


class AsyncExcaiSDKWithStreamedResponse:
    def __init__(self, client: AsyncExcaiSDK) -> None:
        self.assistants = assistants.AsyncAssistantsResourceWithStreamingResponse(client.assistants)
        self.audio = audio.AsyncAudioResourceWithStreamingResponse(client.audio)
        self.batches = batches.AsyncBatchesResourceWithStreamingResponse(client.batches)
        self.chat = chat.AsyncChatResourceWithStreamingResponse(client.chat)
        self.completions = completions.AsyncCompletionsResourceWithStreamingResponse(client.completions)
        self.containers = containers.AsyncContainersResourceWithStreamingResponse(client.containers)
        self.conversations = conversations.AsyncConversationsResourceWithStreamingResponse(client.conversations)
        self.embeddings = embeddings.AsyncEmbeddingsResourceWithStreamingResponse(client.embeddings)
        self.evals = evals.AsyncEvalsResourceWithStreamingResponse(client.evals)
        self.files = files.AsyncFilesResourceWithStreamingResponse(client.files)
        self.fine_tuning = fine_tuning.AsyncFineTuningResourceWithStreamingResponse(client.fine_tuning)
        self.images = images.AsyncImagesResourceWithStreamingResponse(client.images)
        self.models = models.AsyncModelsResourceWithStreamingResponse(client.models)
        self.moderations = moderations.AsyncModerationsResourceWithStreamingResponse(client.moderations)
        self.organization = organization.AsyncOrganizationResourceWithStreamingResponse(client.organization)
        self.realtime = realtime.AsyncRealtimeResourceWithStreamingResponse(client.realtime)
        self.responses = responses.AsyncResponsesResourceWithStreamingResponse(client.responses)
        self.threads = threads.AsyncThreadsResourceWithStreamingResponse(client.threads)
        self.uploads = uploads.AsyncUploadsResourceWithStreamingResponse(client.uploads)
        self.vector_stores = vector_stores.AsyncVectorStoresResourceWithStreamingResponse(client.vector_stores)
        self.videos = videos.AsyncVideosResourceWithStreamingResponse(client.videos)
        self.chatkit = chatkit.AsyncChatkitResourceWithStreamingResponse(client.chatkit)


Client = ExcaiSDK

AsyncClient = AsyncExcaiSDK
