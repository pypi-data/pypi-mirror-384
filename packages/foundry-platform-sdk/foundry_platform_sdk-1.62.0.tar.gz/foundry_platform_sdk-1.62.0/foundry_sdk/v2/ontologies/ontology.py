#  Copyright 2024 Palantir Technologies, Inc.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.


import typing
from functools import cached_property

import pydantic
import typing_extensions

from foundry_sdk import _core as core
from foundry_sdk import _errors as errors
from foundry_sdk.v2.core import models as core_models
from foundry_sdk.v2.ontologies import models as ontologies_models


class OntologyClient:
    """
    The API client for the Ontology Resource.

    :param auth: Your auth configuration.
    :param hostname: Your Foundry hostname (for example, "myfoundry.palantirfoundry.com"). This can also include your API gateway service URI.
    :param config: Optionally specify the configuration for the HTTP session.
    """

    def __init__(
        self,
        auth: core.Auth,
        hostname: str,
        config: typing.Optional[core.Config] = None,
    ):
        self._auth = auth
        self._hostname = hostname
        self._config = config
        self._api_client = core.ApiClient(auth=auth, hostname=hostname, config=config)

        self.with_streaming_response = _OntologyClientStreaming(self)
        self.with_raw_response = _OntologyClientRaw(self)

    @cached_property
    def ActionType(self):
        from foundry_sdk.v2.ontologies.action_type import ActionTypeClient

        return ActionTypeClient(
            auth=self._auth,
            hostname=self._hostname,
            config=self._config,
        )

    @cached_property
    def ObjectType(self):
        from foundry_sdk.v2.ontologies.object_type import ObjectTypeClient

        return ObjectTypeClient(
            auth=self._auth,
            hostname=self._hostname,
            config=self._config,
        )

    @cached_property
    def QueryType(self):
        from foundry_sdk.v2.ontologies.query_type import QueryTypeClient

        return QueryTypeClient(
            auth=self._auth,
            hostname=self._hostname,
            config=self._config,
        )

    @core.maybe_ignore_preview
    @pydantic.validate_call
    @errors.handle_unexpected
    def get(
        self,
        ontology: ontologies_models.OntologyIdentifier,
        *,
        request_timeout: typing.Optional[core.Timeout] = None,
        _sdk_internal: core.SdkInternal = {},
    ) -> ontologies_models.OntologyV2:
        """
        Gets a specific ontology for a given Ontology API name or RID.

        :param ontology:
        :type ontology: OntologyIdentifier
        :param request_timeout: timeout setting for this request in seconds.
        :type request_timeout: Optional[int]
        :return: Returns the result object.
        :rtype: ontologies_models.OntologyV2
        """

        return self._api_client.call_api(
            core.RequestInfo(
                method="GET",
                resource_path="/v2/ontologies/{ontology}",
                query_params={},
                path_params={
                    "ontology": ontology,
                },
                header_params={
                    "Accept": "application/json",
                },
                body=None,
                response_type=ontologies_models.OntologyV2,
                request_timeout=request_timeout,
                throwable_errors={},
                response_mode=_sdk_internal.get("response_mode"),
            ),
        )

    @core.maybe_ignore_preview
    @pydantic.validate_call
    @errors.handle_unexpected
    def get_full_metadata(
        self,
        ontology: ontologies_models.OntologyIdentifier,
        *,
        branch: typing.Optional[core_models.FoundryBranch] = None,
        request_timeout: typing.Optional[core.Timeout] = None,
        _sdk_internal: core.SdkInternal = {},
    ) -> ontologies_models.OntologyFullMetadata:
        """
        Get the full Ontology metadata. This includes the objects, links, actions, queries, and interfaces.
        This endpoint is designed to return as much metadata as possible in a single request to support OSDK workflows.
        It may omit certain entities rather than fail the request.

        :param ontology:
        :type ontology: OntologyIdentifier
        :param branch: The Foundry branch to load metadata from. If not specified, the default branch will be used. Branches are an experimental feature and not all workflows are supported.
        :type branch: Optional[FoundryBranch]
        :param request_timeout: timeout setting for this request in seconds.
        :type request_timeout: Optional[int]
        :return: Returns the result object.
        :rtype: ontologies_models.OntologyFullMetadata
        """

        return self._api_client.call_api(
            core.RequestInfo(
                method="GET",
                resource_path="/v2/ontologies/{ontology}/fullMetadata",
                query_params={
                    "branch": branch,
                },
                path_params={
                    "ontology": ontology,
                },
                header_params={
                    "Accept": "application/json",
                },
                body=None,
                response_type=ontologies_models.OntologyFullMetadata,
                request_timeout=request_timeout,
                throwable_errors={},
                response_mode=_sdk_internal.get("response_mode"),
            ),
        )

    @core.maybe_ignore_preview
    @pydantic.validate_call
    @errors.handle_unexpected
    def list(
        self,
        *,
        request_timeout: typing.Optional[core.Timeout] = None,
        _sdk_internal: core.SdkInternal = {},
    ) -> ontologies_models.ListOntologiesV2Response:
        """
        Lists the Ontologies visible to the current user.

        :param request_timeout: timeout setting for this request in seconds.
        :type request_timeout: Optional[int]
        :return: Returns the result object.
        :rtype: ontologies_models.ListOntologiesV2Response
        """

        return self._api_client.call_api(
            core.RequestInfo(
                method="GET",
                resource_path="/v2/ontologies",
                query_params={},
                path_params={},
                header_params={
                    "Accept": "application/json",
                },
                body=None,
                response_type=ontologies_models.ListOntologiesV2Response,
                request_timeout=request_timeout,
                throwable_errors={},
                response_mode=_sdk_internal.get("response_mode"),
            ),
        )

    @core.maybe_ignore_preview
    @pydantic.validate_call
    @errors.handle_unexpected
    def load_metadata(
        self,
        ontology: ontologies_models.OntologyIdentifier,
        *,
        action_types: typing.List[ontologies_models.ActionTypeApiName],
        interface_types: typing.List[ontologies_models.InterfaceTypeApiName],
        link_types: typing.List[ontologies_models.LinkTypeApiName],
        object_types: typing.List[ontologies_models.ObjectTypeApiName],
        query_types: typing.List[ontologies_models.VersionedQueryTypeApiName],
        branch: typing.Optional[core_models.FoundryBranch] = None,
        preview: typing.Optional[core_models.PreviewMode] = None,
        request_timeout: typing.Optional[core.Timeout] = None,
        _sdk_internal: core.SdkInternal = {},
    ) -> ontologies_models.OntologyFullMetadata:
        """
        Load Ontology metadata for the requested object, link, action, query, and interface types.

        :param ontology:
        :type ontology: OntologyIdentifier
        :param action_types:
        :type action_types: List[ActionTypeApiName]
        :param interface_types:
        :type interface_types: List[InterfaceTypeApiName]
        :param link_types:
        :type link_types: List[LinkTypeApiName]
        :param object_types:
        :type object_types: List[ObjectTypeApiName]
        :param query_types:
        :type query_types: List[VersionedQueryTypeApiName]
        :param branch: The Foundry branch to load metadata from. If not specified, the default branch will be used. Branches are an experimental feature and not all workflows are supported.
        :type branch: Optional[FoundryBranch]
        :param preview: A boolean flag that, when set to true, enables the use of beta features in preview mode.
        :type preview: Optional[PreviewMode]
        :param request_timeout: timeout setting for this request in seconds.
        :type request_timeout: Optional[int]
        :return: Returns the result object.
        :rtype: ontologies_models.OntologyFullMetadata
        """

        return self._api_client.call_api(
            core.RequestInfo(
                method="POST",
                resource_path="/v2/ontologies/{ontology}/metadata",
                query_params={
                    "branch": branch,
                    "preview": preview,
                },
                path_params={
                    "ontology": ontology,
                },
                header_params={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
                body=ontologies_models.LoadOntologyMetadataRequest(
                    object_types=object_types,
                    link_types=link_types,
                    action_types=action_types,
                    query_types=query_types,
                    interface_types=interface_types,
                ),
                response_type=ontologies_models.OntologyFullMetadata,
                request_timeout=request_timeout,
                throwable_errors={},
                response_mode=_sdk_internal.get("response_mode"),
            ),
        )


class _OntologyClientRaw:
    def __init__(self, client: OntologyClient) -> None:
        def get(_: ontologies_models.OntologyV2): ...
        def get_full_metadata(_: ontologies_models.OntologyFullMetadata): ...
        def list(_: ontologies_models.ListOntologiesV2Response): ...
        def load_metadata(_: ontologies_models.OntologyFullMetadata): ...

        self.get = core.with_raw_response(get, client.get)
        self.get_full_metadata = core.with_raw_response(get_full_metadata, client.get_full_metadata)
        self.list = core.with_raw_response(list, client.list)
        self.load_metadata = core.with_raw_response(load_metadata, client.load_metadata)


class _OntologyClientStreaming:
    def __init__(self, client: OntologyClient) -> None:
        def get(_: ontologies_models.OntologyV2): ...
        def get_full_metadata(_: ontologies_models.OntologyFullMetadata): ...
        def list(_: ontologies_models.ListOntologiesV2Response): ...
        def load_metadata(_: ontologies_models.OntologyFullMetadata): ...

        self.get = core.with_streaming_response(get, client.get)
        self.get_full_metadata = core.with_streaming_response(
            get_full_metadata, client.get_full_metadata
        )
        self.list = core.with_streaming_response(list, client.list)
        self.load_metadata = core.with_streaming_response(load_metadata, client.load_metadata)


class AsyncOntologyClient:
    """
    The API client for the Ontology Resource.

    :param auth: Your auth configuration.
    :param hostname: Your Foundry hostname (for example, "myfoundry.palantirfoundry.com"). This can also include your API gateway service URI.
    :param config: Optionally specify the configuration for the HTTP session.
    """

    def __init__(
        self,
        auth: core.Auth,
        hostname: str,
        config: typing.Optional[core.Config] = None,
    ):
        self._auth = auth
        self._hostname = hostname
        self._config = config
        self._api_client = core.AsyncApiClient(auth=auth, hostname=hostname, config=config)

        self.with_streaming_response = _AsyncOntologyClientStreaming(self)
        self.with_raw_response = _AsyncOntologyClientRaw(self)

    @cached_property
    def ActionType(self):
        from foundry_sdk.v2.ontologies.action_type import AsyncActionTypeClient

        return AsyncActionTypeClient(
            auth=self._auth,
            hostname=self._hostname,
            config=self._config,
        )

    @cached_property
    def ObjectType(self):
        from foundry_sdk.v2.ontologies.object_type import AsyncObjectTypeClient

        return AsyncObjectTypeClient(
            auth=self._auth,
            hostname=self._hostname,
            config=self._config,
        )

    @cached_property
    def QueryType(self):
        from foundry_sdk.v2.ontologies.query_type import AsyncQueryTypeClient

        return AsyncQueryTypeClient(
            auth=self._auth,
            hostname=self._hostname,
            config=self._config,
        )

    @core.maybe_ignore_preview
    @pydantic.validate_call
    @errors.handle_unexpected
    def get(
        self,
        ontology: ontologies_models.OntologyIdentifier,
        *,
        request_timeout: typing.Optional[core.Timeout] = None,
        _sdk_internal: core.SdkInternal = {},
    ) -> typing.Awaitable[ontologies_models.OntologyV2]:
        """
        Gets a specific ontology for a given Ontology API name or RID.

        :param ontology:
        :type ontology: OntologyIdentifier
        :param request_timeout: timeout setting for this request in seconds.
        :type request_timeout: Optional[int]
        :return: Returns the result object.
        :rtype: typing.Awaitable[ontologies_models.OntologyV2]
        """

        return self._api_client.call_api(
            core.RequestInfo(
                method="GET",
                resource_path="/v2/ontologies/{ontology}",
                query_params={},
                path_params={
                    "ontology": ontology,
                },
                header_params={
                    "Accept": "application/json",
                },
                body=None,
                response_type=ontologies_models.OntologyV2,
                request_timeout=request_timeout,
                throwable_errors={},
                response_mode=_sdk_internal.get("response_mode"),
            ),
        )

    @core.maybe_ignore_preview
    @pydantic.validate_call
    @errors.handle_unexpected
    def get_full_metadata(
        self,
        ontology: ontologies_models.OntologyIdentifier,
        *,
        branch: typing.Optional[core_models.FoundryBranch] = None,
        request_timeout: typing.Optional[core.Timeout] = None,
        _sdk_internal: core.SdkInternal = {},
    ) -> typing.Awaitable[ontologies_models.OntologyFullMetadata]:
        """
        Get the full Ontology metadata. This includes the objects, links, actions, queries, and interfaces.
        This endpoint is designed to return as much metadata as possible in a single request to support OSDK workflows.
        It may omit certain entities rather than fail the request.

        :param ontology:
        :type ontology: OntologyIdentifier
        :param branch: The Foundry branch to load metadata from. If not specified, the default branch will be used. Branches are an experimental feature and not all workflows are supported.
        :type branch: Optional[FoundryBranch]
        :param request_timeout: timeout setting for this request in seconds.
        :type request_timeout: Optional[int]
        :return: Returns the result object.
        :rtype: typing.Awaitable[ontologies_models.OntologyFullMetadata]
        """

        return self._api_client.call_api(
            core.RequestInfo(
                method="GET",
                resource_path="/v2/ontologies/{ontology}/fullMetadata",
                query_params={
                    "branch": branch,
                },
                path_params={
                    "ontology": ontology,
                },
                header_params={
                    "Accept": "application/json",
                },
                body=None,
                response_type=ontologies_models.OntologyFullMetadata,
                request_timeout=request_timeout,
                throwable_errors={},
                response_mode=_sdk_internal.get("response_mode"),
            ),
        )

    @core.maybe_ignore_preview
    @pydantic.validate_call
    @errors.handle_unexpected
    def list(
        self,
        *,
        request_timeout: typing.Optional[core.Timeout] = None,
        _sdk_internal: core.SdkInternal = {},
    ) -> typing.Awaitable[ontologies_models.ListOntologiesV2Response]:
        """
        Lists the Ontologies visible to the current user.

        :param request_timeout: timeout setting for this request in seconds.
        :type request_timeout: Optional[int]
        :return: Returns the result object.
        :rtype: typing.Awaitable[ontologies_models.ListOntologiesV2Response]
        """

        return self._api_client.call_api(
            core.RequestInfo(
                method="GET",
                resource_path="/v2/ontologies",
                query_params={},
                path_params={},
                header_params={
                    "Accept": "application/json",
                },
                body=None,
                response_type=ontologies_models.ListOntologiesV2Response,
                request_timeout=request_timeout,
                throwable_errors={},
                response_mode=_sdk_internal.get("response_mode"),
            ),
        )

    @core.maybe_ignore_preview
    @pydantic.validate_call
    @errors.handle_unexpected
    def load_metadata(
        self,
        ontology: ontologies_models.OntologyIdentifier,
        *,
        action_types: typing.List[ontologies_models.ActionTypeApiName],
        interface_types: typing.List[ontologies_models.InterfaceTypeApiName],
        link_types: typing.List[ontologies_models.LinkTypeApiName],
        object_types: typing.List[ontologies_models.ObjectTypeApiName],
        query_types: typing.List[ontologies_models.VersionedQueryTypeApiName],
        branch: typing.Optional[core_models.FoundryBranch] = None,
        preview: typing.Optional[core_models.PreviewMode] = None,
        request_timeout: typing.Optional[core.Timeout] = None,
        _sdk_internal: core.SdkInternal = {},
    ) -> typing.Awaitable[ontologies_models.OntologyFullMetadata]:
        """
        Load Ontology metadata for the requested object, link, action, query, and interface types.

        :param ontology:
        :type ontology: OntologyIdentifier
        :param action_types:
        :type action_types: List[ActionTypeApiName]
        :param interface_types:
        :type interface_types: List[InterfaceTypeApiName]
        :param link_types:
        :type link_types: List[LinkTypeApiName]
        :param object_types:
        :type object_types: List[ObjectTypeApiName]
        :param query_types:
        :type query_types: List[VersionedQueryTypeApiName]
        :param branch: The Foundry branch to load metadata from. If not specified, the default branch will be used. Branches are an experimental feature and not all workflows are supported.
        :type branch: Optional[FoundryBranch]
        :param preview: A boolean flag that, when set to true, enables the use of beta features in preview mode.
        :type preview: Optional[PreviewMode]
        :param request_timeout: timeout setting for this request in seconds.
        :type request_timeout: Optional[int]
        :return: Returns the result object.
        :rtype: typing.Awaitable[ontologies_models.OntologyFullMetadata]
        """

        return self._api_client.call_api(
            core.RequestInfo(
                method="POST",
                resource_path="/v2/ontologies/{ontology}/metadata",
                query_params={
                    "branch": branch,
                    "preview": preview,
                },
                path_params={
                    "ontology": ontology,
                },
                header_params={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
                body=ontologies_models.LoadOntologyMetadataRequest(
                    object_types=object_types,
                    link_types=link_types,
                    action_types=action_types,
                    query_types=query_types,
                    interface_types=interface_types,
                ),
                response_type=ontologies_models.OntologyFullMetadata,
                request_timeout=request_timeout,
                throwable_errors={},
                response_mode=_sdk_internal.get("response_mode"),
            ),
        )


class _AsyncOntologyClientRaw:
    def __init__(self, client: AsyncOntologyClient) -> None:
        def get(_: ontologies_models.OntologyV2): ...
        def get_full_metadata(_: ontologies_models.OntologyFullMetadata): ...
        def list(_: ontologies_models.ListOntologiesV2Response): ...
        def load_metadata(_: ontologies_models.OntologyFullMetadata): ...

        self.get = core.async_with_raw_response(get, client.get)
        self.get_full_metadata = core.async_with_raw_response(
            get_full_metadata, client.get_full_metadata
        )
        self.list = core.async_with_raw_response(list, client.list)
        self.load_metadata = core.async_with_raw_response(load_metadata, client.load_metadata)


class _AsyncOntologyClientStreaming:
    def __init__(self, client: AsyncOntologyClient) -> None:
        def get(_: ontologies_models.OntologyV2): ...
        def get_full_metadata(_: ontologies_models.OntologyFullMetadata): ...
        def list(_: ontologies_models.ListOntologiesV2Response): ...
        def load_metadata(_: ontologies_models.OntologyFullMetadata): ...

        self.get = core.async_with_streaming_response(get, client.get)
        self.get_full_metadata = core.async_with_streaming_response(
            get_full_metadata, client.get_full_metadata
        )
        self.list = core.async_with_streaming_response(list, client.list)
        self.load_metadata = core.async_with_streaming_response(load_metadata, client.load_metadata)
