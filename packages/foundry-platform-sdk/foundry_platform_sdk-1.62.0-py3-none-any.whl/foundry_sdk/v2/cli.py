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


from __future__ import annotations

import dataclasses
import io
import json
import os
import typing
from datetime import datetime

import click

from foundry_sdk import EnvironmentNotConfigured
from foundry_sdk import UserTokenAuth
from foundry_sdk.v2 import FoundryClient


@dataclasses.dataclass
class _Context:
    obj: FoundryClient


def get_from_environ(key: str) -> str:
    value = os.environ.get(key)
    if value is None:
        raise EnvironmentNotConfigured(f"Please set {key} using `export {key}=<{key}>`")

    return value


@click.group()  # type: ignore
@click.pass_context  # type: ignore
def cli(ctx: _Context):
    """An experimental CLI for the Foundry API"""
    ctx.obj = FoundryClient(
        auth=UserTokenAuth(token=get_from_environ("FOUNDRY_TOKEN")),
        hostname=get_from_environ("FOUNDRY_HOSTNAME"),
    )


@cli.group("admin")
def admin():
    pass


@admin.group("user")
def admin_user():
    pass


@admin_user.command("delete")
@click.argument("user_id", type=str, required=True)
@click.pass_obj
def admin_user_op_delete(
    client: FoundryClient,
    user_id: str,
):
    """
    Delete the User with the specified id.
    """
    result = client.admin.User.delete(
        user_id=user_id,
    )
    click.echo(repr(result))


@admin_user.command("get")
@click.argument("user_id", type=str, required=True)
@click.option("--status", type=click.Choice(["ACTIVE", "DELETED"]), required=False, help="""""")
@click.pass_obj
def admin_user_op_get(
    client: FoundryClient,
    user_id: str,
    status: typing.Optional[typing.Literal["ACTIVE", "DELETED"]],
):
    """
    Get the User with the specified id.
    """
    result = client.admin.User.get(
        user_id=user_id,
        status=status,
    )
    click.echo(repr(result))


@admin_user.command("get_batch")
@click.argument("body", type=str, required=True)
@click.pass_obj
def admin_user_op_get_batch(
    client: FoundryClient,
    body: str,
):
    """
    Execute multiple get requests on User.

    The maximum batch size for this endpoint is 500.
    """
    result = client.admin.User.get_batch(
        body=json.loads(body),
    )
    click.echo(repr(result))


@admin_user.command("get_current")
@click.pass_obj
def admin_user_op_get_current(
    client: FoundryClient,
):
    """ """
    result = client.admin.User.get_current()
    click.echo(repr(result))


@admin_user.command("get_markings")
@click.argument("user_id", type=str, required=True)
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.pass_obj
def admin_user_op_get_markings(
    client: FoundryClient,
    user_id: str,
    preview: typing.Optional[bool],
):
    """
    Retrieve Markings that the user is currently a member of.
    """
    result = client.admin.User.get_markings(
        user_id=user_id,
        preview=preview,
    )
    click.echo(repr(result))


@admin_user.command("list")
@click.option("--include", type=click.Choice(["ACTIVE", "DELETED"]), required=False, help="""""")
@click.option(
    "--page_size", type=int, required=False, help="""The page size to use for the endpoint."""
)
@click.option(
    "--page_token",
    type=str,
    required=False,
    help="""The page token indicates where to start paging. This should be omitted from the first page's request.
To fetch the next page, clients should take the value from the `nextPageToken` field of the previous response
and use it to populate the `pageToken` field of the next request.""",
)
@click.pass_obj
def admin_user_op_list(
    client: FoundryClient,
    include: typing.Optional[typing.Literal["ACTIVE", "DELETED"]],
    page_size: typing.Optional[int],
    page_token: typing.Optional[str],
):
    """
    Lists all Users.

    This is a paged endpoint. Each page may be smaller or larger than the requested page size. However, it is guaranteed that if there are more results available, the `nextPageToken` field will be populated. To get the next page, make the same request again, but set the value of the `pageToken` query parameter to be value of the `nextPageToken` value of the previous response. If there is no `nextPageToken` field in the response, you are on the last page.
    """
    result = client.admin.User.list(
        include=include,
        page_size=page_size,
        page_token=page_token,
    )
    click.echo(repr(result))


@admin_user.command("profile_picture")
@click.argument("user_id", type=str, required=True)
@click.pass_obj
def admin_user_op_profile_picture(
    client: FoundryClient,
    user_id: str,
):
    """ """
    result = client.admin.User.profile_picture(
        user_id=user_id,
    )
    click.echo(repr(result))


@admin_user.command("revoke_all_tokens")
@click.argument("user_id", type=str, required=True)
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.pass_obj
def admin_user_op_revoke_all_tokens(
    client: FoundryClient,
    user_id: str,
    preview: typing.Optional[bool],
):
    """
    Revoke all active authentication tokens for the user including active browser sessions and long-lived
    development tokens. If the user has active sessions in a browser, this will force re-authentication.

    The caller must have permission to manage users for the target user's organization.

    """
    result = client.admin.User.revoke_all_tokens(
        user_id=user_id,
        preview=preview,
    )
    click.echo(repr(result))


@admin_user.command("search")
@click.option("--where", type=str, required=True, help="""""")
@click.option("--page_size", type=int, required=False, help="""""")
@click.option("--page_token", type=str, required=False, help="""""")
@click.pass_obj
def admin_user_op_search(
    client: FoundryClient,
    where: str,
    page_size: typing.Optional[int],
    page_token: typing.Optional[str],
):
    """
    Perform a case-insensitive prefix search for users based on username, given name and family name.

    """
    result = client.admin.User.search(
        where=json.loads(where),
        page_size=page_size,
        page_token=page_token,
    )
    click.echo(repr(result))


@admin_user.group("group_membership")
def admin_user_group_membership():
    pass


@admin_user_group_membership.command("list")
@click.argument("user_id", type=str, required=True)
@click.option(
    "--page_size", type=int, required=False, help="""The page size to use for the endpoint."""
)
@click.option(
    "--page_token",
    type=str,
    required=False,
    help="""The page token indicates where to start paging. This should be omitted from the first page's request.
To fetch the next page, clients should take the value from the `nextPageToken` field of the previous response
and use it to populate the `pageToken` field of the next request.""",
)
@click.option(
    "--transitive",
    type=bool,
    required=False,
    help="""When true, includes the transitive memberships of the Groups the User is a member of. For example, say the
User is a member of Group A, and Group A is a member of Group B. If `transitive=false` only Group A will
be returned, but if `transitive=true` then Groups A and B will be returned. This
will recursively resolve Groups through all layers of nesting.

Defaults to false.
""",
)
@click.pass_obj
def admin_user_group_membership_op_list(
    client: FoundryClient,
    user_id: str,
    page_size: typing.Optional[int],
    page_token: typing.Optional[str],
    transitive: typing.Optional[bool],
):
    """
    Lists all Groups a given User is a member of.

    This is a paged endpoint. Each page may be smaller or larger than the requested page size. However,
    it is guaranteed that if there are more results available, the `nextPageToken` field will be populated.
    To get the next page, make the same request again, but set the value of the `pageToken` query parameter
    to be value of the `nextPageToken` value of the previous response. If there is no `nextPageToken` field
    in the response, you are on the last page.

    """
    result = client.admin.User.GroupMembership.list(
        user_id=user_id,
        page_size=page_size,
        page_token=page_token,
        transitive=transitive,
    )
    click.echo(repr(result))


@admin_user.group("user_provider_info")
def admin_user_user_provider_info():
    pass


@admin_user_user_provider_info.command("get")
@click.argument("user_id", type=str, required=True)
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.pass_obj
def admin_user_user_provider_info_op_get(
    client: FoundryClient,
    user_id: str,
    preview: typing.Optional[bool],
):
    """
    Get the UserProviderInfo.
    """
    result = client.admin.User.ProviderInfo.get(
        user_id=user_id,
        preview=preview,
    )
    click.echo(repr(result))


@admin_user_user_provider_info.command("replace")
@click.argument("user_id", type=str, required=True)
@click.option(
    "--provider_id",
    type=str,
    required=True,
    help="""The ID of the User in the external authentication provider. This value is determined by the authentication provider.
At most one User can have a given provider ID in a given Realm.
""",
)
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.pass_obj
def admin_user_user_provider_info_op_replace(
    client: FoundryClient,
    user_id: str,
    provider_id: str,
    preview: typing.Optional[bool],
):
    """
    Replace the UserProviderInfo.
    """
    result = client.admin.User.ProviderInfo.replace(
        user_id=user_id,
        provider_id=provider_id,
        preview=preview,
    )
    click.echo(repr(result))


@admin.group("role")
def admin_role():
    pass


@admin_role.command("get")
@click.argument("role_id", type=str, required=True)
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.pass_obj
def admin_role_op_get(
    client: FoundryClient,
    role_id: str,
    preview: typing.Optional[bool],
):
    """
    Get the Role with the specified id.
    """
    result = client.admin.Role.get(
        role_id=role_id,
        preview=preview,
    )
    click.echo(repr(result))


@admin_role.command("get_batch")
@click.argument("body", type=str, required=True)
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.pass_obj
def admin_role_op_get_batch(
    client: FoundryClient,
    body: str,
    preview: typing.Optional[bool],
):
    """
    Execute multiple get requests on Role.

    The maximum batch size for this endpoint is 500.
    """
    result = client.admin.Role.get_batch(
        body=json.loads(body),
        preview=preview,
    )
    click.echo(repr(result))


@admin.group("organization")
def admin_organization():
    pass


@admin_organization.command("create")
@click.option(
    "--administrators",
    type=str,
    required=True,
    help="""The initial administrators of the Organization. At least one principal must be provided.
""",
)
@click.option(
    "--enrollment_rid",
    type=str,
    required=True,
    help="""The RID of the Enrollment that this Organization belongs to. This must be provided.
""",
)
@click.option("--name", type=str, required=True, help="""""")
@click.option("--description", type=str, required=False, help="""""")
@click.option(
    "--host",
    type=str,
    required=False,
    help="""The primary host name of the Organization. This should be used when constructing URLs for users of this
Organization.
""",
)
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.pass_obj
def admin_organization_op_create(
    client: FoundryClient,
    administrators: str,
    enrollment_rid: str,
    name: str,
    description: typing.Optional[str],
    host: typing.Optional[str],
    preview: typing.Optional[bool],
):
    """
    Creates a new Organization.
    """
    result = client.admin.Organization.create(
        administrators=json.loads(administrators),
        enrollment_rid=enrollment_rid,
        name=name,
        description=description,
        host=host,
        preview=preview,
    )
    click.echo(repr(result))


@admin_organization.command("get")
@click.argument("organization_rid", type=str, required=True)
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.pass_obj
def admin_organization_op_get(
    client: FoundryClient,
    organization_rid: str,
    preview: typing.Optional[bool],
):
    """
    Get the Organization with the specified rid.
    """
    result = client.admin.Organization.get(
        organization_rid=organization_rid,
        preview=preview,
    )
    click.echo(repr(result))


@admin_organization.command("list_available_roles")
@click.argument("organization_rid", type=str, required=True)
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.pass_obj
def admin_organization_op_list_available_roles(
    client: FoundryClient,
    organization_rid: str,
    preview: typing.Optional[bool],
):
    """
    List all roles that can be assigned to a principal for the given Organization.

    """
    result = client.admin.Organization.list_available_roles(
        organization_rid=organization_rid,
        preview=preview,
    )
    click.echo(repr(result))


@admin_organization.command("replace")
@click.argument("organization_rid", type=str, required=True)
@click.option("--name", type=str, required=True, help="""""")
@click.option("--description", type=str, required=False, help="""""")
@click.option(
    "--host",
    type=str,
    required=False,
    help="""The primary host name of the Organization. This should be used when constructing URLs for users of this
Organization.
""",
)
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.pass_obj
def admin_organization_op_replace(
    client: FoundryClient,
    organization_rid: str,
    name: str,
    description: typing.Optional[str],
    host: typing.Optional[str],
    preview: typing.Optional[bool],
):
    """
    Replace the Organization with the specified rid.
    """
    result = client.admin.Organization.replace(
        organization_rid=organization_rid,
        name=name,
        description=description,
        host=host,
        preview=preview,
    )
    click.echo(repr(result))


@admin_organization.group("organization_role_assignment")
def admin_organization_organization_role_assignment():
    pass


@admin_organization_organization_role_assignment.command("add")
@click.argument("organization_rid", type=str, required=True)
@click.option("--role_assignments", type=str, required=True, help="""""")
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.pass_obj
def admin_organization_organization_role_assignment_op_add(
    client: FoundryClient,
    organization_rid: str,
    role_assignments: str,
    preview: typing.Optional[bool],
):
    """
    Assign roles to principals for the given Organization. At most 100 role assignments can be added in a single request.

    """
    result = client.admin.Organization.OrganizationRoleAssignment.add(
        organization_rid=organization_rid,
        role_assignments=json.loads(role_assignments),
        preview=preview,
    )
    click.echo(repr(result))


@admin_organization_organization_role_assignment.command("list")
@click.argument("organization_rid", type=str, required=True)
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.pass_obj
def admin_organization_organization_role_assignment_op_list(
    client: FoundryClient,
    organization_rid: str,
    preview: typing.Optional[bool],
):
    """
    List all principals who are assigned a role for the given Organization.

    """
    result = client.admin.Organization.OrganizationRoleAssignment.list(
        organization_rid=organization_rid,
        preview=preview,
    )
    click.echo(repr(result))


@admin_organization_organization_role_assignment.command("remove")
@click.argument("organization_rid", type=str, required=True)
@click.option("--role_assignments", type=str, required=True, help="""""")
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.pass_obj
def admin_organization_organization_role_assignment_op_remove(
    client: FoundryClient,
    organization_rid: str,
    role_assignments: str,
    preview: typing.Optional[bool],
):
    """
    Remove roles from principals for the given Organization. At most 100 role assignments can be removed in a single request.

    """
    result = client.admin.Organization.OrganizationRoleAssignment.remove(
        organization_rid=organization_rid,
        role_assignments=json.loads(role_assignments),
        preview=preview,
    )
    click.echo(repr(result))


@admin.group("marking_category")
def admin_marking_category():
    pass


@admin_marking_category.command("get")
@click.argument("marking_category_id", type=str, required=True)
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.pass_obj
def admin_marking_category_op_get(
    client: FoundryClient,
    marking_category_id: str,
    preview: typing.Optional[bool],
):
    """
    Get the MarkingCategory with the specified id.
    """
    result = client.admin.MarkingCategory.get(
        marking_category_id=marking_category_id,
        preview=preview,
    )
    click.echo(repr(result))


@admin_marking_category.command("list")
@click.option(
    "--page_size", type=int, required=False, help="""The page size to use for the endpoint."""
)
@click.option(
    "--page_token",
    type=str,
    required=False,
    help="""The page token indicates where to start paging. This should be omitted from the first page's request.
To fetch the next page, clients should take the value from the `nextPageToken` field of the previous response
and use it to populate the `pageToken` field of the next request.""",
)
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.pass_obj
def admin_marking_category_op_list(
    client: FoundryClient,
    page_size: typing.Optional[int],
    page_token: typing.Optional[str],
    preview: typing.Optional[bool],
):
    """
    Maximum page size 100.
    """
    result = client.admin.MarkingCategory.list(
        page_size=page_size,
        page_token=page_token,
        preview=preview,
    )
    click.echo(repr(result))


@admin.group("marking")
def admin_marking():
    pass


@admin_marking.command("create")
@click.option("--category_id", type=str, required=True, help="""""")
@click.option(
    "--initial_members",
    type=str,
    required=True,
    help="""Users and Groups that will be able to view resources protected by this Marking. This can be changed later through the MarkingMember operations.
""",
)
@click.option(
    "--initial_role_assignments",
    type=str,
    required=True,
    help="""The initial roles that will be assigned when the Marking is created. At least one ADMIN role must be
provided. This can be changed later through the MarkingRoleAssignment operations.

WARNING: If you do not include your own principal ID or the ID of a Group that you are a member of,
you will create a Marking that you cannot administer.
""",
)
@click.option("--name", type=str, required=True, help="""""")
@click.option("--description", type=str, required=False, help="""""")
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.pass_obj
def admin_marking_op_create(
    client: FoundryClient,
    category_id: str,
    initial_members: str,
    initial_role_assignments: str,
    name: str,
    description: typing.Optional[str],
    preview: typing.Optional[bool],
):
    """
    Creates a new Marking.
    """
    result = client.admin.Marking.create(
        category_id=category_id,
        initial_members=json.loads(initial_members),
        initial_role_assignments=json.loads(initial_role_assignments),
        name=name,
        description=description,
        preview=preview,
    )
    click.echo(repr(result))


@admin_marking.command("get")
@click.argument("marking_id", type=str, required=True)
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.pass_obj
def admin_marking_op_get(
    client: FoundryClient,
    marking_id: str,
    preview: typing.Optional[bool],
):
    """
    Get the Marking with the specified id.
    """
    result = client.admin.Marking.get(
        marking_id=marking_id,
        preview=preview,
    )
    click.echo(repr(result))


@admin_marking.command("get_batch")
@click.argument("body", type=str, required=True)
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.pass_obj
def admin_marking_op_get_batch(
    client: FoundryClient,
    body: str,
    preview: typing.Optional[bool],
):
    """
    Execute multiple get requests on Marking.

    The maximum batch size for this endpoint is 500.
    """
    result = client.admin.Marking.get_batch(
        body=json.loads(body),
        preview=preview,
    )
    click.echo(repr(result))


@admin_marking.command("list")
@click.option(
    "--page_size", type=int, required=False, help="""The page size to use for the endpoint."""
)
@click.option(
    "--page_token",
    type=str,
    required=False,
    help="""The page token indicates where to start paging. This should be omitted from the first page's request.
To fetch the next page, clients should take the value from the `nextPageToken` field of the previous response
and use it to populate the `pageToken` field of the next request.""",
)
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.pass_obj
def admin_marking_op_list(
    client: FoundryClient,
    page_size: typing.Optional[int],
    page_token: typing.Optional[str],
    preview: typing.Optional[bool],
):
    """
    Maximum page size 100.
    """
    result = client.admin.Marking.list(
        page_size=page_size,
        page_token=page_token,
        preview=preview,
    )
    click.echo(repr(result))


@admin_marking.command("replace")
@click.argument("marking_id", type=str, required=True)
@click.option("--name", type=str, required=True, help="""""")
@click.option("--description", type=str, required=False, help="""""")
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.pass_obj
def admin_marking_op_replace(
    client: FoundryClient,
    marking_id: str,
    name: str,
    description: typing.Optional[str],
    preview: typing.Optional[bool],
):
    """
    Replace the Marking with the specified id.
    """
    result = client.admin.Marking.replace(
        marking_id=marking_id,
        name=name,
        description=description,
        preview=preview,
    )
    click.echo(repr(result))


@admin_marking.group("marking_role_assignment")
def admin_marking_marking_role_assignment():
    pass


@admin_marking_marking_role_assignment.command("add")
@click.argument("marking_id", type=str, required=True)
@click.option("--role_assignments", type=str, required=True, help="""""")
@click.pass_obj
def admin_marking_marking_role_assignment_op_add(
    client: FoundryClient,
    marking_id: str,
    role_assignments: str,
):
    """ """
    result = client.admin.Marking.MarkingRoleAssignment.add(
        marking_id=marking_id,
        role_assignments=json.loads(role_assignments),
    )
    click.echo(repr(result))


@admin_marking_marking_role_assignment.command("list")
@click.argument("marking_id", type=str, required=True)
@click.option(
    "--page_size", type=int, required=False, help="""The page size to use for the endpoint."""
)
@click.option(
    "--page_token",
    type=str,
    required=False,
    help="""The page token indicates where to start paging. This should be omitted from the first page's request.
To fetch the next page, clients should take the value from the `nextPageToken` field of the previous response
and use it to populate the `pageToken` field of the next request.""",
)
@click.pass_obj
def admin_marking_marking_role_assignment_op_list(
    client: FoundryClient,
    marking_id: str,
    page_size: typing.Optional[int],
    page_token: typing.Optional[str],
):
    """
    List all principals who are assigned a role for the given Marking. Ignores the `pageSize` parameter.

    """
    result = client.admin.Marking.MarkingRoleAssignment.list(
        marking_id=marking_id,
        page_size=page_size,
        page_token=page_token,
    )
    click.echo(repr(result))


@admin_marking_marking_role_assignment.command("remove")
@click.argument("marking_id", type=str, required=True)
@click.option("--role_assignments", type=str, required=True, help="""""")
@click.pass_obj
def admin_marking_marking_role_assignment_op_remove(
    client: FoundryClient,
    marking_id: str,
    role_assignments: str,
):
    """ """
    result = client.admin.Marking.MarkingRoleAssignment.remove(
        marking_id=marking_id,
        role_assignments=json.loads(role_assignments),
    )
    click.echo(repr(result))


@admin_marking.group("marking_member")
def admin_marking_marking_member():
    pass


@admin_marking_marking_member.command("add")
@click.argument("marking_id", type=str, required=True)
@click.option("--principal_ids", type=str, required=True, help="""""")
@click.pass_obj
def admin_marking_marking_member_op_add(
    client: FoundryClient,
    marking_id: str,
    principal_ids: str,
):
    """ """
    result = client.admin.Marking.MarkingMember.add(
        marking_id=marking_id,
        principal_ids=json.loads(principal_ids),
    )
    click.echo(repr(result))


@admin_marking_marking_member.command("list")
@click.argument("marking_id", type=str, required=True)
@click.option(
    "--page_size", type=int, required=False, help="""The page size to use for the endpoint."""
)
@click.option(
    "--page_token",
    type=str,
    required=False,
    help="""The page token indicates where to start paging. This should be omitted from the first page's request.
To fetch the next page, clients should take the value from the `nextPageToken` field of the previous response
and use it to populate the `pageToken` field of the next request.""",
)
@click.option(
    "--transitive",
    type=bool,
    required=False,
    help="""When true, includes the transitive members of groups contained within groups that are members of this 
Marking. For example, say the Marking has member Group A, and Group A has member User B. If 
`transitive=false` only Group A will be returned, but if `transitive=true` then Group A and User B 
will be returned. This will recursively resolve Groups through all layers of nesting.

Defaults to false.
""",
)
@click.pass_obj
def admin_marking_marking_member_op_list(
    client: FoundryClient,
    marking_id: str,
    page_size: typing.Optional[int],
    page_token: typing.Optional[str],
    transitive: typing.Optional[bool],
):
    """
    Lists all principals who can view resources protected by the given Marking. Ignores the `pageSize` parameter.
    Requires `api:admin-write` because only marking administrators can view marking members.

    """
    result = client.admin.Marking.MarkingMember.list(
        marking_id=marking_id,
        page_size=page_size,
        page_token=page_token,
        transitive=transitive,
    )
    click.echo(repr(result))


@admin_marking_marking_member.command("remove")
@click.argument("marking_id", type=str, required=True)
@click.option("--principal_ids", type=str, required=True, help="""""")
@click.pass_obj
def admin_marking_marking_member_op_remove(
    client: FoundryClient,
    marking_id: str,
    principal_ids: str,
):
    """ """
    result = client.admin.Marking.MarkingMember.remove(
        marking_id=marking_id,
        principal_ids=json.loads(principal_ids),
    )
    click.echo(repr(result))


@admin.group("group")
def admin_group():
    pass


@admin_group.command("create")
@click.option(
    "--attributes",
    type=str,
    required=True,
    help="""A map of the Group's attributes. Attributes prefixed with "multipass:" are reserved for internal use by Foundry and are subject to change.""",
)
@click.option("--name", type=str, required=True, help="""The name of the Group.""")
@click.option(
    "--organizations",
    type=str,
    required=True,
    help="""The RIDs of the Organizations whose members can see this group. At least one Organization RID must be listed.
""",
)
@click.option("--description", type=str, required=False, help="""A description of the Group.""")
@click.pass_obj
def admin_group_op_create(
    client: FoundryClient,
    attributes: str,
    name: str,
    organizations: str,
    description: typing.Optional[str],
):
    """
    Creates a new Group.
    """
    result = client.admin.Group.create(
        attributes=json.loads(attributes),
        name=name,
        organizations=json.loads(organizations),
        description=description,
    )
    click.echo(repr(result))


@admin_group.command("delete")
@click.argument("group_id", type=str, required=True)
@click.pass_obj
def admin_group_op_delete(
    client: FoundryClient,
    group_id: str,
):
    """
    Delete the Group with the specified id.
    """
    result = client.admin.Group.delete(
        group_id=group_id,
    )
    click.echo(repr(result))


@admin_group.command("get")
@click.argument("group_id", type=str, required=True)
@click.pass_obj
def admin_group_op_get(
    client: FoundryClient,
    group_id: str,
):
    """
    Get the Group with the specified id.
    """
    result = client.admin.Group.get(
        group_id=group_id,
    )
    click.echo(repr(result))


@admin_group.command("get_batch")
@click.argument("body", type=str, required=True)
@click.pass_obj
def admin_group_op_get_batch(
    client: FoundryClient,
    body: str,
):
    """
    Execute multiple get requests on Group.

    The maximum batch size for this endpoint is 500.
    """
    result = client.admin.Group.get_batch(
        body=json.loads(body),
    )
    click.echo(repr(result))


@admin_group.command("list")
@click.option(
    "--page_size", type=int, required=False, help="""The page size to use for the endpoint."""
)
@click.option(
    "--page_token",
    type=str,
    required=False,
    help="""The page token indicates where to start paging. This should be omitted from the first page's request.
To fetch the next page, clients should take the value from the `nextPageToken` field of the previous response
and use it to populate the `pageToken` field of the next request.""",
)
@click.pass_obj
def admin_group_op_list(
    client: FoundryClient,
    page_size: typing.Optional[int],
    page_token: typing.Optional[str],
):
    """
    Lists all Groups.

    This is a paged endpoint. Each page may be smaller or larger than the requested page size. However, it is guaranteed that if there are more results available, the `nextPageToken` field will be populated. To get the next page, make the same request again, but set the value of the `pageToken` query parameter to be value of the `nextPageToken` value of the previous response. If there is no `nextPageToken` field in the response, you are on the last page.
    """
    result = client.admin.Group.list(
        page_size=page_size,
        page_token=page_token,
    )
    click.echo(repr(result))


@admin_group.command("search")
@click.option("--where", type=str, required=True, help="""""")
@click.option("--page_size", type=int, required=False, help="""""")
@click.option("--page_token", type=str, required=False, help="""""")
@click.pass_obj
def admin_group_op_search(
    client: FoundryClient,
    where: str,
    page_size: typing.Optional[int],
    page_token: typing.Optional[str],
):
    """
    Perform a case-insensitive prefix search for groups based on group name.

    """
    result = client.admin.Group.search(
        where=json.loads(where),
        page_size=page_size,
        page_token=page_token,
    )
    click.echo(repr(result))


@admin_group.group("group_membership_expiration_policy")
def admin_group_group_membership_expiration_policy():
    pass


@admin_group_group_membership_expiration_policy.command("get")
@click.argument("group_id", type=str, required=True)
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.pass_obj
def admin_group_group_membership_expiration_policy_op_get(
    client: FoundryClient,
    group_id: str,
    preview: typing.Optional[bool],
):
    """
    Get the GroupMembershipExpirationPolicy.
    """
    result = client.admin.Group.MembershipExpirationPolicy.get(
        group_id=group_id,
        preview=preview,
    )
    click.echo(repr(result))


@admin_group_group_membership_expiration_policy.command("replace")
@click.argument("group_id", type=str, required=True)
@click.option(
    "--maximum_duration",
    type=int,
    required=False,
    help="""Members in this group must be added with expirations that are less than this duration in seconds into the future from the time they are added.
""",
)
@click.option(
    "--maximum_value",
    type=click.DateTime(),
    required=False,
    help="""Members in this group must be added with expiration times that occur before this value.""",
)
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.pass_obj
def admin_group_group_membership_expiration_policy_op_replace(
    client: FoundryClient,
    group_id: str,
    maximum_duration: typing.Optional[int],
    maximum_value: typing.Optional[datetime],
    preview: typing.Optional[bool],
):
    """
    Replace the GroupMembershipExpirationPolicy.
    """
    result = client.admin.Group.MembershipExpirationPolicy.replace(
        group_id=group_id,
        maximum_duration=maximum_duration,
        maximum_value=maximum_value,
        preview=preview,
    )
    click.echo(repr(result))


@admin_group.group("group_member")
def admin_group_group_member():
    pass


@admin_group_group_member.command("add")
@click.argument("group_id", type=str, required=True)
@click.option("--principal_ids", type=str, required=True, help="""""")
@click.option("--expiration", type=click.DateTime(), required=False, help="""""")
@click.pass_obj
def admin_group_group_member_op_add(
    client: FoundryClient,
    group_id: str,
    principal_ids: str,
    expiration: typing.Optional[datetime],
):
    """ """
    result = client.admin.Group.GroupMember.add(
        group_id=group_id,
        principal_ids=json.loads(principal_ids),
        expiration=expiration,
    )
    click.echo(repr(result))


@admin_group_group_member.command("list")
@click.argument("group_id", type=str, required=True)
@click.option(
    "--page_size", type=int, required=False, help="""The page size to use for the endpoint."""
)
@click.option(
    "--page_token",
    type=str,
    required=False,
    help="""The page token indicates where to start paging. This should be omitted from the first page's request.
To fetch the next page, clients should take the value from the `nextPageToken` field of the previous response
and use it to populate the `pageToken` field of the next request.""",
)
@click.option(
    "--transitive",
    type=bool,
    required=False,
    help="""When true, includes the transitive members of groups contained within this group. For example, say the
Group has member Group A, and Group A has member User B. If `transitive=false` only Group A will
be returned, but if `transitive=true` then Group A and User B will be returned. This
will recursively resolve Groups through all layers of nesting.

Defaults to false.
""",
)
@click.pass_obj
def admin_group_group_member_op_list(
    client: FoundryClient,
    group_id: str,
    page_size: typing.Optional[int],
    page_token: typing.Optional[str],
    transitive: typing.Optional[bool],
):
    """
    Lists all members (which can be a User or a Group) of a given Group.

    This is a paged endpoint. Each page may be smaller or larger than the requested page size. However,
    it is guaranteed that if there are more results available, the `nextPageToken` field will be populated.
    To get the next page, make the same request again, but set the value of the `pageToken` query parameter
    to be value of the `nextPageToken` value of the previous response. If there is no `nextPageToken` field
    in the response, you are on the last page.

    """
    result = client.admin.Group.GroupMember.list(
        group_id=group_id,
        page_size=page_size,
        page_token=page_token,
        transitive=transitive,
    )
    click.echo(repr(result))


@admin_group_group_member.command("remove")
@click.argument("group_id", type=str, required=True)
@click.option("--principal_ids", type=str, required=True, help="""""")
@click.pass_obj
def admin_group_group_member_op_remove(
    client: FoundryClient,
    group_id: str,
    principal_ids: str,
):
    """ """
    result = client.admin.Group.GroupMember.remove(
        group_id=group_id,
        principal_ids=json.loads(principal_ids),
    )
    click.echo(repr(result))


@admin_group.group("group_provider_info")
def admin_group_group_provider_info():
    pass


@admin_group_group_provider_info.command("get")
@click.argument("group_id", type=str, required=True)
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.pass_obj
def admin_group_group_provider_info_op_get(
    client: FoundryClient,
    group_id: str,
    preview: typing.Optional[bool],
):
    """
    Get the GroupProviderInfo.
    """
    result = client.admin.Group.ProviderInfo.get(
        group_id=group_id,
        preview=preview,
    )
    click.echo(repr(result))


@admin_group_group_provider_info.command("replace")
@click.argument("group_id", type=str, required=True)
@click.option(
    "--provider_id",
    type=str,
    required=True,
    help="""The ID of the Group in the external authentication provider. This value is determined by the authentication provider.
At most one Group can have a given provider ID in a given Realm.
""",
)
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.pass_obj
def admin_group_group_provider_info_op_replace(
    client: FoundryClient,
    group_id: str,
    provider_id: str,
    preview: typing.Optional[bool],
):
    """
    Replace the GroupProviderInfo.
    """
    result = client.admin.Group.ProviderInfo.replace(
        group_id=group_id,
        provider_id=provider_id,
        preview=preview,
    )
    click.echo(repr(result))


@admin.group("enrollment")
def admin_enrollment():
    pass


@admin_enrollment.command("get")
@click.argument("enrollment_rid", type=str, required=True)
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.pass_obj
def admin_enrollment_op_get(
    client: FoundryClient,
    enrollment_rid: str,
    preview: typing.Optional[bool],
):
    """
    Get the Enrollment with the specified rid.
    """
    result = client.admin.Enrollment.get(
        enrollment_rid=enrollment_rid,
        preview=preview,
    )
    click.echo(repr(result))


@admin_enrollment.command("get_current")
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.pass_obj
def admin_enrollment_op_get_current(
    client: FoundryClient,
    preview: typing.Optional[bool],
):
    """
    Returns the Enrollment associated with the current User's primary organization.

    """
    result = client.admin.Enrollment.get_current(
        preview=preview,
    )
    click.echo(repr(result))


@admin_enrollment.group("authentication_provider")
def admin_enrollment_authentication_provider():
    pass


@admin_enrollment_authentication_provider.command("get")
@click.argument("enrollment_rid", type=str, required=True)
@click.argument("authentication_provider_rid", type=str, required=True)
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.pass_obj
def admin_enrollment_authentication_provider_op_get(
    client: FoundryClient,
    enrollment_rid: str,
    authentication_provider_rid: str,
    preview: typing.Optional[bool],
):
    """
    Get the AuthenticationProvider with the specified rid.
    """
    result = client.admin.Enrollment.AuthenticationProvider.get(
        enrollment_rid=enrollment_rid,
        authentication_provider_rid=authentication_provider_rid,
        preview=preview,
    )
    click.echo(repr(result))


@admin_enrollment_authentication_provider.command("list")
@click.argument("enrollment_rid", type=str, required=True)
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.pass_obj
def admin_enrollment_authentication_provider_op_list(
    client: FoundryClient,
    enrollment_rid: str,
    preview: typing.Optional[bool],
):
    """
    Lists all AuthenticationProviders.


    """
    result = client.admin.Enrollment.AuthenticationProvider.list(
        enrollment_rid=enrollment_rid,
        preview=preview,
    )
    click.echo(repr(result))


@admin_enrollment_authentication_provider.command("preregister_group")
@click.argument("enrollment_rid", type=str, required=True)
@click.argument("authentication_provider_rid", type=str, required=True)
@click.option("--name", type=str, required=True, help="""""")
@click.option(
    "--organizations",
    type=str,
    required=True,
    help="""The RIDs of the Organizations that can view this group.
""",
)
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.pass_obj
def admin_enrollment_authentication_provider_op_preregister_group(
    client: FoundryClient,
    enrollment_rid: str,
    authentication_provider_rid: str,
    name: str,
    organizations: str,
    preview: typing.Optional[bool],
):
    """
    Register a Group with a given name before any users with this group log in through this Authentication Provider.
    Preregistered groups can be used anywhere other groups are used in the platform.

    """
    result = client.admin.Enrollment.AuthenticationProvider.preregister_group(
        enrollment_rid=enrollment_rid,
        authentication_provider_rid=authentication_provider_rid,
        name=name,
        organizations=json.loads(organizations),
        preview=preview,
    )
    click.echo(repr(result))


