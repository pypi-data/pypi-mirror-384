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

import pydantic
import typing_extensions

from foundry_sdk import _core as core
from foundry_sdk import _errors as errors
from foundry_sdk.v2.core import models as core_models
from foundry_sdk.v2.ontologies import models as ontologies_models


class MediaReferencePropertyClient:
    """
    The API client for the MediaReferenceProperty Resource.

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

        self.with_streaming_response = _MediaReferencePropertyClientStreaming(self)
        self.with_raw_response = _MediaReferencePropertyClientRaw(self)

    @core.maybe_ignore_preview
    @pydantic.validate_call
    @errors.handle_unexpected
    def get_media_content(
        self,
        ontology: ontologies_models.OntologyIdentifier,
        object_type: ontologies_models.ObjectTypeApiName,
        primary_key: ontologies_models.PropertyValueEscapedString,
        property: ontologies_models.PropertyApiName,
        *,
        preview: typing.Optional[core_models.PreviewMode] = None,
        sdk_package_rid: typing.Optional[ontologies_models.SdkPackageRid] = None,
        sdk_version: typing.Optional[ontologies_models.SdkVersion] = None,
        request_timeout: typing.Optional[core.Timeout] = None,
        _sdk_internal: core.SdkInternal = {},
    ) -> bytes:
        """
        Gets the content of a media item referenced by this property.

        :param ontology:
        :type ontology: OntologyIdentifier
        :param object_type: The API name of the object type. To find the API name, use the **List object types** endpoint or check the **Ontology Manager**.
        :type object_type: ObjectTypeApiName
        :param primary_key: The primary key of the object with the media reference property.
        :type primary_key: PropertyValueEscapedString
        :param property: The API name of the media reference property. To find the API name, check the **Ontology Manager** or use the **Get object type** endpoint.
        :type property: PropertyApiName
        :param preview: A boolean flag that, when set to true, enables the use of beta features in preview mode.
        :type preview: Optional[PreviewMode]
        :param sdk_package_rid: The package rid of the generated SDK.
        :type sdk_package_rid: Optional[SdkPackageRid]
        :param sdk_version: The version of the generated SDK.
        :type sdk_version: Optional[SdkVersion]
        :param request_timeout: timeout setting for this request in seconds.
        :type request_timeout: Optional[int]
        :return: Returns the result object.
        :rtype: bytes
        """

        return self._api_client.call_api(
            core.RequestInfo(
                method="GET",
                resource_path="/v2/ontologies/{ontology}/objects/{objectType}/{primaryKey}/media/{property}/content",
                query_params={
                    "preview": preview,
                    "sdkPackageRid": sdk_package_rid,
                    "sdkVersion": sdk_version,
                },
                path_params={
                    "ontology": ontology,
                    "objectType": object_type,
                    "primaryKey": primary_key,
                    "property": property,
                },
                header_params={
                    "Accept": "*/*",
                },
                body=None,
                response_type=bytes,
                request_timeout=request_timeout,
                throwable_errors={},
                response_mode=_sdk_internal.get("response_mode"),
            ),
        )

    @core.maybe_ignore_preview
    @pydantic.validate_call
    @errors.handle_unexpected
    def get_media_metadata(
        self,
        ontology: ontologies_models.OntologyIdentifier,
        object_type: ontologies_models.ObjectTypeApiName,
        primary_key: ontologies_models.PropertyValueEscapedString,
        property: ontologies_models.PropertyApiName,
        *,
        preview: typing.Optional[core_models.PreviewMode] = None,
        sdk_package_rid: typing.Optional[ontologies_models.SdkPackageRid] = None,
        sdk_version: typing.Optional[ontologies_models.SdkVersion] = None,
        request_timeout: typing.Optional[core.Timeout] = None,
        _sdk_internal: core.SdkInternal = {},
    ) -> ontologies_models.MediaMetadata:
        """
        Gets metadata about the media item referenced by this property.

        :param ontology:
        :type ontology: OntologyIdentifier
        :param object_type: The API name of the object type. To find the API name, use the **List object types** endpoint or check the **Ontology Manager**.
        :type object_type: ObjectTypeApiName
        :param primary_key: The primary key of the object with the media reference property.
        :type primary_key: PropertyValueEscapedString
        :param property: The API name of the media reference backed property. To find the API name, check the **Ontology Manager** or use the **Get object type** endpoint.
        :type property: PropertyApiName
        :param preview: A boolean flag that, when set to true, enables the use of beta features in preview mode.
        :type preview: Optional[PreviewMode]
        :param sdk_package_rid: The package rid of the generated SDK.
        :type sdk_package_rid: Optional[SdkPackageRid]
        :param sdk_version: The version of the generated SDK.
        :type sdk_version: Optional[SdkVersion]
        :param request_timeout: timeout setting for this request in seconds.
        :type request_timeout: Optional[int]
        :return: Returns the result object.
        :rtype: ontologies_models.MediaMetadata
        """

        return self._api_client.call_api(
            core.RequestInfo(
                method="GET",
                resource_path="/v2/ontologies/{ontology}/objects/{objectType}/{primaryKey}/media/{property}/metadata",
                query_params={
                    "preview": preview,
                    "sdkPackageRid": sdk_package_rid,
                    "sdkVersion": sdk_version,
                },
                path_params={
                    "ontology": ontology,
                    "objectType": object_type,
                    "primaryKey": primary_key,
                    "property": property,
                },
                header_params={
                    "Accept": "application/json",
                },
                body=None,
                response_type=ontologies_models.MediaMetadata,
                request_timeout=request_timeout,
                throwable_errors={},
                response_mode=_sdk_internal.get("response_mode"),
            ),
        )

    @core.maybe_ignore_preview
    @pydantic.validate_call
    @errors.handle_unexpected
    def upload(
        self,
        ontology: ontologies_models.OntologyIdentifier,
        object_type: ontologies_models.ObjectTypeApiName,
        property: ontologies_models.PropertyApiName,
        body: bytes,
        *,
        media_item_path: typing.Optional[core_models.MediaItemPath] = None,
        preview: typing.Optional[core_models.PreviewMode] = None,
        request_timeout: typing.Optional[core.Timeout] = None,
        _sdk_internal: core.SdkInternal = {},
    ) -> core_models.MediaReference:
        """
        Uploads a media item to the media set which backs the specified property.  The property must be backed by a single media set and branch, otherwise an error will be thrown.
        The body of the request must contain the binary content of the file and the `Content-Type` header must be `application/octet-stream`.

        :param ontology:
        :type ontology: OntologyIdentifier
        :param object_type: The API name of the object type. To find the API name, use the **List object types** endpoint or check the **Ontology Manager**.
        :type object_type: ObjectTypeApiName
        :param property: The API name of the media reference property. To find the API name, check the **Ontology Manager** or use the **Get object type** endpoint.
        :type property: PropertyApiName
        :param body: Body of the request
        :type body: bytes
        :param media_item_path: A path for the media item within its backing media set. Required if the backing media set requires paths.
        :type media_item_path: Optional[MediaItemPath]
        :param preview: A boolean flag that, when set to true, enables the use of beta features in preview mode.
        :type preview: Optional[PreviewMode]
        :param request_timeout: timeout setting for this request in seconds.
        :type request_timeout: Optional[int]
        :return: Returns the result object.
        :rtype: core_models.MediaReference
        """

        return self._api_client.call_api(
            core.RequestInfo(
                method="POST",
                resource_path="/v2/ontologies/{ontology}/objectTypes/{objectType}/media/{property}/upload",
                query_params={
                    "mediaItemPath": media_item_path,
                    "preview": preview,
                },
                path_params={
                    "ontology": ontology,
                    "objectType": object_type,
                    "property": property,
                },
                header_params={
                    "Content-Type": "*/*",
                    "Accept": "application/json",
                },
                body=body,
                response_type=core_models.MediaReference,
                request_timeout=request_timeout,
                throwable_errors={},
                response_mode=_sdk_internal.get("response_mode"),
            ),
        )

    @core.maybe_ignore_preview
    @pydantic.validate_call
    @errors.handle_unexpected
    def upload_media(
        self,
        ontology: ontologies_models.OntologyIdentifier,
        action_type: ontologies_models.ActionTypeApiName,
        body: bytes,
        *,
        media_item_path: typing.Optional[core_models.MediaItemPath] = None,
        preview: typing.Optional[core_models.PreviewMode] = None,
        request_timeout: typing.Optional[core.Timeout] = None,
        _sdk_internal: core.SdkInternal = {},
    ) -> core_models.MediaReference:
        """
        Uploads a media item for use by the specified action. If the media item isn't persisted by the associated action within 1 hour, the item will be deleted.

        The body of the request must contain the binary content of the file and the `Content-Type` header must be `application/octet-stream`.

        :param ontology:
        :type ontology: OntologyIdentifier
        :param action_type: The name of the action type in the API.
        :type action_type: ActionTypeApiName
        :param body: Body of the request
        :type body: bytes
        :param media_item_path: The path to write the media item to. Required if the backing media set requires paths.
        :type media_item_path: Optional[MediaItemPath]
        :param preview: A boolean flag that, when set to true, enables the use of beta features in preview mode.
        :type preview: Optional[PreviewMode]
        :param request_timeout: timeout setting for this request in seconds.
        :type request_timeout: Optional[int]
        :return: Returns the result object.
        :rtype: core_models.MediaReference
        """

        return self._api_client.call_api(
            core.RequestInfo(
                method="POST",
                resource_path="/v2/ontologies/{ontology}/actions/{actionType}/media/upload",
                query_params={
                    "mediaItemPath": media_item_path,
                    "preview": preview,
                },
                path_params={
                    "ontology": ontology,
                    "actionType": action_type,
                },
                header_params={
                    "Content-Type": "*/*",
                    "Accept": "application/json",
                },
                body=body,
                response_type=core_models.MediaReference,
                request_timeout=request_timeout,
                throwable_errors={},
                response_mode=_sdk_internal.get("response_mode"),
            ),
        )


class _MediaReferencePropertyClientRaw:
    def __init__(self, client: MediaReferencePropertyClient) -> None:
        def get_media_content(_: bytes): ...
        def get_media_metadata(_: ontologies_models.MediaMetadata): ...
        def upload(_: core_models.MediaReference): ...
        def upload_media(_: core_models.MediaReference): ...

        self.get_media_content = core.with_raw_response(get_media_content, client.get_media_content)
        self.get_media_metadata = core.with_raw_response(
            get_media_metadata, client.get_media_metadata
        )
        self.upload = core.with_raw_response(upload, client.upload)
        self.upload_media = core.with_raw_response(upload_media, client.upload_media)


class _MediaReferencePropertyClientStreaming:
    def __init__(self, client: MediaReferencePropertyClient) -> None:
        def get_media_content(_: bytes): ...
        def get_media_metadata(_: ontologies_models.MediaMetadata): ...
        def upload(_: core_models.MediaReference): ...
        def upload_media(_: core_models.MediaReference): ...

        self.get_media_content = core.with_streaming_response(
            get_media_content, client.get_media_content
        )
        self.get_media_metadata = core.with_streaming_response(
            get_media_metadata, client.get_media_metadata
        )
        self.upload = core.with_streaming_response(upload, client.upload)
        self.upload_media = core.with_streaming_response(upload_media, client.upload_media)


class AsyncMediaReferencePropertyClient:
    """
    The API client for the MediaReferenceProperty Resource.

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

        self.with_streaming_response = _AsyncMediaReferencePropertyClientStreaming(self)
        self.with_raw_response = _AsyncMediaReferencePropertyClientRaw(self)

    @core.maybe_ignore_preview
    @pydantic.validate_call
    @errors.handle_unexpected
    def get_media_content(
        self,
        ontology: ontologies_models.OntologyIdentifier,
        object_type: ontologies_models.ObjectTypeApiName,
        primary_key: ontologies_models.PropertyValueEscapedString,
        property: ontologies_models.PropertyApiName,
        *,
        preview: typing.Optional[core_models.PreviewMode] = None,
        sdk_package_rid: typing.Optional[ontologies_models.SdkPackageRid] = None,
        sdk_version: typing.Optional[ontologies_models.SdkVersion] = None,
        request_timeout: typing.Optional[core.Timeout] = None,
        _sdk_internal: core.SdkInternal = {},
    ) -> typing.Awaitable[bytes]:
        """
        Gets the content of a media item referenced by this property.

        :param ontology:
        :type ontology: OntologyIdentifier
        :param object_type: The API name of the object type. To find the API name, use the **List object types** endpoint or check the **Ontology Manager**.
        :type object_type: ObjectTypeApiName
        :param primary_key: The primary key of the object with the media reference property.
        :type primary_key: PropertyValueEscapedString
        :param property: The API name of the media reference property. To find the API name, check the **Ontology Manager** or use the **Get object type** endpoint.
        :type property: PropertyApiName
        :param preview: A boolean flag that, when set to true, enables the use of beta features in preview mode.
        :type preview: Optional[PreviewMode]
        :param sdk_package_rid: The package rid of the generated SDK.
        :type sdk_package_rid: Optional[SdkPackageRid]
        :param sdk_version: The version of the generated SDK.
        :type sdk_version: Optional[SdkVersion]
        :param request_timeout: timeout setting for this request in seconds.
        :type request_timeout: Optional[int]
        :return: Returns the result object.
        :rtype: typing.Awaitable[bytes]
        """

        return self._api_client.call_api(
            core.RequestInfo(
                method="GET",
                resource_path="/v2/ontologies/{ontology}/objects/{objectType}/{primaryKey}/media/{property}/content",
                query_params={
                    "preview": preview,
                    "sdkPackageRid": sdk_package_rid,
                    "sdkVersion": sdk_version,
                },
                path_params={
                    "ontology": ontology,
                    "objectType": object_type,
                    "primaryKey": primary_key,
                    "property": property,
                },
                header_params={
                    "Accept": "*/*",
                },
                body=None,
                response_type=bytes,
                request_timeout=request_timeout,
                throwable_errors={},
                response_mode=_sdk_internal.get("response_mode"),
            ),
        )

    @core.maybe_ignore_preview
    @pydantic.validate_call
    @errors.handle_unexpected
    def get_media_metadata(
        self,
        ontology: ontologies_models.OntologyIdentifier,
        object_type: ontologies_models.ObjectTypeApiName,
        primary_key: ontologies_models.PropertyValueEscapedString,
        property: ontologies_models.PropertyApiName,
        *,
        preview: typing.Optional[core_models.PreviewMode] = None,
        sdk_package_rid: typing.Optional[ontologies_models.SdkPackageRid] = None,
        sdk_version: typing.Optional[ontologies_models.SdkVersion] = None,
        request_timeout: typing.Optional[core.Timeout] = None,
        _sdk_internal: core.SdkInternal = {},
    ) -> typing.Awaitable[ontologies_models.MediaMetadata]:
        """
        Gets metadata about the media item referenced by this property.

        :param ontology:
        :type ontology: OntologyIdentifier
        :param object_type: The API name of the object type. To find the API name, use the **List object types** endpoint or check the **Ontology Manager**.
        :type object_type: ObjectTypeApiName
        :param primary_key: The primary key of the object with the media reference property.
        :type primary_key: PropertyValueEscapedString
        :param property: The API name of the media reference backed property. To find the API name, check the **Ontology Manager** or use the **Get object type** endpoint.
        :type property: PropertyApiName
        :param preview: A boolean flag that, when set to true, enables the use of beta features in preview mode.
        :type preview: Optional[PreviewMode]
        :param sdk_package_rid: The package rid of the generated SDK.
        :type sdk_package_rid: Optional[SdkPackageRid]
        :param sdk_version: The version of the generated SDK.
        :type sdk_version: Optional[SdkVersion]
        :param request_timeout: timeout setting for this request in seconds.
        :type request_timeout: Optional[int]
        :return: Returns the result object.
        :rtype: typing.Awaitable[ontologies_models.MediaMetadata]
        """

        return self._api_client.call_api(
            core.RequestInfo(
                method="GET",
                resource_path="/v2/ontologies/{ontology}/objects/{objectType}/{primaryKey}/media/{property}/metadata",
                query_params={
                    "preview": preview,
                    "sdkPackageRid": sdk_package_rid,
                    "sdkVersion": sdk_version,
                },
                path_params={
                    "ontology": ontology,
                    "objectType": object_type,
                    "primaryKey": primary_key,
                    "property": property,
                },
                header_params={
                    "Accept": "application/json",
                },
                body=None,
                response_type=ontologies_models.MediaMetadata,
                request_timeout=request_timeout,
                throwable_errors={},
                response_mode=_sdk_internal.get("response_mode"),
            ),
        )

    @core.maybe_ignore_preview
    @pydantic.validate_call
    @errors.handle_unexpected
    def upload(
        self,
        ontology: ontologies_models.OntologyIdentifier,
        object_type: ontologies_models.ObjectTypeApiName,
        property: ontologies_models.PropertyApiName,
        body: bytes,
        *,
        media_item_path: typing.Optional[core_models.MediaItemPath] = None,
        preview: typing.Optional[core_models.PreviewMode] = None,
        request_timeout: typing.Optional[core.Timeout] = None,
        _sdk_internal: core.SdkInternal = {},
    ) -> typing.Awaitable[core_models.MediaReference]:
        """
        Uploads a media item to the media set which backs the specified property.  The property must be backed by a single media set and branch, otherwise an error will be thrown.
        The body of the request must contain the binary content of the file and the `Content-Type` header must be `application/octet-stream`.

        :param ontology:
        :type ontology: OntologyIdentifier
        :param object_type: The API name of the object type. To find the API name, use the **List object types** endpoint or check the **Ontology Manager**.
        :type object_type: ObjectTypeApiName
        :param property: The API name of the media reference property. To find the API name, check the **Ontology Manager** or use the **Get object type** endpoint.
        :type property: PropertyApiName
        :param body: Body of the request
        :type body: bytes
        :param media_item_path: A path for the media item within its backing media set. Required if the backing media set requires paths.
        :type media_item_path: Optional[MediaItemPath]
        :param preview: A boolean flag that, when set to true, enables the use of beta features in preview mode.
        :type preview: Optional[PreviewMode]
        :param request_timeout: timeout setting for this request in seconds.
        :type request_timeout: Optional[int]
        :return: Returns the result object.
        :rtype: typing.Awaitable[core_models.MediaReference]
        """

        return self._api_client.call_api(
            core.RequestInfo(
                method="POST",
                resource_path="/v2/ontologies/{ontology}/objectTypes/{objectType}/media/{property}/upload",
                query_params={
                    "mediaItemPath": media_item_path,
                    "preview": preview,
                },
                path_params={
                    "ontology": ontology,
                    "objectType": object_type,
                    "property": property,
                },
                header_params={
                    "Content-Type": "*/*",
                    "Accept": "application/json",
                },
                body=body,
                response_type=core_models.MediaReference,
                request_timeout=request_timeout,
                throwable_errors={},
                response_mode=_sdk_internal.get("response_mode"),
            ),
        )

    @core.maybe_ignore_preview
    @pydantic.validate_call
    @errors.handle_unexpected
    def upload_media(
        self,
        ontology: ontologies_models.OntologyIdentifier,
        action_type: ontologies_models.ActionTypeApiName,
        body: bytes,
        *,
        media_item_path: typing.Optional[core_models.MediaItemPath] = None,
        preview: typing.Optional[core_models.PreviewMode] = None,
        request_timeout: typing.Optional[core.Timeout] = None,
        _sdk_internal: core.SdkInternal = {},
    ) -> typing.Awaitable[core_models.MediaReference]:
        """
        Uploads a media item for use by the specified action. If the media item isn't persisted by the associated action within 1 hour, the item will be deleted.

        The body of the request must contain the binary content of the file and the `Content-Type` header must be `application/octet-stream`.

        :param ontology:
        :type ontology: OntologyIdentifier
        :param action_type: The name of the action type in the API.
        :type action_type: ActionTypeApiName
        :param body: Body of the request
        :type body: bytes
        :param media_item_path: The path to write the media item to. Required if the backing media set requires paths.
        :type media_item_path: Optional[MediaItemPath]
        :param preview: A boolean flag that, when set to true, enables the use of beta features in preview mode.
        :type preview: Optional[PreviewMode]
        :param request_timeout: timeout setting for this request in seconds.
        :type request_timeout: Optional[int]
        :return: Returns the result object.
        :rtype: typing.Awaitable[core_models.MediaReference]
        """

        return self._api_client.call_api(
            core.RequestInfo(
                method="POST",
                resource_path="/v2/ontologies/{ontology}/actions/{actionType}/media/upload",
                query_params={
                    "mediaItemPath": media_item_path,
                    "preview": preview,
                },
                path_params={
                    "ontology": ontology,
                    "actionType": action_type,
                },
                header_params={
                    "Content-Type": "*/*",
                    "Accept": "application/json",
                },
                body=body,
                response_type=core_models.MediaReference,
                request_timeout=request_timeout,
                throwable_errors={},
                response_mode=_sdk_internal.get("response_mode"),
            ),
        )


