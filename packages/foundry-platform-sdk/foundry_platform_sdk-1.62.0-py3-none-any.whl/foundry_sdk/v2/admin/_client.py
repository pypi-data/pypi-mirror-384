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

from foundry_sdk import _core as core


class AdminClient:
    """
    The API client for the Admin Namespace.

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

    @cached_property
    def Enrollment(self):
        from foundry_sdk.v2.admin.enrollment import EnrollmentClient

        return EnrollmentClient(
            auth=self._auth,
            hostname=self._hostname,
            config=self._config,
        )

    @cached_property
    def Group(self):
        from foundry_sdk.v2.admin.group import GroupClient

        return GroupClient(
            auth=self._auth,
            hostname=self._hostname,
            config=self._config,
        )

    @cached_property
    def Marking(self):
        from foundry_sdk.v2.admin.marking import MarkingClient

        return MarkingClient(
            auth=self._auth,
            hostname=self._hostname,
            config=self._config,
        )

    @cached_property
    def MarkingCategory(self):
        from foundry_sdk.v2.admin.marking_category import MarkingCategoryClient

        return MarkingCategoryClient(
            auth=self._auth,
            hostname=self._hostname,
            config=self._config,
        )

    @cached_property
    def Organization(self):
        from foundry_sdk.v2.admin.organization import OrganizationClient

        return OrganizationClient(
            auth=self._auth,
            hostname=self._hostname,
            config=self._config,
        )

    @cached_property
    def Role(self):
        from foundry_sdk.v2.admin.role import RoleClient

        return RoleClient(
            auth=self._auth,
            hostname=self._hostname,
            config=self._config,
        )

    @cached_property
    def User(self):
        from foundry_sdk.v2.admin.user import UserClient

        return UserClient(
            auth=self._auth,
            hostname=self._hostname,
            config=self._config,
        )


class AsyncAdminClient:
    """
    The Async API client for the Admin Namespace.

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
        from foundry_sdk.v2.admin.enrollment import AsyncEnrollmentClient
        from foundry_sdk.v2.admin.group import AsyncGroupClient
        from foundry_sdk.v2.admin.marking import AsyncMarkingClient
        from foundry_sdk.v2.admin.marking_category import AsyncMarkingCategoryClient
        from foundry_sdk.v2.admin.organization import AsyncOrganizationClient
        from foundry_sdk.v2.admin.role import AsyncRoleClient
        from foundry_sdk.v2.admin.user import AsyncUserClient

        self.Enrollment = AsyncEnrollmentClient(auth=auth, hostname=hostname, config=config)

        self.Group = AsyncGroupClient(auth=auth, hostname=hostname, config=config)

        self.Marking = AsyncMarkingClient(auth=auth, hostname=hostname, config=config)

        self.MarkingCategory = AsyncMarkingCategoryClient(
            auth=auth, hostname=hostname, config=config
        )

        self.Organization = AsyncOrganizationClient(auth=auth, hostname=hostname, config=config)

        self.Role = AsyncRoleClient(auth=auth, hostname=hostname, config=config)

        self.User = AsyncUserClient(auth=auth, hostname=hostname, config=config)