@admin_enrollment_authentication_provider.command("preregister_user")
@click.argument("enrollment_rid", type=str, required=True)
@click.argument("authentication_provider_rid", type=str, required=True)
@click.option(
    "--organization",
    type=str,
    required=True,
    help="""The RID of the user's primary Organization. This may be changed when the user logs in for the first
time depending on any configured Organization assignment rules.
""",
)
@click.option(
    "--username",
    type=str,
    required=True,
    help="""The new user's username. This must match one of the provider's supported username patterns.""",
)
@click.option("--attributes", type=str, required=False, help="""""")
@click.option("--email", type=str, required=False, help="""""")
@click.option("--family_name", type=str, required=False, help="""""")
@click.option("--given_name", type=str, required=False, help="""""")
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.pass_obj
def admin_enrollment_authentication_provider_op_preregister_user(
    client: FoundryClient,
    enrollment_rid: str,
    authentication_provider_rid: str,
    organization: str,
    username: str,
    attributes: typing.Optional[str],
    email: typing.Optional[str],
    family_name: typing.Optional[str],
    given_name: typing.Optional[str],
    preview: typing.Optional[bool],
):
    """
    Register a User with a given username before they log in to the platform for the first time through this
    Authentication Provider. Preregistered users can be assigned to groups and roles prior to first login.

    """
    result = client.admin.Enrollment.AuthenticationProvider.preregister_user(
        enrollment_rid=enrollment_rid,
        authentication_provider_rid=authentication_provider_rid,
        organization=organization,
        username=username,
        attributes=None if attributes is None else json.loads(attributes),
        email=email,
        family_name=family_name,
        given_name=given_name,
        preview=preview,
    )
    click.echo(repr(result))


@admin_enrollment.group("host")
def admin_enrollment_host():
    pass


@admin_enrollment_host.command("list")
@click.argument("enrollment_rid", type=str, required=True)
@click.option(
    "--page_size", type=int, required=False, help="""The page size to use for the endpoint."""
)
@click.option(
    "--page_token",
    type=str,
    required=False,
    help="""The page token indicates where to start paging. This should be omitted from the first page's request.
To fetch the next page, clients should take the value from the `nextPageToken` field of the previous response
and use it to populate the `pageToken` field of the next request.""",
)
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.pass_obj
def admin_enrollment_host_op_list(
    client: FoundryClient,
    enrollment_rid: str,
    page_size: typing.Optional[int],
    page_token: typing.Optional[str],
    preview: typing.Optional[bool],
):
    """
    Lists all Hosts.

    This is a paged endpoint. Each page may be smaller or larger than the requested page size. However, it is guaranteed that if there are more results available, the `nextPageToken` field will be populated. To get the next page, make the same request again, but set the value of the `pageToken` query parameter to be value of the `nextPageToken` value of the previous response. If there is no `nextPageToken` field in the response, you are on the last page.
    """
    result = client.admin.Enrollment.Host.list(
        enrollment_rid=enrollment_rid,
        page_size=page_size,
        page_token=page_token,
        preview=preview,
    )
    click.echo(repr(result))


@admin_enrollment.group("enrollment_role_assignment")
def admin_enrollment_enrollment_role_assignment():
    pass


@admin_enrollment_enrollment_role_assignment.command("add")
@click.argument("enrollment_rid", type=str, required=True)
@click.option("--role_assignments", type=str, required=True, help="""""")
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.pass_obj
def admin_enrollment_enrollment_role_assignment_op_add(
    client: FoundryClient,
    enrollment_rid: str,
    role_assignments: str,
    preview: typing.Optional[bool],
):
    """
    Assign roles to principals for the given Enrollment. At most 100 role assignments can be added in a single request.

    """
    result = client.admin.Enrollment.EnrollmentRoleAssignment.add(
        enrollment_rid=enrollment_rid,
        role_assignments=json.loads(role_assignments),
        preview=preview,
    )
    click.echo(repr(result))


@admin_enrollment_enrollment_role_assignment.command("list")
@click.argument("enrollment_rid", type=str, required=True)
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.pass_obj
def admin_enrollment_enrollment_role_assignment_op_list(
    client: FoundryClient,
    enrollment_rid: str,
    preview: typing.Optional[bool],
):
    """
    List all principals who are assigned a role for the given Enrollment.

    """
    result = client.admin.Enrollment.EnrollmentRoleAssignment.list(
        enrollment_rid=enrollment_rid,
        preview=preview,
    )
    click.echo(repr(result))


@admin_enrollment_enrollment_role_assignment.command("remove")
@click.argument("enrollment_rid", type=str, required=True)
@click.option("--role_assignments", type=str, required=True, help="""""")
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.pass_obj
def admin_enrollment_enrollment_role_assignment_op_remove(
    client: FoundryClient,
    enrollment_rid: str,
    role_assignments: str,
    preview: typing.Optional[bool],
):
    """
    Remove roles from principals for the given Enrollment. At most 100 role assignments can be removed in a single request.

    """
    result = client.admin.Enrollment.EnrollmentRoleAssignment.remove(
        enrollment_rid=enrollment_rid,
        role_assignments=json.loads(role_assignments),
        preview=preview,
    )
    click.echo(repr(result))


@cli.group("aip_agents")
def aip_agents():
    pass


@aip_agents.group("agent")
def aip_agents_agent():
    pass


@aip_agents_agent.command("all_sessions")
@click.option(
    "--page_size",
    type=int,
    required=False,
    help="""The maximum number of sessions to return in a single page. The maximum allowed value is 100.
Defaults to 100 if not specified.
""",
)
@click.option("--page_token", type=str, required=False, help="""""")
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.pass_obj
def aip_agents_agent_op_all_sessions(
    client: FoundryClient,
    page_size: typing.Optional[int],
    page_token: typing.Optional[str],
    preview: typing.Optional[bool],
):
    """
    List all conversation sessions between the calling user and all accessible Agents that were created by this client.
    Sessions are returned in order of most recently updated first.

    """
    result = client.aip_agents.Agent.all_sessions(
        page_size=page_size,
        page_token=page_token,
        preview=preview,
    )
    click.echo(repr(result))


@aip_agents_agent.command("get")
@click.argument("agent_rid", type=str, required=True)
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.option(
    "--version",
    type=str,
    required=False,
    help="""The version of the Agent to retrieve. If not specified, the latest published version will be returned.
""",
)
@click.pass_obj
def aip_agents_agent_op_get(
    client: FoundryClient,
    agent_rid: str,
    preview: typing.Optional[bool],
    version: typing.Optional[str],
):
    """
    Get details for an AIP Agent.
    """
    result = client.aip_agents.Agent.get(
        agent_rid=agent_rid,
        preview=preview,
        version=version,
    )
    click.echo(repr(result))


@aip_agents_agent.group("session")
def aip_agents_agent_session():
    pass


@aip_agents_agent_session.command("blocking_continue")
@click.argument("agent_rid", type=str, required=True)
@click.argument("session_rid", type=str, required=True)
@click.option(
    "--parameter_inputs",
    type=str,
    required=True,
    help="""Any supplied values for [application variables](https://palantir.com/docs/foundry/agent-studio/application-state/) to pass to the Agent for the exchange.
""",
)
@click.option(
    "--user_input",
    type=str,
    required=True,
    help="""The user message for the Agent to respond to.""",
)
@click.option(
    "--contexts_override",
    type=str,
    required=False,
    help="""If set, automatic [context retrieval](https://palantir.com/docs/foundry/agent-studio/retrieval-context/) is skipped and the list of specified context is provided to the Agent instead.
If omitted, relevant context for the user message is automatically retrieved and included in the prompt, based on data sources configured on the Agent for the session.
""",
)
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.option(
    "--session_trace_id",
    type=str,
    required=False,
    help="""The unique identifier to use for this continue session trace. By generating and passing this ID to the
`blockingContinue` endpoint, clients can use this trace ID to separately load details of the trace used
to generate a result, while the result is in progress. If omitted, it will be generated automatically.
Clients can check the generated ID by inspecting the `sessionTraceId` in the `SessionExchangeResult`.
""",
)
@click.pass_obj
def aip_agents_agent_session_op_blocking_continue(
    client: FoundryClient,
    agent_rid: str,
    session_rid: str,
    parameter_inputs: str,
    user_input: str,
    contexts_override: typing.Optional[str],
    preview: typing.Optional[bool],
    session_trace_id: typing.Optional[str],
):
    """
    Continue a conversation session with an Agent, or add the first exchange to a session after creation.
    Adds a new exchange to the session with the provided inputs, and generates a response from the Agent.
    Blocks on returning the result of the added exchange until the response is fully generated.
    Streamed responses are also supported; see `streamingContinue` for details.
    Concurrent requests to continue the same session are not supported.
    Clients should wait to receive a response before sending the next message.

    """
    result = client.aip_agents.Agent.Session.blocking_continue(
        agent_rid=agent_rid,
        session_rid=session_rid,
        parameter_inputs=json.loads(parameter_inputs),
        user_input=json.loads(user_input),
        contexts_override=None if contexts_override is None else json.loads(contexts_override),
        preview=preview,
        session_trace_id=session_trace_id,
    )
    click.echo(repr(result))


@aip_agents_agent_session.command("cancel")
@click.argument("agent_rid", type=str, required=True)
@click.argument("session_rid", type=str, required=True)
@click.option(
    "--message_id",
    type=str,
    required=True,
    help="""The identifier for the in-progress exchange to cancel.
This should match the `messageId` which was provided when initiating the exchange with `streamingContinue`.
""",
)
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.option(
    "--response",
    type=str,
    required=False,
    help="""When specified, the exchange is added to the session with the client-provided response as the result.
When omitted, the exchange is not added to the session.
""",
)
@click.pass_obj
def aip_agents_agent_session_op_cancel(
    client: FoundryClient,
    agent_rid: str,
    session_rid: str,
    message_id: str,
    preview: typing.Optional[bool],
    response: typing.Optional[str],
):
    """
    Cancel an in-progress streamed exchange with an Agent which was initiated with `streamingContinue`.
    Canceling an exchange allows clients to prevent the exchange from being added to the session, or to provide a response to replace the Agent-generated response.
    Note that canceling an exchange does not terminate the stream returned by `streamingContinue`; clients should close the stream on triggering the cancellation request to stop reading from the stream.

    """
    result = client.aip_agents.Agent.Session.cancel(
        agent_rid=agent_rid,
        session_rid=session_rid,
        message_id=message_id,
        preview=preview,
        response=response,
    )
    click.echo(repr(result))


@aip_agents_agent_session.command("create")
@click.argument("agent_rid", type=str, required=True)
@click.option(
    "--agent_version",
    type=str,
    required=False,
    help="""The version of the Agent associated with the session.
This can be set by clients on session creation.
If not specified, defaults to use the latest published version of the Agent at session creation time.
""",
)
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.pass_obj
def aip_agents_agent_session_op_create(
    client: FoundryClient,
    agent_rid: str,
    agent_version: typing.Optional[str],
    preview: typing.Optional[bool],
):
    """
    Create a new conversation session between the calling user and an Agent.
    Use `blockingContinue` or `streamingContinue` to start adding exchanges to the session.

    """
    result = client.aip_agents.Agent.Session.create(
        agent_rid=agent_rid,
        agent_version=agent_version,
        preview=preview,
    )
    click.echo(repr(result))


@aip_agents_agent_session.command("get")
@click.argument("agent_rid", type=str, required=True)
@click.argument("session_rid", type=str, required=True)
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.pass_obj
def aip_agents_agent_session_op_get(
    client: FoundryClient,
    agent_rid: str,
    session_rid: str,
    preview: typing.Optional[bool],
):
    """
    Get the details of a conversation session between the calling user and an Agent.
    """
    result = client.aip_agents.Agent.Session.get(
        agent_rid=agent_rid,
        session_rid=session_rid,
        preview=preview,
    )
    click.echo(repr(result))


@aip_agents_agent_session.command("list")
@click.argument("agent_rid", type=str, required=True)
@click.option(
    "--page_size", type=int, required=False, help="""The page size to use for the endpoint."""
)
@click.option(
    "--page_token",
    type=str,
    required=False,
    help="""The page token indicates where to start paging. This should be omitted from the first page's request.
To fetch the next page, clients should take the value from the `nextPageToken` field of the previous response
and use it to populate the `pageToken` field of the next request.""",
)
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.pass_obj
def aip_agents_agent_session_op_list(
    client: FoundryClient,
    agent_rid: str,
    page_size: typing.Optional[int],
    page_token: typing.Optional[str],
    preview: typing.Optional[bool],
):
    """
    List all conversation sessions between the calling user and an Agent that was created by this client.
    This does not list sessions for the user created by other clients.
    For example, any sessions created by the user in AIP Agent Studio will not be listed here.
    Sessions are returned in order of most recently updated first.

    """
    result = client.aip_agents.Agent.Session.list(
        agent_rid=agent_rid,
        page_size=page_size,
        page_token=page_token,
        preview=preview,
    )
    click.echo(repr(result))


@aip_agents_agent_session.command("rag_context")
@click.argument("agent_rid", type=str, required=True)
@click.argument("session_rid", type=str, required=True)
@click.option(
    "--parameter_inputs",
    type=str,
    required=True,
    help="""Any values for [application variables](https://palantir.com/docs/foundry/agent-studio/application-state/) to use for the context retrieval.
""",
)
@click.option(
    "--user_input",
    type=str,
    required=True,
    help="""The user message to retrieve relevant context for from the configured Agent data sources.""",
)
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.pass_obj
def aip_agents_agent_session_op_rag_context(
    client: FoundryClient,
    agent_rid: str,
    session_rid: str,
    parameter_inputs: str,
    user_input: str,
    preview: typing.Optional[bool],
):
    """
    Retrieve relevant [context](https://palantir.com/docs/foundry/agent-studio/core-concepts/#retrieval-context) for a user message from the data sources configured for the session.
    This allows clients to pre-retrieve context for a user message before sending it to the Agent with the `contextsOverride` option when continuing a session, to allow any pre-processing of the context before sending it to the Agent.

    """
    result = client.aip_agents.Agent.Session.rag_context(
        agent_rid=agent_rid,
        session_rid=session_rid,
        parameter_inputs=json.loads(parameter_inputs),
        user_input=json.loads(user_input),
        preview=preview,
    )
    click.echo(repr(result))


@aip_agents_agent_session.command("streaming_continue")
@click.argument("agent_rid", type=str, required=True)
@click.argument("session_rid", type=str, required=True)
@click.option(
    "--parameter_inputs",
    type=str,
    required=True,
    help="""Any supplied values for [application variables](https://palantir.com/docs/foundry/agent-studio/application-state/) to pass to the Agent for the exchange.
""",
)
@click.option(
    "--user_input",
    type=str,
    required=True,
    help="""The user message for the Agent to respond to.""",
)
@click.option(
    "--contexts_override",
    type=str,
    required=False,
    help="""If set, automatic [context](https://palantir.com/docs/foundry/agent-studio/retrieval-context/) retrieval is skipped and the list of specified context is provided to the Agent instead.
If omitted, relevant context for the user message is automatically retrieved and included in the prompt, based on data sources configured on the Agent for the session.
""",
)
@click.option(
    "--message_id",
    type=str,
    required=False,
    help="""A client-generated Universally Unique Identifier (UUID) to identify the message, which the client can use to cancel the exchange before the streaming response is complete.
""",
)
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.option(
    "--session_trace_id",
    type=str,
    required=False,
    help="""The unique identifier to use for this continue session trace. By generating and passing this ID to the
`streamingContinue` endpoint, clients can use this trace ID to separately load details of the trace used
to generate a result, while the result is in progress. If omitted, it will be generated automatically.
Clients can check the generated ID by inspecting the `sessionTraceId` in the `SessionExchangeResult`,
which can be loaded via the `getContent` endpoint.
""",
)
@click.pass_obj
def aip_agents_agent_session_op_streaming_continue(
    client: FoundryClient,
    agent_rid: str,
    session_rid: str,
    parameter_inputs: str,
    user_input: str,
    contexts_override: typing.Optional[str],
    message_id: typing.Optional[str],
    preview: typing.Optional[bool],
    session_trace_id: typing.Optional[str],
):
    """
    Continue a conversation session with an Agent, or add the first exchange to a session after creation.
    Adds a new exchange to the session with the provided inputs, and generates a response from the Agent.
    Returns a stream of the Agent response text (formatted using markdown) for clients to consume as the response is generated.
    On completion of the streamed response, clients can load the full details of the exchange that was added to the session by reloading the session content.
    Streamed exchanges also support cancellation; see `cancel` for details.
    Concurrent requests to continue the same session are not supported.
    Clients should wait to receive a response, or cancel the in-progress exchange, before sending the next message.

    """
    result = client.aip_agents.Agent.Session.streaming_continue(
        agent_rid=agent_rid,
        session_rid=session_rid,
        parameter_inputs=json.loads(parameter_inputs),
        user_input=json.loads(user_input),
        contexts_override=None if contexts_override is None else json.loads(contexts_override),
        message_id=message_id,
        preview=preview,
        session_trace_id=session_trace_id,
    )
    click.echo(result)


@aip_agents_agent_session.command("update_title")
@click.argument("agent_rid", type=str, required=True)
@click.argument("session_rid", type=str, required=True)
@click.option(
    "--title",
    type=str,
    required=True,
    help="""The new title for the session.
The maximum title length is 200 characters. Titles are truncated if they exceed this length.
""",
)
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.pass_obj
def aip_agents_agent_session_op_update_title(
    client: FoundryClient,
    agent_rid: str,
    session_rid: str,
    title: str,
    preview: typing.Optional[bool],
):
    """
    Update the title for a session.
    Use this to set a custom title for a session to help identify it in the list of sessions with an Agent.

    """
    result = client.aip_agents.Agent.Session.update_title(
        agent_rid=agent_rid,
        session_rid=session_rid,
        title=title,
        preview=preview,
    )
    click.echo(repr(result))


@aip_agents_agent_session.group("session_trace")
def aip_agents_agent_session_session_trace():
    pass


@aip_agents_agent_session_session_trace.command("get")
@click.argument("agent_rid", type=str, required=True)
@click.argument("session_rid", type=str, required=True)
@click.argument("session_trace_id", type=str, required=True)
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.pass_obj
def aip_agents_agent_session_session_trace_op_get(
    client: FoundryClient,
    agent_rid: str,
    session_rid: str,
    session_trace_id: str,
    preview: typing.Optional[bool],
):
    """
    Get the trace of an Agent response. The trace lists the sequence of steps that an Agent took to arrive at
    an answer. For example, a trace may include steps such as context retrieval and tool calls. Clients should
    poll this endpoint to check the realtime progress of a response until the trace is completed.

    """
    result = client.aip_agents.Agent.Session.SessionTrace.get(
        agent_rid=agent_rid,
        session_rid=session_rid,
        session_trace_id=session_trace_id,
        preview=preview,
    )
    click.echo(repr(result))


@aip_agents_agent_session.group("content")
def aip_agents_agent_session_content():
    pass


@aip_agents_agent_session_content.command("get")
@click.argument("agent_rid", type=str, required=True)
@click.argument("session_rid", type=str, required=True)
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.pass_obj
def aip_agents_agent_session_content_op_get(
    client: FoundryClient,
    agent_rid: str,
    session_rid: str,
    preview: typing.Optional[bool],
):
    """
    Get the conversation content for a session between the calling user and an Agent.
    """
    result = client.aip_agents.Agent.Session.Content.get(
        agent_rid=agent_rid,
        session_rid=session_rid,
        preview=preview,
    )
    click.echo(repr(result))


@aip_agents_agent.group("agent_version")
def aip_agents_agent_agent_version():
    pass


@aip_agents_agent_agent_version.command("get")
@click.argument("agent_rid", type=str, required=True)
@click.argument("agent_version_string", type=str, required=True)
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.pass_obj
def aip_agents_agent_agent_version_op_get(
    client: FoundryClient,
    agent_rid: str,
    agent_version_string: str,
    preview: typing.Optional[bool],
):
    """
    Get version details for an AIP Agent.
    """
    result = client.aip_agents.Agent.AgentVersion.get(
        agent_rid=agent_rid,
        agent_version_string=agent_version_string,
        preview=preview,
    )
    click.echo(repr(result))


@aip_agents_agent_agent_version.command("list")
@click.argument("agent_rid", type=str, required=True)
@click.option(
    "--page_size", type=int, required=False, help="""The page size to use for the endpoint."""
)
@click.option(
    "--page_token",
    type=str,
    required=False,
    help="""The page token indicates where to start paging. This should be omitted from the first page's request.
To fetch the next page, clients should take the value from the `nextPageToken` field of the previous response
and use it to populate the `pageToken` field of the next request.""",
)
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.pass_obj
def aip_agents_agent_agent_version_op_list(
    client: FoundryClient,
    agent_rid: str,
    page_size: typing.Optional[int],
    page_token: typing.Optional[str],
    preview: typing.Optional[bool],
):
    """
    List all versions for an AIP Agent.
    Versions are returned in descending order, by most recent versions first.

    """
    result = client.aip_agents.Agent.AgentVersion.list(
        agent_rid=agent_rid,
        page_size=page_size,
        page_token=page_token,
        preview=preview,
    )
    click.echo(repr(result))


@cli.group("audit")
def audit():
    pass


@audit.group("organization")
def audit_organization():
    pass


@audit_organization.group("log_file")
def audit_organization_log_file():
    pass


@audit_organization_log_file.command("content")
@click.argument("organization_rid", type=str, required=True)
@click.argument("log_file_id", type=str, required=True)
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.pass_obj
def audit_organization_log_file_op_content(
    client: FoundryClient,
    organization_rid: str,
    log_file_id: str,
    preview: typing.Optional[bool],
):
    """ """
    result = client.audit.Organization.LogFile.content(
        organization_rid=organization_rid,
        log_file_id=log_file_id,
        preview=preview,
    )
    click.echo(result)


@audit_organization_log_file.command("list")
@click.argument("organization_rid", type=str, required=True)
@click.option(
    "--end_date",
    type=click.DateTime(),
    required=False,
    help="""List log files for audit events up until this date (inclusive). If absent, defaults to no end date. Use the returned `nextPageToken` to continually poll the  `listLogFiles` endpoint to list the latest available logs.
""",
)
@click.option(
    "--page_size", type=int, required=False, help="""The page size to use for the endpoint."""
)
@click.option(
    "--page_token",
    type=str,
    required=False,
    help="""The page token indicates where to start paging. This should be omitted from the first page's request.
To fetch the next page, clients should take the value from the `nextPageToken` field of the previous response
and use it to populate the `pageToken` field of the next request.""",
)
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.option(
    "--start_date",
    type=click.DateTime(),
    required=False,
    help="""List log files for audit events starting from this date. If absent, defaults to the current date.
""",
)
@click.pass_obj
def audit_organization_log_file_op_list(
    client: FoundryClient,
    organization_rid: str,
    end_date: typing.Optional[datetime],
    page_size: typing.Optional[int],
    page_token: typing.Optional[str],
    preview: typing.Optional[bool],
    start_date: typing.Optional[datetime],
):
    """
    Lists all LogFiles.

    This is a paged endpoint. Each page may be smaller or larger than the requested page size. However, it is guaranteed that if there are more results available, the `nextPageToken` field will be populated. To get the next page, make the same request again, but set the value of the `pageToken` query parameter to be value of the `nextPageToken` value of the previous response. If there is no `nextPageToken` field in the response, you are on the last page.
    """
    result = client.audit.Organization.LogFile.list(
        organization_rid=organization_rid,
        end_date=end_date,
        page_size=page_size,
        page_token=page_token,
        preview=preview,
        start_date=start_date,
    )
    click.echo(repr(result))


@cli.group("connectivity")
def connectivity():
    pass


@connectivity.group("connection")
def connectivity_connection():
    pass


@connectivity_connection.command("create")
@click.option("--configuration", type=str, required=True, help="""""")
@click.option(
    "--display_name",
    type=str,
    required=True,
    help="""The display name of the Connection. The display name must not be blank.""",
)
@click.option("--parent_folder_rid", type=str, required=True, help="""""")
@click.option("--worker", type=str, required=True, help="""""")
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.pass_obj
def connectivity_connection_op_create(
    client: FoundryClient,
    configuration: str,
    display_name: str,
    parent_folder_rid: str,
    worker: str,
    preview: typing.Optional[bool],
):
    """
    Creates a new Connection with a [direct connection](https://palantir.com/docs/foundry/data-connection/core-concepts/#direct-connection) runtime.

    Any secrets specified in the request body are transmitted over the network encrypted using TLS. Once the
    secrets reach Foundry's servers, they will be temporarily decrypted and remain in plaintext in memory to
    be processed as needed. They will stay in plaintext in memory until the garbage collection process cleans
    up the memory. The secrets are always stored encrypted on our servers.
    By using this endpoint, you acknowledge and accept any potential risks associated with the temporary
    in-memory handling of secrets. If you do not want your secrets to be temporarily decrypted, you should
    use the Foundry UI instead.

    """
    result = client.connectivity.Connection.create(
        configuration=json.loads(configuration),
        display_name=display_name,
        parent_folder_rid=parent_folder_rid,
        worker=json.loads(worker),
        preview=preview,
    )
    click.echo(repr(result))


@connectivity_connection.command("get")
@click.argument("connection_rid", type=str, required=True)
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.pass_obj
def connectivity_connection_op_get(
    client: FoundryClient,
    connection_rid: str,
    preview: typing.Optional[bool],
):
    """
    Get the Connection with the specified rid.
    """
    result = client.connectivity.Connection.get(
        connection_rid=connection_rid,
        preview=preview,
    )
    click.echo(repr(result))


@connectivity_connection.command("get_configuration")
@click.argument("connection_rid", type=str, required=True)
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.pass_obj
def connectivity_connection_op_get_configuration(
    client: FoundryClient,
    connection_rid: str,
    preview: typing.Optional[bool],
):
    """
    Retrieves the ConnectionConfiguration of the [Connection](https://palantir.com/docs/foundry/data-connection/set-up-source/) itself.
    This operation is intended for use when other Connection data is not required, providing a lighter-weight alternative to `getConnection` operation.

    """
    result = client.connectivity.Connection.get_configuration(
        connection_rid=connection_rid,
        preview=preview,
    )
    click.echo(repr(result))


@connectivity_connection.command("update_export_settings")
@click.argument("connection_rid", type=str, required=True)
@click.option("--export_settings", type=str, required=True, help="""""")
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.pass_obj
def connectivity_connection_op_update_export_settings(
    client: FoundryClient,
    connection_rid: str,
    export_settings: str,
    preview: typing.Optional[bool],
):
    """
    Updates the [export settings on the Connection.](https://palantir.com/docs/foundry/data-connection/export-overview/#enable-exports-for-source)
    Only users with Information Security Officer role can modify the export settings.

    """
    result = client.connectivity.Connection.update_export_settings(
        connection_rid=connection_rid,
        export_settings=json.loads(export_settings),
        preview=preview,
    )
    click.echo(repr(result))


@connectivity_connection.command("update_secrets")
@click.argument("connection_rid", type=str, required=True)
@click.option(
    "--secrets",
    type=str,
    required=True,
    help="""The secrets to be updated. The specified secret names must already be configured on the connection.
""",
)
@click.pass_obj
def connectivity_connection_op_update_secrets(
    client: FoundryClient,
    connection_rid: str,
    secrets: str,
):
    """
    Updates the secrets on the connection to the specified secret values.
    Secrets that are currently configured on the connection but are omitted in the request will remain unchanged.

    Secrets are transmitted over the network encrypted using TLS. Once the secrets reach Foundry's servers,
    they will be temporarily decrypted and remain in plaintext in memory to be processed as needed.
    They will stay in plaintext in memory until the garbage collection process cleans up the memory.
    The secrets are always stored encrypted on our servers.

    By using this endpoint, you acknowledge and accept any potential risks associated with the temporary
    in-memory handling of secrets. If you do not want your secrets to be temporarily decrypted, you should
    use the Foundry UI instead.

    """
    result = client.connectivity.Connection.update_secrets(
        connection_rid=connection_rid,
        secrets=json.loads(secrets),
    )
    click.echo(repr(result))


@connectivity_connection.command("upload_custom_jdbc_drivers")
@click.argument("connection_rid", type=str, required=True)
@click.argument("body", type=click.File("rb"), required=True)
@click.option(
    "--file_name",
    type=str,
    required=True,
    help="""The file name of the uploaded JDBC driver. Must end with .jar
""",
)
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.pass_obj
def connectivity_connection_op_upload_custom_jdbc_drivers(
    client: FoundryClient,
    connection_rid: str,
    body: io.BufferedReader,
    file_name: str,
    preview: typing.Optional[bool],
):
    """
    Upload custom jdbc drivers to an existing JDBC connection.
    The body of the request must contain the binary content of the file and the `Content-Type` header must be `application/octet-stream`.

    """
    result = client.connectivity.Connection.upload_custom_jdbc_drivers(
        connection_rid=connection_rid,
        body=body.read(),
        file_name=file_name,
        preview=preview,
    )
    click.echo(repr(result))


@connectivity_connection.group("table_import")
def connectivity_connection_table_import():
    pass


@connectivity_connection_table_import.command("create")
@click.argument("connection_rid", type=str, required=True)
@click.option("--config", type=str, required=True, help="""""")
@click.option(
    "--dataset_rid",
    type=str,
    required=True,
    help="""The RID of the output dataset. Can not be modified after the table import is created.""",
)
@click.option("--display_name", type=str, required=True, help="""""")
@click.option(
    "--import_mode", type=click.Choice(["SNAPSHOT", "APPEND"]), required=True, help=""""""
)
@click.option(
    "--allow_schema_changes",
    type=bool,
    required=False,
    help="""Allow the TableImport to succeed if the schema of imported rows does not match the existing dataset's schema. Defaults to false for new table imports.""",
)
@click.option(
    "--branch_name",
    type=str,
    required=False,
    help="""The branch name in the output dataset that will contain the imported data. Defaults to `master` for most enrollments. Can not be modified after the table import is created.""",
)
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.pass_obj
def connectivity_connection_table_import_op_create(
    client: FoundryClient,
    connection_rid: str,
    config: str,
    dataset_rid: str,
    display_name: str,
    import_mode: typing.Literal["SNAPSHOT", "APPEND"],
    allow_schema_changes: typing.Optional[bool],
    branch_name: typing.Optional[str],
    preview: typing.Optional[bool],
):
    """
    Creates a new TableImport.
    """
    result = client.connectivity.Connection.TableImport.create(
        connection_rid=connection_rid,
        config=json.loads(config),
        dataset_rid=dataset_rid,
        display_name=display_name,
        import_mode=import_mode,
        allow_schema_changes=allow_schema_changes,
        branch_name=branch_name,
        preview=preview,
    )
    click.echo(repr(result))


@connectivity_connection_table_import.command("delete")
@click.argument("connection_rid", type=str, required=True)
@click.argument("table_import_rid", type=str, required=True)
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.pass_obj
def connectivity_connection_table_import_op_delete(
    client: FoundryClient,
    connection_rid: str,
    table_import_rid: str,
    preview: typing.Optional[bool],
):
    """
    Delete the TableImport with the specified RID.
    Deleting the table import does not delete the destination dataset but the dataset will no longer
    be updated by this import.

    """
    result = client.connectivity.Connection.TableImport.delete(
        connection_rid=connection_rid,
        table_import_rid=table_import_rid,
        preview=preview,
    )
    click.echo(repr(result))


@connectivity_connection_table_import.command("execute")
@click.argument("connection_rid", type=str, required=True)
@click.argument("table_import_rid", type=str, required=True)
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.pass_obj
def connectivity_connection_table_import_op_execute(
    client: FoundryClient,
    connection_rid: str,
    table_import_rid: str,
    preview: typing.Optional[bool],
):
    """
    Executes the TableImport, which runs asynchronously as a [Foundry Build](https://palantir.com/docs/foundry/data-integration/builds/).
    The returned BuildRid can be used to check the status via the Orchestration API.

    """
    result = client.connectivity.Connection.TableImport.execute(
        connection_rid=connection_rid,
        table_import_rid=table_import_rid,
        preview=preview,
    )
    click.echo(repr(result))


@connectivity_connection_table_import.command("get")
@click.argument("connection_rid", type=str, required=True)
@click.argument("table_import_rid", type=str, required=True)
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.pass_obj
def connectivity_connection_table_import_op_get(
    client: FoundryClient,
    connection_rid: str,
    table_import_rid: str,
    preview: typing.Optional[bool],
):
    """
    Get the TableImport with the specified rid.
    """
    result = client.connectivity.Connection.TableImport.get(
        connection_rid=connection_rid,
        table_import_rid=table_import_rid,
        preview=preview,
    )
    click.echo(repr(result))


@connectivity_connection_table_import.command("list")
@click.argument("connection_rid", type=str, required=True)
@click.option(
    "--page_size", type=int, required=False, help="""The page size to use for the endpoint."""
)
@click.option(
    "--page_token",
    type=str,
    required=False,
    help="""The page token indicates where to start paging. This should be omitted from the first page's request.
To fetch the next page, clients should take the value from the `nextPageToken` field of the previous response
and use it to populate the `pageToken` field of the next request.""",
)
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.pass_obj
def connectivity_connection_table_import_op_list(
    client: FoundryClient,
    connection_rid: str,
    page_size: typing.Optional[int],
    page_token: typing.Optional[str],
    preview: typing.Optional[bool],
):
    """
    Lists all table imports defined for this connection.
    Only table imports that the user has permissions to view will be returned.

    """
    result = client.connectivity.Connection.TableImport.list(
        connection_rid=connection_rid,
        page_size=page_size,
        page_token=page_token,
        preview=preview,
    )
    click.echo(repr(result))


@connectivity_connection_table_import.command("replace")
@click.argument("connection_rid", type=str, required=True)
@click.argument("table_import_rid", type=str, required=True)
@click.option("--config", type=str, required=True, help="""""")
@click.option("--display_name", type=str, required=True, help="""""")
@click.option(
    "--import_mode", type=click.Choice(["SNAPSHOT", "APPEND"]), required=True, help=""""""
)
@click.option(
    "--allow_schema_changes",
    type=bool,
    required=False,
    help="""Allow the TableImport to succeed if the schema of imported rows does not match the existing dataset's schema. Defaults to false for new table imports.""",
)
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.pass_obj
def connectivity_connection_table_import_op_replace(
    client: FoundryClient,
    connection_rid: str,
    table_import_rid: str,
    config: str,
    display_name: str,
    import_mode: typing.Literal["SNAPSHOT", "APPEND"],
    allow_schema_changes: typing.Optional[bool],
    preview: typing.Optional[bool],
):
    """
    Replace the TableImport with the specified rid.
    """
    result = client.connectivity.Connection.TableImport.replace(
        connection_rid=connection_rid,
        table_import_rid=table_import_rid,
        config=json.loads(config),
        display_name=display_name,
        import_mode=import_mode,
        allow_schema_changes=allow_schema_changes,
        preview=preview,
    )
    click.echo(repr(result))


@connectivity_connection.group("file_import")
def connectivity_connection_file_import():
    pass