class _AsyncMediaReferencePropertyClientRaw:
    def __init__(self, client: AsyncMediaReferencePropertyClient) -> None:
        def get_media_content(_: bytes): ...
        def get_media_metadata(_: ontologies_models.MediaMetadata): ...
        def upload(_: core_models.MediaReference): ...
        def upload_media(_: core_models.MediaReference): ...

        self.get_media_content = core.async_with_raw_response(
            get_media_content, client.get_media_content
        )
        self.get_media_metadata = core.async_with_raw_response(
            get_media_metadata, client.get_media_metadata
        )
        self.upload = core.async_with_raw_response(upload, client.upload)
        self.upload_media = core.async_with_raw_response(upload_media, client.upload_media)


class _AsyncMediaReferencePropertyClientStreaming:
    def __init__(self, client: AsyncMediaReferencePropertyClient) -> None:
        def get_media_content(_: bytes): ...
        def get_media_metadata(_: ontologies_models.MediaMetadata): ...
        def upload(_: core_models.MediaReference): ...
        def upload_media(_: core_models.MediaReference): ...

        self.get_media_content = core.async_with_streaming_response(
            get_media_content, client.get_media_content
        )
        self.get_media_metadata = core.async_with_streaming_response(
            get_media_metadata, client.get_media_metadata
        )
        self.upload = core.async_with_streaming_response(upload, client.upload)
        self.upload_media = core.async_with_streaming_response(upload_media, client.upload_media)
