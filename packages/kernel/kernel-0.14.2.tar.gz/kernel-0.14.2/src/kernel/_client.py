# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, Dict, Mapping, cast
from typing_extensions import Self, Literal, override

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
from .resources import apps, proxies, profiles, extensions, deployments, invocations
from ._streaming import Stream as Stream, AsyncStream as AsyncStream
from ._exceptions import KernelError, APIStatusError
from ._base_client import (
    DEFAULT_MAX_RETRIES,
    SyncAPIClient,
    AsyncAPIClient,
)
from .resources.browsers import browsers

__all__ = [
    "ENVIRONMENTS",
    "Timeout",
    "Transport",
    "ProxiesTypes",
    "RequestOptions",
    "Kernel",
    "AsyncKernel",
    "Client",
    "AsyncClient",
]

ENVIRONMENTS: Dict[str, str] = {
    "production": "https://api.onkernel.com/",
    "development": "https://localhost:3001/",
}


class Kernel(SyncAPIClient):
    deployments: deployments.DeploymentsResource
    apps: apps.AppsResource
    invocations: invocations.InvocationsResource
    browsers: browsers.BrowsersResource
    profiles: profiles.ProfilesResource
    proxies: proxies.ProxiesResource
    extensions: extensions.ExtensionsResource
    with_raw_response: KernelWithRawResponse
    with_streaming_response: KernelWithStreamedResponse

    # client options
    api_key: str

    _environment: Literal["production", "development"] | NotGiven

    def __init__(
        self,
        *,
        api_key: str | None = None,
        environment: Literal["production", "development"] | NotGiven = not_given,
        base_url: str | httpx.URL | None | NotGiven = not_given,
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
        """Construct a new synchronous Kernel client instance.

        This automatically infers the `api_key` argument from the `KERNEL_API_KEY` environment variable if it is not provided.
        """
        if api_key is None:
            api_key = os.environ.get("KERNEL_API_KEY")
        if api_key is None:
            raise KernelError(
                "The api_key client option must be set either by passing api_key to the client or by setting the KERNEL_API_KEY environment variable"
            )
        self.api_key = api_key

        self._environment = environment

        base_url_env = os.environ.get("KERNEL_BASE_URL")
        if is_given(base_url) and base_url is not None:
            # cast required because mypy doesn't understand the type narrowing
            base_url = cast("str | httpx.URL", base_url)  # pyright: ignore[reportUnnecessaryCast]
        elif is_given(environment):
            if base_url_env and base_url is not None:
                raise ValueError(
                    "Ambiguous URL; The `KERNEL_BASE_URL` env var and the `environment` argument are given. If you want to use the environment, you must pass base_url=None",
                )

            try:
                base_url = ENVIRONMENTS[environment]
            except KeyError as exc:
                raise ValueError(f"Unknown environment: {environment}") from exc
        elif base_url_env is not None:
            base_url = base_url_env
        else:
            self._environment = environment = "production"

            try:
                base_url = ENVIRONMENTS[environment]
            except KeyError as exc:
                raise ValueError(f"Unknown environment: {environment}") from exc

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

        self.deployments = deployments.DeploymentsResource(self)
        self.apps = apps.AppsResource(self)
        self.invocations = invocations.InvocationsResource(self)
        self.browsers = browsers.BrowsersResource(self)
        self.profiles = profiles.ProfilesResource(self)
        self.proxies = proxies.ProxiesResource(self)
        self.extensions = extensions.ExtensionsResource(self)
        self.with_raw_response = KernelWithRawResponse(self)
        self.with_streaming_response = KernelWithStreamedResponse(self)

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
        environment: Literal["production", "development"] | None = None,
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
            environment=environment or self._environment,
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


class AsyncKernel(AsyncAPIClient):
    deployments: deployments.AsyncDeploymentsResource
    apps: apps.AsyncAppsResource
    invocations: invocations.AsyncInvocationsResource
    browsers: browsers.AsyncBrowsersResource
    profiles: profiles.AsyncProfilesResource
    proxies: proxies.AsyncProxiesResource
    extensions: extensions.AsyncExtensionsResource
    with_raw_response: AsyncKernelWithRawResponse
    with_streaming_response: AsyncKernelWithStreamedResponse

    # client options
    api_key: str

    _environment: Literal["production", "development"] | NotGiven

    def __init__(
        self,
        *,
        api_key: str | None = None,
        environment: Literal["production", "development"] | NotGiven = not_given,
        base_url: str | httpx.URL | None | NotGiven = not_given,
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
        """Construct a new async AsyncKernel client instance.

        This automatically infers the `api_key` argument from the `KERNEL_API_KEY` environment variable if it is not provided.
        """
        if api_key is None:
            api_key = os.environ.get("KERNEL_API_KEY")
        if api_key is None:
            raise KernelError(
                "The api_key client option must be set either by passing api_key to the client or by setting the KERNEL_API_KEY environment variable"
            )
        self.api_key = api_key

        self._environment = environment

        base_url_env = os.environ.get("KERNEL_BASE_URL")
        if is_given(base_url) and base_url is not None:
            # cast required because mypy doesn't understand the type narrowing
            base_url = cast("str | httpx.URL", base_url)  # pyright: ignore[reportUnnecessaryCast]
        elif is_given(environment):
            if base_url_env and base_url is not None:
                raise ValueError(
                    "Ambiguous URL; The `KERNEL_BASE_URL` env var and the `environment` argument are given. If you want to use the environment, you must pass base_url=None",
                )

            try:
                base_url = ENVIRONMENTS[environment]
            except KeyError as exc:
                raise ValueError(f"Unknown environment: {environment}") from exc
        elif base_url_env is not None:
            base_url = base_url_env
        else:
            self._environment = environment = "production"

            try:
                base_url = ENVIRONMENTS[environment]
            except KeyError as exc:
                raise ValueError(f"Unknown environment: {environment}") from exc

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

        self.deployments = deployments.AsyncDeploymentsResource(self)
        self.apps = apps.AsyncAppsResource(self)
        self.invocations = invocations.AsyncInvocationsResource(self)
        self.browsers = browsers.AsyncBrowsersResource(self)
        self.profiles = profiles.AsyncProfilesResource(self)
        self.proxies = proxies.AsyncProxiesResource(self)
        self.extensions = extensions.AsyncExtensionsResource(self)
        self.with_raw_response = AsyncKernelWithRawResponse(self)
        self.with_streaming_response = AsyncKernelWithStreamedResponse(self)

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
        environment: Literal["production", "development"] | None = None,
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
            environment=environment or self._environment,
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


class KernelWithRawResponse:
    def __init__(self, client: Kernel) -> None:
        self.deployments = deployments.DeploymentsResourceWithRawResponse(client.deployments)
        self.apps = apps.AppsResourceWithRawResponse(client.apps)
        self.invocations = invocations.InvocationsResourceWithRawResponse(client.invocations)
        self.browsers = browsers.BrowsersResourceWithRawResponse(client.browsers)
        self.profiles = profiles.ProfilesResourceWithRawResponse(client.profiles)
        self.proxies = proxies.ProxiesResourceWithRawResponse(client.proxies)
        self.extensions = extensions.ExtensionsResourceWithRawResponse(client.extensions)


class AsyncKernelWithRawResponse:
    def __init__(self, client: AsyncKernel) -> None:
        self.deployments = deployments.AsyncDeploymentsResourceWithRawResponse(client.deployments)
        self.apps = apps.AsyncAppsResourceWithRawResponse(client.apps)
        self.invocations = invocations.AsyncInvocationsResourceWithRawResponse(client.invocations)
        self.browsers = browsers.AsyncBrowsersResourceWithRawResponse(client.browsers)
        self.profiles = profiles.AsyncProfilesResourceWithRawResponse(client.profiles)
        self.proxies = proxies.AsyncProxiesResourceWithRawResponse(client.proxies)
        self.extensions = extensions.AsyncExtensionsResourceWithRawResponse(client.extensions)


class KernelWithStreamedResponse:
    def __init__(self, client: Kernel) -> None:
        self.deployments = deployments.DeploymentsResourceWithStreamingResponse(client.deployments)
        self.apps = apps.AppsResourceWithStreamingResponse(client.apps)
        self.invocations = invocations.InvocationsResourceWithStreamingResponse(client.invocations)
        self.browsers = browsers.BrowsersResourceWithStreamingResponse(client.browsers)
        self.profiles = profiles.ProfilesResourceWithStreamingResponse(client.profiles)
        self.proxies = proxies.ProxiesResourceWithStreamingResponse(client.proxies)
        self.extensions = extensions.ExtensionsResourceWithStreamingResponse(client.extensions)


class AsyncKernelWithStreamedResponse:
    def __init__(self, client: AsyncKernel) -> None:
        self.deployments = deployments.AsyncDeploymentsResourceWithStreamingResponse(client.deployments)
        self.apps = apps.AsyncAppsResourceWithStreamingResponse(client.apps)
        self.invocations = invocations.AsyncInvocationsResourceWithStreamingResponse(client.invocations)
        self.browsers = browsers.AsyncBrowsersResourceWithStreamingResponse(client.browsers)
        self.profiles = profiles.AsyncProfilesResourceWithStreamingResponse(client.profiles)
        self.proxies = proxies.AsyncProxiesResourceWithStreamingResponse(client.proxies)
        self.extensions = extensions.AsyncExtensionsResourceWithStreamingResponse(client.extensions)


Client = Kernel

AsyncClient = AsyncKernel