@connectivity_connection_file_import.command("create")
@click.argument("connection_rid", type=str, required=True)
@click.option(
    "--dataset_rid",
    type=str,
    required=True,
    help="""The RID of the output dataset. Can not be modified after the file import is created.""",
)
@click.option("--display_name", type=str, required=True, help="""""")
@click.option(
    "--file_import_filters",
    type=str,
    required=True,
    help="""Use filters to limit which files should be imported. Filters are applied in the order they are defined. A different ordering of filters may lead to a more optimized import. [Learn more about optimizing file imports.](https://palantir.com/docs/foundry/data-connection/file-based-syncs/#optimize-file-based-syncs)""",
)
@click.option(
    "--import_mode", type=click.Choice(["SNAPSHOT", "APPEND", "UPDATE"]), required=True, help=""""""
)
@click.option(
    "--branch_name",
    type=str,
    required=False,
    help="""The branch name in the output dataset that will contain the imported data. Defaults to `master` for most enrollments. Can not be modified after the file import is created.""",
)
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.option(
    "--subfolder",
    type=str,
    required=False,
    help="""A subfolder in the external system that will be imported. If not specified, defaults to the root folder of the external system.""",
)
@click.pass_obj
def connectivity_connection_file_import_op_create(
    client: FoundryClient,
    connection_rid: str,
    dataset_rid: str,
    display_name: str,
    file_import_filters: str,
    import_mode: typing.Literal["SNAPSHOT", "APPEND", "UPDATE"],
    branch_name: typing.Optional[str],
    preview: typing.Optional[bool],
    subfolder: typing.Optional[str],
):
    """
    Creates a new FileImport.
    """
    result = client.connectivity.Connection.FileImport.create(
        connection_rid=connection_rid,
        dataset_rid=dataset_rid,
        display_name=display_name,
        file_import_filters=json.loads(file_import_filters),
        import_mode=import_mode,
        branch_name=branch_name,
        preview=preview,
        subfolder=subfolder,
    )
    click.echo(repr(result))


@connectivity_connection_file_import.command("delete")
@click.argument("connection_rid", type=str, required=True)
@click.argument("file_import_rid", type=str, required=True)
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.pass_obj
def connectivity_connection_file_import_op_delete(
    client: FoundryClient,
    connection_rid: str,
    file_import_rid: str,
    preview: typing.Optional[bool],
):
    """
    Delete the FileImport with the specified RID.
    Deleting the file import does not delete the destination dataset but the dataset will no longer
    be updated by this import.

    """
    result = client.connectivity.Connection.FileImport.delete(
        connection_rid=connection_rid,
        file_import_rid=file_import_rid,
        preview=preview,
    )
    click.echo(repr(result))


@connectivity_connection_file_import.command("execute")
@click.argument("connection_rid", type=str, required=True)
@click.argument("file_import_rid", type=str, required=True)
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.pass_obj
def connectivity_connection_file_import_op_execute(
    client: FoundryClient,
    connection_rid: str,
    file_import_rid: str,
    preview: typing.Optional[bool],
):
    """
    Executes the FileImport, which runs asynchronously as a [Foundry Build](https://palantir.com/docs/foundry/data-integration/builds/).
    The returned BuildRid can be used to check the status via the Orchestration API.

    """
    result = client.connectivity.Connection.FileImport.execute(
        connection_rid=connection_rid,
        file_import_rid=file_import_rid,
        preview=preview,
    )
    click.echo(repr(result))


@connectivity_connection_file_import.command("get")
@click.argument("connection_rid", type=str, required=True)
@click.argument("file_import_rid", type=str, required=True)
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.pass_obj
def connectivity_connection_file_import_op_get(
    client: FoundryClient,
    connection_rid: str,
    file_import_rid: str,
    preview: typing.Optional[bool],
):
    """
    Get the FileImport with the specified rid.
    """
    result = client.connectivity.Connection.FileImport.get(
        connection_rid=connection_rid,
        file_import_rid=file_import_rid,
        preview=preview,
    )
    click.echo(repr(result))


@connectivity_connection_file_import.command("list")
@click.argument("connection_rid", type=str, required=True)
@click.option(
    "--page_size", type=int, required=False, help="""The page size to use for the endpoint."""
)
@click.option(
    "--page_token",
    type=str,
    required=False,
    help="""The page token indicates where to start paging. This should be omitted from the first page's request.
To fetch the next page, clients should take the value from the `nextPageToken` field of the previous response
and use it to populate the `pageToken` field of the next request.""",
)
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.pass_obj
def connectivity_connection_file_import_op_list(
    client: FoundryClient,
    connection_rid: str,
    page_size: typing.Optional[int],
    page_token: typing.Optional[str],
    preview: typing.Optional[bool],
):
    """
    Lists all file imports defined for this connection.
    Only file imports that the user has permissions to view will be returned.

    """
    result = client.connectivity.Connection.FileImport.list(
        connection_rid=connection_rid,
        page_size=page_size,
        page_token=page_token,
        preview=preview,
    )
    click.echo(repr(result))


@connectivity_connection_file_import.command("replace")
@click.argument("connection_rid", type=str, required=True)
@click.argument("file_import_rid", type=str, required=True)
@click.option("--display_name", type=str, required=True, help="""""")
@click.option(
    "--file_import_filters",
    type=str,
    required=True,
    help="""Use filters to limit which files should be imported. Filters are applied in the order they are defined. A different ordering of filters may lead to a more optimized import. [Learn more about optimizing file imports.](https://palantir.com/docs/foundry/data-connection/file-based-syncs/#optimize-file-based-syncs)""",
)
@click.option(
    "--import_mode", type=click.Choice(["SNAPSHOT", "APPEND", "UPDATE"]), required=True, help=""""""
)
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.option(
    "--subfolder",
    type=str,
    required=False,
    help="""A subfolder in the external system that will be imported. If not specified, defaults to the root folder of the external system.""",
)
@click.pass_obj
def connectivity_connection_file_import_op_replace(
    client: FoundryClient,
    connection_rid: str,
    file_import_rid: str,
    display_name: str,
    file_import_filters: str,
    import_mode: typing.Literal["SNAPSHOT", "APPEND", "UPDATE"],
    preview: typing.Optional[bool],
    subfolder: typing.Optional[str],
):
    """
    Replace the FileImport with the specified rid.
    """
    result = client.connectivity.Connection.FileImport.replace(
        connection_rid=connection_rid,
        file_import_rid=file_import_rid,
        display_name=display_name,
        file_import_filters=json.loads(file_import_filters),
        import_mode=import_mode,
        preview=preview,
        subfolder=subfolder,
    )
    click.echo(repr(result))


@cli.group("core")
def core():
    pass


@cli.group("data_health")
def data_health():
    pass


@data_health.group("check")
def data_health_check():
    pass


@data_health_check.command("create")
@click.option("--config", type=str, required=True, help="""""")
@click.option("--intent", type=str, required=False, help="""""")
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.pass_obj
def data_health_check_op_create(
    client: FoundryClient,
    config: str,
    intent: typing.Optional[str],
    preview: typing.Optional[bool],
):
    """
    Creates a new Check.
    """
    result = client.data_health.Check.create(
        config=json.loads(config),
        intent=intent,
        preview=preview,
    )
    click.echo(repr(result))


@data_health_check.command("delete")
@click.argument("check_rid", type=str, required=True)
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.pass_obj
def data_health_check_op_delete(
    client: FoundryClient,
    check_rid: str,
    preview: typing.Optional[bool],
):
    """
    Delete the Check with the specified rid.
    """
    result = client.data_health.Check.delete(
        check_rid=check_rid,
        preview=preview,
    )
    click.echo(repr(result))


@data_health_check.command("get")
@click.argument("check_rid", type=str, required=True)
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.pass_obj
def data_health_check_op_get(
    client: FoundryClient,
    check_rid: str,
    preview: typing.Optional[bool],
):
    """
    Get the Check with the specified rid.
    """
    result = client.data_health.Check.get(
        check_rid=check_rid,
        preview=preview,
    )
    click.echo(repr(result))


@data_health_check.command("replace")
@click.argument("check_rid", type=str, required=True)
@click.option("--config", type=str, required=True, help="""""")
@click.option("--intent", type=str, required=False, help="""""")
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.pass_obj
def data_health_check_op_replace(
    client: FoundryClient,
    check_rid: str,
    config: str,
    intent: typing.Optional[str],
    preview: typing.Optional[bool],
):
    """
    Replace the Check with the specified rid. Changing the type of a check after it has been created  is not supported.
    """
    result = client.data_health.Check.replace(
        check_rid=check_rid,
        config=json.loads(config),
        intent=intent,
        preview=preview,
    )
    click.echo(repr(result))


@cli.group("datasets")
def datasets():
    pass


@datasets.group("view")
def datasets_view():
    pass


@datasets_view.command("add_backing_datasets")
@click.argument("view_dataset_rid", type=str, required=True)
@click.option("--backing_datasets", type=str, required=True, help="""""")
@click.option("--branch", type=str, required=False, help="""""")
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.pass_obj
def datasets_view_op_add_backing_datasets(
    client: FoundryClient,
    view_dataset_rid: str,
    backing_datasets: str,
    branch: typing.Optional[str],
    preview: typing.Optional[bool],
):
    """
    Adds one or more backing datasets to a View. Any duplicates with the same dataset RID and branch name are
    ignored.

    """
    result = client.datasets.View.add_backing_datasets(
        view_dataset_rid=view_dataset_rid,
        backing_datasets=json.loads(backing_datasets),
        branch=branch,
        preview=preview,
    )
    click.echo(repr(result))


@datasets_view.command("add_primary_key")
@click.argument("view_dataset_rid", type=str, required=True)
@click.option("--primary_key", type=str, required=True, help="""""")
@click.option("--branch", type=str, required=False, help="""""")
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.pass_obj
def datasets_view_op_add_primary_key(
    client: FoundryClient,
    view_dataset_rid: str,
    primary_key: str,
    branch: typing.Optional[str],
    preview: typing.Optional[bool],
):
    """
    Adds a primary key to a View that does not already have one. Primary keys are treated as
    guarantees provided by the creator of the dataset.

    """
    result = client.datasets.View.add_primary_key(
        view_dataset_rid=view_dataset_rid,
        primary_key=json.loads(primary_key),
        branch=branch,
        preview=preview,
    )
    click.echo(repr(result))


@datasets_view.command("create")
@click.option("--backing_datasets", type=str, required=True, help="""""")
@click.option("--parent_folder_rid", type=str, required=True, help="""""")
@click.option("--view_name", type=str, required=True, help="""""")
@click.option(
    "--branch",
    type=str,
    required=False,
    help="""The branch name of the View. If not specified, defaults to `master` for most enrollments.""",
)
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.option("--primary_key", type=str, required=False, help="""""")
@click.pass_obj
def datasets_view_op_create(
    client: FoundryClient,
    backing_datasets: str,
    parent_folder_rid: str,
    view_name: str,
    branch: typing.Optional[str],
    preview: typing.Optional[bool],
    primary_key: typing.Optional[str],
):
    """
    Create a new View.
    """
    result = client.datasets.View.create(
        backing_datasets=json.loads(backing_datasets),
        parent_folder_rid=parent_folder_rid,
        view_name=view_name,
        branch=branch,
        preview=preview,
        primary_key=None if primary_key is None else json.loads(primary_key),
    )
    click.echo(repr(result))


@datasets_view.command("get")
@click.argument("view_dataset_rid", type=str, required=True)
@click.option("--branch", type=str, required=False, help="""""")
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.pass_obj
def datasets_view_op_get(
    client: FoundryClient,
    view_dataset_rid: str,
    branch: typing.Optional[str],
    preview: typing.Optional[bool],
):
    """
    Get metadata for a View.
    """
    result = client.datasets.View.get(
        view_dataset_rid=view_dataset_rid,
        branch=branch,
        preview=preview,
    )
    click.echo(repr(result))


@datasets_view.command("remove_backing_datasets")
@click.argument("view_dataset_rid", type=str, required=True)
@click.option("--backing_datasets", type=str, required=True, help="""""")
@click.option("--branch", type=str, required=False, help="""""")
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.pass_obj
def datasets_view_op_remove_backing_datasets(
    client: FoundryClient,
    view_dataset_rid: str,
    backing_datasets: str,
    branch: typing.Optional[str],
    preview: typing.Optional[bool],
):
    """
    Removes specified backing datasets from a View. Removing a dataset triggers a
    [SNAPSHOT](https://palantir.com/docs/foundry/data-integration/datasets#snapshot) transaction on the next update. If a
    specified dataset does not exist, no error is thrown.

    """
    result = client.datasets.View.remove_backing_datasets(
        view_dataset_rid=view_dataset_rid,
        backing_datasets=json.loads(backing_datasets),
        branch=branch,
        preview=preview,
    )
    click.echo(repr(result))


@datasets_view.command("replace_backing_datasets")
@click.argument("view_dataset_rid", type=str, required=True)
@click.option("--backing_datasets", type=str, required=True, help="""""")
@click.option("--branch", type=str, required=False, help="""""")
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.pass_obj
def datasets_view_op_replace_backing_datasets(
    client: FoundryClient,
    view_dataset_rid: str,
    backing_datasets: str,
    branch: typing.Optional[str],
    preview: typing.Optional[bool],
):
    """
    Replaces the backing datasets for a View. Removing any backing dataset triggers a
    [SNAPSHOT](https://palantir.com/docs/foundry/data-integration/datasets#snapshot) transaction the next time the View is updated.

    """
    result = client.datasets.View.replace_backing_datasets(
        view_dataset_rid=view_dataset_rid,
        backing_datasets=json.loads(backing_datasets),
        branch=branch,
        preview=preview,
    )
    click.echo(repr(result))


@datasets.group("dataset")
def datasets_dataset():
    pass


@datasets_dataset.command("create")
@click.option("--name", type=str, required=True, help="""""")
@click.option("--parent_folder_rid", type=str, required=True, help="""""")
@click.pass_obj
def datasets_dataset_op_create(
    client: FoundryClient,
    name: str,
    parent_folder_rid: str,
):
    """
    Creates a new Dataset. A default branch - `master` for most enrollments - will be created on the Dataset.

    """
    result = client.datasets.Dataset.create(
        name=name,
        parent_folder_rid=parent_folder_rid,
    )
    click.echo(repr(result))


@datasets_dataset.command("get")
@click.argument("dataset_rid", type=str, required=True)
@click.pass_obj
def datasets_dataset_op_get(
    client: FoundryClient,
    dataset_rid: str,
):
    """
    Get the Dataset with the specified rid.
    """
    result = client.datasets.Dataset.get(
        dataset_rid=dataset_rid,
    )
    click.echo(repr(result))


@datasets_dataset.command("get_health_checks")
@click.argument("dataset_rid", type=str, required=True)
@click.option(
    "--branch_name",
    type=str,
    required=False,
    help="""The name of the Branch. If none is provided, the default Branch name - `master` for most enrollments - will be used.
""",
)
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.pass_obj
def datasets_dataset_op_get_health_checks(
    client: FoundryClient,
    dataset_rid: str,
    branch_name: typing.Optional[str],
    preview: typing.Optional[bool],
):
    """
    Get the RIDs of the Data Health Checks that are configured for the given Dataset.

    """
    result = client.datasets.Dataset.get_health_checks(
        dataset_rid=dataset_rid,
        branch_name=branch_name,
        preview=preview,
    )
    click.echo(repr(result))


@datasets_dataset.command("get_schedules")
@click.argument("dataset_rid", type=str, required=True)
@click.option(
    "--branch_name",
    type=str,
    required=False,
    help="""The name of the Branch. If none is provided, the default Branch name - `master` for most enrollments - will be used.
""",
)
@click.option("--page_size", type=int, required=False, help="""""")
@click.option("--page_token", type=str, required=False, help="""""")
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.pass_obj
def datasets_dataset_op_get_schedules(
    client: FoundryClient,
    dataset_rid: str,
    branch_name: typing.Optional[str],
    page_size: typing.Optional[int],
    page_token: typing.Optional[str],
    preview: typing.Optional[bool],
):
    """
    Get the RIDs of the Schedules that target the given Dataset

    """
    result = client.datasets.Dataset.get_schedules(
        dataset_rid=dataset_rid,
        branch_name=branch_name,
        page_size=page_size,
        page_token=page_token,
        preview=preview,
    )
    click.echo(repr(result))


@datasets_dataset.command("get_schema")
@click.argument("dataset_rid", type=str, required=True)
@click.option("--branch_name", type=str, required=False, help="""""")
@click.option(
    "--end_transaction_rid",
    type=str,
    required=False,
    help="""The Resource Identifier (RID) of the end Transaction. If a user does not provide a value, the RID of the latest committed transaction will be used.
""",
)
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.option(
    "--version_id",
    type=str,
    required=False,
    help="""The schema version that should be used. If none is provided, the latest version will be used.
""",
)
@click.pass_obj
def datasets_dataset_op_get_schema(
    client: FoundryClient,
    dataset_rid: str,
    branch_name: typing.Optional[str],
    end_transaction_rid: typing.Optional[str],
    preview: typing.Optional[bool],
    version_id: typing.Optional[str],
):
    """
    Gets a dataset's schema. If no `endTransactionRid` is provided, the latest committed version will be used.

    """
    result = client.datasets.Dataset.get_schema(
        dataset_rid=dataset_rid,
        branch_name=branch_name,
        end_transaction_rid=end_transaction_rid,
        preview=preview,
        version_id=version_id,
    )
    click.echo(repr(result))


@datasets_dataset.command("jobs")
@click.argument("dataset_rid", type=str, required=True)
@click.option("--order_by", type=str, required=True, help="""""")
@click.option(
    "--branch_name",
    type=str,
    required=False,
    help="""The name of the Branch. If none is provided, the default Branch name - `master` for most enrollments - will be used.
""",
)
@click.option(
    "--page_size",
    type=int,
    required=False,
    help="""Max number of results to return. A limit of 1000 on if no limit is supplied in the search request
""",
)
@click.option("--page_token", type=str, required=False, help="""""")
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.option("--where", type=str, required=False, help="""""")
@click.pass_obj
def datasets_dataset_op_jobs(
    client: FoundryClient,
    dataset_rid: str,
    order_by: str,
    branch_name: typing.Optional[str],
    page_size: typing.Optional[int],
    page_token: typing.Optional[str],
    preview: typing.Optional[bool],
    where: typing.Optional[str],
):
    """
    Get the RIDs of the Jobs for the given dataset. By default, returned Jobs are sorted in descending order by the Job start time.

    """
    result = client.datasets.Dataset.jobs(
        dataset_rid=dataset_rid,
        order_by=json.loads(order_by),
        branch_name=branch_name,
        page_size=page_size,
        page_token=page_token,
        preview=preview,
        where=None if where is None else json.loads(where),
    )
    click.echo(repr(result))


@datasets_dataset.command("put_schema")
@click.argument("dataset_rid", type=str, required=True)
@click.option(
    "--schema",
    type=str,
    required=True,
    help="""The schema that will be added.
""",
)
@click.option("--branch_name", type=str, required=False, help="""""")
@click.option(
    "--dataframe_reader",
    type=click.Choice(["AVRO", "CSV", "PARQUET", "DATASOURCE"]),
    required=False,
    help="""The dataframe reader used for reading the dataset schema. Defaults to PARQUET.""",
)
@click.option(
    "--end_transaction_rid",
    type=str,
    required=False,
    help="""The Resource Identifier (RID) of the end Transaction.
""",
)
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.pass_obj
def datasets_dataset_op_put_schema(
    client: FoundryClient,
    dataset_rid: str,
    schema: str,
    branch_name: typing.Optional[str],
    dataframe_reader: typing.Optional[typing.Literal["AVRO", "CSV", "PARQUET", "DATASOURCE"]],
    end_transaction_rid: typing.Optional[str],
    preview: typing.Optional[bool],
):
    """
    Adds a schema on an existing dataset using a PUT request.

    """
    result = client.datasets.Dataset.put_schema(
        dataset_rid=dataset_rid,
        schema=json.loads(schema),
        branch_name=branch_name,
        dataframe_reader=dataframe_reader,
        end_transaction_rid=end_transaction_rid,
        preview=preview,
    )
    click.echo(repr(result))


@datasets_dataset.command("read_table")
@click.argument("dataset_rid", type=str, required=True)
@click.option(
    "--format",
    type=click.Choice(["ARROW", "CSV"]),
    required=True,
    help="""The export format. Must be `ARROW` or `CSV`.
""",
)
@click.option(
    "--branch_name",
    type=str,
    required=False,
    help="""The name of the Branch.
""",
)
@click.option(
    "--columns",
    type=str,
    required=False,
    help="""A subset of the dataset columns to include in the result. Defaults to all columns.
""",
)
@click.option(
    "--end_transaction_rid",
    type=str,
    required=False,
    help="""The Resource Identifier (RID) of the end Transaction.
""",
)
@click.option(
    "--row_limit",
    type=int,
    required=False,
    help="""A limit on the number of rows to return. Note that row ordering is non-deterministic.
""",
)
@click.option(
    "--start_transaction_rid",
    type=str,
    required=False,
    help="""The Resource Identifier (RID) of the start Transaction.
""",
)
@click.pass_obj
def datasets_dataset_op_read_table(
    client: FoundryClient,
    dataset_rid: str,
    format: typing.Literal["ARROW", "CSV"],
    branch_name: typing.Optional[str],
    columns: typing.Optional[str],
    end_transaction_rid: typing.Optional[str],
    row_limit: typing.Optional[int],
    start_transaction_rid: typing.Optional[str],
):
    """
    Gets the content of a dataset as a table in the specified format.

    This endpoint currently does not support views (virtual datasets composed of other datasets).

    """
    result = client.datasets.Dataset.read_table(
        dataset_rid=dataset_rid,
        format=format,
        branch_name=branch_name,
        columns=None if columns is None else json.loads(columns),
        end_transaction_rid=end_transaction_rid,
        row_limit=row_limit,
        start_transaction_rid=start_transaction_rid,
    )
    click.echo(result)


@datasets_dataset.command("transactions")
@click.argument("dataset_rid", type=str, required=True)
@click.option(
    "--page_size", type=int, required=False, help="""The page size to use for the endpoint."""
)
@click.option(
    "--page_token",
    type=str,
    required=False,
    help="""The page token indicates where to start paging. This should be omitted from the first page's request.
To fetch the next page, clients should take the value from the `nextPageToken` field of the previous response
and use it to populate the `pageToken` field of the next request.""",
)
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.pass_obj
def datasets_dataset_op_transactions(
    client: FoundryClient,
    dataset_rid: str,
    page_size: typing.Optional[int],
    page_token: typing.Optional[str],
    preview: typing.Optional[bool],
):
    """
    Get the Transaction history for the given Dataset

    """
    result = client.datasets.Dataset.transactions(
        dataset_rid=dataset_rid,
        page_size=page_size,
        page_token=page_token,
        preview=preview,
    )
    click.echo(repr(result))


@datasets_dataset.group("file")
def datasets_dataset_file():
    pass


@datasets_dataset_file.command("content")
@click.argument("dataset_rid", type=str, required=True)
@click.argument("file_path", type=str, required=True)
@click.option(
    "--branch_name",
    type=str,
    required=False,
    help="""The name of the Branch that contains the File. Defaults to `master` for most enrollments.
""",
)
@click.option(
    "--end_transaction_rid",
    type=str,
    required=False,
    help="""The Resource Identifier (RID) of the end Transaction.
""",
)
@click.option(
    "--start_transaction_rid",
    type=str,
    required=False,
    help="""The Resource Identifier (RID) of the start Transaction.
""",
)
@click.pass_obj
def datasets_dataset_file_op_content(
    client: FoundryClient,
    dataset_rid: str,
    file_path: str,
    branch_name: typing.Optional[str],
    end_transaction_rid: typing.Optional[str],
    start_transaction_rid: typing.Optional[str],
):
    """
    Gets the content of a File contained in a Dataset. By default this retrieves the file's content from the latest
    view of the default branch - `master` for most enrollments.
    #### Advanced Usage
    See [Datasets Core Concepts](https://palantir.com/docs/foundry/data-integration/datasets/) for details on using branches and transactions.
    To **get a file's content from a specific Branch** specify the Branch's name as `branchName`. This will
    retrieve the content for the most recent version of the file since the latest snapshot transaction, or the
    earliest ancestor transaction of the branch if there are no snapshot transactions.
    To **get a file's content from the resolved view of a transaction** specify the Transaction's resource identifier
    as `endTransactionRid`. This will retrieve the content for the most recent version of the file since the latest
    snapshot transaction, or the earliest ancestor transaction if there are no snapshot transactions.
    To **get a file's content from the resolved view of a range of transactions** specify the the start transaction's
    resource identifier as `startTransactionRid` and the end transaction's resource identifier as `endTransactionRid`.
    This will retrieve the content for the most recent version of the file since the `startTransactionRid` up to the
    `endTransactionRid`. Note that an intermediate snapshot transaction will remove all files from the view. Behavior
    is undefined when the start and end transactions do not belong to the same root-to-leaf path.
    To **get a file's content from a specific transaction** specify the Transaction's resource identifier as both the
    `startTransactionRid` and `endTransactionRid`.

    """
    result = client.datasets.Dataset.File.content(
        dataset_rid=dataset_rid,
        file_path=file_path,
        branch_name=branch_name,
        end_transaction_rid=end_transaction_rid,
        start_transaction_rid=start_transaction_rid,
    )
    click.echo(result)


@datasets_dataset_file.command("delete")
@click.argument("dataset_rid", type=str, required=True)
@click.argument("file_path", type=str, required=True)
@click.option(
    "--branch_name",
    type=str,
    required=False,
    help="""The name of the Branch on which to delete the File. Defaults to `master` for most enrollments.
""",
)
@click.option(
    "--transaction_rid",
    type=str,
    required=False,
    help="""The Resource Identifier (RID) of the open delete Transaction on which to delete the File.
""",
)
@click.pass_obj
def datasets_dataset_file_op_delete(
    client: FoundryClient,
    dataset_rid: str,
    file_path: str,
    branch_name: typing.Optional[str],
    transaction_rid: typing.Optional[str],
):
    """
    Deletes a File from a Dataset. By default the file is deleted in a new transaction on the default
    branch - `master` for most enrollments. The file will still be visible on historical views.
    #### Advanced Usage
    See [Datasets Core Concepts](https://palantir.com/docs/foundry/data-integration/datasets/) for details on using branches and transactions.
    To **delete a File from a specific Branch** specify the Branch's name as `branchName`. A new delete Transaction
    will be created and committed on this branch.
    To **delete a File using a manually opened Transaction**, specify the Transaction's resource identifier
    as `transactionRid`. The transaction must be of type `DELETE`. This is useful for deleting multiple files in a
    single transaction. See [createTransaction](https://palantir.com/docs/foundry/api/datasets-resources/transactions/create-transaction/) to
    open a transaction.

    """
    result = client.datasets.Dataset.File.delete(
        dataset_rid=dataset_rid,
        file_path=file_path,
        branch_name=branch_name,
        transaction_rid=transaction_rid,
    )
    click.echo(repr(result))


@datasets_dataset_file.command("get")
@click.argument("dataset_rid", type=str, required=True)
@click.argument("file_path", type=str, required=True)
@click.option(
    "--branch_name",
    type=str,
    required=False,
    help="""The name of the Branch that contains the File. Defaults to `master` for most enrollments.
""",
)
@click.option(
    "--end_transaction_rid",
    type=str,
    required=False,
    help="""The Resource Identifier (RID) of the end Transaction.
""",
)
@click.option(
    "--start_transaction_rid",
    type=str,
    required=False,
    help="""The Resource Identifier (RID) of the start Transaction.
""",
)
@click.pass_obj
def datasets_dataset_file_op_get(
    client: FoundryClient,
    dataset_rid: str,
    file_path: str,
    branch_name: typing.Optional[str],
    end_transaction_rid: typing.Optional[str],
    start_transaction_rid: typing.Optional[str],
):
    """
    Gets metadata about a File contained in a Dataset. By default this retrieves the file's metadata from the latest
    view of the default branch - `master` for most enrollments.
    #### Advanced Usage
    See [Datasets Core Concepts](https://palantir.com/docs/foundry/data-integration/datasets/) for details on using branches and transactions.
    To **get a file's metadata from a specific Branch** specify the Branch's name as `branchName`. This will
    retrieve metadata for the most recent version of the file since the latest snapshot transaction, or the earliest
    ancestor transaction of the branch if there are no snapshot transactions.
    To **get a file's metadata from the resolved view of a transaction** specify the Transaction's resource identifier
    as `endTransactionRid`. This will retrieve metadata for the most recent version of the file since the latest snapshot
    transaction, or the earliest ancestor transaction if there are no snapshot transactions.
    To **get a file's metadata from the resolved view of a range of transactions** specify the the start transaction's
    resource identifier as `startTransactionRid` and the end transaction's resource identifier as `endTransactionRid`.
    This will retrieve metadata for the most recent version of the file since the `startTransactionRid` up to the
    `endTransactionRid`. Behavior is undefined when the start and end transactions do not belong to the same root-to-leaf path.
    To **get a file's metadata from a specific transaction** specify the Transaction's resource identifier as both the
    `startTransactionRid` and `endTransactionRid`.

    """
    result = client.datasets.Dataset.File.get(
        dataset_rid=dataset_rid,
        file_path=file_path,
        branch_name=branch_name,
        end_transaction_rid=end_transaction_rid,
        start_transaction_rid=start_transaction_rid,
    )
    click.echo(repr(result))


@datasets_dataset_file.command("list")
@click.argument("dataset_rid", type=str, required=True)
@click.option(
    "--branch_name",
    type=str,
    required=False,
    help="""The name of the Branch on which to list Files. Defaults to `master` for most enrollments.
""",
)
@click.option(
    "--end_transaction_rid",
    type=str,
    required=False,
    help="""The Resource Identifier (RID) of the end Transaction.
""",
)
@click.option(
    "--page_size", type=int, required=False, help="""The page size to use for the endpoint."""
)
@click.option(
    "--page_token",
    type=str,
    required=False,
    help="""The page token indicates where to start paging. This should be omitted from the first page's request.
To fetch the next page, clients should take the value from the `nextPageToken` field of the previous response
and use it to populate the `pageToken` field of the next request.""",
)
@click.option(
    "--start_transaction_rid",
    type=str,
    required=False,
    help="""The Resource Identifier (RID) of the start Transaction.
""",
)
@click.pass_obj
def datasets_dataset_file_op_list(
    client: FoundryClient,
    dataset_rid: str,
    branch_name: typing.Optional[str],
    end_transaction_rid: typing.Optional[str],
    page_size: typing.Optional[int],
    page_token: typing.Optional[str],
    start_transaction_rid: typing.Optional[str],
):
    """
    Lists Files contained in a Dataset. By default files are listed on the latest view of the default
    branch - `master` for most enrollments.
    #### Advanced Usage
    See [Datasets Core Concepts](https://palantir.com/docs/foundry/data-integration/datasets/) for details on using branches and transactions.
    To **list files on a specific Branch** specify the Branch's name as `branchName`. This will include the most
    recent version of all files since the latest snapshot transaction, or the earliest ancestor transaction of the
    branch if there are no snapshot transactions.
    To **list files on the resolved view of a transaction** specify the Transaction's resource identifier
    as `endTransactionRid`. This will include the most recent version of all files since the latest snapshot
    transaction, or the earliest ancestor transaction if there are no snapshot transactions.
    To **list files on the resolved view of a range of transactions** specify the the start transaction's resource
    identifier as `startTransactionRid` and the end transaction's resource identifier as `endTransactionRid`. This
    will include the most recent version of all files since the `startTransactionRid` up to the `endTransactionRid`.
    Note that an intermediate snapshot transaction will remove all files from the view. Behavior is undefined when
    the start and end transactions do not belong to the same root-to-leaf path.
    To **list files on a specific transaction** specify the Transaction's resource identifier as both the
    `startTransactionRid` and `endTransactionRid`. This will include only files that were modified as part of that
    Transaction.

    """
    result = client.datasets.Dataset.File.list(
        dataset_rid=dataset_rid,
        branch_name=branch_name,
        end_transaction_rid=end_transaction_rid,
        page_size=page_size,
        page_token=page_token,
        start_transaction_rid=start_transaction_rid,
    )
    click.echo(repr(result))


@datasets_dataset_file.command("upload")
@click.argument("dataset_rid", type=str, required=True)
@click.argument("file_path", type=str, required=True)
@click.argument("body", type=click.File("rb"), required=True)
@click.option(
    "--branch_name",
    type=str,
    required=False,
    help="""The name of the Branch on which to upload the File. Defaults to `master` for most enrollments.
""",
)
@click.option(
    "--transaction_rid",
    type=str,
    required=False,
    help="""The Resource Identifier (RID) of the open Transaction on which to upload the File.
""",
)
@click.option(
    "--transaction_type",
    type=click.Choice(["APPEND", "UPDATE", "SNAPSHOT", "DELETE"]),
    required=False,
    help="""The type of the Transaction to create when using branchName. Defaults to `UPDATE`.
""",
)
@click.pass_obj
def datasets_dataset_file_op_upload(
    client: FoundryClient,
    dataset_rid: str,
    file_path: str,
    body: io.BufferedReader,
    branch_name: typing.Optional[str],
    transaction_rid: typing.Optional[str],
    transaction_type: typing.Optional[typing.Literal["APPEND", "UPDATE", "SNAPSHOT", "DELETE"]],
):
    """
    Uploads a File to an existing Dataset.
    The body of the request must contain the binary content of the file and the `Content-Type` header must be `application/octet-stream`.
    By default the file is uploaded to a new transaction on the default branch - `master` for most enrollments.
    If the file already exists only the most recent version will be visible in the updated view.
    #### Advanced Usage
    See [Datasets Core Concepts](https://palantir.com/docs/foundry/data-integration/datasets/) for details on using branches and transactions.
    To **upload a file to a specific Branch** specify the Branch's name as `branchName`. A new transaction will
    be created and committed on this branch. By default the TransactionType will be `UPDATE`, to override this
    default specify `transactionType` in addition to `branchName`.
    See [createBranch](https://palantir.com/docs/foundry/api/datasets-resources/branches/create-branch/) to create a custom branch.
    To **upload a file on a manually opened transaction** specify the Transaction's resource identifier as
    `transactionRid`. This is useful for uploading multiple files in a single transaction.
    See [createTransaction](https://palantir.com/docs/foundry/api/datasets-resources/transactions/create-transaction/) to open a transaction.

    """
    result = client.datasets.Dataset.File.upload(
        dataset_rid=dataset_rid,
        file_path=file_path,
        body=body.read(),
        branch_name=branch_name,
        transaction_rid=transaction_rid,
        transaction_type=transaction_type,
    )
    click.echo(repr(result))


@datasets_dataset.group("transaction")
def datasets_dataset_transaction():
    pass


@datasets_dataset_transaction.command("abort")
@click.argument("dataset_rid", type=str, required=True)
@click.argument("transaction_rid", type=str, required=True)
@click.pass_obj
def datasets_dataset_transaction_op_abort(
    client: FoundryClient,
    dataset_rid: str,
    transaction_rid: str,
):
    """
    Aborts an open Transaction. File modifications made on this Transaction are not preserved and the Branch is
    not updated.

    """
    result = client.datasets.Dataset.Transaction.abort(
        dataset_rid=dataset_rid,
        transaction_rid=transaction_rid,
    )
    click.echo(repr(result))


@datasets_dataset_transaction.command("build")
@click.argument("dataset_rid", type=str, required=True)
@click.argument("transaction_rid", type=str, required=True)
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.pass_obj
def datasets_dataset_transaction_op_build(
    client: FoundryClient,
    dataset_rid: str,
    transaction_rid: str,
    preview: typing.Optional[bool],
):
    """
    Get the [Build](https://palantir.com/docs/foundry/data-integration/builds#builds) that computed the
    given Transaction. Not all Transactions have an associated Build. For example, if a Dataset
    is updated by a User uploading a CSV file into the browser, no Build will be tied to the Transaction.

    """
    result = client.datasets.Dataset.Transaction.build(
        dataset_rid=dataset_rid,
        transaction_rid=transaction_rid,
        preview=preview,
    )
    click.echo(repr(result))


