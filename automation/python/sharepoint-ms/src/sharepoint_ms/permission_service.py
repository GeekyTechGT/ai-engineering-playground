"""
SharePoint user-permission inspection via the SharePoint REST API.

The Microsoft Graph API does not expose SharePoint role assignments for
individual users; this service uses the SharePoint REST ``/_api/web/`` endpoints
instead (with a separate SharePoint-scoped bearer token obtained from the
same ``TokenProvider``).

Coverage:
- Direct user assignments (PrincipalType == 1)
- SharePoint group membership  (PrincipalType == 8)
- AAD security-group membership (PrincipalType == 4)
"""
from __future__ import annotations

import re
from typing import Any, Callable

from ._http import GraphHttpClient, SharePointRestClient


class PermissionService:
    """
    Inspects effective SharePoint permissions for a specific user on a site.

    Single responsibility: translate SharePoint role assignments into a
    structured permission report.

    Args:
        graph:               Authenticated Graph HTTP client.
        rest_client_factory: Callable ``(hostname: str) -> SharePointRestClient``.
                             Called lazily once per unique hostname.
    """

    def __init__(
        self,
        graph: GraphHttpClient,
        rest_client_factory: Callable[[str], SharePointRestClient],
    ) -> None:
        self._graph = graph
        self._rest_factory = rest_client_factory

    def get_user_site_permissions(
        self,
        user_email: str,
        hostname: str,
        site_path: str,
    ) -> dict[str, Any]:
        """
        Return the effective SharePoint permissions of a user on a site.

        Args:
            user_email: UPN or email address of the user to inspect.
            hostname:   SharePoint hostname, e.g. ``contoso.sharepoint.com``.
            site_path:  Server-relative site path, e.g. ``/sites/TeamSite``.

        Returns:
            Dict with the following keys:

            ``user``
                Basic user info (``email``, ``id``, ``display_name``,
                ``user_principal_name``).

            ``site``
                The resolved ``hostname`` and ``site_path``.

            ``effective_roles``
                Sorted list of unique role names the user holds on the site
                (union of direct and group-based assignments).

            ``direct_assignments``
                Role assignments where the user is the principal directly.

            ``group_assignments``
                Role assignments where the user gains access through a
                SharePoint group or an AAD security group.

            ``has_access``
                ``True`` if ``effective_roles`` is non-empty.
        """
        email = user_email.strip().lower()
        path = self._normalize_path(site_path)
        rest = self._rest_factory(hostname)

        assignments = rest.get_list(
            path,
            "/_api/web/roleassignments"
            "?$expand=Member,RoleDefinitionBindings"
            "&$select=PrincipalId,Member/Id,Member/Title,Member/LoginName,"
            "Member/PrincipalType,RoleDefinitionBindings/Name",
        )

        user = self._graph.get(
            f"/users/{email}?$select=id,displayName,mail,userPrincipalName"
        )
        user_id: str = user["id"]
        aad_group_ids = self._get_transitive_group_ids(user_id)

        direct: list[dict[str, Any]] = []
        via_group: list[dict[str, Any]] = []

        for assignment in assignments:
            member = assignment.get("Member") or {}
            principal_type = int(member.get("PrincipalType") or 0)
            principal_id = assignment.get("PrincipalId") or member.get("Id")
            roles = self._extract_role_names(assignment)

            if principal_type == 1:
                # Direct user principal
                if self._matches_user(member, email):
                    direct.append(
                        {
                            "principal_id": principal_id,
                            "principal_type": "user",
                            "principal_title": member.get("Title"),
                            "principal_login_name": member.get("LoginName"),
                            "roles": roles,
                        }
                    )

            elif principal_type == 8 and principal_id is not None:
                # SharePoint group
                if self._user_in_sharepoint_group(
                    rest, path, int(principal_id), email
                ):
                    via_group.append(
                        {
                            "principal_id": principal_id,
                            "principal_type": "sharepoint_group",
                            "principal_title": member.get("Title"),
                            "principal_login_name": member.get("LoginName"),
                            "roles": roles,
                        }
                    )

            elif principal_type == 4:
                # AAD security group
                obj_id = self._extract_guid(member.get("LoginName"))
                if obj_id and obj_id in aad_group_ids:
                    via_group.append(
                        {
                            "principal_id": principal_id,
                            "principal_type": "aad_group",
                            "principal_title": member.get("Title"),
                            "principal_login_name": member.get("LoginName"),
                            "aad_group_id": obj_id,
                            "roles": roles,
                        }
                    )

        effective_roles = sorted(
            {
                role
                for entry in [*direct, *via_group]
                for role in entry.get("roles", [])
            }
        )

        return {
            "user": {
                "email": email,
                "id": user_id,
                "display_name": user.get("displayName"),
                "user_principal_name": user.get("userPrincipalName"),
            },
            "site": {
                "hostname": hostname,
                "site_path": path,
            },
            "effective_roles": effective_roles,
            "direct_assignments": direct,
            "group_assignments": via_group,
            "has_access": bool(effective_roles),
        }

    # ------------------------------------------------------------------ #
    # Private helpers
    # ------------------------------------------------------------------ #

    def _get_transitive_group_ids(self, user_id: str) -> set[str]:
        groups = self._graph.get_paged(
            f"/users/{user_id}/transitiveMemberOf"
            "/microsoft.graph.group?$select=id"
        )
        return {g["id"] for g in groups if "id" in g}

    @staticmethod
    def _user_in_sharepoint_group(
        rest: SharePointRestClient,
        site_path: str,
        group_id: int,
        user_email: str,
    ) -> bool:
        members = rest.get_list(
            site_path,
            f"/_api/web/sitegroups({group_id})/users"
            "?$select=Id,Email,LoginName,Title",
        )
        for m in members:
            email = (m.get("Email") or "").strip().lower()
            login = (m.get("LoginName") or "").strip().lower()
            if email == user_email or user_email in login:
                return True
        return False

    @staticmethod
    def _normalize_path(site_path: str) -> str:
        raw = site_path.strip()
        if not raw:
            raise ValueError("site_path cannot be empty.")
        if not raw.startswith("/"):
            raw = "/" + raw
        return raw.rstrip("/")

    @staticmethod
    def _extract_role_names(assignment: dict[str, Any]) -> list[str]:
        bindings = assignment.get("RoleDefinitionBindings") or []
        return [str(b["Name"]) for b in bindings if b.get("Name")]

    @staticmethod
    def _matches_user(member: dict[str, Any], email: str) -> bool:
        login = (member.get("LoginName") or "").lower()
        title = (member.get("Title") or "").lower()
        return email in login or title == email

    @staticmethod
    def _extract_guid(value: str | None) -> str | None:
        if not value:
            return None
        m = re.search(
            r"([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})",
            value,
            re.IGNORECASE,
        )
        return m.group(1).lower() if m else None