@datasets_dataset_transaction.command("commit")
@click.argument("dataset_rid", type=str, required=True)
@click.argument("transaction_rid", type=str, required=True)
@click.pass_obj
def datasets_dataset_transaction_op_commit(
    client: FoundryClient,
    dataset_rid: str,
    transaction_rid: str,
):
    """
    Commits an open Transaction. File modifications made on this Transaction are preserved and the Branch is
    updated to point to the Transaction.

    """
    result = client.datasets.Dataset.Transaction.commit(
        dataset_rid=dataset_rid,
        transaction_rid=transaction_rid,
    )
    click.echo(repr(result))


@datasets_dataset_transaction.command("create")
@click.argument("dataset_rid", type=str, required=True)
@click.option(
    "--transaction_type",
    type=click.Choice(["APPEND", "UPDATE", "SNAPSHOT", "DELETE"]),
    required=True,
    help="""""",
)
@click.option(
    "--branch_name",
    type=str,
    required=False,
    help="""The name of the Branch on which to create the Transaction. Defaults to `master` for most enrollments.
""",
)
@click.pass_obj
def datasets_dataset_transaction_op_create(
    client: FoundryClient,
    dataset_rid: str,
    transaction_type: typing.Literal["APPEND", "UPDATE", "SNAPSHOT", "DELETE"],
    branch_name: typing.Optional[str],
):
    """
    Creates a Transaction on a Branch of a Dataset.

    """
    result = client.datasets.Dataset.Transaction.create(
        dataset_rid=dataset_rid,
        transaction_type=transaction_type,
        branch_name=branch_name,
    )
    click.echo(repr(result))


@datasets_dataset_transaction.command("get")
@click.argument("dataset_rid", type=str, required=True)
@click.argument("transaction_rid", type=str, required=True)
@click.pass_obj
def datasets_dataset_transaction_op_get(
    client: FoundryClient,
    dataset_rid: str,
    transaction_rid: str,
):
    """
    Gets a Transaction of a Dataset.

    """
    result = client.datasets.Dataset.Transaction.get(
        dataset_rid=dataset_rid,
        transaction_rid=transaction_rid,
    )
    click.echo(repr(result))


@datasets_dataset_transaction.command("job")
@click.argument("dataset_rid", type=str, required=True)
@click.argument("transaction_rid", type=str, required=True)
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.pass_obj
def datasets_dataset_transaction_op_job(
    client: FoundryClient,
    dataset_rid: str,
    transaction_rid: str,
    preview: typing.Optional[bool],
):
    """
    Get the [Job](https://palantir.com/docs/foundry/data-integration/builds#jobs-and-jobspecs) that computed the
    given Transaction. Not all Transactions have an associated Job. For example, if a Dataset
    is updated by a User uploading a CSV file into the browser, no Job will be tied to the Transaction.

    """
    result = client.datasets.Dataset.Transaction.job(
        dataset_rid=dataset_rid,
        transaction_rid=transaction_rid,
        preview=preview,
    )
    click.echo(repr(result))


@datasets_dataset.group("branch")
def datasets_dataset_branch():
    pass


@datasets_dataset_branch.command("create")
@click.argument("dataset_rid", type=str, required=True)
@click.option("--name", type=str, required=True, help="""""")
@click.option(
    "--transaction_rid",
    type=str,
    required=False,
    help="""The most recent OPEN or COMMITTED transaction on the branch. This will never be an ABORTED transaction.""",
)
@click.pass_obj
def datasets_dataset_branch_op_create(
    client: FoundryClient,
    dataset_rid: str,
    name: str,
    transaction_rid: typing.Optional[str],
):
    """
    Creates a branch on an existing dataset. A branch may optionally point to a (committed) transaction.

    """
    result = client.datasets.Dataset.Branch.create(
        dataset_rid=dataset_rid,
        name=name,
        transaction_rid=transaction_rid,
    )
    click.echo(repr(result))


@datasets_dataset_branch.command("delete")
@click.argument("dataset_rid", type=str, required=True)
@click.argument("branch_name", type=str, required=True)
@click.pass_obj
def datasets_dataset_branch_op_delete(
    client: FoundryClient,
    dataset_rid: str,
    branch_name: str,
):
    """
    Deletes the Branch with the given BranchName.

    """
    result = client.datasets.Dataset.Branch.delete(
        dataset_rid=dataset_rid,
        branch_name=branch_name,
    )
    click.echo(repr(result))


@datasets_dataset_branch.command("get")
@click.argument("dataset_rid", type=str, required=True)
@click.argument("branch_name", type=str, required=True)
@click.pass_obj
def datasets_dataset_branch_op_get(
    client: FoundryClient,
    dataset_rid: str,
    branch_name: str,
):
    """
    Get a Branch of a Dataset.

    """
    result = client.datasets.Dataset.Branch.get(
        dataset_rid=dataset_rid,
        branch_name=branch_name,
    )
    click.echo(repr(result))


@datasets_dataset_branch.command("list")
@click.argument("dataset_rid", type=str, required=True)
@click.option(
    "--page_size", type=int, required=False, help="""The page size to use for the endpoint."""
)
@click.option(
    "--page_token",
    type=str,
    required=False,
    help="""The page token indicates where to start paging. This should be omitted from the first page's request.
To fetch the next page, clients should take the value from the `nextPageToken` field of the previous response
and use it to populate the `pageToken` field of the next request.""",
)
@click.pass_obj
def datasets_dataset_branch_op_list(
    client: FoundryClient,
    dataset_rid: str,
    page_size: typing.Optional[int],
    page_token: typing.Optional[str],
):
    """
    Lists the Branches of a Dataset.

    """
    result = client.datasets.Dataset.Branch.list(
        dataset_rid=dataset_rid,
        page_size=page_size,
        page_token=page_token,
    )
    click.echo(repr(result))


@datasets_dataset_branch.command("transactions")
@click.argument("dataset_rid", type=str, required=True)
@click.argument("branch_name", type=str, required=True)
@click.option(
    "--page_size",
    type=int,
    required=False,
    help="""The default pageSize is 20 transactions and the maximum allowed pageSize is 50 transactions
""",
)
@click.option("--page_token", type=str, required=False, help="""""")
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.pass_obj
def datasets_dataset_branch_op_transactions(
    client: FoundryClient,
    dataset_rid: str,
    branch_name: str,
    page_size: typing.Optional[int],
    page_token: typing.Optional[str],
    preview: typing.Optional[bool],
):
    """
    Get the Transaction history for the given Dataset.

    """
    result = client.datasets.Dataset.Branch.transactions(
        dataset_rid=dataset_rid,
        branch_name=branch_name,
        page_size=page_size,
        page_token=page_token,
        preview=preview,
    )
    click.echo(repr(result))


@cli.group("filesystem")
def filesystem():
    pass


@filesystem.group("space")
def filesystem_space():
    pass


@filesystem_space.command("create")
@click.option(
    "--deletion_policy_organizations",
    type=str,
    required=True,
    help="""By default, this Space will use a Last Out deletion policy, meaning that this Space and its projects will be deleted when the last Organization listed here is deleted. Only Organizations in the Space's Enrollment can be included here.
""",
)
@click.option("--display_name", type=str, required=True, help="""""")
@click.option(
    "--enrollment_rid",
    type=str,
    required=True,
    help="""The RID of the Enrollment that this Space belongs to.
""",
)
@click.option(
    "--organizations",
    type=str,
    required=True,
    help="""The list of Organizations that are provisioned access to this Space. In order to access this Space, a user must be a member of at least one of these Organizations.
""",
)
@click.option(
    "--default_role_set_id",
    type=str,
    required=False,
    help="""The ID of the default Role Set for this Space, which defines the set of roles that Projects in this Space must use. If not provided, the default Role Set for Projects will be used.
""",
)
@click.option("--description", type=str, required=False, help="""The description of the Space.""")
@click.option(
    "--file_system_id",
    type=str,
    required=False,
    help="""The ID of the Filesystem for this Space, which is where the contents of the Space are stored. If not provided, the default Filesystem for this Enrollment will be used.""",
)
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.option(
    "--usage_account_rid",
    type=str,
    required=False,
    help="""The RID of the Usage Account for this Space. Resource usage for projects in this space will accrue to this Usage Account by default. If not provided, the default Usage Account for this Enrollment will be used.""",
)
@click.pass_obj
def filesystem_space_op_create(
    client: FoundryClient,
    deletion_policy_organizations: str,
    display_name: str,
    enrollment_rid: str,
    organizations: str,
    default_role_set_id: typing.Optional[str],
    description: typing.Optional[str],
    file_system_id: typing.Optional[str],
    preview: typing.Optional[bool],
    usage_account_rid: typing.Optional[str],
):
    """
    Creates a new Space.
    """
    result = client.filesystem.Space.create(
        deletion_policy_organizations=json.loads(deletion_policy_organizations),
        display_name=display_name,
        enrollment_rid=enrollment_rid,
        organizations=json.loads(organizations),
        default_role_set_id=default_role_set_id,
        description=description,
        file_system_id=file_system_id,
        preview=preview,
        usage_account_rid=usage_account_rid,
    )
    click.echo(repr(result))


@filesystem_space.command("delete")
@click.argument("space_rid", type=str, required=True)
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.pass_obj
def filesystem_space_op_delete(
    client: FoundryClient,
    space_rid: str,
    preview: typing.Optional[bool],
):
    """
    Delete the space. This will only work if the Space is empty, meaning any Projects or Resources have been deleted first.

    """
    result = client.filesystem.Space.delete(
        space_rid=space_rid,
        preview=preview,
    )
    click.echo(repr(result))


@filesystem_space.command("get")
@click.argument("space_rid", type=str, required=True)
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.pass_obj
def filesystem_space_op_get(
    client: FoundryClient,
    space_rid: str,
    preview: typing.Optional[bool],
):
    """
    Get the Space with the specified rid.
    """
    result = client.filesystem.Space.get(
        space_rid=space_rid,
        preview=preview,
    )
    click.echo(repr(result))


@filesystem_space.command("list")
@click.option(
    "--page_size", type=int, required=False, help="""The page size to use for the endpoint."""
)
@click.option(
    "--page_token",
    type=str,
    required=False,
    help="""The page token indicates where to start paging. This should be omitted from the first page's request.
To fetch the next page, clients should take the value from the `nextPageToken` field of the previous response
and use it to populate the `pageToken` field of the next request.""",
)
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.pass_obj
def filesystem_space_op_list(
    client: FoundryClient,
    page_size: typing.Optional[int],
    page_token: typing.Optional[str],
    preview: typing.Optional[bool],
):
    """
    Lists all Spaces.

    This is a paged endpoint. Each page may be smaller or larger than the requested page size. However, it is guaranteed that if there are more results available, the `nextPageToken` field will be populated. To get the next page, make the same request again, but set the value of the `pageToken` query parameter to be value of the `nextPageToken` value of the previous response. If there is no `nextPageToken` field in the response, you are on the last page.
    """
    result = client.filesystem.Space.list(
        page_size=page_size,
        page_token=page_token,
        preview=preview,
    )
    click.echo(repr(result))


@filesystem_space.command("replace")
@click.argument("space_rid", type=str, required=True)
@click.option("--display_name", type=str, required=True, help="""""")
@click.option(
    "--default_role_set_id",
    type=str,
    required=False,
    help="""The ID of the default Role Set for this Space, which defines the set of roles that Projects in this Space must use. If not provided, the default Role Set for Projects will be used.
""",
)
@click.option("--description", type=str, required=False, help="""The description of the Space.""")
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.option(
    "--usage_account_rid",
    type=str,
    required=False,
    help="""The RID of the Usage Account for this Space. Resource usage for projects in this space will accrue to this Usage Account by default. If not provided, the default Usage Account for this Enrollment will be used.""",
)
@click.pass_obj
def filesystem_space_op_replace(
    client: FoundryClient,
    space_rid: str,
    display_name: str,
    default_role_set_id: typing.Optional[str],
    description: typing.Optional[str],
    preview: typing.Optional[bool],
    usage_account_rid: typing.Optional[str],
):
    """
    Replace the Space with the specified rid.
    """
    result = client.filesystem.Space.replace(
        space_rid=space_rid,
        display_name=display_name,
        default_role_set_id=default_role_set_id,
        description=description,
        preview=preview,
        usage_account_rid=usage_account_rid,
    )
    click.echo(repr(result))


@filesystem.group("resource")
def filesystem_resource():
    pass


@filesystem_resource.command("add_markings")
@click.argument("resource_rid", type=str, required=True)
@click.option("--marking_ids", type=str, required=True, help="""""")
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.pass_obj
def filesystem_resource_op_add_markings(
    client: FoundryClient,
    resource_rid: str,
    marking_ids: str,
    preview: typing.Optional[bool],
):
    """
    Adds a list of Markings to a resource.
    """
    result = client.filesystem.Resource.add_markings(
        resource_rid=resource_rid,
        marking_ids=json.loads(marking_ids),
        preview=preview,
    )
    click.echo(repr(result))


@filesystem_resource.command("delete")
@click.argument("resource_rid", type=str, required=True)
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.pass_obj
def filesystem_resource_op_delete(
    client: FoundryClient,
    resource_rid: str,
    preview: typing.Optional[bool],
):
    """
    Move the given resource to the trash. Following this operation, the resource can be restored, using the
    `restore` operation, or permanently deleted using the `permanentlyDelete` operation.

    """
    result = client.filesystem.Resource.delete(
        resource_rid=resource_rid,
        preview=preview,
    )
    click.echo(repr(result))


@filesystem_resource.command("get")
@click.argument("resource_rid", type=str, required=True)
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.pass_obj
def filesystem_resource_op_get(
    client: FoundryClient,
    resource_rid: str,
    preview: typing.Optional[bool],
):
    """
    Get the Resource with the specified rid.
    """
    result = client.filesystem.Resource.get(
        resource_rid=resource_rid,
        preview=preview,
    )
    click.echo(repr(result))


@filesystem_resource.command("get_access_requirements")
@click.argument("resource_rid", type=str, required=True)
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.pass_obj
def filesystem_resource_op_get_access_requirements(
    client: FoundryClient,
    resource_rid: str,
    preview: typing.Optional[bool],
):
    """
    Returns a list of access requirements a user needs in order to view a resource. Access requirements are
    composed of Organizations and Markings, and can either be applied directly to the resource or inherited.

    """
    result = client.filesystem.Resource.get_access_requirements(
        resource_rid=resource_rid,
        preview=preview,
    )
    click.echo(repr(result))


@filesystem_resource.command("get_batch")
@click.argument("body", type=str, required=True)
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.pass_obj
def filesystem_resource_op_get_batch(
    client: FoundryClient,
    body: str,
    preview: typing.Optional[bool],
):
    """
    Fetches multiple resources in a single request.
    Returns a map from RID to the corresponding resource. If a resource does not exist, or if it is a root folder or space, its RID will not be included in the map.
    At most 1,000 resources should be requested at once.


    The maximum batch size for this endpoint is 1000.
    """
    result = client.filesystem.Resource.get_batch(
        body=json.loads(body),
        preview=preview,
    )
    click.echo(repr(result))


@filesystem_resource.command("get_by_path")
@click.option(
    "--path",
    type=str,
    required=True,
    help="""The path to the Resource. The leading slash is optional.""",
)
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.pass_obj
def filesystem_resource_op_get_by_path(
    client: FoundryClient,
    path: str,
    preview: typing.Optional[bool],
):
    """
    Get a Resource by its absolute path.
    """
    result = client.filesystem.Resource.get_by_path(
        path=path,
        preview=preview,
    )
    click.echo(repr(result))


@filesystem_resource.command("markings")
@click.argument("resource_rid", type=str, required=True)
@click.option(
    "--page_size", type=int, required=False, help="""The page size to use for the endpoint."""
)
@click.option(
    "--page_token",
    type=str,
    required=False,
    help="""The page token indicates where to start paging. This should be omitted from the first page's request.
To fetch the next page, clients should take the value from the `nextPageToken` field of the previous response
and use it to populate the `pageToken` field of the next request.""",
)
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.pass_obj
def filesystem_resource_op_markings(
    client: FoundryClient,
    resource_rid: str,
    page_size: typing.Optional[int],
    page_token: typing.Optional[str],
    preview: typing.Optional[bool],
):
    """
    List of Markings directly applied to a resource. The number of Markings on a resource is typically small
    so the `pageSize` and `pageToken` parameters are not required.

    """
    result = client.filesystem.Resource.markings(
        resource_rid=resource_rid,
        page_size=page_size,
        page_token=page_token,
        preview=preview,
    )
    click.echo(repr(result))


@filesystem_resource.command("permanently_delete")
@click.argument("resource_rid", type=str, required=True)
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.pass_obj
def filesystem_resource_op_permanently_delete(
    client: FoundryClient,
    resource_rid: str,
    preview: typing.Optional[bool],
):
    """
    Permanently delete the given resource from the trash. If the Resource is not directly trashed, a
    `ResourceNotTrashed` error will be thrown.

    """
    result = client.filesystem.Resource.permanently_delete(
        resource_rid=resource_rid,
        preview=preview,
    )
    click.echo(repr(result))


@filesystem_resource.command("remove_markings")
@click.argument("resource_rid", type=str, required=True)
@click.option("--marking_ids", type=str, required=True, help="""""")
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.pass_obj
def filesystem_resource_op_remove_markings(
    client: FoundryClient,
    resource_rid: str,
    marking_ids: str,
    preview: typing.Optional[bool],
):
    """
    Removes Markings from a resource.
    """
    result = client.filesystem.Resource.remove_markings(
        resource_rid=resource_rid,
        marking_ids=json.loads(marking_ids),
        preview=preview,
    )
    click.echo(repr(result))


@filesystem_resource.command("restore")
@click.argument("resource_rid", type=str, required=True)
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.pass_obj
def filesystem_resource_op_restore(
    client: FoundryClient,
    resource_rid: str,
    preview: typing.Optional[bool],
):
    """
    Restore the given resource and any directly trashed ancestors from the trash. If the resource is not
    trashed, this operation will be ignored.

    """
    result = client.filesystem.Resource.restore(
        resource_rid=resource_rid,
        preview=preview,
    )
    click.echo(repr(result))


@filesystem_resource.group("resource_role")
def filesystem_resource_resource_role():
    pass


@filesystem_resource_resource_role.command("add")
@click.argument("resource_rid", type=str, required=True)
@click.option("--roles", type=str, required=True, help="""""")
@click.pass_obj
def filesystem_resource_resource_role_op_add(
    client: FoundryClient,
    resource_rid: str,
    roles: str,
):
    """ """
    result = client.filesystem.Resource.Role.add(
        resource_rid=resource_rid,
        roles=json.loads(roles),
    )
    click.echo(repr(result))


@filesystem_resource_resource_role.command("list")
@click.argument("resource_rid", type=str, required=True)
@click.option(
    "--include_inherited",
    type=bool,
    required=False,
    help="""Whether to include inherited roles on the resource.""",
)
@click.option(
    "--page_size", type=int, required=False, help="""The page size to use for the endpoint."""
)
@click.option(
    "--page_token",
    type=str,
    required=False,
    help="""The page token indicates where to start paging. This should be omitted from the first page's request.
To fetch the next page, clients should take the value from the `nextPageToken` field of the previous response
and use it to populate the `pageToken` field of the next request.""",
)
@click.pass_obj
def filesystem_resource_resource_role_op_list(
    client: FoundryClient,
    resource_rid: str,
    include_inherited: typing.Optional[bool],
    page_size: typing.Optional[int],
    page_token: typing.Optional[str],
):
    """
    List the roles on a resource.

    """
    result = client.filesystem.Resource.Role.list(
        resource_rid=resource_rid,
        include_inherited=include_inherited,
        page_size=page_size,
        page_token=page_token,
    )
    click.echo(repr(result))


@filesystem_resource_resource_role.command("remove")
@click.argument("resource_rid", type=str, required=True)
@click.option("--roles", type=str, required=True, help="""""")
@click.pass_obj
def filesystem_resource_resource_role_op_remove(
    client: FoundryClient,
    resource_rid: str,
    roles: str,
):
    """ """
    result = client.filesystem.Resource.Role.remove(
        resource_rid=resource_rid,
        roles=json.loads(roles),
    )
    click.echo(repr(result))


@filesystem.group("project")
def filesystem_project():
    pass


@filesystem_project.command("add_organizations")
@click.argument("project_rid", type=str, required=True)
@click.option("--organization_rids", type=str, required=True, help="""""")
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.pass_obj
def filesystem_project_op_add_organizations(
    client: FoundryClient,
    project_rid: str,
    organization_rids: str,
    preview: typing.Optional[bool],
):
    """
    Adds a list of Organizations to a Project.
    """
    result = client.filesystem.Project.add_organizations(
        project_rid=project_rid,
        organization_rids=json.loads(organization_rids),
        preview=preview,
    )
    click.echo(repr(result))


@filesystem_project.command("create")
@click.option("--default_roles", type=str, required=True, help="""""")
@click.option("--display_name", type=str, required=True, help="""""")
@click.option("--organization_rids", type=str, required=True, help="""""")
@click.option("--role_grants", type=str, required=True, help="""""")
@click.option("--space_rid", type=str, required=True, help="""""")
@click.option("--description", type=str, required=False, help="""""")
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.pass_obj
def filesystem_project_op_create(
    client: FoundryClient,
    default_roles: str,
    display_name: str,
    organization_rids: str,
    role_grants: str,
    space_rid: str,
    description: typing.Optional[str],
    preview: typing.Optional[bool],
):
    """
    Creates a new Project.

    Note that third-party applications using this endpoint via OAuth2 cannot be associated with an
    Ontology SDK as this will reduce the scope of operations to only those within specified projects.
    When creating the application, select "No, I won't use an Ontology SDK" on the Resources page.

    """
    result = client.filesystem.Project.create(
        default_roles=json.loads(default_roles),
        display_name=display_name,
        organization_rids=json.loads(organization_rids),
        role_grants=json.loads(role_grants),
        space_rid=space_rid,
        description=description,
        preview=preview,
    )
    click.echo(repr(result))


@filesystem_project.command("create_from_template")
@click.option("--template_rid", type=str, required=True, help="""""")
@click.option("--variable_values", type=str, required=True, help="""""")
@click.option("--default_roles", type=str, required=False, help="""""")
@click.option("--organization_rids", type=str, required=False, help="""""")
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.option("--project_description", type=str, required=False, help="""""")
@click.pass_obj
def filesystem_project_op_create_from_template(
    client: FoundryClient,
    template_rid: str,
    variable_values: str,
    default_roles: typing.Optional[str],
    organization_rids: typing.Optional[str],
    preview: typing.Optional[bool],
    project_description: typing.Optional[str],
):
    """
    Creates a project from a project template.
    """
    result = client.filesystem.Project.create_from_template(
        template_rid=template_rid,
        variable_values=json.loads(variable_values),
        default_roles=None if default_roles is None else json.loads(default_roles),
        organization_rids=None if organization_rids is None else json.loads(organization_rids),
        preview=preview,
        project_description=project_description,
    )
    click.echo(repr(result))


@filesystem_project.command("get")
@click.argument("project_rid", type=str, required=True)
@click.pass_obj
def filesystem_project_op_get(
    client: FoundryClient,
    project_rid: str,
):
    """
    Get the Project with the specified rid.
    """
    result = client.filesystem.Project.get(
        project_rid=project_rid,
    )
    click.echo(repr(result))


@filesystem_project.command("organizations")
@click.argument("project_rid", type=str, required=True)
@click.option(
    "--page_size", type=int, required=False, help="""The page size to use for the endpoint."""
)
@click.option(
    "--page_token",
    type=str,
    required=False,
    help="""The page token indicates where to start paging. This should be omitted from the first page's request.
To fetch the next page, clients should take the value from the `nextPageToken` field of the previous response
and use it to populate the `pageToken` field of the next request.""",
)
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.pass_obj
def filesystem_project_op_organizations(
    client: FoundryClient,
    project_rid: str,
    page_size: typing.Optional[int],
    page_token: typing.Optional[str],
    preview: typing.Optional[bool],
):
    """
    List of Organizations directly applied to a Project. The number of Organizations on a Project is
    typically small so the `pageSize` and `pageToken` parameters are not required.

    """
    result = client.filesystem.Project.organizations(
        project_rid=project_rid,
        page_size=page_size,
        page_token=page_token,
        preview=preview,
    )
    click.echo(repr(result))


@filesystem_project.command("remove_organizations")
@click.argument("project_rid", type=str, required=True)
@click.option("--organization_rids", type=str, required=True, help="""""")
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.pass_obj
def filesystem_project_op_remove_organizations(
    client: FoundryClient,
    project_rid: str,
    organization_rids: str,
    preview: typing.Optional[bool],
):
    """
    Removes Organizations from a Project.
    """
    result = client.filesystem.Project.remove_organizations(
        project_rid=project_rid,
        organization_rids=json.loads(organization_rids),
        preview=preview,
    )
    click.echo(repr(result))


@filesystem_project.command("replace")
@click.argument("project_rid", type=str, required=True)
@click.option(
    "--display_name",
    type=str,
    required=True,
    help="""The display name of the Project. Must be unique and cannot contain a /""",
)
@click.option(
    "--description",
    type=str,
    required=False,
    help="""The description associated with the Project.""",
)
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.pass_obj
def filesystem_project_op_replace(
    client: FoundryClient,
    project_rid: str,
    display_name: str,
    description: typing.Optional[str],
    preview: typing.Optional[bool],
):
    """
    Replace the Project with the specified rid.
    """
    result = client.filesystem.Project.replace(
        project_rid=project_rid,
        display_name=display_name,
        description=description,
        preview=preview,
    )
    click.echo(repr(result))


@filesystem.group("folder")
def filesystem_folder():
    pass


@filesystem_folder.command("children")
@click.argument("folder_rid", type=str, required=True)
@click.option(
    "--page_size", type=int, required=False, help="""The page size to use for the endpoint."""
)
@click.option(
    "--page_token",
    type=str,
    required=False,
    help="""The page token indicates where to start paging. This should be omitted from the first page's request.
To fetch the next page, clients should take the value from the `nextPageToken` field of the previous response
and use it to populate the `pageToken` field of the next request.""",
)
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.pass_obj
def filesystem_folder_op_children(
    client: FoundryClient,
    folder_rid: str,
    page_size: typing.Optional[int],
    page_token: typing.Optional[str],
    preview: typing.Optional[bool],
):
    """
    List all child Resources of the Folder.

    This is a paged endpoint. The page size will be limited to 2,000 results per page. If no page size is
    provided, this page size will also be used as the default.

    """
    result = client.filesystem.Folder.children(
        folder_rid=folder_rid,
        page_size=page_size,
        page_token=page_token,
        preview=preview,
    )
    click.echo(repr(result))


@filesystem_folder.command("create")
@click.option("--display_name", type=str, required=True, help="""""")
@click.option(
    "--parent_folder_rid",
    type=str,
    required=True,
    help="""The parent folder Resource Identifier (RID). For Projects, this will be the Space RID and for Spaces,
this value will be the root folder (`ri.compass.main.folder.0`).
""",
)
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.pass_obj
def filesystem_folder_op_create(
    client: FoundryClient,
    display_name: str,
    parent_folder_rid: str,
    preview: typing.Optional[bool],
):
    """
    Creates a new Folder.
    """
    result = client.filesystem.Folder.create(
        display_name=display_name,
        parent_folder_rid=parent_folder_rid,
        preview=preview,
    )
    click.echo(repr(result))


@filesystem_folder.command("get")
@click.argument("folder_rid", type=str, required=True)
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.pass_obj
def filesystem_folder_op_get(
    client: FoundryClient,
    folder_rid: str,
    preview: typing.Optional[bool],
):
    """
    Get the Folder with the specified rid.
    """
    result = client.filesystem.Folder.get(
        folder_rid=folder_rid,
        preview=preview,
    )
    click.echo(repr(result))


@filesystem_folder.command("get_batch")
@click.argument("body", type=str, required=True)
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.pass_obj
def filesystem_folder_op_get_batch(
    client: FoundryClient,
    body: str,
    preview: typing.Optional[bool],
):
    """
    Fetches multiple folders in a single request.


    The maximum batch size for this endpoint is 1000.
    """
    result = client.filesystem.Folder.get_batch(
        body=json.loads(body),
        preview=preview,
    )
    click.echo(repr(result))


@cli.group("functions")
def functions():
    pass


@functions.group("value_type")
def functions_value_type():
    pass


@functions_value_type.command("get")
@click.argument("value_type_rid", type=str, required=True)
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.pass_obj
def functions_value_type_op_get(
    client: FoundryClient,
    value_type_rid: str,
    preview: typing.Optional[bool],
):
    """
    Gets a specific value type with the given RID. The latest version is returned.

    """
    result = client.functions.ValueType.get(
        value_type_rid=value_type_rid,
        preview=preview,
    )
    click.echo(repr(result))


@functions_value_type.group("version_id")
def functions_value_type_version_id():
    pass


@functions_value_type_version_id.command("get")
@click.argument("value_type_rid", type=str, required=True)
@click.argument("version_id_version_id", type=str, required=True)
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.pass_obj
def functions_value_type_version_id_op_get(
    client: FoundryClient,
    value_type_rid: str,
    version_id_version_id: str,
    preview: typing.Optional[bool],
):
    """
    Gets a specific value type with the given RID. The specified version is returned.

    """
    result = client.functions.ValueType.VersionId.get(
        value_type_rid=value_type_rid,
        version_id_version_id=version_id_version_id,
        preview=preview,
    )
    click.echo(repr(result))


@functions.group("query")
def functions_query():
    pass


@functions_query.command("execute")
@click.argument("query_api_name", type=str, required=True)
@click.option("--parameters", type=str, required=True, help="""""")
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.option("--trace_parent", type=str, required=False, help="""""")
@click.option("--trace_state", type=str, required=False, help="""""")
@click.option("--version", type=str, required=False, help="""""")
@click.pass_obj
def functions_query_op_execute(
    client: FoundryClient,
    query_api_name: str,
    parameters: str,
    preview: typing.Optional[bool],
    trace_parent: typing.Optional[str],
    trace_state: typing.Optional[str],
    version: typing.Optional[str],
):
    """
    Executes a Query using the given parameters. By default, this executes the latest version of the query.

    Optional parameters do not need to be supplied.

    """
    result = client.functions.Query.execute(
        query_api_name=query_api_name,
        parameters=json.loads(parameters),
        preview=preview,
        trace_parent=trace_parent,
        trace_state=trace_state,
        version=version,
    )
    click.echo(repr(result))


@functions_query.command("get")
@click.argument("query_api_name", type=str, required=True)
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.option("--version", type=str, required=False, help="""""")
@click.pass_obj
def functions_query_op_get(
    client: FoundryClient,
    query_api_name: str,
    preview: typing.Optional[bool],
    version: typing.Optional[str],
):
    """
    Gets a specific query type with the given API name. By default, this gets the latest version of the query.

    """
    result = client.functions.Query.get(
        query_api_name=query_api_name,
        preview=preview,
        version=version,
    )
    click.echo(repr(result))


@functions_query.command("get_by_rid")
@click.option("--rid", type=str, required=True, help="""""")
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.option("--version", type=str, required=False, help="""""")
@click.pass_obj
def functions_query_op_get_by_rid(
    client: FoundryClient,
    rid: str,
    preview: typing.Optional[bool],
    version: typing.Optional[str],
):
    """
    Gets a specific query type with the given RID.By default, this gets the latest version of the query.

    """
    result = client.functions.Query.get_by_rid(
        rid=rid,
        preview=preview,
        version=version,
    )
    click.echo(repr(result))


@cli.group("geo")
def geo():
    pass


@cli.group("language_models")
def language_models():
    pass


@language_models.group("open_ai_model")
def language_models_open_ai_model():
    pass


@language_models_open_ai_model.command("embeddings")
@click.argument("open_ai_model_model_id", type=str, required=True)
@click.option(
    "--input",
    type=str,
    required=True,
    help="""Input text to embed, encoded as an array of strings. Each input must not exceed the max input 
tokens for the model (8192 tokens for all embedding models).
""",
)
@click.option(
    "--dimensions",
    type=int,
    required=False,
    help="""The number of dimensions the resulting output embeddings should have. 
Only supported in text-embedding-3 and later models.
""",
)
@click.option(
    "--encoding_format",
    type=click.Choice(["FLOAT", "BASE64"]),
    required=False,
    help="""The format to return the embeddings in. Can be either float or base64.""",
)
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.pass_obj
def language_models_open_ai_model_op_embeddings(
    client: FoundryClient,
    open_ai_model_model_id: str,
    input: str,
    dimensions: typing.Optional[int],
    encoding_format: typing.Optional[typing.Literal["FLOAT", "BASE64"]],
    preview: typing.Optional[bool],
):
    """ """
    result = client.language_models.OpenAiModel.embeddings(
        open_ai_model_model_id=open_ai_model_model_id,
        input=json.loads(input),
        dimensions=dimensions,
        encoding_format=encoding_format,
        preview=preview,
    )
    click.echo(repr(result))


@language_models.group("anthropic_model")
def language_models_anthropic_model():
    pass


@language_models_anthropic_model.command("messages")
@click.argument("anthropic_model_model_id", type=str, required=True)
@click.option(
    "--max_tokens",
    type=int,
    required=True,
    help="""The maximum number of tokens to generate before stopping.""",
)
@click.option(
    "--messages",
    type=str,
    required=True,
    help="""Input messages to the model. This can include a single user-role message or multiple messages with
alternating user and assistant roles.
""",
)
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.option(
    "--stop_sequences",
    type=str,
    required=False,
    help="""Custom text sequences that will cause the model to stop generating.""",
)
@click.option(
    "--system",
    type=str,
    required=False,
    help="""A system prompt is a way of providing context and instructions to Claude, such as specifying a 
particular goal or role. As of now, sending multiple system prompts is not supported.
""",
)
@click.option(
    "--temperature",
    type=float,
    required=False,
    help="""Amount of randomness injected into the response. Ranges from 0.0 to 1.0. Note that even with 
temperature of 0.0, the results will not be fully deterministic. Defaults to 1.0
""",
)
@click.option(
    "--thinking",
    type=str,
    required=False,
    help="""Configuration for enabling Claude's extended thinking.""",
)
@click.option(
    "--tool_choice",
    type=str,
    required=False,
    help="""How the model should use the provided tools.""",
)
@click.option(
    "--tools", type=str, required=False, help="""Definitions of tools that the model may use."""
)
@click.option(
    "--top_k",
    type=int,
    required=False,
    help="""Only sample from the top K options for each subsequent token.""",
)
@click.option(
    "--top_p",
    type=float,
    required=False,
    help="""Use nucleus sampling. You should either alter temperature or top_p, but not both""",
)
@click.pass_obj
def language_models_anthropic_model_op_messages(
    client: FoundryClient,
    anthropic_model_model_id: str,
    max_tokens: int,
    messages: str,
    preview: typing.Optional[bool],
    stop_sequences: typing.Optional[str],
    system: typing.Optional[str],
    temperature: typing.Optional[float],
    thinking: typing.Optional[str],
    tool_choice: typing.Optional[str],
    tools: typing.Optional[str],
    top_k: typing.Optional[int],
    top_p: typing.Optional[float],
):
    """ """
    result = client.language_models.AnthropicModel.messages(
        anthropic_model_model_id=anthropic_model_model_id,
        max_tokens=max_tokens,
        messages=json.loads(messages),
        preview=preview,
        stop_sequences=None if stop_sequences is None else json.loads(stop_sequences),
        system=None if system is None else json.loads(system),
        temperature=temperature,
        thinking=None if thinking is None else json.loads(thinking),
        tool_choice=None if tool_choice is None else json.loads(tool_choice),
        tools=None if tools is None else json.loads(tools),
        top_k=top_k,
        top_p=top_p,
    )
    click.echo(repr(result))


@cli.group("media_sets")
def media_sets():
    pass


@media_sets.group("media_set")
def media_sets_media_set():
    pass


@media_sets_media_set.command("abort")
@click.argument("media_set_rid", type=str, required=True)
@click.argument("transaction_id", type=str, required=True)
@click.option(
    "--preview",
    type=bool,
    required=False,
    help="""A boolean flag that, when set to true, enables the use of beta features in preview mode.
""",
)
@click.pass_obj
def media_sets_media_set_op_abort(
    client: FoundryClient,
    media_set_rid: str,
    transaction_id: str,
    preview: typing.Optional[bool],
):
    """
    Aborts an open transaction. Items uploaded to the media set during this transaction will be deleted.

    """
    result = client.media_sets.MediaSet.abort(
        media_set_rid=media_set_rid,
        transaction_id=transaction_id,
        preview=preview,
    )
    click.echo(repr(result))


@media_sets_media_set.command("calculate")
@click.argument("media_set_rid", type=str, required=True)
@click.argument("media_item_rid", type=str, required=True)
@click.option(
    "--preview",
    type=bool,
    required=False,
    help="""A boolean flag that, when set to true, enables the use of beta features in preview mode.
""",
)
@click.option("--read_token", type=str, required=False, help="""""")
@click.pass_obj
def media_sets_media_set_op_calculate(
    client: FoundryClient,
    media_set_rid: str,
    media_item_rid: str,
    preview: typing.Optional[bool],
    read_token: typing.Optional[str],
):
    """
    Starts calculation of a thumbnail for a given image.

    """
    result = client.media_sets.MediaSet.calculate(
        media_set_rid=media_set_rid,
        media_item_rid=media_item_rid,
        preview=preview,
        read_token=read_token,
    )
    click.echo(repr(result))


@media_sets_media_set.command("commit")
@click.argument("media_set_rid", type=str, required=True)
@click.argument("transaction_id", type=str, required=True)
@click.option(
    "--preview",
    type=bool,
    required=False,
    help="""A boolean flag that, when set to true, enables the use of beta features in preview mode.
""",
)
@click.pass_obj
def media_sets_media_set_op_commit(
    client: FoundryClient,
    media_set_rid: str,
    transaction_id: str,
    preview: typing.Optional[bool],
):
    """
    Commits an open transaction. On success, items uploaded to the media set during this transaction will become available.

    """
    result = client.media_sets.MediaSet.commit(
        media_set_rid=media_set_rid,
        transaction_id=transaction_id,
        preview=preview,
    )
    click.echo(repr(result))


@media_sets_media_set.command("create")
@click.argument("media_set_rid", type=str, required=True)
@click.option(
    "--branch_name",
    type=str,
    required=False,
    help="""The branch on which to open the transaction. Defaults to `master` for most enrollments.
""",
)
@click.option(
    "--preview",
    type=bool,
    required=False,
    help="""A boolean flag that, when set to true, enables the use of beta features in preview mode.
""",
)
@click.pass_obj
def media_sets_media_set_op_create(
    client: FoundryClient,
    media_set_rid: str,
    branch_name: typing.Optional[str],
    preview: typing.Optional[bool],
):
    """
    Creates a new transaction. Items uploaded to the media set while this transaction is open will not be reflected until the transaction is committed.

    """
    result = client.media_sets.MediaSet.create(
        media_set_rid=media_set_rid,
        branch_name=branch_name,
        preview=preview,
    )
    click.echo(repr(result))


@media_sets_media_set.command("get_rid_by_path")
@click.argument("media_set_rid", type=str, required=True)
@click.option(
    "--media_item_path",
    type=str,
    required=True,
    help="""The path of the media item.
""",
)
@click.option(
    "--branch_name",
    type=str,
    required=False,
    help="""Specifies the specific branch by name in which to search for this media item. May not be provided if branch rid or view rid are provided.""",
)
@click.option(
    "--branch_rid",
    type=str,
    required=False,
    help="""Specifies the specific branch by rid in which to search for this media item. May not be provided if branch name or view rid are provided.""",
)
@click.option(
    "--preview",
    type=bool,
    required=False,
    help="""A boolean flag that, when set to true, enables the use of beta features in preview mode.
""",
)
@click.option(
    "--view_rid",
    type=str,
    required=False,
    help="""Specifies the specific view by rid in which to search for this media item. May not be provided if branch name or branch rid are provided.""",
)
@click.pass_obj
def media_sets_media_set_op_get_rid_by_path(
    client: FoundryClient,
    media_set_rid: str,
    media_item_path: str,
    branch_name: typing.Optional[str],
    branch_rid: typing.Optional[str],
    preview: typing.Optional[bool],
    view_rid: typing.Optional[str],
):
    """
    Returns the media item RID for the media item with the specified path.

    """
    result = client.media_sets.MediaSet.get_rid_by_path(
        media_set_rid=media_set_rid,
        media_item_path=media_item_path,
        branch_name=branch_name,
        branch_rid=branch_rid,
        preview=preview,
        view_rid=view_rid,
    )
    click.echo(repr(result))


@media_sets_media_set.command("info")
@click.argument("media_set_rid", type=str, required=True)
@click.argument("media_item_rid", type=str, required=True)
@click.option(
    "--preview",
    type=bool,
    required=False,
    help="""A boolean flag that, when set to true, enables the use of beta features in preview mode.
""",
)
@click.option("--read_token", type=str, required=False, help="""""")
@click.pass_obj
def media_sets_media_set_op_info(
    client: FoundryClient,
    media_set_rid: str,
    media_item_rid: str,
    preview: typing.Optional[bool],
    read_token: typing.Optional[str],
):
    """
    Gets information about the media item.

    """
    result = client.media_sets.MediaSet.info(
        media_set_rid=media_set_rid,
        media_item_rid=media_item_rid,
        preview=preview,
        read_token=read_token,
    )
    click.echo(repr(result))


@media_sets_media_set.command("read")
@click.argument("media_set_rid", type=str, required=True)
@click.argument("media_item_rid", type=str, required=True)
@click.option(
    "--preview",
    type=bool,
    required=False,
    help="""A boolean flag that, when set to true, enables the use of beta features in preview mode.
""",
)
@click.option("--read_token", type=str, required=False, help="""""")
@click.pass_obj
def media_sets_media_set_op_read(
    client: FoundryClient,
    media_set_rid: str,
    media_item_rid: str,
    preview: typing.Optional[bool],
    read_token: typing.Optional[str],
):
    """
    Gets the content of a media item.

    """
    result = client.media_sets.MediaSet.read(
        media_set_rid=media_set_rid,
        media_item_rid=media_item_rid,
        preview=preview,
        read_token=read_token,
    )
    click.echo(result)


@media_sets_media_set.command("read_original")
@click.argument("media_set_rid", type=str, required=True)
@click.argument("media_item_rid", type=str, required=True)
@click.option(
    "--preview",
    type=bool,
    required=False,
    help="""A boolean flag that, when set to true, enables the use of beta features in preview mode.
""",
)
@click.option("--read_token", type=str, required=False, help="""""")
@click.pass_obj
def media_sets_media_set_op_read_original(
    client: FoundryClient,
    media_set_rid: str,
    media_item_rid: str,
    preview: typing.Optional[bool],
    read_token: typing.Optional[str],
):
    """
    Gets the content of an original file uploaded to the media item, even if it was transformed on upload due to being an additional input format.

    """
    result = client.media_sets.MediaSet.read_original(
        media_set_rid=media_set_rid,
        media_item_rid=media_item_rid,
        preview=preview,
        read_token=read_token,
    )
    click.echo(result)


@media_sets_media_set.command("reference")
@click.argument("media_set_rid", type=str, required=True)
@click.argument("media_item_rid", type=str, required=True)
@click.option(
    "--preview",
    type=bool,
    required=False,
    help="""A boolean flag that, when set to true, enables the use of beta features in preview mode.
""",
)
@click.option("--read_token", type=str, required=False, help="""""")
@click.pass_obj
def media_sets_media_set_op_reference(
    client: FoundryClient,
    media_set_rid: str,
    media_item_rid: str,
    preview: typing.Optional[bool],
    read_token: typing.Optional[str],
):
    """
    Gets the [media reference](https://palantir.com/docs/foundry/data-integration/media-sets/#media-references) for this media item.

    """
    result = client.media_sets.MediaSet.reference(
        media_set_rid=media_set_rid,
        media_item_rid=media_item_rid,
        preview=preview,
        read_token=read_token,
    )
    click.echo(repr(result))


@media_sets_media_set.command("retrieve")
@click.argument("media_set_rid", type=str, required=True)
@click.argument("media_item_rid", type=str, required=True)
@click.option(
    "--preview",
    type=bool,
    required=False,
    help="""A boolean flag that, when set to true, enables the use of beta features in preview mode.
""",
)
@click.option("--read_token", type=str, required=False, help="""""")
@click.pass_obj
def media_sets_media_set_op_retrieve(
    client: FoundryClient,
    media_set_rid: str,
    media_item_rid: str,
    preview: typing.Optional[bool],
    read_token: typing.Optional[str],
):
    """
    Retrieves a successfully calculated thumbnail for a given image.

    Thumbnails are 200px wide in the format of `image/webp`

    """
    result = client.media_sets.MediaSet.retrieve(
        media_set_rid=media_set_rid,
        media_item_rid=media_item_rid,
        preview=preview,
        read_token=read_token,
    )
    click.echo(result)


@media_sets_media_set.command("upload")
@click.argument("media_set_rid", type=str, required=True)
@click.argument("body", type=click.File("rb"), required=True)
@click.option(
    "--branch_name",
    type=str,
    required=False,
    help="""Specifies the specific branch by name to which this media item will be uploaded. May not be provided if branch rid or view rid are provided.""",
)
@click.option(
    "--branch_rid",
    type=str,
    required=False,
    help="""Specifies the specific branch by rid to which this media item will be uploaded. May not be provided if branch name or view rid are provided.""",
)
@click.option(
    "--media_item_path",
    type=str,
    required=False,
    help="""An identifier for a media item within a media set. Necessary if the backing media set requires paths.""",
)
@click.option(
    "--preview",
    type=bool,
    required=False,
    help="""A boolean flag that, when set to true, enables the use of beta features in preview mode.
""",
)
@click.option(
    "--transaction_id",
    type=str,
    required=False,
    help="""The id of the transaction associated with this request.  Required if this is a transactional media set.
""",
)
@click.option(
    "--view_rid",
    type=str,
    required=False,
    help="""Specifies the specific view by rid to which this media item will be uploaded. May not be provided if branch name or branch rid are provided.""",
)
@click.pass_obj
def media_sets_media_set_op_upload(
    client: FoundryClient,
    media_set_rid: str,
    body: io.BufferedReader,
    branch_name: typing.Optional[str],
    branch_rid: typing.Optional[str],
    media_item_path: typing.Optional[str],
    preview: typing.Optional[bool],
    transaction_id: typing.Optional[str],
    view_rid: typing.Optional[str],
):
    """
    Uploads a media item to an existing media set.
    The body of the request must contain the binary content of the file and the `Content-Type` header must be `application/octet-stream`.
    A branch name, or branch rid, or view rid may optionally be specified.  If none is specified, the item will be uploaded to the default branch. If more than one is specified, an error is thrown.

    """
    result = client.media_sets.MediaSet.upload(
        media_set_rid=media_set_rid,
        body=body.read(),
        branch_name=branch_name,
        branch_rid=branch_rid,
        media_item_path=media_item_path,
        preview=preview,
        transaction_id=transaction_id,
        view_rid=view_rid,
    )
    click.echo(repr(result))


@cli.group("ontologies")
def ontologies():
    pass


@ontologies.group("time_series_value_bank_property")
def ontologies_time_series_value_bank_property():
    pass


@ontologies_time_series_value_bank_property.command("get_latest_value")
@click.argument("ontology", type=str, required=True)
@click.argument("object_type", type=str, required=True)
@click.argument("primary_key", type=str, required=True)
@click.argument("property_name", type=str, required=True)
@click.option(
    "--sdk_package_rid",
    type=str,
    required=False,
    help="""The package rid of the generated SDK.
""",
)
@click.option(
    "--sdk_version",
    type=str,
    required=False,
    help="""The version of the generated SDK.
""",
)
@click.pass_obj
def ontologies_time_series_value_bank_property_op_get_latest_value(
    client: FoundryClient,
    ontology: str,
    object_type: str,
    primary_key: str,
    property_name: str,
    sdk_package_rid: typing.Optional[str],
    sdk_version: typing.Optional[str],
):
    """
    Get the latest value of a property backed by a timeseries. If a specific geotime series integration has both a history and a live integration, we will give precedence to the live integration.

    """
    result = client.ontologies.TimeSeriesValueBankProperty.get_latest_value(
        ontology=ontology,
        object_type=object_type,
        primary_key=primary_key,
        property_name=property_name,
        sdk_package_rid=sdk_package_rid,
        sdk_version=sdk_version,
    )
    click.echo(repr(result))


@ontologies_time_series_value_bank_property.command("stream_values")
@click.argument("ontology", type=str, required=True)
@click.argument("object_type", type=str, required=True)
@click.argument("primary_key", type=str, required=True)
@click.argument("property", type=str, required=True)
@click.option("--range", type=str, required=False, help="""""")
@click.option(
    "--sdk_package_rid",
    type=str,
    required=False,
    help="""The package rid of the generated SDK.
""",
)
@click.option(
    "--sdk_version",
    type=str,
    required=False,
    help="""The version of the generated SDK.
""",
)
@click.pass_obj
def ontologies_time_series_value_bank_property_op_stream_values(
    client: FoundryClient,
    ontology: str,
    object_type: str,
    primary_key: str,
    property: str,
    range: typing.Optional[str],
    sdk_package_rid: typing.Optional[str],
    sdk_version: typing.Optional[str],
):
    """
    Stream all of the points of a time series property (this includes geotime series references).

    """
    result = client.ontologies.TimeSeriesValueBankProperty.stream_values(
        ontology=ontology,
        object_type=object_type,
        primary_key=primary_key,
        property=property,
        range=None if range is None else json.loads(range),
        sdk_package_rid=sdk_package_rid,
        sdk_version=sdk_version,
    )
    click.echo(result)


@ontologies.group("time_series_property_v2")
def ontologies_time_series_property_v2():
    pass


@ontologies_time_series_property_v2.command("get_first_point")
@click.argument("ontology", type=str, required=True)
@click.argument("object_type", type=str, required=True)
@click.argument("primary_key", type=str, required=True)
@click.argument("property", type=str, required=True)
@click.option(
    "--sdk_package_rid",
    type=str,
    required=False,
    help="""The package rid of the generated SDK.
""",
)
@click.option(
    "--sdk_version",
    type=str,
    required=False,
    help="""The version of the generated SDK.
""",
)
@click.pass_obj
def ontologies_time_series_property_v2_op_get_first_point(
    client: FoundryClient,
    ontology: str,
    object_type: str,
    primary_key: str,
    property: str,
    sdk_package_rid: typing.Optional[str],
    sdk_version: typing.Optional[str],
):
    """
    Get the first point of a time series property.

    """
    result = client.ontologies.TimeSeriesPropertyV2.get_first_point(
        ontology=ontology,
        object_type=object_type,
        primary_key=primary_key,
        property=property,
        sdk_package_rid=sdk_package_rid,
        sdk_version=sdk_version,
    )
    click.echo(repr(result))


@ontologies_time_series_property_v2.command("get_last_point")
@click.argument("ontology", type=str, required=True)
@click.argument("object_type", type=str, required=True)
@click.argument("primary_key", type=str, required=True)
@click.argument("property", type=str, required=True)
@click.option(
    "--sdk_package_rid",
    type=str,
    required=False,
    help="""The package rid of the generated SDK.
""",
)
@click.option(
    "--sdk_version",
    type=str,
    required=False,
    help="""The version of the generated SDK.
""",
)
@click.pass_obj
def ontologies_time_series_property_v2_op_get_last_point(
    client: FoundryClient,
    ontology: str,
    object_type: str,
    primary_key: str,
    property: str,
    sdk_package_rid: typing.Optional[str],
    sdk_version: typing.Optional[str],
):
    """
    Get the last point of a time series property.

    """
    result = client.ontologies.TimeSeriesPropertyV2.get_last_point(
        ontology=ontology,
        object_type=object_type,
        primary_key=primary_key,
        property=property,
        sdk_package_rid=sdk_package_rid,
        sdk_version=sdk_version,
    )
    click.echo(repr(result))


@ontologies_time_series_property_v2.command("stream_points")
@click.argument("ontology", type=str, required=True)
@click.argument("object_type", type=str, required=True)
@click.argument("primary_key", type=str, required=True)
@click.argument("property", type=str, required=True)
@click.option("--aggregate", type=str, required=False, help="""""")
@click.option(
    "--format",
    type=click.Choice(["JSON", "ARROW"]),
    required=False,
    help="""The output format to serialize the output binary stream in. Default is
JSON. ARROW is more efficient than JSON at streaming a large sized response.
""",
)
@click.option("--range", type=str, required=False, help="""""")
@click.option(
    "--sdk_package_rid",
    type=str,
    required=False,
    help="""The package rid of the generated SDK.
""",
)
@click.option(
    "--sdk_version",
    type=str,
    required=False,
    help="""The version of the generated SDK.
""",
)
@click.pass_obj
def ontologies_time_series_property_v2_op_stream_points(
    client: FoundryClient,
    ontology: str,
    object_type: str,
    primary_key: str,
    property: str,
    aggregate: typing.Optional[str],
    format: typing.Optional[typing.Literal["JSON", "ARROW"]],
    range: typing.Optional[str],
    sdk_package_rid: typing.Optional[str],
    sdk_version: typing.Optional[str],
):
    """
    Stream all of the points of a time series property.

    """
    result = client.ontologies.TimeSeriesPropertyV2.stream_points(
        ontology=ontology,
        object_type=object_type,
        primary_key=primary_key,
        property=property,
        aggregate=None if aggregate is None else json.loads(aggregate),
        format=format,
        range=None if range is None else json.loads(range),
        sdk_package_rid=sdk_package_rid,
        sdk_version=sdk_version,
    )
    click.echo(result)


@ontologies.group("query")
def ontologies_query():
    pass


@ontologies_query.command("execute")
@click.argument("ontology", type=str, required=True)
@click.argument("query_api_name", type=str, required=True)
@click.option("--parameters", type=str, required=True, help="""""")
@click.option(
    "--sdk_package_rid",
    type=str,
    required=False,
    help="""The package rid of the generated SDK.
""",
)
@click.option(
    "--sdk_version",
    type=str,
    required=False,
    help="""The version of the generated SDK.
""",
)
@click.option(
    "--trace_parent",
    type=str,
    required=False,
    help="""The W3C trace parent header included in the request.
""",
)
@click.option(
    "--trace_state",
    type=str,
    required=False,
    help="""The W3C trace state header included in the request.
""",
)
@click.option(
    "--version",
    type=str,
    required=False,
    help="""The version of the Query to execute.
""",
)
@click.pass_obj
def ontologies_query_op_execute(
    client: FoundryClient,
    ontology: str,
    query_api_name: str,
    parameters: str,
    sdk_package_rid: typing.Optional[str],
    sdk_version: typing.Optional[str],
    trace_parent: typing.Optional[str],
    trace_state: typing.Optional[str],
    version: typing.Optional[str],
):
    """
    Executes a Query using the given parameters.

    Optional parameters do not need to be supplied.

    """
    result = client.ontologies.Query.execute(
        ontology=ontology,
        query_api_name=query_api_name,
        parameters=json.loads(parameters),
        sdk_package_rid=sdk_package_rid,
        sdk_version=sdk_version,
        trace_parent=trace_parent,
        trace_state=trace_state,
        version=version,
    )
    click.echo(repr(result))


@ontologies.group("ontology_value_type")
def ontologies_ontology_value_type():
    pass


@ontologies_ontology_value_type.command("get")
@click.argument("ontology", type=str, required=True)
@click.argument("value_type", type=str, required=True)
@click.option(
    "--preview",
    type=bool,
    required=False,
    help="""A boolean flag that, when set to true, enables the use of beta features in preview mode.
""",
)
@click.pass_obj
def ontologies_ontology_value_type_op_get(
    client: FoundryClient,
    ontology: str,
    value_type: str,
    preview: typing.Optional[bool],
):
    """
    Gets a specific value type with the given API name.

    """
    result = client.ontologies.OntologyValueType.get(
        ontology=ontology,
        value_type=value_type,
        preview=preview,
    )
    click.echo(repr(result))


@ontologies_ontology_value_type.command("list")
@click.argument("ontology", type=str, required=True)
@click.option(
    "--preview",
    type=bool,
    required=False,
    help="""A boolean flag that, when set to true, enables the use of beta features in preview mode.
""",
)
@click.pass_obj
def ontologies_ontology_value_type_op_list(
    client: FoundryClient,
    ontology: str,
    preview: typing.Optional[bool],
):
    """
    Lists the latest versions of the value types for the given Ontology.

    """
    result = client.ontologies.OntologyValueType.list(
        ontology=ontology,
        preview=preview,
    )
    click.echo(repr(result))


@ontologies.group("ontology_transaction")
def ontologies_ontology_transaction():
    pass


@ontologies_ontology_transaction.command("post_edits")
@click.argument("ontology", type=str, required=True)
@click.argument("transaction_rid", type=str, required=True)
@click.option("--edits", type=str, required=True, help="""""")
@click.option(
    "--preview",
    type=bool,
    required=False,
    help="""A boolean flag that, when set to true, enables the use of beta features in preview mode.
""",
)
@click.pass_obj
def ontologies_ontology_transaction_op_post_edits(
    client: FoundryClient,
    ontology: str,
    transaction_rid: str,
    edits: str,
    preview: typing.Optional[bool],
):
    """
    Applies a set of edits to a transaction in order.

    """
    result = client.ontologies.OntologyTransaction.post_edits(
        ontology=ontology,
        transaction_rid=transaction_rid,
        edits=json.loads(edits),
        preview=preview,
    )
    click.echo(repr(result))


@ontologies.group("ontology_object_set")
def ontologies_ontology_object_set():
    pass


@ontologies_ontology_object_set.command("aggregate")
@click.argument("ontology", type=str, required=True)
@click.option("--aggregation", type=str, required=True, help="""""")
@click.option("--group_by", type=str, required=True, help="""""")
@click.option("--object_set", type=str, required=True, help="""""")
@click.option(
    "--accuracy",
    type=click.Choice(["REQUIRE_ACCURATE", "ALLOW_APPROXIMATE"]),
    required=False,
    help="""""",
)
@click.option(
    "--branch",
    type=str,
    required=False,
    help="""The Foundry branch to aggregate the objects from. If not specified, the default branch is used.
Branches are an experimental feature and not all workflows are supported.
""",
)
@click.option("--include_compute_usage", type=bool, required=False, help="""""")
@click.option(
    "--sdk_package_rid",
    type=str,
    required=False,
    help="""The package rid of the generated SDK.
""",
)
@click.option(
    "--sdk_version",
    type=str,
    required=False,
    help="""The package version of the generated SDK.
""",
)
@click.pass_obj
def ontologies_ontology_object_set_op_aggregate(
    client: FoundryClient,
    ontology: str,
    aggregation: str,
    group_by: str,
    object_set: str,
    accuracy: typing.Optional[typing.Literal["REQUIRE_ACCURATE", "ALLOW_APPROXIMATE"]],
    branch: typing.Optional[str],
    include_compute_usage: typing.Optional[bool],
    sdk_package_rid: typing.Optional[str],
    sdk_version: typing.Optional[str],
):
    """
    Aggregates the ontology objects present in the `ObjectSet` from the provided object set definition.

    """
    result = client.ontologies.OntologyObjectSet.aggregate(
        ontology=ontology,
        aggregation=json.loads(aggregation),
        group_by=json.loads(group_by),
        object_set=json.loads(object_set),
        accuracy=accuracy,
        branch=branch,
        include_compute_usage=include_compute_usage,
        sdk_package_rid=sdk_package_rid,
        sdk_version=sdk_version,
    )
    click.echo(repr(result))


@ontologies_ontology_object_set.command("create_temporary")
@click.argument("ontology", type=str, required=True)
@click.option("--object_set", type=str, required=True, help="""""")
@click.option(
    "--sdk_package_rid",
    type=str,
    required=False,
    help="""The package rid of the generated SDK.
""",
)
@click.option(
    "--sdk_version",
    type=str,
    required=False,
    help="""The package version of the generated SDK.
""",
)
@click.pass_obj
def ontologies_ontology_object_set_op_create_temporary(
    client: FoundryClient,
    ontology: str,
    object_set: str,
    sdk_package_rid: typing.Optional[str],
    sdk_version: typing.Optional[str],
):
    """
    Creates a temporary `ObjectSet` from the given definition. This `ObjectSet` expires after one hour.

    """
    result = client.ontologies.OntologyObjectSet.create_temporary(
        ontology=ontology,
        object_set=json.loads(object_set),
        sdk_package_rid=sdk_package_rid,
        sdk_version=sdk_version,
    )
    click.echo(repr(result))


@ontologies_ontology_object_set.command("get")
@click.argument("ontology", type=str, required=True)
@click.argument("object_set_rid", type=str, required=True)
@click.pass_obj
def ontologies_ontology_object_set_op_get(
    client: FoundryClient,
    ontology: str,
    object_set_rid: str,
):
    """
    Gets the definition of the `ObjectSet` with the given RID.

    """
    result = client.ontologies.OntologyObjectSet.get(
        ontology=ontology,
        object_set_rid=object_set_rid,
    )
    click.echo(repr(result))


@ontologies_ontology_object_set.command("load")
@click.argument("ontology", type=str, required=True)
@click.option("--object_set", type=str, required=True, help="""""")
@click.option("--select", type=str, required=True, help="""""")
@click.option(
    "--branch",
    type=str,
    required=False,
    help="""The Foundry branch to load the object set from. If not specified, the default branch is used.
Branches are an experimental feature and not all workflows are supported.
""",
)
@click.option(
    "--exclude_rid",
    type=bool,
    required=False,
    help="""A flag to exclude the retrieval of the `__rid` property.
Setting this to true may improve performance of this endpoint for object types in OSV2.
""",
)
@click.option("--include_compute_usage", type=bool, required=False, help="""""")
@click.option("--order_by", type=str, required=False, help="""""")
@click.option("--page_size", type=int, required=False, help="""""")
@click.option("--page_token", type=str, required=False, help="""""")
@click.option(
    "--sdk_package_rid",
    type=str,
    required=False,
    help="""The package rid of the generated SDK.
""",
)
@click.option(
    "--sdk_version",
    type=str,
    required=False,
    help="""The package version of the generated SDK.
""",
)
@click.option(
    "--snapshot",
    type=bool,
    required=False,
    help="""A flag to use snapshot consistency when paging.
Setting this to true will give you a consistent view from before you start paging through the results, ensuring you do not get duplicate or missing items.
Setting this to false will let new results enter as you page, but you may encounter duplicate or missing items.
This defaults to false if not specified, which means you will always get the latest results.
""",
)
@click.pass_obj
def ontologies_ontology_object_set_op_load(
    client: FoundryClient,
    ontology: str,
    object_set: str,
    select: str,
    branch: typing.Optional[str],
    exclude_rid: typing.Optional[bool],
    include_compute_usage: typing.Optional[bool],
    order_by: typing.Optional[str],
    page_size: typing.Optional[int],
    page_token: typing.Optional[str],
    sdk_package_rid: typing.Optional[str],
    sdk_version: typing.Optional[str],
    snapshot: typing.Optional[bool],
):
    """
    Load the ontology objects present in the `ObjectSet` from the provided object set definition.

    For Object Storage V1 backed objects, this endpoint returns a maximum of 10,000 objects. After 10,000 objects have been returned and if more objects
    are available, attempting to load another page will result in an `ObjectsExceededLimit` error being returned. There is no limit on Object Storage V2 backed objects.

    Note that null value properties will not be returned.

    Vector properties will not be returned unless included in the `select` parameter.

    """
    result = client.ontologies.OntologyObjectSet.load(
        ontology=ontology,
        object_set=json.loads(object_set),
        select=json.loads(select),
        branch=branch,
        exclude_rid=exclude_rid,
        include_compute_usage=include_compute_usage,
        order_by=None if order_by is None else json.loads(order_by),
        page_size=page_size,
        page_token=page_token,
        sdk_package_rid=sdk_package_rid,
        sdk_version=sdk_version,
        snapshot=snapshot,
    )
    click.echo(repr(result))


@ontologies_ontology_object_set.command("load_multiple_object_types")
@click.argument("ontology", type=str, required=True)
@click.option("--object_set", type=str, required=True, help="""""")
@click.option("--select", type=str, required=True, help="""""")
@click.option(
    "--branch",
    type=str,
    required=False,
    help="""The Foundry branch to load the object set for multiple object types. If not specified, the default branch is used.
Branches are an experimental feature and not all workflows are supported.
""",
)
@click.option(
    "--exclude_rid",
    type=bool,
    required=False,
    help="""A flag to exclude the retrieval of the `$rid` property.
Setting this to true may improve performance of this endpoint for object types in OSV2.
""",
)
@click.option("--include_compute_usage", type=bool, required=False, help="""""")
@click.option("--order_by", type=str, required=False, help="""""")
@click.option("--page_size", type=int, required=False, help="""""")
@click.option("--page_token", type=str, required=False, help="""""")
@click.option(
    "--preview",
    type=bool,
    required=False,
    help="""A boolean flag that, when set to true, enables the use of beta features in preview mode.
""",
)
@click.option(
    "--sdk_package_rid",
    type=str,
    required=False,
    help="""The package rid of the generated SDK.
""",
)
@click.option(
    "--sdk_version",
    type=str,
    required=False,
    help="""The package version of the generated SDK.
""",
)
@click.option(
    "--snapshot",
    type=bool,
    required=False,
    help="""A flag to use snapshot consistency when paging.
Setting this to true will give you a consistent view from before you start paging through the results, ensuring you do not get duplicate or missing items.
Setting this to false will let new results enter as you page, but you may encounter duplicate or missing items.
This defaults to false if not specified, which means you will always get the latest results.
""",
)
@click.pass_obj
def ontologies_ontology_object_set_op_load_multiple_object_types(
    client: FoundryClient,
    ontology: str,
    object_set: str,
    select: str,
    branch: typing.Optional[str],
    exclude_rid: typing.Optional[bool],
    include_compute_usage: typing.Optional[bool],
    order_by: typing.Optional[str],
    page_size: typing.Optional[int],
    page_token: typing.Optional[str],
    preview: typing.Optional[bool],
    sdk_package_rid: typing.Optional[str],
    sdk_version: typing.Optional[str],
    snapshot: typing.Optional[bool],
):
    """
    Load the ontology objects present in the `ObjectSet` from the provided object set definition. The resulting
    objects may be scoped to an object type, in which all the selected properties on the object type are returned, or scoped
    to an interface, in which only the object type properties that implement the properties of any interfaces in its
    scope are returned. For objects that are scoped to an interface in the result, a mapping from interface to
    object implementation is returned in order to interpret the objects as the interfaces that they implement.

    For Object Storage V1 backed objects, this endpoint returns a maximum of 10,000 objects. After 10,000 objects have been returned and if more objects
    are available, attempting to load another page will result in an `ObjectsExceededLimit` error being returned. There is no limit on Object Storage V2 backed objects.

    Note that null value properties will not be returned. In addition, property metadata (rid, apiName, and primaryKey)
    will be prefixed with '$' instead of '__' as is the case in `loadObjects`.

    Vector properties will not be returned unless included in the `select` parameter.

    """
    result = client.ontologies.OntologyObjectSet.load_multiple_object_types(
        ontology=ontology,
        object_set=json.loads(object_set),
        select=json.loads(select),
        branch=branch,
        exclude_rid=exclude_rid,
        include_compute_usage=include_compute_usage,
        order_by=None if order_by is None else json.loads(order_by),
        page_size=page_size,
        page_token=page_token,
        preview=preview,
        sdk_package_rid=sdk_package_rid,
        sdk_version=sdk_version,
        snapshot=snapshot,
    )
    click.echo(repr(result))


@ontologies_ontology_object_set.command("load_objects_or_interfaces")
@click.argument("ontology", type=str, required=True)
@click.option("--object_set", type=str, required=True, help="""""")
@click.option("--select", type=str, required=True, help="""""")
@click.option(
    "--branch",
    type=str,
    required=False,
    help="""The Foundry branch to load the objects or interfaces from. If not specified, the default branch is used.
Branches are an experimental feature and not all workflows are supported.
""",
)
@click.option(
    "--exclude_rid",
    type=bool,
    required=False,
    help="""A flag to exclude the retrieval of the `$rid` property.
Setting this to true may improve performance of this endpoint for object types in OSV2.
""",
)
@click.option("--order_by", type=str, required=False, help="""""")
@click.option("--page_size", type=int, required=False, help="""""")
@click.option("--page_token", type=str, required=False, help="""""")
@click.option(
    "--preview",
    type=bool,
    required=False,
    help="""A boolean flag that, when set to true, enables the use of beta features in preview mode.
""",
)
@click.option(
    "--sdk_package_rid",
    type=str,
    required=False,
    help="""The package rid of the generated SDK.
""",
)
@click.option(
    "--sdk_version",
    type=str,
    required=False,
    help="""The package version of the generated SDK.
""",
)
@click.option(
    "--snapshot",
    type=bool,
    required=False,
    help="""A flag to use snapshot consistency when paging.
Setting this to true will give you a consistent view from before you start paging through the results, ensuring you do not get duplicate or missing items.
Setting this to false will let new results enter as you page, but you may encounter duplicate or missing items.
This defaults to false if not specified, which means you will always get the latest results.
""",
)
@click.pass_obj
def ontologies_ontology_object_set_op_load_objects_or_interfaces(
    client: FoundryClient,
    ontology: str,
    object_set: str,
    select: str,
    branch: typing.Optional[str],
    exclude_rid: typing.Optional[bool],
    order_by: typing.Optional[str],
    page_size: typing.Optional[int],
    page_token: typing.Optional[str],
    preview: typing.Optional[bool],
    sdk_package_rid: typing.Optional[str],
    sdk_version: typing.Optional[str],
    snapshot: typing.Optional[bool],
):
    """
    Load the ontology objects present in the `ObjectSet` from the provided object set definition. If the requested
    object set contains interfaces and the object can be viewed as an interface, it will contain the properties
    defined by the interface. If not, it will contain the properties defined by its object type. This allows directly
    loading all objects of an interface where all objects are viewed as the interface, for example.

    Note that the result object set cannot contain a mix of objects with "interface" properties and "object type"
    properties. Attempting to load an object set like this will result in an error.

    For Object Storage V1 backed objects, this endpoint returns a maximum of 10,000 objects. After 10,000 objects have been returned and if more objects
    are available, attempting to load another page will result in an `ObjectsExceededLimit` error being returned. There is no limit on Object Storage V2 backed objects.

    Note that null value properties will not be returned. In addition, property metadata (rid, apiName, and primaryKey)
    will be prefixed with '$' instead of '__' as is the case in `/loadObjects`.

    Vector properties will not be returned unless included in the `select` parameter.

    """
    result = client.ontologies.OntologyObjectSet.load_objects_or_interfaces(
        ontology=ontology,
        object_set=json.loads(object_set),
        select=json.loads(select),
        branch=branch,
        exclude_rid=exclude_rid,
        order_by=None if order_by is None else json.loads(order_by),
        page_size=page_size,
        page_token=page_token,
        preview=preview,
        sdk_package_rid=sdk_package_rid,
        sdk_version=sdk_version,
        snapshot=snapshot,
    )
    click.echo(repr(result))


@ontologies.group("ontology_object")
def ontologies_ontology_object():
    pass


@ontologies_ontology_object.command("aggregate")
@click.argument("ontology", type=str, required=True)
@click.argument("object_type", type=str, required=True)
@click.option("--aggregation", type=str, required=True, help="""""")
@click.option("--group_by", type=str, required=True, help="""""")
@click.option(
    "--accuracy",
    type=click.Choice(["REQUIRE_ACCURATE", "ALLOW_APPROXIMATE"]),
    required=False,
    help="""""",
)
@click.option(
    "--branch",
    type=str,
    required=False,
    help="""The Foundry branch to aggregate objects from. If not specified, the default branch will be used.
Branches are an experimental feature and not all workflows are supported.
""",
)
@click.option(
    "--sdk_package_rid",
    type=str,
    required=False,
    help="""The package rid of the generated SDK.
""",
)
@click.option(
    "--sdk_version",
    type=str,
    required=False,
    help="""The version of the generated SDK.
""",
)
@click.option("--where", type=str, required=False, help="""""")
@click.pass_obj
def ontologies_ontology_object_op_aggregate(
    client: FoundryClient,
    ontology: str,
    object_type: str,
    aggregation: str,
    group_by: str,
    accuracy: typing.Optional[typing.Literal["REQUIRE_ACCURATE", "ALLOW_APPROXIMATE"]],
    branch: typing.Optional[str],
    sdk_package_rid: typing.Optional[str],
    sdk_version: typing.Optional[str],
    where: typing.Optional[str],
):
    """
    Perform functions on object fields in the specified ontology and object type.

    """
    result = client.ontologies.OntologyObject.aggregate(
        ontology=ontology,
        object_type=object_type,
        aggregation=json.loads(aggregation),
        group_by=json.loads(group_by),
        accuracy=accuracy,
        branch=branch,
        sdk_package_rid=sdk_package_rid,
        sdk_version=sdk_version,
        where=None if where is None else json.loads(where),
    )
    click.echo(repr(result))


@ontologies_ontology_object.command("count")
@click.argument("ontology", type=str, required=True)
@click.argument("object_type", type=str, required=True)
@click.option(
    "--branch",
    type=str,
    required=False,
    help="""The Foundry branch to count the objects from. If not specified, the default branch is used.
Branches are an experimental feature and not all workflows are supported.
""",
)
@click.option(
    "--sdk_package_rid",
    type=str,
    required=False,
    help="""The package rid of the generated SDK.
""",
)
@click.option(
    "--sdk_version",
    type=str,
    required=False,
    help="""The package version of the generated SDK.
""",
)
@click.pass_obj
def ontologies_ontology_object_op_count(
    client: FoundryClient,
    ontology: str,
    object_type: str,
    branch: typing.Optional[str],
    sdk_package_rid: typing.Optional[str],
    sdk_version: typing.Optional[str],
):
    """
    Returns a count of the objects of the given object type.

    """
    result = client.ontologies.OntologyObject.count(
        ontology=ontology,
        object_type=object_type,
        branch=branch,
        sdk_package_rid=sdk_package_rid,
        sdk_version=sdk_version,
    )
    click.echo(repr(result))


@ontologies_ontology_object.command("get")
@click.argument("ontology", type=str, required=True)
@click.argument("object_type", type=str, required=True)
@click.argument("primary_key", type=str, required=True)
@click.option(
    "--branch",
    type=str,
    required=False,
    help="""The Foundry branch to get the object from. If not specified, the default branch is used.
Branches are an experimental feature and not all workflows are supported.
""",
)
@click.option(
    "--exclude_rid",
    type=bool,
    required=False,
    help="""A flag to exclude the retrieval of the `__rid` property. 
Setting this to true may improve performance of this endpoint for object types in OSV2.
""",
)
@click.option(
    "--sdk_package_rid",
    type=str,
    required=False,
    help="""The package rid of the generated SDK.
""",
)
@click.option(
    "--sdk_version",
    type=str,
    required=False,
    help="""The version of the generated SDK.
""",
)
@click.option(
    "--select",
    type=str,
    required=False,
    help="""The properties of the object type that should be included in the response. Omit this parameter to get all
the properties.
""",
)
@click.pass_obj
def ontologies_ontology_object_op_get(
    client: FoundryClient,
    ontology: str,
    object_type: str,
    primary_key: str,
    branch: typing.Optional[str],
    exclude_rid: typing.Optional[bool],
    sdk_package_rid: typing.Optional[str],
    sdk_version: typing.Optional[str],
    select: typing.Optional[str],
):
    """
    Gets a specific object with the given primary key.

    """
    result = client.ontologies.OntologyObject.get(
        ontology=ontology,
        object_type=object_type,
        primary_key=primary_key,
        branch=branch,
        exclude_rid=exclude_rid,
        sdk_package_rid=sdk_package_rid,
        sdk_version=sdk_version,
        select=None if select is None else json.loads(select),
    )
    click.echo(repr(result))


@ontologies_ontology_object.command("list")
@click.argument("ontology", type=str, required=True)
@click.argument("object_type", type=str, required=True)
@click.option(
    "--branch",
    type=str,
    required=False,
    help="""The Foundry branch to list objects from. If not specified, the default branch will be used.
Branches are an experimental feature and not all workflows are supported.
""",
)
@click.option(
    "--exclude_rid",
    type=bool,
    required=False,
    help="""A flag to exclude the retrieval of the `__rid` property. 
Setting this to true may improve performance of this endpoint for object types in OSV2.
""",
)
@click.option("--order_by", type=str, required=False, help="""""")
@click.option(
    "--page_size",
    type=int,
    required=False,
    help="""The desired size of the page to be returned. Defaults to 1,000.
See [page sizes](https://palantir.com/docs/foundry/api/general/overview/paging/#page-sizes) for details.
""",
)
@click.option("--page_token", type=str, required=False, help="""""")
@click.option(
    "--sdk_package_rid",
    type=str,
    required=False,
    help="""The package rid of the generated SDK.
""",
)
@click.option(
    "--sdk_version",
    type=str,
    required=False,
    help="""The version of the generated SDK.
""",
)
@click.option(
    "--select",
    type=str,
    required=False,
    help="""The properties of the object type that should be included in the response. Omit this parameter to get all
the properties.
""",
)
@click.option(
    "--snapshot",
    type=bool,
    required=False,
    help="""A flag to use snapshot consistency when paging.
Setting this to true will give you a consistent view from before you start paging through the results, ensuring you do not get duplicate or missing items.
Setting this to false will let new results enter as you page, but you may encounter duplicate or missing items.
This defaults to false if not specified, which means you will always get the latest results.
""",
)
@click.pass_obj
def ontologies_ontology_object_op_list(
    client: FoundryClient,
    ontology: str,
    object_type: str,
    branch: typing.Optional[str],
    exclude_rid: typing.Optional[bool],
    order_by: typing.Optional[str],
    page_size: typing.Optional[int],
    page_token: typing.Optional[str],
    sdk_package_rid: typing.Optional[str],
    sdk_version: typing.Optional[str],
    select: typing.Optional[str],
    snapshot: typing.Optional[bool],
):
    """
    Lists the objects for the given Ontology and object type.

    Note that this endpoint does not guarantee consistency. Changes to the data could result in missing or
    repeated objects in the response pages.

    For Object Storage V1 backed objects, this endpoint returns a maximum of 10,000 objects. After 10,000 objects have been returned and if more objects
    are available, attempting to load another page will result in an `ObjectsExceededLimit` error being returned. There is no limit on Object Storage V2 backed objects.

    Each page may be smaller or larger than the requested page size. However, it
    is guaranteed that if there are more results available, at least one result will be present
    in the response.

    Note that null value properties will not be returned.

    """
    result = client.ontologies.OntologyObject.list(
        ontology=ontology,
        object_type=object_type,
        branch=branch,
        exclude_rid=exclude_rid,
        order_by=order_by,
        page_size=page_size,
        page_token=page_token,
        sdk_package_rid=sdk_package_rid,
        sdk_version=sdk_version,
        select=None if select is None else json.loads(select),
        snapshot=snapshot,
    )
    click.echo(repr(result))


@ontologies_ontology_object.command("search")
@click.argument("ontology", type=str, required=True)
@click.argument("object_type", type=str, required=True)
@click.option(
    "--select",
    type=str,
    required=True,
    help="""The API names of the object type properties to include in the response.
""",
)
@click.option(
    "--branch",
    type=str,
    required=False,
    help="""The Foundry branch to search objects from. If not specified, the default branch will be used.
Branches are an experimental feature and not all workflows are supported.
""",
)
@click.option(
    "--exclude_rid",
    type=bool,
    required=False,
    help="""A flag to exclude the retrieval of the `__rid` property.
Setting this to true may improve performance of this endpoint for object types in OSV2.
""",
)
@click.option("--order_by", type=str, required=False, help="""""")
@click.option("--page_size", type=int, required=False, help="""""")
@click.option("--page_token", type=str, required=False, help="""""")
@click.option(
    "--sdk_package_rid",
    type=str,
    required=False,
    help="""The package rid of the generated SDK.
""",
)
@click.option(
    "--sdk_version",
    type=str,
    required=False,
    help="""The version of the generated SDK.
""",
)
@click.option(
    "--snapshot",
    type=bool,
    required=False,
    help="""A flag to use snapshot consistency when paging.
Setting this to true will give you a consistent view from before you start paging through the results, ensuring you do not get duplicate or missing items.
Setting this to false will let new results enter as you page, but you may encounter duplicate or missing items.
This defaults to false if not specified, which means you will always get the latest results.
""",
)
@click.option("--where", type=str, required=False, help="""""")
@click.pass_obj
def ontologies_ontology_object_op_search(
    client: FoundryClient,
    ontology: str,
    object_type: str,
    select: str,
    branch: typing.Optional[str],
    exclude_rid: typing.Optional[bool],
    order_by: typing.Optional[str],
    page_size: typing.Optional[int],
    page_token: typing.Optional[str],
    sdk_package_rid: typing.Optional[str],
    sdk_version: typing.Optional[str],
    snapshot: typing.Optional[bool],
    where: typing.Optional[str],
):
    """
    Search for objects in the specified ontology and object type. The request body is used
    to filter objects based on the specified query. The supported queries are:

    | Query type                              | Description                                                                                                       | Supported Types                 |
    |-----------------------------------------|-------------------------------------------------------------------------------------------------------------------|---------------------------------|
    | lt                                      | The provided property is less than the provided value.                                                            | number, string, date, timestamp |
    | gt                                      | The provided property is greater than the provided value.                                                         | number, string, date, timestamp |
    | lte                                     | The provided property is less than or equal to the provided value.                                                | number, string, date, timestamp |
    | gte                                     | The provided property is greater than or equal to the provided value.                                             | number, string, date, timestamp |
    | eq                                      | The provided property is exactly equal to the provided value.                                                     | number, string, date, timestamp |
    | isNull                                  | The provided property is (or is not) null.                                                                        | all                             |
    | contains                                | The provided property contains the provided value.                                                                | array                           |
    | not                                     | The sub-query does not match.                                                                                     | N/A (applied on a query)        |
    | and                                     | All the sub-queries match.                                                                                        | N/A (applied on queries)        |
    | or                                      | At least one of the sub-queries match.                                                                            | N/A (applied on queries)        |
    | containsAllTermsInOrderPrefixLastTerm   | The provided property contains all the terms provided in order. The last term can be a partial prefix match.      | string                          |
    | containsAllTermsInOrder                 | The provided property contains the provided term as a substring.                                                  | string                          |
    | containsAnyTerm                         | The provided property contains at least one of the terms separated by whitespace.                                 | string                          |
    | containsAllTerms                        | The provided property contains all the terms separated by whitespace.                                             | string                          |
    | startsWith                              | Deprecated alias for containsAllTermsInOrderPrefixLastTerm.                                                       | string                          |

    Queries can be at most three levels deep. By default, terms are separated by whitespace or punctuation (`?!,:;-[](){}'"~`). Periods (`.`) on their own are ignored.
    Partial terms are not matched by terms filters except where explicitly noted.

    """
    result = client.ontologies.OntologyObject.search(
        ontology=ontology,
        object_type=object_type,
        select=json.loads(select),
        branch=branch,
        exclude_rid=exclude_rid,
        order_by=None if order_by is None else json.loads(order_by),
        page_size=page_size,
        page_token=page_token,
        sdk_package_rid=sdk_package_rid,
        sdk_version=sdk_version,
        snapshot=snapshot,
        where=None if where is None else json.loads(where),
    )
    click.echo(repr(result))


@ontologies.group("ontology_interface")
def ontologies_ontology_interface():
    pass


@ontologies_ontology_interface.command("aggregate")
@click.argument("ontology", type=str, required=True)
@click.argument("interface_type", type=str, required=True)
@click.option("--aggregation", type=str, required=True, help="""""")
@click.option("--group_by", type=str, required=True, help="""""")
@click.option(
    "--accuracy",
    type=click.Choice(["REQUIRE_ACCURATE", "ALLOW_APPROXIMATE"]),
    required=False,
    help="""""",
)
@click.option(
    "--branch",
    type=str,
    required=False,
    help="""The Foundry branch to aggregate objects from. If not specified, the default branch will be used.
Branches are an experimental feature and not all workflows are supported.
""",
)
@click.option(
    "--preview",
    type=bool,
    required=False,
    help="""A boolean flag that, when set to true, enables the use of beta features in preview mode.
""",
)
@click.option("--where", type=str, required=False, help="""""")
@click.pass_obj
def ontologies_ontology_interface_op_aggregate(
    client: FoundryClient,
    ontology: str,
    interface_type: str,
    aggregation: str,
    group_by: str,
    accuracy: typing.Optional[typing.Literal["REQUIRE_ACCURATE", "ALLOW_APPROXIMATE"]],
    branch: typing.Optional[str],
    preview: typing.Optional[bool],
    where: typing.Optional[str],
):
    """
    :::callout{theme=warning title=Warning}
    This endpoint will be removed once TS OSDK is updated to use `objectSets/aggregate` with interface object
    sets.
    :::
    Perform functions on object fields in the specified ontology and of the specified interface type. Any
    properties specified in the query must be shared property type API names defined on the interface.

    """
    result = client.ontologies.OntologyInterface.aggregate(
        ontology=ontology,
        interface_type=interface_type,
        aggregation=json.loads(aggregation),
        group_by=json.loads(group_by),
        accuracy=accuracy,
        branch=branch,
        preview=preview,
        where=None if where is None else json.loads(where),
    )
    click.echo(repr(result))


@ontologies_ontology_interface.command("get")
@click.argument("ontology", type=str, required=True)
@click.argument("interface_type", type=str, required=True)
@click.option(
    "--branch",
    type=str,
    required=False,
    help="""The Foundry branch to load the interface type definition from. If not specified, the default branch will be used.
Branches are an experimental feature and not all workflows are supported.
""",
)
@click.option(
    "--preview",
    type=bool,
    required=False,
    help="""A boolean flag that, when set to true, enables the use of beta features in preview mode.
""",
)
@click.pass_obj
def ontologies_ontology_interface_op_get(
    client: FoundryClient,
    ontology: str,
    interface_type: str,
    branch: typing.Optional[str],
    preview: typing.Optional[bool],
):
    """
    Gets a specific interface type with the given API name.

    """
    result = client.ontologies.OntologyInterface.get(
        ontology=ontology,
        interface_type=interface_type,
        branch=branch,
        preview=preview,
    )
    click.echo(repr(result))


@ontologies_ontology_interface.command("get_outgoing_interface_link_type")
@click.argument("ontology", type=str, required=True)
@click.argument("interface_type", type=str, required=True)
@click.argument("interface_link_type", type=str, required=True)
@click.option(
    "--branch",
    type=str,
    required=False,
    help="""The Foundry branch to get the outgoing link types for an object type from. If not specified, the default branch will be used.
Branches are an experimental feature and not all workflows are supported.
""",
)
@click.pass_obj
def ontologies_ontology_interface_op_get_outgoing_interface_link_type(
    client: FoundryClient,
    ontology: str,
    interface_type: str,
    interface_link_type: str,
    branch: typing.Optional[str],
):
    """
    Get an outgoing interface link type for an interface type.

    """
    result = client.ontologies.OntologyInterface.get_outgoing_interface_link_type(
        ontology=ontology,
        interface_type=interface_type,
        interface_link_type=interface_link_type,
        branch=branch,
    )
    click.echo(repr(result))


@ontologies_ontology_interface.command("list")
@click.argument("ontology", type=str, required=True)
@click.option(
    "--branch",
    type=str,
    required=False,
    help="""The Foundry branch to list the interface types from. If not specified, the default branch will be used.
Branches are an experimental feature and not all workflows are supported.
""",
)
@click.option(
    "--page_size",
    type=int,
    required=False,
    help="""The desired size of the page to be returned. Defaults to 500.
See [page sizes](https://palantir.com/docs/foundry/api/general/overview/paging/#page-sizes) for details.
""",
)
@click.option("--page_token", type=str, required=False, help="""""")
@click.option(
    "--preview",
    type=bool,
    required=False,
    help="""A boolean flag that, when set to true, enables the use of beta features in preview mode.
""",
)
@click.pass_obj
def ontologies_ontology_interface_op_list(
    client: FoundryClient,
    ontology: str,
    branch: typing.Optional[str],
    page_size: typing.Optional[int],
    page_token: typing.Optional[str],
    preview: typing.Optional[bool],
):
    """
    Lists the interface types for the given Ontology.

    Each page may be smaller than the requested page size. However, it is guaranteed that if there are more
    results available, at least one result will be present in the response.

    """
    result = client.ontologies.OntologyInterface.list(
        ontology=ontology,
        branch=branch,
        page_size=page_size,
        page_token=page_token,
        preview=preview,
    )
    click.echo(repr(result))


@ontologies_ontology_interface.command("list_interface_linked_objects")
@click.argument("ontology", type=str, required=True)
@click.argument("interface_type", type=str, required=True)
@click.argument("object_type", type=str, required=True)
@click.argument("primary_key", type=str, required=True)
@click.argument("interface_link_type", type=str, required=True)
@click.option(
    "--branch",
    type=str,
    required=False,
    help="""The Foundry branch to get the outgoing link types for an object type from. If not specified, the default branch will be used.
Branches are an experimental feature and not all workflows are supported.
""",
)
@click.option(
    "--exclude_rid",
    type=bool,
    required=False,
    help="""A flag to exclude the retrieval of the `__rid` property. 
Setting this to true may improve performance of this endpoint for object types in OSV2.
""",
)
@click.option("--order_by", type=str, required=False, help="""""")
@click.option(
    "--page_size",
    type=int,
    required=False,
    help="""The desired size of the page to be returned. Defaults to 1,000.
See [page sizes](https://palantir.com/docs/foundry/api/general/overview/paging/#page-sizes) for details.
""",
)
@click.option("--page_token", type=str, required=False, help="""""")
@click.option(
    "--preview",
    type=bool,
    required=False,
    help="""A boolean flag that, when set to true, enables the use of beta features in preview mode.
""",
)
@click.option(
    "--select",
    type=str,
    required=False,
    help="""The properties of the object type that should be included in the response. Omit this parameter to get all
the properties.
""",
)
@click.option(
    "--snapshot",
    type=bool,
    required=False,
    help="""A flag to use snapshot consistency when paging.
Setting this to true will give you a consistent view from before you start paging through the results, ensuring you do not get duplicate or missing items.
Setting this to false will let new results enter as you page, but you may encounter duplicate or missing items.
This defaults to false if not specified, which means you will always get the latest results.
""",
)
@click.pass_obj
def ontologies_ontology_interface_op_list_interface_linked_objects(
    client: FoundryClient,
    ontology: str,
    interface_type: str,
    object_type: str,
    primary_key: str,
    interface_link_type: str,
    branch: typing.Optional[str],
    exclude_rid: typing.Optional[bool],
    order_by: typing.Optional[str],
    page_size: typing.Optional[int],
    page_token: typing.Optional[str],
    preview: typing.Optional[bool],
    select: typing.Optional[str],
    snapshot: typing.Optional[bool],
):
    """
    Lists the linked objects for a specific object and the given interface link type.

    Note that this endpoint does not guarantee consistency. Changes to the data could result in missing or
    repeated objects in the response pages.

    For Object Storage V1 backed objects, this endpoint returns a maximum of 10,000 objects. After 10,000 objects have been returned and if more objects
    are available, attempting to load another page will result in an `ObjectsExceededLimit` error being returned. There is no limit on Object Storage V2 backed objects.

    Each page may be smaller or larger than the requested page size. However, it
    is guaranteed that if there are more results available, at least one result will be present
    in the response.

    Note that null value properties will not be returned.

    """
    result = client.ontologies.OntologyInterface.list_interface_linked_objects(
        ontology=ontology,
        interface_type=interface_type,
        object_type=object_type,
        primary_key=primary_key,
        interface_link_type=interface_link_type,
        branch=branch,
        exclude_rid=exclude_rid,
        order_by=order_by,
        page_size=page_size,
        page_token=page_token,
        preview=preview,
        select=None if select is None else json.loads(select),
        snapshot=snapshot,
    )
    click.echo(repr(result))


@ontologies_ontology_interface.command("list_objects_for_interface")
@click.argument("ontology", type=str, required=True)
@click.argument("interface_type", type=str, required=True)
@click.option(
    "--branch",
    type=str,
    required=False,
    help="""The Foundry branch to list objects from. If not specified, the default branch will be used.
Branches are an experimental feature and not all workflows are supported.
""",
)
@click.option(
    "--exclude_rid",
    type=bool,
    required=False,
    help="""A flag to exclude the retrieval of the `__rid` property. 
Setting this to true may improve performance of this endpoint for object types in OSV2.
""",
)
@click.option("--order_by", type=str, required=False, help="""""")
@click.option(
    "--page_size",
    type=int,
    required=False,
    help="""The desired size of the page to be returned. Defaults to 1,000.
See [page sizes](https://palantir.com/docs/foundry/api/general/overview/paging/#page-sizes) for details.
""",
)
@click.option("--page_token", type=str, required=False, help="""""")
@click.option(
    "--select",
    type=str,
    required=False,
    help="""The properties of the interface type that should be included in the response. Omit this parameter to get all
the properties.
""",
)
@click.option(
    "--snapshot",
    type=bool,
    required=False,
    help="""A flag to use snapshot consistency when paging.
Setting this to true will give you a consistent view from before you start paging through the results, ensuring you do not get duplicate or missing items.
Setting this to false will let new results enter as you page, but you may encounter duplicate or missing items.
This defaults to false if not specified, which means you will always get the latest results.
""",
)
@click.pass_obj
def ontologies_ontology_interface_op_list_objects_for_interface(
    client: FoundryClient,
    ontology: str,
    interface_type: str,
    branch: typing.Optional[str],
    exclude_rid: typing.Optional[bool],
    order_by: typing.Optional[str],
    page_size: typing.Optional[int],
    page_token: typing.Optional[str],
    select: typing.Optional[str],
    snapshot: typing.Optional[bool],
):
    """
    Lists the objects for the given Ontology and interface type.

    Note that this endpoint does not guarantee consistency, unless you use the snapshot flag specified below. Changes to the data could result in missing or
    repeated objects in the response pages.

    For Object Storage V1 backed objects, this endpoint returns a maximum of 10,000 objects. After 10,000 objects have been returned and if more objects
    are available, attempting to load another page will result in an `ObjectsExceededLimit` error being returned. There is no limit on Object Storage V2 backed objects.

    Each page may be smaller or larger than the requested page size. However, it
    is guaranteed that if there are more results available, at least one result will be present
    in the response.

    Note that null value properties will not be returned.

    """
    result = client.ontologies.OntologyInterface.list_objects_for_interface(
        ontology=ontology,
        interface_type=interface_type,
        branch=branch,
        exclude_rid=exclude_rid,
        order_by=order_by,
        page_size=page_size,
        page_token=page_token,
        select=None if select is None else json.loads(select),
        snapshot=snapshot,
    )
    click.echo(repr(result))


@ontologies_ontology_interface.command("list_outgoing_interface_link_types")
@click.argument("ontology", type=str, required=True)
@click.argument("interface_type", type=str, required=True)
@click.option(
    "--branch",
    type=str,
    required=False,
    help="""The Foundry branch to get the outgoing link type from. If not specified, the default branch will be used.
Branches are an experimental feature and not all workflows are supported.
""",
)
@click.pass_obj
def ontologies_ontology_interface_op_list_outgoing_interface_link_types(
    client: FoundryClient,
    ontology: str,
    interface_type: str,
    branch: typing.Optional[str],
):
    """
    List the outgoing interface link types for an interface type.

    """
    result = client.ontologies.OntologyInterface.list_outgoing_interface_link_types(
        ontology=ontology,
        interface_type=interface_type,
        branch=branch,
    )
    click.echo(repr(result))


@ontologies_ontology_interface.command("search")
@click.argument("ontology", type=str, required=True)
@click.argument("interface_type", type=str, required=True)
@click.option(
    "--augmented_properties",
    type=str,
    required=True,
    help="""A map from object type API name to a list of property type API names. For each returned object, if the 
object’s object type is a key in the map, then we augment the response for that object type with the list 
of properties specified in the value.
""",
)
@click.option(
    "--augmented_shared_property_types",
    type=str,
    required=True,
    help="""A map from interface type API name to a list of shared property type API names. For each returned object, if
the object implements an interface that is a key in the map, then we augment the response for that object 
type with the list of properties specified in the value.
""",
)
@click.option(
    "--other_interface_types",
    type=str,
    required=True,
    help="""A list of interface type API names. Object types must implement all the mentioned interfaces in order to be 
included in the response.
""",
)
@click.option(
    "--selected_object_types",
    type=str,
    required=True,
    help="""A list of object type API names that should be included in the response. If non-empty, object types that are
not mentioned will not be included in the response even if they implement the specified interface. Omit the 
parameter to include all object types.
""",
)
@click.option(
    "--selected_shared_property_types",
    type=str,
    required=True,
    help="""A list of shared property type API names of the interface type that should be included in the response. 
Omit this parameter to include all properties of the interface type in the response.
""",
)
@click.option(
    "--branch",
    type=str,
    required=False,
    help="""The Foundry branch to search objects from. If not specified, the default branch will be used.
Branches are an experimental feature and not all workflows are supported.
""",
)
@click.option("--order_by", type=str, required=False, help="""""")
@click.option("--page_size", type=int, required=False, help="""""")
@click.option("--page_token", type=str, required=False, help="""""")
@click.option(
    "--preview",
    type=bool,
    required=False,
    help="""A boolean flag that, when set to true, enables the use of beta features in preview mode.
""",
)
@click.option("--where", type=str, required=False, help="""""")
@click.pass_obj
def ontologies_ontology_interface_op_search(
    client: FoundryClient,
    ontology: str,
    interface_type: str,
    augmented_properties: str,
    augmented_shared_property_types: str,
    other_interface_types: str,
    selected_object_types: str,
    selected_shared_property_types: str,
    branch: typing.Optional[str],
    order_by: typing.Optional[str],
    page_size: typing.Optional[int],
    page_token: typing.Optional[str],
    preview: typing.Optional[bool],
    where: typing.Optional[str],
):
    """
    :::callout{theme=warning title=Warning}
      This endpoint will be removed once TS OSDK is updated to use `objectSets/loadObjects` with interface object
      sets.
    :::
    Search for objects in the specified ontology and interface type. Any properties specified in the "where" or
    "orderBy" parameters must be shared property type API names defined on the interface. The following search
    queries are supported:

    | Query type                              | Description                                                                                                       | Supported Types                 |
    |-----------------------------------------|-------------------------------------------------------------------------------------------------------------------|---------------------------------|
    | lt                                      | The provided property is less than the provided value.                                                            | number, string, date, timestamp |
    | gt                                      | The provided property is greater than the provided value.                                                         | number, string, date, timestamp |
    | lte                                     | The provided property is less than or equal to the provided value.                                                | number, string, date, timestamp |
    | gte                                     | The provided property is greater than or equal to the provided value.                                             | number, string, date, timestamp |
    | eq                                      | The provided property is exactly equal to the provided value.                                                     | number, string, date, timestamp |
    | isNull                                  | The provided property is (or is not) null.                                                                        | all                             |
    | contains                                | The provided property contains the provided value.                                                                | array                           |
    | not                                     | The sub-query does not match.                                                                                     | N/A (applied on a query)        |
    | and                                     | All the sub-queries match.                                                                                        | N/A (applied on queries)        |
    | or                                      | At least one of the sub-queries match.                                                                            | N/A (applied on queries)        |
    | startsWith                              | The provided property starts with the provided term.                                                              | string                          |
    | containsAllTermsInOrderPrefixLastTerm   | The provided property contains all the terms provided in order. The last term can be a partial prefix match.      | string                          |
    | containsAllTermsInOrder                 | The provided property contains the provided terms as a substring.                                                 | string                          |
    | containsAnyTerm                         | The provided property contains at least one of the terms separated by whitespace.                                 | string                          |
    | containsAllTerms                        | The provided property contains all the terms separated by whitespace.                                             | string                          |

    Queries can be at most three levels deep. By default, terms are separated by whitespace or punctuation (`?!,:;-[](){}'"~`). Periods (`.`) on their own are ignored.
    Partial terms are not matched by terms filters except where explicitly noted.

    Attempting to use an unsupported query will result in a validation error. Third-party applications using this
    endpoint via OAuth2 must request the following operation scope: `api:ontologies-read`.

    """
    result = client.ontologies.OntologyInterface.search(
        ontology=ontology,
        interface_type=interface_type,
        augmented_properties=json.loads(augmented_properties),
        augmented_shared_property_types=json.loads(augmented_shared_property_types),
        other_interface_types=json.loads(other_interface_types),
        selected_object_types=json.loads(selected_object_types),
        selected_shared_property_types=json.loads(selected_shared_property_types),
        branch=branch,
        order_by=None if order_by is None else json.loads(order_by),
        page_size=page_size,
        page_token=page_token,
        preview=preview,
        where=None if where is None else json.loads(where),
    )
    click.echo(repr(result))


@ontologies.group("ontology")
def ontologies_ontology():
    pass


@ontologies_ontology.command("get")
@click.argument("ontology", type=str, required=True)
@click.pass_obj
def ontologies_ontology_op_get(
    client: FoundryClient,
    ontology: str,
):
    """
    Gets a specific ontology for a given Ontology API name or RID.

    """
    result = client.ontologies.Ontology.get(
        ontology=ontology,
    )
    click.echo(repr(result))


@ontologies_ontology.command("get_full_metadata")
@click.argument("ontology", type=str, required=True)
@click.option(
    "--branch",
    type=str,
    required=False,
    help="""The Foundry branch to load metadata from. If not specified, the default branch will be used.
Branches are an experimental feature and not all workflows are supported.
""",
)
@click.pass_obj
def ontologies_ontology_op_get_full_metadata(
    client: FoundryClient,
    ontology: str,
    branch: typing.Optional[str],
):
    """
    Get the full Ontology metadata. This includes the objects, links, actions, queries, and interfaces.
    This endpoint is designed to return as much metadata as possible in a single request to support OSDK workflows.
    It may omit certain entities rather than fail the request.

    """
    result = client.ontologies.Ontology.get_full_metadata(
        ontology=ontology,
        branch=branch,
    )
    click.echo(repr(result))


@ontologies_ontology.command("list")
@click.pass_obj
def ontologies_ontology_op_list(
    client: FoundryClient,
):
    """
    Lists the Ontologies visible to the current user.

    """
    result = client.ontologies.Ontology.list()
    click.echo(repr(result))


@ontologies_ontology.command("load_metadata")
@click.argument("ontology", type=str, required=True)
@click.option("--action_types", type=str, required=True, help="""""")
@click.option("--interface_types", type=str, required=True, help="""""")
@click.option("--link_types", type=str, required=True, help="""""")
@click.option("--object_types", type=str, required=True, help="""""")
@click.option("--query_types", type=str, required=True, help="""""")
@click.option(
    "--branch",
    type=str,
    required=False,
    help="""The Foundry branch to load metadata from. If not specified, the default branch will be used.
Branches are an experimental feature and not all workflows are supported.
""",
)
@click.option(
    "--preview",
    type=bool,
    required=False,
    help="""A boolean flag that, when set to true, enables the use of beta features in preview mode.
""",
)
@click.pass_obj
def ontologies_ontology_op_load_metadata(
    client: FoundryClient,
    ontology: str,
    action_types: str,
    interface_types: str,
    link_types: str,
    object_types: str,
    query_types: str,
    branch: typing.Optional[str],
    preview: typing.Optional[bool],
):
    """
    Load Ontology metadata for the requested object, link, action, query, and interface types.

    """
    result = client.ontologies.Ontology.load_metadata(
        ontology=ontology,
        action_types=json.loads(action_types),
        interface_types=json.loads(interface_types),
        link_types=json.loads(link_types),
        object_types=json.loads(object_types),
        query_types=json.loads(query_types),
        branch=branch,
        preview=preview,
    )
    click.echo(repr(result))


@ontologies_ontology.group("query_type")
def ontologies_ontology_query_type():
    pass


@ontologies_ontology_query_type.command("get")
@click.argument("ontology", type=str, required=True)
@click.argument("query_api_name", type=str, required=True)
@click.option(
    "--sdk_package_rid",
    type=str,
    required=False,
    help="""The package rid of the generated SDK.
""",
)
@click.option(
    "--sdk_version",
    type=str,
    required=False,
    help="""The version of the generated SDK.
""",
)
@click.option(
    "--version",
    type=str,
    required=False,
    help="""The version of the Query to get.
""",
)
@click.pass_obj
def ontologies_ontology_query_type_op_get(
    client: FoundryClient,
    ontology: str,
    query_api_name: str,
    sdk_package_rid: typing.Optional[str],
    sdk_version: typing.Optional[str],
    version: typing.Optional[str],
):
    """
    Gets a specific query type with the given API name.

    """
    result = client.ontologies.Ontology.QueryType.get(
        ontology=ontology,
        query_api_name=query_api_name,
        sdk_package_rid=sdk_package_rid,
        sdk_version=sdk_version,
        version=version,
    )
    click.echo(repr(result))


@ontologies_ontology_query_type.command("list")
@click.argument("ontology", type=str, required=True)
@click.option(
    "--page_size",
    type=int,
    required=False,
    help="""The desired size of the page to be returned. Defaults to 100.
See [page sizes](https://palantir.com/docs/foundry/api/general/overview/paging/#page-sizes) for details.
""",
)
@click.option("--page_token", type=str, required=False, help="""""")
@click.pass_obj
def ontologies_ontology_query_type_op_list(
    client: FoundryClient,
    ontology: str,
    page_size: typing.Optional[int],
    page_token: typing.Optional[str],
):
    """
    Lists the query types for the given Ontology.

    Each page may be smaller than the requested page size. However, it is guaranteed that if there are more
    results available, at least one result will be present in the response.

    """
    result = client.ontologies.Ontology.QueryType.list(
        ontology=ontology,
        page_size=page_size,
        page_token=page_token,
    )
    click.echo(repr(result))


@ontologies_ontology.group("object_type")
def ontologies_ontology_object_type():
    pass


@ontologies_ontology_object_type.command("get")
@click.argument("ontology", type=str, required=True)
@click.argument("object_type", type=str, required=True)
@click.option(
    "--branch",
    type=str,
    required=False,
    help="""The Foundry branch to load the object type definition from. If not specified, the default branch will be used.
Branches are an experimental feature and not all workflows are supported.
""",
)
@click.pass_obj
def ontologies_ontology_object_type_op_get(
    client: FoundryClient,
    ontology: str,
    object_type: str,
    branch: typing.Optional[str],
):
    """
    Gets a specific object type with the given API name.

    """
    result = client.ontologies.Ontology.ObjectType.get(
        ontology=ontology,
        object_type=object_type,
        branch=branch,
    )
    click.echo(repr(result))


@ontologies_ontology_object_type.command("get_full_metadata")
@click.argument("ontology", type=str, required=True)
@click.argument("object_type", type=str, required=True)
@click.option(
    "--branch",
    type=str,
    required=False,
    help="""The Foundry branch to load the action type definition from. If not specified, the default branch will be used.
Branches are an experimental feature and not all workflows are supported.
""",
)
@click.option(
    "--preview",
    type=bool,
    required=False,
    help="""A boolean flag that, when set to true, enables the use of beta features in preview mode.
""",
)
@click.option(
    "--sdk_package_rid",
    type=str,
    required=False,
    help="""The package rid of the generated SDK.
""",
)
@click.option(
    "--sdk_version",
    type=str,
    required=False,
    help="""The version of the generated SDK.
""",
)
@click.pass_obj
def ontologies_ontology_object_type_op_get_full_metadata(
    client: FoundryClient,
    ontology: str,
    object_type: str,
    branch: typing.Optional[str],
    preview: typing.Optional[bool],
    sdk_package_rid: typing.Optional[str],
    sdk_version: typing.Optional[str],
):
    """
    Gets the full metadata for a specific object type with the given API name.

    """
    result = client.ontologies.Ontology.ObjectType.get_full_metadata(
        ontology=ontology,
        object_type=object_type,
        branch=branch,
        preview=preview,
        sdk_package_rid=sdk_package_rid,
        sdk_version=sdk_version,
    )
    click.echo(repr(result))


@ontologies_ontology_object_type.command("get_outgoing_link_type")
@click.argument("ontology", type=str, required=True)
@click.argument("object_type", type=str, required=True)
@click.argument("link_type", type=str, required=True)
@click.option(
    "--branch",
    type=str,
    required=False,
    help="""The Foundry branch to get the outgoing link types for an object type from. If not specified, the default branch will be used.
Branches are an experimental feature and not all workflows are supported.
""",
)
@click.pass_obj
def ontologies_ontology_object_type_op_get_outgoing_link_type(
    client: FoundryClient,
    ontology: str,
    object_type: str,
    link_type: str,
    branch: typing.Optional[str],
):
    """
    Get an outgoing link for an object type.

    """
    result = client.ontologies.Ontology.ObjectType.get_outgoing_link_type(
        ontology=ontology,
        object_type=object_type,
        link_type=link_type,
        branch=branch,
    )
    click.echo(repr(result))


@ontologies_ontology_object_type.command("list")
@click.argument("ontology", type=str, required=True)
@click.option(
    "--branch",
    type=str,
    required=False,
    help="""The Foundry branch to list the object types from. If not specified, the default branch will be used.
Branches are an experimental feature and not all workflows are supported.
""",
)
@click.option(
    "--page_size",
    type=int,
    required=False,
    help="""The desired size of the page to be returned. Defaults to 500.
See [page sizes](https://palantir.com/docs/foundry/api/general/overview/paging/#page-sizes) for details.
""",
)
@click.option("--page_token", type=str, required=False, help="""""")
@click.pass_obj
def ontologies_ontology_object_type_op_list(
    client: FoundryClient,
    ontology: str,
    branch: typing.Optional[str],
    page_size: typing.Optional[int],
    page_token: typing.Optional[str],
):
    """
    Lists the object types for the given Ontology.

    Each page may be smaller or larger than the requested page size. However, it is guaranteed that if there are
    more results available, at least one result will be present in the
    response.

    """
    result = client.ontologies.Ontology.ObjectType.list(
        ontology=ontology,
        branch=branch,
        page_size=page_size,
        page_token=page_token,
    )
    click.echo(repr(result))


@ontologies_ontology_object_type.command("list_outgoing_link_types")
@click.argument("ontology", type=str, required=True)
@click.argument("object_type", type=str, required=True)
@click.option(
    "--branch",
    type=str,
    required=False,
    help="""The Foundry branch to load the outgoing link types from. If not specified, the default branch will be used.
Branches are an experimental feature and not all workflows are supported.
""",
)
@click.option(
    "--page_size", type=int, required=False, help="""The desired size of the page to be returned."""
)
@click.option("--page_token", type=str, required=False, help="""""")
@click.pass_obj
def ontologies_ontology_object_type_op_list_outgoing_link_types(
    client: FoundryClient,
    ontology: str,
    object_type: str,
    branch: typing.Optional[str],
    page_size: typing.Optional[int],
    page_token: typing.Optional[str],
):
    """
    List the outgoing links for an object type.

    """
    result = client.ontologies.Ontology.ObjectType.list_outgoing_link_types(
        ontology=ontology,
        object_type=object_type,
        branch=branch,
        page_size=page_size,
        page_token=page_token,
    )
    click.echo(repr(result))


@ontologies_ontology.group("action_type")
def ontologies_ontology_action_type():
    pass


@ontologies_ontology_action_type.command("get")
@click.argument("ontology", type=str, required=True)
@click.argument("action_type", type=str, required=True)
@click.option(
    "--branch",
    type=str,
    required=False,
    help="""The Foundry branch to load the action type definition from. If not specified, the default branch will be used.
Branches are an experimental feature and not all workflows are supported.
""",
)
@click.pass_obj
def ontologies_ontology_action_type_op_get(
    client: FoundryClient,
    ontology: str,
    action_type: str,
    branch: typing.Optional[str],
):
    """
    Gets a specific action type with the given API name.

    """
    result = client.ontologies.Ontology.ActionType.get(
        ontology=ontology,
        action_type=action_type,
        branch=branch,
    )
    click.echo(repr(result))


@ontologies_ontology_action_type.command("get_by_rid")
@click.argument("ontology", type=str, required=True)
@click.argument("action_type_rid", type=str, required=True)
@click.option(
    "--branch",
    type=str,
    required=False,
    help="""The Foundry branch to load the action type definition from. If not specified, the default branch will be used.
Branches are an experimental feature and not all workflows are supported.
""",
)
@click.pass_obj
def ontologies_ontology_action_type_op_get_by_rid(
    client: FoundryClient,
    ontology: str,
    action_type_rid: str,
    branch: typing.Optional[str],
):
    """
    Gets a specific action type with the given RID.

    """
    result = client.ontologies.Ontology.ActionType.get_by_rid(
        ontology=ontology,
        action_type_rid=action_type_rid,
        branch=branch,
    )
    click.echo(repr(result))


@ontologies_ontology_action_type.command("list")
@click.argument("ontology", type=str, required=True)
@click.option(
    "--branch",
    type=str,
    required=False,
    help="""The Foundry branch to list the action types from. If not specified, the default branch will be used.
Branches are an experimental feature and not all workflows are supported.
""",
)
@click.option(
    "--page_size",
    type=int,
    required=False,
    help="""The desired size of the page to be returned. Defaults to 500.
See [page sizes](https://palantir.com/docs/foundry/api/general/overview/paging/#page-sizes) for details.
""",
)
@click.option("--page_token", type=str, required=False, help="""""")
@click.pass_obj
def ontologies_ontology_action_type_op_list(
    client: FoundryClient,
    ontology: str,
    branch: typing.Optional[str],
    page_size: typing.Optional[int],
    page_token: typing.Optional[str],
):
    """
    Lists the action types for the given Ontology.

    Each page may be smaller than the requested page size. However, it is guaranteed that if there are more
    results available, at least one result will be present in the response.

    """
    result = client.ontologies.Ontology.ActionType.list(
        ontology=ontology,
        branch=branch,
        page_size=page_size,
        page_token=page_token,
    )
    click.echo(repr(result))


@ontologies.group("media_reference_property")
def ontologies_media_reference_property():
    pass


@ontologies_media_reference_property.command("get_media_content")
@click.argument("ontology", type=str, required=True)
@click.argument("object_type", type=str, required=True)
@click.argument("primary_key", type=str, required=True)
@click.argument("property", type=str, required=True)
@click.option(
    "--preview",
    type=bool,
    required=False,
    help="""A boolean flag that, when set to true, enables the use of beta features in preview mode.
""",
)
@click.option(
    "--sdk_package_rid",
    type=str,
    required=False,
    help="""The package rid of the generated SDK.
""",
)
@click.option(
    "--sdk_version",
    type=str,
    required=False,
    help="""The version of the generated SDK.
""",
)
@click.pass_obj
def ontologies_media_reference_property_op_get_media_content(
    client: FoundryClient,
    ontology: str,
    object_type: str,
    primary_key: str,
    property: str,
    preview: typing.Optional[bool],
    sdk_package_rid: typing.Optional[str],
    sdk_version: typing.Optional[str],
):
    """
    Gets the content of a media item referenced by this property.

    """
    result = client.ontologies.MediaReferenceProperty.get_media_content(
        ontology=ontology,
        object_type=object_type,
        primary_key=primary_key,
        property=property,
        preview=preview,
        sdk_package_rid=sdk_package_rid,
        sdk_version=sdk_version,
    )
    click.echo(result)


@ontologies_media_reference_property.command("get_media_metadata")
@click.argument("ontology", type=str, required=True)
@click.argument("object_type", type=str, required=True)
@click.argument("primary_key", type=str, required=True)
@click.argument("property", type=str, required=True)
@click.option(
    "--preview",
    type=bool,
    required=False,
    help="""A boolean flag that, when set to true, enables the use of beta features in preview mode.
""",
)
@click.option(
    "--sdk_package_rid",
    type=str,
    required=False,
    help="""The package rid of the generated SDK.
""",
)
@click.option(
    "--sdk_version",
    type=str,
    required=False,
    help="""The version of the generated SDK.
""",
)
@click.pass_obj
def ontologies_media_reference_property_op_get_media_metadata(
    client: FoundryClient,
    ontology: str,
    object_type: str,
    primary_key: str,
    property: str,
    preview: typing.Optional[bool],
    sdk_package_rid: typing.Optional[str],
    sdk_version: typing.Optional[str],
):
    """
    Gets metadata about the media item referenced by this property.

    """
    result = client.ontologies.MediaReferenceProperty.get_media_metadata(
        ontology=ontology,
        object_type=object_type,
        primary_key=primary_key,
        property=property,
        preview=preview,
        sdk_package_rid=sdk_package_rid,
        sdk_version=sdk_version,
    )
    click.echo(repr(result))


@ontologies_media_reference_property.command("upload")
@click.argument("ontology", type=str, required=True)
@click.argument("object_type", type=str, required=True)
@click.argument("property", type=str, required=True)
@click.argument("body", type=click.File("rb"), required=True)
@click.option(
    "--media_item_path",
    type=str,
    required=False,
    help="""A path for the media item within its backing media set. Required if the backing media set requires paths.
""",
)
@click.option(
    "--preview",
    type=bool,
    required=False,
    help="""A boolean flag that, when set to true, enables the use of beta features in preview mode.
""",
)
@click.pass_obj
def ontologies_media_reference_property_op_upload(
    client: FoundryClient,
    ontology: str,
    object_type: str,
    property: str,
    body: io.BufferedReader,
    media_item_path: typing.Optional[str],
    preview: typing.Optional[bool],
):
    """
    Uploads a media item to the media set which backs the specified property.  The property must be backed by a single media set and branch, otherwise an error will be thrown.
    The body of the request must contain the binary content of the file and the `Content-Type` header must be `application/octet-stream`.

    """
    result = client.ontologies.MediaReferenceProperty.upload(
        ontology=ontology,
        object_type=object_type,
        property=property,
        body=body.read(),
        media_item_path=media_item_path,
        preview=preview,
    )
    click.echo(repr(result))


@ontologies_media_reference_property.command("upload_media")
@click.argument("ontology", type=str, required=True)
@click.argument("action_type", type=str, required=True)
@click.argument("body", type=click.File("rb"), required=True)
@click.option(
    "--media_item_path",
    type=str,
    required=False,
    help="""The path to write the media item to. Required if the backing media set requires paths.
""",
)
@click.option(
    "--preview",
    type=bool,
    required=False,
    help="""A boolean flag that, when set to true, enables the use of beta features in preview mode.
""",
)
@click.pass_obj
def ontologies_media_reference_property_op_upload_media(
    client: FoundryClient,
    ontology: str,
    action_type: str,
    body: io.BufferedReader,
    media_item_path: typing.Optional[str],
    preview: typing.Optional[bool],
):
    """
    Uploads a media item for use by the specified action. If the media item isn't persisted by the associated action within 1 hour, the item will be deleted.

    The body of the request must contain the binary content of the file and the `Content-Type` header must be `application/octet-stream`.

    """
    result = client.ontologies.MediaReferenceProperty.upload_media(
        ontology=ontology,
        action_type=action_type,
        body=body.read(),
        media_item_path=media_item_path,
        preview=preview,
    )
    click.echo(repr(result))


@ontologies.group("linked_object")
def ontologies_linked_object():
    pass


@ontologies_linked_object.command("get_linked_object")
@click.argument("ontology", type=str, required=True)
@click.argument("object_type", type=str, required=True)
@click.argument("primary_key", type=str, required=True)
@click.argument("link_type", type=str, required=True)
@click.argument("linked_object_primary_key", type=str, required=True)
@click.option(
    "--branch",
    type=str,
    required=False,
    help="""The Foundry branch to load the object set for multiple object types. If not specified, the default branch is used.
Branches are an experimental feature and not all workflows are supported.
""",
)
@click.option(
    "--exclude_rid",
    type=bool,
    required=False,
    help="""A flag to exclude the retrieval of the `__rid` property. 
Setting this to true may improve performance of this endpoint for object types in OSV2.
""",
)
@click.option(
    "--sdk_package_rid",
    type=str,
    required=False,
    help="""The package rid of the generated SDK.
""",
)
@click.option(
    "--sdk_version",
    type=str,
    required=False,
    help="""The version of the generated SDK.
""",
)
@click.option(
    "--select",
    type=str,
    required=False,
    help="""The properties of the object type that should be included in the response. Omit this parameter to get all
the properties.
""",
)
@click.pass_obj
def ontologies_linked_object_op_get_linked_object(
    client: FoundryClient,
    ontology: str,
    object_type: str,
    primary_key: str,
    link_type: str,
    linked_object_primary_key: str,
    branch: typing.Optional[str],
    exclude_rid: typing.Optional[bool],
    sdk_package_rid: typing.Optional[str],
    sdk_version: typing.Optional[str],
    select: typing.Optional[str],
):
    """
    Get a specific linked object that originates from another object.

    If there is no link between the two objects, `LinkedObjectNotFound` is thrown.

    """
    result = client.ontologies.LinkedObject.get_linked_object(
        ontology=ontology,
        object_type=object_type,
        primary_key=primary_key,
        link_type=link_type,
        linked_object_primary_key=linked_object_primary_key,
        branch=branch,
        exclude_rid=exclude_rid,
        sdk_package_rid=sdk_package_rid,
        sdk_version=sdk_version,
        select=None if select is None else json.loads(select),
    )
    click.echo(repr(result))


@ontologies_linked_object.command("list_linked_objects")
@click.argument("ontology", type=str, required=True)
@click.argument("object_type", type=str, required=True)
@click.argument("primary_key", type=str, required=True)
@click.argument("link_type", type=str, required=True)
@click.option(
    "--branch",
    type=str,
    required=False,
    help="""The Foundry branch to list linked objects from. If not specified, the default branch will be used.
Branches are an experimental feature and not all workflows are supported.
""",
)
@click.option(
    "--exclude_rid",
    type=bool,
    required=False,
    help="""A flag to exclude the retrieval of the `__rid` property. 
Setting this to true may improve performance of this endpoint for object types in OSV2.
""",
)
@click.option("--order_by", type=str, required=False, help="""""")
@click.option(
    "--page_size",
    type=int,
    required=False,
    help="""The desired size of the page to be returned. Defaults to 1,000.
See [page sizes](https://palantir.com/docs/foundry/api/general/overview/paging/#page-sizes) for details.
""",
)
@click.option("--page_token", type=str, required=False, help="""""")
@click.option(
    "--sdk_package_rid",
    type=str,
    required=False,
    help="""The package rid of the generated SDK.
""",
)
@click.option(
    "--sdk_version",
    type=str,
    required=False,
    help="""The version of the generated SDK.
""",
)
@click.option(
    "--select",
    type=str,
    required=False,
    help="""The properties of the object type that should be included in the response. Omit this parameter to get all
the properties.
""",
)
@click.option(
    "--snapshot",
    type=bool,
    required=False,
    help="""A flag to use snapshot consistency when paging.
Setting this to true will give you a consistent view from before you start paging through the results, ensuring you do not get duplicate or missing items.
Setting this to false will let new results enter as you page, but you may encounter duplicate or missing items.
This defaults to false if not specified, which means you will always get the latest results.
""",
)
@click.pass_obj
def ontologies_linked_object_op_list_linked_objects(
    client: FoundryClient,
    ontology: str,
    object_type: str,
    primary_key: str,
    link_type: str,
    branch: typing.Optional[str],
    exclude_rid: typing.Optional[bool],
    order_by: typing.Optional[str],
    page_size: typing.Optional[int],
    page_token: typing.Optional[str],
    sdk_package_rid: typing.Optional[str],
    sdk_version: typing.Optional[str],
    select: typing.Optional[str],
    snapshot: typing.Optional[bool],
):
    """
    Lists the linked objects for a specific object and the given link type.

    Note that this endpoint does not guarantee consistency. Changes to the data could result in missing or
    repeated objects in the response pages.

    For Object Storage V1 backed objects, this endpoint returns a maximum of 10,000 objects. After 10,000 objects have been returned and if more objects
    are available, attempting to load another page will result in an `ObjectsExceededLimit` error being returned. There is no limit on Object Storage V2 backed objects.

    Each page may be smaller or larger than the requested page size. However, it
    is guaranteed that if there are more results available, at least one result will be present
    in the response.

    Note that null value properties will not be returned.

    """
    result = client.ontologies.LinkedObject.list_linked_objects(
        ontology=ontology,
        object_type=object_type,
        primary_key=primary_key,
        link_type=link_type,
        branch=branch,
        exclude_rid=exclude_rid,
        order_by=order_by,
        page_size=page_size,
        page_token=page_token,
        sdk_package_rid=sdk_package_rid,
        sdk_version=sdk_version,
        select=None if select is None else json.loads(select),
        snapshot=snapshot,
    )
    click.echo(repr(result))


@ontologies.group("cipher_text_property")
def ontologies_cipher_text_property():
    pass


@ontologies_cipher_text_property.command("decrypt")
@click.argument("ontology", type=str, required=True)
@click.argument("object_type", type=str, required=True)
@click.argument("primary_key", type=str, required=True)
@click.argument("property", type=str, required=True)
@click.pass_obj
def ontologies_cipher_text_property_op_decrypt(
    client: FoundryClient,
    ontology: str,
    object_type: str,
    primary_key: str,
    property: str,
):
    """
    Decrypt the value of a ciphertext property.

    """
    result = client.ontologies.CipherTextProperty.decrypt(
        ontology=ontology,
        object_type=object_type,
        primary_key=primary_key,
        property=property,
    )
    click.echo(repr(result))


@ontologies.group("attachment_property")
def ontologies_attachment_property():
    pass


@ontologies_attachment_property.command("get_attachment")
@click.argument("ontology", type=str, required=True)
@click.argument("object_type", type=str, required=True)
@click.argument("primary_key", type=str, required=True)
@click.argument("property", type=str, required=True)
@click.option(
    "--sdk_package_rid",
    type=str,
    required=False,
    help="""The package rid of the generated SDK.
""",
)
@click.option(
    "--sdk_version",
    type=str,
    required=False,
    help="""The version of the generated SDK.
""",
)
@click.pass_obj
def ontologies_attachment_property_op_get_attachment(
    client: FoundryClient,
    ontology: str,
    object_type: str,
    primary_key: str,
    property: str,
    sdk_package_rid: typing.Optional[str],
    sdk_version: typing.Optional[str],
):
    """
    Get the metadata of attachments parented to the given object.

    """
    result = client.ontologies.AttachmentProperty.get_attachment(
        ontology=ontology,
        object_type=object_type,
        primary_key=primary_key,
        property=property,
        sdk_package_rid=sdk_package_rid,
        sdk_version=sdk_version,
    )
    click.echo(repr(result))


@ontologies_attachment_property.command("get_attachment_by_rid")
@click.argument("ontology", type=str, required=True)
@click.argument("object_type", type=str, required=True)
@click.argument("primary_key", type=str, required=True)
@click.argument("property", type=str, required=True)
@click.argument("attachment_rid", type=str, required=True)
@click.option(
    "--sdk_package_rid",
    type=str,
    required=False,
    help="""The package rid of the generated SDK.
""",
)
@click.option(
    "--sdk_version",
    type=str,
    required=False,
    help="""The version of the generated SDK.
""",
)
@click.pass_obj
def ontologies_attachment_property_op_get_attachment_by_rid(
    client: FoundryClient,
    ontology: str,
    object_type: str,
    primary_key: str,
    property: str,
    attachment_rid: str,
    sdk_package_rid: typing.Optional[str],
    sdk_version: typing.Optional[str],
):
    """
    Get the metadata of a particular attachment in an attachment list.

    """
    result = client.ontologies.AttachmentProperty.get_attachment_by_rid(
        ontology=ontology,
        object_type=object_type,
        primary_key=primary_key,
        property=property,
        attachment_rid=attachment_rid,
        sdk_package_rid=sdk_package_rid,
        sdk_version=sdk_version,
    )
    click.echo(repr(result))


@ontologies_attachment_property.command("read_attachment")
@click.argument("ontology", type=str, required=True)
@click.argument("object_type", type=str, required=True)
@click.argument("primary_key", type=str, required=True)
@click.argument("property", type=str, required=True)
@click.option(
    "--sdk_package_rid",
    type=str,
    required=False,
    help="""The package rid of the generated SDK.
""",
)
@click.option(
    "--sdk_version",
    type=str,
    required=False,
    help="""The version of the generated SDK.
""",
)
@click.pass_obj
def ontologies_attachment_property_op_read_attachment(
    client: FoundryClient,
    ontology: str,
    object_type: str,
    primary_key: str,
    property: str,
    sdk_package_rid: typing.Optional[str],
    sdk_version: typing.Optional[str],
):
    """
    Get the content of an attachment.

    """
    result = client.ontologies.AttachmentProperty.read_attachment(
        ontology=ontology,
        object_type=object_type,
        primary_key=primary_key,
        property=property,
        sdk_package_rid=sdk_package_rid,
        sdk_version=sdk_version,
    )
    click.echo(result)


@ontologies_attachment_property.command("read_attachment_by_rid")
@click.argument("ontology", type=str, required=True)
@click.argument("object_type", type=str, required=True)
@click.argument("primary_key", type=str, required=True)
@click.argument("property", type=str, required=True)
@click.argument("attachment_rid", type=str, required=True)
@click.option(
    "--sdk_package_rid",
    type=str,
    required=False,
    help="""The package rid of the generated SDK.
""",
)
@click.option(
    "--sdk_version",
    type=str,
    required=False,
    help="""The version of the generated SDK.
""",
)
@click.pass_obj
def ontologies_attachment_property_op_read_attachment_by_rid(
    client: FoundryClient,
    ontology: str,
    object_type: str,
    primary_key: str,
    property: str,
    attachment_rid: str,
    sdk_package_rid: typing.Optional[str],
    sdk_version: typing.Optional[str],
):
    """
    Get the content of an attachment by its RID.

    The RID must exist in the attachment array of the property.

    """
    result = client.ontologies.AttachmentProperty.read_attachment_by_rid(
        ontology=ontology,
        object_type=object_type,
        primary_key=primary_key,
        property=property,
        attachment_rid=attachment_rid,
        sdk_package_rid=sdk_package_rid,
        sdk_version=sdk_version,
    )
    click.echo(result)


@ontologies.group("attachment")
def ontologies_attachment():
    pass


@ontologies_attachment.command("get")
@click.argument("attachment_rid", type=str, required=True)
@click.pass_obj
def ontologies_attachment_op_get(
    client: FoundryClient,
    attachment_rid: str,
):
    """
    Get the metadata of an attachment.

    """
    result = client.ontologies.Attachment.get(
        attachment_rid=attachment_rid,
    )
    click.echo(repr(result))


@ontologies_attachment.command("read")
@click.argument("attachment_rid", type=str, required=True)
@click.pass_obj
def ontologies_attachment_op_read(
    client: FoundryClient,
    attachment_rid: str,
):
    """
    Get the content of an attachment.

    """
    result = client.ontologies.Attachment.read(
        attachment_rid=attachment_rid,
    )
    click.echo(result)


@ontologies_attachment.command("upload")
@click.argument("body", type=click.File("rb"), required=True)
@click.option(
    "--content_length",
    type=int,
    required=True,
    help="""The size in bytes of the file content being uploaded.""",
)
@click.option(
    "--content_type", type=str, required=True, help="""The media type of the file being uploaded."""
)
@click.option(
    "--filename", type=str, required=True, help="""The name of the file being uploaded."""
)
@click.pass_obj
def ontologies_attachment_op_upload(
    client: FoundryClient,
    body: io.BufferedReader,
    content_length: int,
    content_type: str,
    filename: str,
):
    """
    Upload an attachment to use in an action. Any attachment which has not been linked to an object via
    an action within one hour after upload will be removed.
    Previously mapped attachments which are not connected to any object anymore are also removed on
    a biweekly basis.
    The body of the request must contain the binary content of the file and the `Content-Type` header must be `application/octet-stream`.

    """
    result = client.ontologies.Attachment.upload(
        body=body.read(),
        content_length=content_length,
        content_type=content_type,
        filename=filename,
    )
    click.echo(repr(result))


@ontologies.group("action_type_full_metadata")
def ontologies_action_type_full_metadata():
    pass


@ontologies_action_type_full_metadata.command("get")
@click.argument("ontology", type=str, required=True)
@click.argument("action_type", type=str, required=True)
@click.option(
    "--branch",
    type=str,
    required=False,
    help="""The Foundry branch to load the action type definition from. If not specified, the default branch will be used.
""",
)
@click.pass_obj
def ontologies_action_type_full_metadata_op_get(
    client: FoundryClient,
    ontology: str,
    action_type: str,
    branch: typing.Optional[str],
):
    """
    Gets the full metadata associated with an action type.

    """
    result = client.ontologies.ActionTypeFullMetadata.get(
        ontology=ontology,
        action_type=action_type,
        branch=branch,
    )
    click.echo(repr(result))


@ontologies.group("action")
def ontologies_action():
    pass


@ontologies_action.command("apply")
@click.argument("ontology", type=str, required=True)
@click.argument("action", type=str, required=True)
@click.option("--parameters", type=str, required=True, help="""""")
@click.option(
    "--branch",
    type=str,
    required=False,
    help="""The Foundry branch to apply the action against. If not specified, the default branch is used.
Branches are an experimental feature and not all workflows are supported.
""",
)
@click.option("--options", type=str, required=False, help="""""")
@click.option(
    "--sdk_package_rid",
    type=str,
    required=False,
    help="""The package rid of the generated SDK.
""",
)
@click.option(
    "--sdk_version",
    type=str,
    required=False,
    help="""The version of the generated SDK.
""",
)
@click.pass_obj
def ontologies_action_op_apply(
    client: FoundryClient,
    ontology: str,
    action: str,
    parameters: str,
    branch: typing.Optional[str],
    options: typing.Optional[str],
    sdk_package_rid: typing.Optional[str],
    sdk_version: typing.Optional[str],
):
    """
    Applies an action using the given parameters.

    Changes to objects or links stored in Object Storage V1 are eventually consistent and may take some time to be visible.
    Edits to objects or links in Object Storage V2 will be visible immediately after the action completes.

    Note that a 200 HTTP status code only indicates that the request was received and processed by the server.
    See the validation result in the response body to determine if the action was applied successfully.

    Note that [parameter default values](https://palantir.com/docs/foundry/action-types/parameters-default-value/) are not currently supported by
    this endpoint.

    """
    result = client.ontologies.Action.apply(
        ontology=ontology,
        action=action,
        parameters=json.loads(parameters),
        branch=branch,
        options=None if options is None else json.loads(options),
        sdk_package_rid=sdk_package_rid,
        sdk_version=sdk_version,
    )
    click.echo(repr(result))


@ontologies_action.command("apply_batch")
@click.argument("ontology", type=str, required=True)
@click.argument("action", type=str, required=True)
@click.option("--requests", type=str, required=True, help="""""")
@click.option(
    "--branch",
    type=str,
    required=False,
    help="""The Foundry branch to apply the action against. If not specified, the default branch is used.
Branches are an experimental feature and not all workflows are supported.
""",
)
@click.option("--options", type=str, required=False, help="""""")
@click.option(
    "--sdk_package_rid",
    type=str,
    required=False,
    help="""The package rid of the generated SDK.
""",
)
@click.option(
    "--sdk_version",
    type=str,
    required=False,
    help="""The version of the generated SDK.
""",
)
@click.pass_obj
def ontologies_action_op_apply_batch(
    client: FoundryClient,
    ontology: str,
    action: str,
    requests: str,
    branch: typing.Optional[str],
    options: typing.Optional[str],
    sdk_package_rid: typing.Optional[str],
    sdk_version: typing.Optional[str],
):
    """
    Applies multiple actions (of the same Action Type) using the given parameters.

    Changes to objects or links stored in Object Storage V1 are eventually consistent and may take some time to be visible.
    Edits to objects or links in Object Storage V2 will be visible immediately after the action completes.

    Up to 20 actions may be applied in one call. Actions that only modify objects in Object Storage v2 and do not
    call Functions may receive a higher limit.

    Note that [notifications](https://palantir.com/docs/foundry/action-types/notifications/) are not currently supported by this endpoint.

    """
    result = client.ontologies.Action.apply_batch(
        ontology=ontology,
        action=action,
        requests=json.loads(requests),
        branch=branch,
        options=None if options is None else json.loads(options),
        sdk_package_rid=sdk_package_rid,
        sdk_version=sdk_version,
    )
    click.echo(repr(result))


@cli.group("orchestration")
def orchestration():
    pass


@orchestration.group("schedule_version")
def orchestration_schedule_version():
    pass


@orchestration_schedule_version.command("get")
@click.argument("schedule_version_rid", type=str, required=True)
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.pass_obj
def orchestration_schedule_version_op_get(
    client: FoundryClient,
    schedule_version_rid: str,
    preview: typing.Optional[bool],
):
    """
    Get the ScheduleVersion with the specified rid.
    """
    result = client.orchestration.ScheduleVersion.get(
        schedule_version_rid=schedule_version_rid,
        preview=preview,
    )
    click.echo(repr(result))


@orchestration_schedule_version.command("schedule")
@click.argument("schedule_version_rid", type=str, required=True)
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.pass_obj
def orchestration_schedule_version_op_schedule(
    client: FoundryClient,
    schedule_version_rid: str,
    preview: typing.Optional[bool],
):
    """ """
    result = client.orchestration.ScheduleVersion.schedule(
        schedule_version_rid=schedule_version_rid,
        preview=preview,
    )
    click.echo(repr(result))


@orchestration.group("schedule_run")
def orchestration_schedule_run():
    pass


@orchestration.group("schedule")
def orchestration_schedule():
    pass


@orchestration_schedule.command("create")
@click.option("--action", type=str, required=True, help="""""")
@click.option("--description", type=str, required=False, help="""""")
@click.option("--display_name", type=str, required=False, help="""""")
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.option("--scope_mode", type=str, required=False, help="""""")
@click.option(
    "--trigger",
    type=str,
    required=False,
    help="""The schedule trigger. If the requesting user does not have
permission to see the trigger, this will be empty.
""",
)
@click.pass_obj
def orchestration_schedule_op_create(
    client: FoundryClient,
    action: str,
    description: typing.Optional[str],
    display_name: typing.Optional[str],
    preview: typing.Optional[bool],
    scope_mode: typing.Optional[str],
    trigger: typing.Optional[str],
):
    """
    Creates a new Schedule.
    """
    result = client.orchestration.Schedule.create(
        action=json.loads(action),
        description=description,
        display_name=display_name,
        preview=preview,
        scope_mode=None if scope_mode is None else json.loads(scope_mode),
        trigger=None if trigger is None else json.loads(trigger),
    )
    click.echo(repr(result))


@orchestration_schedule.command("delete")
@click.argument("schedule_rid", type=str, required=True)
@click.pass_obj
def orchestration_schedule_op_delete(
    client: FoundryClient,
    schedule_rid: str,
):
    """
    Delete the Schedule with the specified rid.
    """
    result = client.orchestration.Schedule.delete(
        schedule_rid=schedule_rid,
    )
    click.echo(repr(result))


@orchestration_schedule.command("get")
@click.argument("schedule_rid", type=str, required=True)
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.pass_obj
def orchestration_schedule_op_get(
    client: FoundryClient,
    schedule_rid: str,
    preview: typing.Optional[bool],
):
    """
    Get the Schedule with the specified rid.
    """
    result = client.orchestration.Schedule.get(
        schedule_rid=schedule_rid,
        preview=preview,
    )
    click.echo(repr(result))


@orchestration_schedule.command("get_affected_resources")
@click.argument("schedule_rid", type=str, required=True)
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.pass_obj
def orchestration_schedule_op_get_affected_resources(
    client: FoundryClient,
    schedule_rid: str,
    preview: typing.Optional[bool],
):
    """ """
    result = client.orchestration.Schedule.get_affected_resources(
        schedule_rid=schedule_rid,
        preview=preview,
    )
    click.echo(repr(result))


@orchestration_schedule.command("get_batch")
@click.argument("body", type=str, required=True)
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.pass_obj
def orchestration_schedule_op_get_batch(
    client: FoundryClient,
    body: str,
    preview: typing.Optional[bool],
):
    """
    Fetch multiple schedules in a single request. Schedules not found or inaccessible to the user will be
    omitted from the response.


    The maximum batch size for this endpoint is 1000.
    """
    result = client.orchestration.Schedule.get_batch(
        body=json.loads(body),
        preview=preview,
    )
    click.echo(repr(result))


@orchestration_schedule.command("pause")
@click.argument("schedule_rid", type=str, required=True)
@click.pass_obj
def orchestration_schedule_op_pause(
    client: FoundryClient,
    schedule_rid: str,
):
    """ """
    result = client.orchestration.Schedule.pause(
        schedule_rid=schedule_rid,
    )
    click.echo(repr(result))


@orchestration_schedule.command("replace")
@click.argument("schedule_rid", type=str, required=True)
@click.option("--action", type=str, required=True, help="""""")
@click.option("--description", type=str, required=False, help="""""")
@click.option("--display_name", type=str, required=False, help="""""")
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.option("--scope_mode", type=str, required=False, help="""""")
@click.option(
    "--trigger",
    type=str,
    required=False,
    help="""The schedule trigger. If the requesting user does not have
permission to see the trigger, this will be empty.
""",
)
@click.pass_obj
def orchestration_schedule_op_replace(
    client: FoundryClient,
    schedule_rid: str,
    action: str,
    description: typing.Optional[str],
    display_name: typing.Optional[str],
    preview: typing.Optional[bool],
    scope_mode: typing.Optional[str],
    trigger: typing.Optional[str],
):
    """
    Replace the Schedule with the specified rid.
    """
    result = client.orchestration.Schedule.replace(
        schedule_rid=schedule_rid,
        action=json.loads(action),
        description=description,
        display_name=display_name,
        preview=preview,
        scope_mode=None if scope_mode is None else json.loads(scope_mode),
        trigger=None if trigger is None else json.loads(trigger),
    )
    click.echo(repr(result))


@orchestration_schedule.command("run")
@click.argument("schedule_rid", type=str, required=True)
@click.pass_obj
def orchestration_schedule_op_run(
    client: FoundryClient,
    schedule_rid: str,
):
    """ """
    result = client.orchestration.Schedule.run(
        schedule_rid=schedule_rid,
    )
    click.echo(repr(result))


@orchestration_schedule.command("runs")
@click.argument("schedule_rid", type=str, required=True)
@click.option(
    "--page_size", type=int, required=False, help="""The page size to use for the endpoint."""
)
@click.option(
    "--page_token",
    type=str,
    required=False,
    help="""The page token indicates where to start paging. This should be omitted from the first page's request.
To fetch the next page, clients should take the value from the `nextPageToken` field of the previous response
and use it to populate the `pageToken` field of the next request.""",
)
@click.pass_obj
def orchestration_schedule_op_runs(
    client: FoundryClient,
    schedule_rid: str,
    page_size: typing.Optional[int],
    page_token: typing.Optional[str],
):
    """
    Get the most recent runs of a Schedule. If no page size is provided, a page size of 100 will be used.

    """
    result = client.orchestration.Schedule.runs(
        schedule_rid=schedule_rid,
        page_size=page_size,
        page_token=page_token,
    )
    click.echo(repr(result))


@orchestration_schedule.command("unpause")
@click.argument("schedule_rid", type=str, required=True)
@click.pass_obj
def orchestration_schedule_op_unpause(
    client: FoundryClient,
    schedule_rid: str,
):
    """ """
    result = client.orchestration.Schedule.unpause(
        schedule_rid=schedule_rid,
    )
    click.echo(repr(result))


@orchestration.group("job")
def orchestration_job():
    pass


@orchestration_job.command("get")
@click.argument("job_rid", type=str, required=True)
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.pass_obj
def orchestration_job_op_get(
    client: FoundryClient,
    job_rid: str,
    preview: typing.Optional[bool],
):
    """
    Get the Job with the specified rid.
    """
    result = client.orchestration.Job.get(
        job_rid=job_rid,
        preview=preview,
    )
    click.echo(repr(result))


@orchestration_job.command("get_batch")
@click.argument("body", type=str, required=True)
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.pass_obj
def orchestration_job_op_get_batch(
    client: FoundryClient,
    body: str,
    preview: typing.Optional[bool],
):
    """
    Execute multiple get requests on Job.

    The maximum batch size for this endpoint is 500.
    """
    result = client.orchestration.Job.get_batch(
        body=json.loads(body),
        preview=preview,
    )
    click.echo(repr(result))


@orchestration.group("build")
def orchestration_build():
    pass


@orchestration_build.command("cancel")
@click.argument("build_rid", type=str, required=True)
@click.pass_obj
def orchestration_build_op_cancel(
    client: FoundryClient,
    build_rid: str,
):
    """
    Request a cancellation for all unfinished jobs in a build. The build's status will not update immediately. This endpoint is asynchronous and a success response indicates that the cancellation request has been acknowledged and the build is expected to be canceled soon. If the build has already finished or finishes shortly after the request and before the cancellation, the build will not change.

    """
    result = client.orchestration.Build.cancel(
        build_rid=build_rid,
    )
    click.echo(repr(result))


@orchestration_build.command("create")
@click.option("--fallback_branches", type=str, required=True, help="""""")
@click.option("--target", type=str, required=True, help="""The targets of the schedule.""")
@click.option("--abort_on_failure", type=bool, required=False, help="""""")
@click.option(
    "--branch_name", type=str, required=False, help="""The target branch the build should run on."""
)
@click.option("--force_build", type=bool, required=False, help="""""")
@click.option("--notifications_enabled", type=bool, required=False, help="""""")
@click.option("--retry_backoff_duration", type=str, required=False, help="""""")
@click.option(
    "--retry_count",
    type=int,
    required=False,
    help="""The number of retry attempts for failed jobs.""",
)
@click.pass_obj
def orchestration_build_op_create(
    client: FoundryClient,
    fallback_branches: str,
    target: str,
    abort_on_failure: typing.Optional[bool],
    branch_name: typing.Optional[str],
    force_build: typing.Optional[bool],
    notifications_enabled: typing.Optional[bool],
    retry_backoff_duration: typing.Optional[str],
    retry_count: typing.Optional[int],
):
    """ """
    result = client.orchestration.Build.create(
        fallback_branches=json.loads(fallback_branches),
        target=json.loads(target),
        abort_on_failure=abort_on_failure,
        branch_name=branch_name,
        force_build=force_build,
        notifications_enabled=notifications_enabled,
        retry_backoff_duration=(
            None if retry_backoff_duration is None else json.loads(retry_backoff_duration)
        ),
        retry_count=retry_count,
    )
    click.echo(repr(result))


@orchestration_build.command("get")
@click.argument("build_rid", type=str, required=True)
@click.pass_obj
def orchestration_build_op_get(
    client: FoundryClient,
    build_rid: str,
):
    """
    Get the Build with the specified rid.
    """
    result = client.orchestration.Build.get(
        build_rid=build_rid,
    )
    click.echo(repr(result))


@orchestration_build.command("get_batch")
@click.argument("body", type=str, required=True)
@click.pass_obj
def orchestration_build_op_get_batch(
    client: FoundryClient,
    body: str,
):
    """
    Execute multiple get requests on Build.

    The maximum batch size for this endpoint is 100.
    """
    result = client.orchestration.Build.get_batch(
        body=json.loads(body),
    )
    click.echo(repr(result))


@orchestration_build.command("jobs")
@click.argument("build_rid", type=str, required=True)
@click.option(
    "--page_size", type=int, required=False, help="""The page size to use for the endpoint."""
)
@click.option(
    "--page_token",
    type=str,
    required=False,
    help="""The page token indicates where to start paging. This should be omitted from the first page's request.
To fetch the next page, clients should take the value from the `nextPageToken` field of the previous response
and use it to populate the `pageToken` field of the next request.""",
)
@click.pass_obj
def orchestration_build_op_jobs(
    client: FoundryClient,
    build_rid: str,
    page_size: typing.Optional[int],
    page_token: typing.Optional[str],
):
    """
    Get the Jobs in the Build.
    """
    result = client.orchestration.Build.jobs(
        build_rid=build_rid,
        page_size=page_size,
        page_token=page_token,
    )
    click.echo(repr(result))


@orchestration_build.command("search")
@click.option("--where", type=str, required=True, help="""""")
@click.option("--order_by", type=str, required=False, help="""""")
@click.option(
    "--page_size",
    type=int,
    required=False,
    help="""The page size for the search request. If no value is provided, a default of `100` will be used.
""",
)
@click.option("--page_token", type=str, required=False, help="""""")
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.pass_obj
def orchestration_build_op_search(
    client: FoundryClient,
    where: str,
    order_by: typing.Optional[str],
    page_size: typing.Optional[int],
    page_token: typing.Optional[str],
    preview: typing.Optional[bool],
):
    """
    Search for Builds.
    """
    result = client.orchestration.Build.search(
        where=json.loads(where),
        order_by=None if order_by is None else json.loads(order_by),
        page_size=page_size,
        page_token=page_token,
        preview=preview,
    )
    click.echo(repr(result))


@cli.group("sql_queries")
def sql_queries():
    pass


@sql_queries.group("sql_query")
def sql_queries_sql_query():
    pass


@sql_queries_sql_query.command("cancel")
@click.argument("sql_query_id", type=str, required=True)
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.pass_obj
def sql_queries_sql_query_op_cancel(
    client: FoundryClient,
    sql_query_id: str,
    preview: typing.Optional[bool],
):
    """
    Cancels a query. If the query is no longer running this is effectively a no-op.

    """
    result = client.sql_queries.SqlQuery.cancel(
        sql_query_id=sql_query_id,
        preview=preview,
    )
    click.echo(repr(result))


@sql_queries_sql_query.command("execute")
@click.option(
    "--query",
    type=str,
    required=True,
    help="""The SQL query to execute. Queries should conform to the
[Spark SQL dialect](https://spark.apache.org/docs/latest/sql-ref.html). This supports SELECT
queries only. Datasets can be referenced in SQL queries by path or by RID. See the 
[documentation](https://www.palantir.com/docs/foundry/analytics-connectivity/odbc-jdbc-drivers/#use-sql-to-query-foundry-datasets)
for more details.
""",
)
@click.option(
    "--fallback_branch_ids",
    type=str,
    required=False,
    help="""The list of branch ids to use as fallbacks if the query fails to execute on the primary branch. If a
is not explicitly provided in the SQL query, the resource will be queried on the first fallback branch
provided that exists. If no fallback branches are provided the default branch is used. This is
`master` for most enrollments.
""",
)
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.pass_obj
def sql_queries_sql_query_op_execute(
    client: FoundryClient,
    query: str,
    fallback_branch_ids: typing.Optional[str],
    preview: typing.Optional[bool],
):
    """
    Executes a new query. Only the user that invoked the query can operate on the query. The size of query
    results are limited by default to 1 million rows. Contact your Palantir representative to discuss limit
    increases.

    """
    result = client.sql_queries.SqlQuery.execute(
        query=query,
        fallback_branch_ids=(
            None if fallback_branch_ids is None else json.loads(fallback_branch_ids)
        ),
        preview=preview,
    )
    click.echo(repr(result))


@sql_queries_sql_query.command("get_results")
@click.argument("sql_query_id", type=str, required=True)
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.pass_obj
def sql_queries_sql_query_op_get_results(
    client: FoundryClient,
    sql_query_id: str,
    preview: typing.Optional[bool],
):
    """
    Gets the results of a query. The results of the query are returned in the
    [Apache Arrow](https://arrow.apache.org/) format.

    This endpoint implements long polling and requests will time out after one minute. They can be safely
    retried while the query is still running.

    """
    result = client.sql_queries.SqlQuery.get_results(
        sql_query_id=sql_query_id,
        preview=preview,
    )
    click.echo(result)


@sql_queries_sql_query.command("get_status")
@click.argument("sql_query_id", type=str, required=True)
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.pass_obj
def sql_queries_sql_query_op_get_status(
    client: FoundryClient,
    sql_query_id: str,
    preview: typing.Optional[bool],
):
    """
    Gets the status of a query.

    """
    result = client.sql_queries.SqlQuery.get_status(
        sql_query_id=sql_query_id,
        preview=preview,
    )
    click.echo(repr(result))


@cli.group("streams")
def streams():
    pass


@streams.group("dataset")
def streams_dataset():
    pass


@streams_dataset.command("create")
@click.option("--name", type=str, required=True, help="""""")
@click.option("--parent_folder_rid", type=str, required=True, help="""""")
@click.option(
    "--schema",
    type=str,
    required=True,
    help="""The Foundry schema to apply to the new stream.
""",
)
@click.option(
    "--branch_name",
    type=str,
    required=False,
    help="""The branch to create the initial stream on. If not specified, the default branch will be used
('master' for most enrollments).
""",
)
@click.option(
    "--compressed",
    type=bool,
    required=False,
    help="""Whether or not compression is enabled for the stream. Defaults to false.
""",
)
@click.option(
    "--partitions_count",
    type=int,
    required=False,
    help="""The number of partitions for the Foundry stream.

Generally, each partition can handle about 5 mb/s of data, so for higher volume streams, more partitions
are recommended.

If not specified, 1 partition is used.

This value cannot be changed later.
""",
)
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.option(
    "--stream_type",
    type=click.Choice(["LOW_LATENCY", "HIGH_THROUGHPUT"]),
    required=False,
    help="""A conceptual representation of the expected shape of the data for a stream. HIGH_THROUGHPUT and
LOW_LATENCY are not compatible with each other. Defaults to LOW_LATENCY.
""",
)
@click.pass_obj
def streams_dataset_op_create(
    client: FoundryClient,
    name: str,
    parent_folder_rid: str,
    schema: str,
    branch_name: typing.Optional[str],
    compressed: typing.Optional[bool],
    partitions_count: typing.Optional[int],
    preview: typing.Optional[bool],
    stream_type: typing.Optional[typing.Literal["LOW_LATENCY", "HIGH_THROUGHPUT"]],
):
    """
    Creates a streaming dataset with a stream on the specified branch, or if no branch is specified, on the
    default branch ('master' for most enrollments). For more information on streaming datasets, refer to the
    [streams](https://palantir.com/docs/foundry/data-integration/streams/) user documentation.

    """
    result = client.streams.Dataset.create(
        name=name,
        parent_folder_rid=parent_folder_rid,
        schema=json.loads(schema),
        branch_name=branch_name,
        compressed=compressed,
        partitions_count=partitions_count,
        preview=preview,
        stream_type=stream_type,
    )
    click.echo(repr(result))


@streams_dataset.group("stream")
def streams_dataset_stream():
    pass


@streams_dataset_stream.command("create")
@click.argument("dataset_rid", type=str, required=True)
@click.option("--branch_name", type=str, required=True, help="""""")
@click.option("--schema", type=str, required=True, help="""The Foundry schema for this stream.""")
@click.option(
    "--compressed",
    type=bool,
    required=False,
    help="""Whether or not compression is enabled for the stream. Defaults to false.
""",
)
@click.option(
    "--partitions_count",
    type=int,
    required=False,
    help="""The number of partitions for the Foundry stream. Defaults to 1.

Generally, each partition can handle about 5 mb/s of data, so for higher volume streams, more partitions
are recommended.
""",
)
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.option(
    "--stream_type",
    type=click.Choice(["LOW_LATENCY", "HIGH_THROUGHPUT"]),
    required=False,
    help="""A conceptual representation of the expected shape of the data for a stream. HIGH_THROUGHPUT and
LOW_LATENCY are not compatible with each other. Defaults to LOW_LATENCY.
""",
)
@click.pass_obj
def streams_dataset_stream_op_create(
    client: FoundryClient,
    dataset_rid: str,
    branch_name: str,
    schema: str,
    compressed: typing.Optional[bool],
    partitions_count: typing.Optional[int],
    preview: typing.Optional[bool],
    stream_type: typing.Optional[typing.Literal["LOW_LATENCY", "HIGH_THROUGHPUT"]],
):
    """
    Creates a new branch on the backing streaming dataset, and creates a new stream on that branch.

    """
    result = client.streams.Dataset.Stream.create(
        dataset_rid=dataset_rid,
        branch_name=branch_name,
        schema=json.loads(schema),
        compressed=compressed,
        partitions_count=partitions_count,
        preview=preview,
        stream_type=stream_type,
    )
    click.echo(repr(result))


@streams_dataset_stream.command("get")
@click.argument("dataset_rid", type=str, required=True)
@click.argument("stream_branch_name", type=str, required=True)
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.pass_obj
def streams_dataset_stream_op_get(
    client: FoundryClient,
    dataset_rid: str,
    stream_branch_name: str,
    preview: typing.Optional[bool],
):
    """
    Get a stream by its branch name. If the branch does not exist, there is no stream on that branch, or the
    user does not have permission to access the stream, a 404 error will be returned.

    """
    result = client.streams.Dataset.Stream.get(
        dataset_rid=dataset_rid,
        stream_branch_name=stream_branch_name,
        preview=preview,
    )
    click.echo(repr(result))


@streams_dataset_stream.command("publish_binary_record")
@click.argument("dataset_rid", type=str, required=True)
@click.argument("stream_branch_name", type=str, required=True)
@click.argument("body", type=click.File("rb"), required=True)
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.option(
    "--view_rid",
    type=str,
    required=False,
    help="""If provided, this operation will only write to the stream corresponding to the specified view rid. If
not provided, this operation will write to the latest stream on the branch.

Providing this value is an advanced configuration, to be used when additional control over the
underlying streaming data structures is needed.
""",
)
@click.pass_obj
def streams_dataset_stream_op_publish_binary_record(
    client: FoundryClient,
    dataset_rid: str,
    stream_branch_name: str,
    body: io.BufferedReader,
    preview: typing.Optional[bool],
    view_rid: typing.Optional[str],
):
    """
    Publish a single binary record to the stream. The stream's schema must be a single binary field.

    """
    result = client.streams.Dataset.Stream.publish_binary_record(
        dataset_rid=dataset_rid,
        stream_branch_name=stream_branch_name,
        body=body.read(),
        preview=preview,
        view_rid=view_rid,
    )
    click.echo(repr(result))


@streams_dataset_stream.command("publish_record")
@click.argument("dataset_rid", type=str, required=True)
@click.argument("stream_branch_name", type=str, required=True)
@click.option(
    "--record",
    type=str,
    required=True,
    help="""The record to publish to the stream
""",
)
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.option(
    "--view_rid",
    type=str,
    required=False,
    help="""If provided, this endpoint will only write to the stream corresponding to the specified view rid. If
not provided, this endpoint will write the latest stream on the branch.

Providing this value is an advanced configuration, to be used when additional control over the
underlying streaming data structures is needed.
""",
)
@click.pass_obj
def streams_dataset_stream_op_publish_record(
    client: FoundryClient,
    dataset_rid: str,
    stream_branch_name: str,
    record: str,
    preview: typing.Optional[bool],
    view_rid: typing.Optional[str],
):
    """
    Publish a single record to the stream. The record will be validated against the stream's schema, and
    rejected if it is invalid.

    """
    result = client.streams.Dataset.Stream.publish_record(
        dataset_rid=dataset_rid,
        stream_branch_name=stream_branch_name,
        record=json.loads(record),
        preview=preview,
        view_rid=view_rid,
    )
    click.echo(repr(result))


@streams_dataset_stream.command("publish_records")
@click.argument("dataset_rid", type=str, required=True)
@click.argument("stream_branch_name", type=str, required=True)
@click.option(
    "--records",
    type=str,
    required=True,
    help="""The records to publish to the stream
""",
)
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.option(
    "--view_rid",
    type=str,
    required=False,
    help="""If provided, this endpoint will only write to the stream corresponding to the specified view rid. If
not provided, this endpoint will write to the latest stream on the branch.

Providing this value is an advanced configuration, to be used when additional control over the
underlying streaming data structures is needed.
""",
)
@click.pass_obj
def streams_dataset_stream_op_publish_records(
    client: FoundryClient,
    dataset_rid: str,
    stream_branch_name: str,
    records: str,
    preview: typing.Optional[bool],
    view_rid: typing.Optional[str],
):
    """
    Publish a batch of records to the stream. The records will be validated against the stream's schema, and
    the batch will be rejected if one or more of the records are invalid.

    """
    result = client.streams.Dataset.Stream.publish_records(
        dataset_rid=dataset_rid,
        stream_branch_name=stream_branch_name,
        records=json.loads(records),
        preview=preview,
        view_rid=view_rid,
    )
    click.echo(repr(result))


@streams_dataset_stream.command("reset")
@click.argument("dataset_rid", type=str, required=True)
@click.argument("stream_branch_name", type=str, required=True)
@click.option(
    "--compressed",
    type=bool,
    required=False,
    help="""Whether or not compression is enabled for the stream.

If omitted, the compression setting of the existing stream on the branch will be used.
""",
)
@click.option(
    "--partitions_count",
    type=int,
    required=False,
    help="""The number of partitions for the Foundry stream.
Generally, each partition can handle about 5 mb/s of data, so for higher volume streams, more partitions
are recommended.

If omitted, the partitions count of the existing stream on the branch will be used.
""",
)
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.option(
    "--schema",
    type=str,
    required=False,
    help="""The Foundry schema to apply to the new stream. 

If omitted, the schema of the existing stream on the branch will be used.
""",
)
@click.option(
    "--stream_type",
    type=click.Choice(["LOW_LATENCY", "HIGH_THROUGHPUT"]),
    required=False,
    help="""A conceptual representation of the expected shape of the data for a stream. HIGH_THROUGHPUT and
LOW_LATENCY are not compatible with each other. Defaults to LOW_LATENCY.

If omitted, the stream type of the existing stream on the branch will be used.
""",
)
@click.pass_obj
def streams_dataset_stream_op_reset(
    client: FoundryClient,
    dataset_rid: str,
    stream_branch_name: str,
    compressed: typing.Optional[bool],
    partitions_count: typing.Optional[int],
    preview: typing.Optional[bool],
    schema: typing.Optional[str],
    stream_type: typing.Optional[typing.Literal["LOW_LATENCY", "HIGH_THROUGHPUT"]],
):
    """
    Reset the stream on the given dataset branch, clearing the existing records and allowing new configurations
    to be applied.

    To change the stream settings without clearing the records, update the stream settings in-platform.

    This will create a new stream view (as seen by the change of the `viewRid` on the branch),
    which will be the new stream view that will be written to for the branch.

    """
    result = client.streams.Dataset.Stream.reset(
        dataset_rid=dataset_rid,
        stream_branch_name=stream_branch_name,
        compressed=compressed,
        partitions_count=partitions_count,
        preview=preview,
        schema=None if schema is None else json.loads(schema),
        stream_type=stream_type,
    )
    click.echo(repr(result))


@cli.group("third_party_applications")
def third_party_applications():
    pass


@third_party_applications.group("third_party_application")
def third_party_applications_third_party_application():
    pass


@third_party_applications_third_party_application.command("get")
@click.argument("third_party_application_rid", type=str, required=True)
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.pass_obj
def third_party_applications_third_party_application_op_get(
    client: FoundryClient,
    third_party_application_rid: str,
    preview: typing.Optional[bool],
):
    """
    Get the ThirdPartyApplication with the specified rid.
    """
    result = client.third_party_applications.ThirdPartyApplication.get(
        third_party_application_rid=third_party_application_rid,
        preview=preview,
    )
    click.echo(repr(result))


@third_party_applications_third_party_application.group("website")
def third_party_applications_third_party_application_website():
    pass


@third_party_applications_third_party_application_website.command("deploy")
@click.argument("third_party_application_rid", type=str, required=True)
@click.option("--version", type=str, required=True, help="""""")
@click.pass_obj
def third_party_applications_third_party_application_website_op_deploy(
    client: FoundryClient,
    third_party_application_rid: str,
    version: str,
):
    """
    Deploy a version of the Website.
    """
    result = client.third_party_applications.ThirdPartyApplication.Website.deploy(
        third_party_application_rid=third_party_application_rid,
        version=version,
    )
    click.echo(repr(result))


@third_party_applications_third_party_application_website.command("get")
@click.argument("third_party_application_rid", type=str, required=True)
@click.pass_obj
def third_party_applications_third_party_application_website_op_get(
    client: FoundryClient,
    third_party_application_rid: str,
):
    """
    Get the Website.
    """
    result = client.third_party_applications.ThirdPartyApplication.Website.get(
        third_party_application_rid=third_party_application_rid,
    )
    click.echo(repr(result))


@third_party_applications_third_party_application_website.command("undeploy")
@click.argument("third_party_application_rid", type=str, required=True)
@click.pass_obj
def third_party_applications_third_party_application_website_op_undeploy(
    client: FoundryClient,
    third_party_application_rid: str,
):
    """
    Remove the currently deployed version of the Website.
    """
    result = client.third_party_applications.ThirdPartyApplication.Website.undeploy(
        third_party_application_rid=third_party_application_rid,
    )
    click.echo(repr(result))


@third_party_applications_third_party_application_website.group("version")
def third_party_applications_third_party_application_website_version():
    pass


@third_party_applications_third_party_application_website_version.command("delete")
@click.argument("third_party_application_rid", type=str, required=True)
@click.argument("version_version", type=str, required=True)
@click.pass_obj
def third_party_applications_third_party_application_website_version_op_delete(
    client: FoundryClient,
    third_party_application_rid: str,
    version_version: str,
):
    """
    Delete the Version with the specified version.
    """
    result = client.third_party_applications.ThirdPartyApplication.Website.Version.delete(
        third_party_application_rid=third_party_application_rid,
        version_version=version_version,
    )
    click.echo(repr(result))


@third_party_applications_third_party_application_website_version.command("get")
@click.argument("third_party_application_rid", type=str, required=True)
@click.argument("version_version", type=str, required=True)
@click.pass_obj
def third_party_applications_third_party_application_website_version_op_get(
    client: FoundryClient,
    third_party_application_rid: str,
    version_version: str,
):
    """
    Get the Version with the specified version.
    """
    result = client.third_party_applications.ThirdPartyApplication.Website.Version.get(
        third_party_application_rid=third_party_application_rid,
        version_version=version_version,
    )
    click.echo(repr(result))


@third_party_applications_third_party_application_website_version.command("list")
@click.argument("third_party_application_rid", type=str, required=True)
@click.option(
    "--page_size", type=int, required=False, help="""The page size to use for the endpoint."""
)
@click.option(
    "--page_token",
    type=str,
    required=False,
    help="""The page token indicates where to start paging. This should be omitted from the first page's request.
To fetch the next page, clients should take the value from the `nextPageToken` field of the previous response
and use it to populate the `pageToken` field of the next request.""",
)
@click.pass_obj
def third_party_applications_third_party_application_website_version_op_list(
    client: FoundryClient,
    third_party_application_rid: str,
    page_size: typing.Optional[int],
    page_token: typing.Optional[str],
):
    """
    Lists all Versions.

    This is a paged endpoint. Each page may be smaller or larger than the requested page size. However, it is guaranteed that if there are more results available, the `nextPageToken` field will be populated. To get the next page, make the same request again, but set the value of the `pageToken` query parameter to be value of the `nextPageToken` value of the previous response. If there is no `nextPageToken` field in the response, you are on the last page.
    """
    result = client.third_party_applications.ThirdPartyApplication.Website.Version.list(
        third_party_application_rid=third_party_application_rid,
        page_size=page_size,
        page_token=page_token,
    )
    click.echo(repr(result))


@third_party_applications_third_party_application_website_version.command("upload")
@click.argument("third_party_application_rid", type=str, required=True)
@click.argument("body", type=click.File("rb"), required=True)
@click.option("--version", type=str, required=True, help="""""")
@click.pass_obj
def third_party_applications_third_party_application_website_version_op_upload(
    client: FoundryClient,
    third_party_application_rid: str,
    body: io.BufferedReader,
    version: str,
):
    """
    Upload a new version of the Website.
    """
    result = client.third_party_applications.ThirdPartyApplication.Website.Version.upload(
        third_party_application_rid=third_party_application_rid,
        body=body.read(),
        version=version,
    )
    click.echo(repr(result))


@third_party_applications_third_party_application_website_version.command("upload_snapshot")
@click.argument("third_party_application_rid", type=str, required=True)
@click.argument("body", type=click.File("rb"), required=True)
@click.option("--version", type=str, required=True, help="""""")
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.option(
    "--snapshot_identifier",
    type=str,
    required=False,
    help="""The identifier of the snapshot. If the identifier follows the format
`foundry.v1@<repositoryRid>@<pullRequestRid>@<commitHash>`, PR preview for such identifier will be
accessible from foundry code repositories.
""",
)
@click.pass_obj
def third_party_applications_third_party_application_website_version_op_upload_snapshot(
    client: FoundryClient,
    third_party_application_rid: str,
    body: io.BufferedReader,
    version: str,
    preview: typing.Optional[bool],
    snapshot_identifier: typing.Optional[str],
):
    """
    Upload a snapshot version of the Website. Snapshot versions are automatically deleted after two days.

    """
    result = client.third_party_applications.ThirdPartyApplication.Website.Version.upload_snapshot(
        third_party_application_rid=third_party_application_rid,
        body=body.read(),
        version=version,
        preview=preview,
        snapshot_identifier=snapshot_identifier,
    )
    click.echo(repr(result))


@cli.group("widgets")
def widgets():
    pass


@widgets.group("widget_set")
def widgets_widget_set():
    pass


@widgets_widget_set.command("get")
@click.argument("widget_set_rid", type=str, required=True)
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.pass_obj
def widgets_widget_set_op_get(
    client: FoundryClient,
    widget_set_rid: str,
    preview: typing.Optional[bool],
):
    """
    Get the WidgetSet with the specified rid.
    """
    result = client.widgets.WidgetSet.get(
        widget_set_rid=widget_set_rid,
        preview=preview,
    )
    click.echo(repr(result))


@widgets_widget_set.group("release")
def widgets_widget_set_release():
    pass


@widgets_widget_set_release.command("delete")
@click.argument("widget_set_rid", type=str, required=True)
@click.argument("release_version", type=str, required=True)
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.pass_obj
def widgets_widget_set_release_op_delete(
    client: FoundryClient,
    widget_set_rid: str,
    release_version: str,
    preview: typing.Optional[bool],
):
    """
    Delete the Release with the specified version.
    """
    result = client.widgets.WidgetSet.Release.delete(
        widget_set_rid=widget_set_rid,
        release_version=release_version,
        preview=preview,
    )
    click.echo(repr(result))


@widgets_widget_set_release.command("get")
@click.argument("widget_set_rid", type=str, required=True)
@click.argument("release_version", type=str, required=True)
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.pass_obj
def widgets_widget_set_release_op_get(
    client: FoundryClient,
    widget_set_rid: str,
    release_version: str,
    preview: typing.Optional[bool],
):
    """
    Get the Release with the specified version.
    """
    result = client.widgets.WidgetSet.Release.get(
        widget_set_rid=widget_set_rid,
        release_version=release_version,
        preview=preview,
    )
    click.echo(repr(result))


@widgets_widget_set_release.command("list")
@click.argument("widget_set_rid", type=str, required=True)
@click.option(
    "--page_size", type=int, required=False, help="""The page size to use for the endpoint."""
)
@click.option(
    "--page_token",
    type=str,
    required=False,
    help="""The page token indicates where to start paging. This should be omitted from the first page's request.
To fetch the next page, clients should take the value from the `nextPageToken` field of the previous response
and use it to populate the `pageToken` field of the next request.""",
)
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.pass_obj
def widgets_widget_set_release_op_list(
    client: FoundryClient,
    widget_set_rid: str,
    page_size: typing.Optional[int],
    page_token: typing.Optional[str],
    preview: typing.Optional[bool],
):
    """
    Lists all Releases.

    This is a paged endpoint. Each page may be smaller or larger than the requested page size. However, it is guaranteed that if there are more results available, the `nextPageToken` field will be populated. To get the next page, make the same request again, but set the value of the `pageToken` query parameter to be value of the `nextPageToken` value of the previous response. If there is no `nextPageToken` field in the response, you are on the last page.
    """
    result = client.widgets.WidgetSet.Release.list(
        widget_set_rid=widget_set_rid,
        page_size=page_size,
        page_token=page_token,
        preview=preview,
    )
    click.echo(repr(result))


@widgets.group("repository")
def widgets_repository():
    pass


@widgets_repository.command("get")
@click.argument("repository_rid", type=str, required=True)
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.pass_obj
def widgets_repository_op_get(
    client: FoundryClient,
    repository_rid: str,
    preview: typing.Optional[bool],
):
    """
    Get the Repository with the specified rid.
    """
    result = client.widgets.Repository.get(
        repository_rid=repository_rid,
        preview=preview,
    )
    click.echo(repr(result))


@widgets_repository.command("publish")
@click.argument("repository_rid", type=str, required=True)
@click.argument("body", type=click.File("rb"), required=True)
@click.option("--repository_version", type=str, required=True, help="""""")
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.pass_obj
def widgets_repository_op_publish(
    client: FoundryClient,
    repository_rid: str,
    body: io.BufferedReader,
    repository_version: str,
    preview: typing.Optional[bool],
):
    """
    Publish a new release of a widget set.
    """
    result = client.widgets.Repository.publish(
        repository_rid=repository_rid,
        body=body.read(),
        repository_version=repository_version,
        preview=preview,
    )
    click.echo(repr(result))


@widgets.group("dev_mode_settings")
def widgets_dev_mode_settings():
    pass


@widgets_dev_mode_settings.command("disable")
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.pass_obj
def widgets_dev_mode_settings_op_disable(
    client: FoundryClient,
    preview: typing.Optional[bool],
):
    """
    Disable dev mode for the user associated with the provided token.
    """
    result = client.widgets.DevModeSettings.disable(
        preview=preview,
    )
    click.echo(repr(result))


@widgets_dev_mode_settings.command("enable")
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.pass_obj
def widgets_dev_mode_settings_op_enable(
    client: FoundryClient,
    preview: typing.Optional[bool],
):
    """
    Enable dev mode for the user associated with the provided token.
    """
    result = client.widgets.DevModeSettings.enable(
        preview=preview,
    )
    click.echo(repr(result))


@widgets_dev_mode_settings.command("get")
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.pass_obj
def widgets_dev_mode_settings_op_get(
    client: FoundryClient,
    preview: typing.Optional[bool],
):
    """
    Get the dev mode settings for the user associated with the provided token.
    """
    result = client.widgets.DevModeSettings.get(
        preview=preview,
    )
    click.echo(repr(result))


@widgets_dev_mode_settings.command("pause")
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.pass_obj
def widgets_dev_mode_settings_op_pause(
    client: FoundryClient,
    preview: typing.Optional[bool],
):
    """
    Pause dev mode for the user associated with the provided token.
    """
    result = client.widgets.DevModeSettings.pause(
        preview=preview,
    )
    click.echo(repr(result))


@widgets_dev_mode_settings.command("set_widget_set")
@click.option("--settings", type=str, required=True, help="""""")
@click.option("--widget_set_rid", type=str, required=True, help="""""")
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.pass_obj
def widgets_dev_mode_settings_op_set_widget_set(
    client: FoundryClient,
    settings: str,
    widget_set_rid: str,
    preview: typing.Optional[bool],
):
    """
    Set the dev mode settings for the given widget set for the user associated with the provided token.
    """
    result = client.widgets.DevModeSettings.set_widget_set(
        settings=json.loads(settings),
        widget_set_rid=widget_set_rid,
        preview=preview,
    )
    click.echo(repr(result))


@widgets_dev_mode_settings.command("set_widget_set_by_id")
@click.option("--settings", type=str, required=True, help="""""")
@click.option("--widget_set_rid", type=str, required=True, help="""""")
@click.option(
    "--preview", type=bool, required=False, help="""Enables the use of preview functionality."""
)
@click.pass_obj
def widgets_dev_mode_settings_op_set_widget_set_by_id(
    client: FoundryClient,
    settings: str,
    widget_set_rid: str,
    preview: typing.Optional[bool],
):
    """
    Set the dev mode settings for the given widget set for the user associated with the
    provided token. Uses widget IDs to identify widgets within the set.

    """
    result = client.widgets.DevModeSettings.set_widget_set_by_id(
        settings=json.loads(settings),
        widget_set_rid=widget_set_rid,
        preview=preview,
    )
    click.echo(repr(result))


if __name__ == "__main__":
    cli()
