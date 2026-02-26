from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any

import requests


class SharePointError(RuntimeError):
    """Errore applicativo per operazioni SharePoint/Graph."""


@dataclass(slots=True)
class SharePointConfig:
    tenant_id: str
    client_id: str
    client_secret: str
    timeout_seconds: int = 30


class SharePointClient:
    """Client minimale per SharePoint Online via Microsoft Graph."""

    def __init__(self, config: SharePointConfig):
        self.config = config
        self._access_token: str | None = None
        self._sharepoint_tokens: dict[str, str] = {}
        self._base_graph = "https://graph.microsoft.com/v1.0"

    def authenticate(self) -> str:
        token_url = f"https://login.microsoftonline.com/{self.config.tenant_id}/oauth2/v2.0/token"
        payload = {
            "client_id": self.config.client_id,
            "client_secret": self.config.client_secret,
            "grant_type": "client_credentials",
            "scope": "https://graph.microsoft.com/.default",
        }

        response = requests.post(token_url, data=payload, timeout=self.config.timeout_seconds)
        if response.status_code >= 400:
            raise SharePointError(f"Autenticazione fallita ({response.status_code}): {response.text}")

        token = response.json().get("access_token")
        if not token:
            raise SharePointError("Token non presente nella risposta OAuth2.")

        self._access_token = token
        return token

    def get_site(self, hostname: str, site_path: str) -> dict[str, Any]:
        endpoint = f"/sites/{hostname}:{site_path}"
        return self._get(endpoint)

    def list_drive_root_items(self, site_id: str) -> list[dict[str, Any]]:
        endpoint = f"/sites/{site_id}/drive/root/children"
        data = self._get(endpoint)
        return data.get("value", [])

    def download_file(self, site_id: str, item_id: str, destination: str | Path) -> Path:
        endpoint = f"/sites/{site_id}/drive/items/{item_id}/content"
        target = Path(destination)
        target.parent.mkdir(parents=True, exist_ok=True)

        response = self._request("GET", endpoint, raw=True)
        with target.open("wb") as f:
            f.write(response.content)

        return target

    def upload_file(self, site_id: str, folder_path: str, local_file: str | Path) -> dict[str, Any]:
        file_path = Path(local_file)
        if not file_path.exists():
            raise SharePointError(f"File locale non trovato: {file_path}")

        upload_endpoint = (
            f"/sites/{site_id}/drive/root:/{folder_path.strip('/')}/{file_path.name}:/content"
        )
        content = file_path.read_bytes()
        return self._put(upload_endpoint, content, headers={"Content-Type": "application/octet-stream"})

    def get_user_site_permissions(
        self,
        user_email: str,
        hostname: str,
        site_path: str,
    ) -> dict[str, Any]:
        """
        Restituisce i permessi rilevati di un utente su un sito SharePoint.

        Copre:
        - assegnazioni dirette utente
        - assegnazioni tramite gruppi SharePoint
        - assegnazioni tramite gruppi AAD presenti nei role assignments
        """
        normalized_email = user_email.strip().lower()
        normalized_site_path = self._normalize_site_path(site_path)
        assignments = self._sharepoint_get(
            hostname=hostname,
            site_path=normalized_site_path,
            endpoint=(
                "/_api/web/roleassignments"
                "?$expand=Member,RoleDefinitionBindings"
                "&$select=PrincipalId,Member/Id,Member/Title,Member/LoginName,Member/PrincipalType,"
                "RoleDefinitionBindings/Name"
            ),
        )

        user = self._get_graph_user(normalized_email)
        aad_group_ids = self._get_user_transitive_group_ids(user["id"])

        direct_matches: list[dict[str, Any]] = []
        via_group_matches: list[dict[str, Any]] = []

        for assignment in assignments:
            member = assignment.get("Member", {})
            principal_type = int(member.get("PrincipalType") or 0)
            principal_id = assignment.get("PrincipalId") or member.get("Id")
            roles = self._extract_role_names(assignment)

            if principal_type == 1 and self._principal_matches_user(member, normalized_email):
                direct_matches.append(
                    {
                        "principal_id": principal_id,
                        "principal_type": "user",
                        "principal_title": member.get("Title"),
                        "principal_login_name": member.get("LoginName"),
                        "roles": roles,
                    }
                )
                continue

            # 8 = SharePoint group
            if principal_type == 8 and principal_id is not None:
                if self._user_in_sharepoint_group(
                    hostname=hostname,
                    site_path=normalized_site_path,
                    group_id=int(principal_id),
                    user_email=normalized_email,
                ):
                    via_group_matches.append(
                        {
                            "principal_id": principal_id,
                            "principal_type": "sharepoint_group",
                            "principal_title": member.get("Title"),
                            "principal_login_name": member.get("LoginName"),
                            "roles": roles,
                        }
                    )
                continue

            # 4 = Security group (tipicamente AAD), match via object id nel claim.
            if principal_type == 4:
                principal_object_id = self._extract_guid_from_claim(member.get("LoginName"))
                if principal_object_id and principal_object_id in aad_group_ids:
                    via_group_matches.append(
                        {
                            "principal_id": principal_id,
                            "principal_type": "aad_group",
                            "principal_title": member.get("Title"),
                            "principal_login_name": member.get("LoginName"),
                            "aad_group_id": principal_object_id,
                            "roles": roles,
                        }
                    )

        effective_roles = sorted(
            {
                role
                for entry in [*direct_matches, *via_group_matches]
                for role in entry.get("roles", [])
            }
        )

        return {
            "user": {
                "email": normalized_email,
                "id": user.get("id"),
                "display_name": user.get("displayName"),
                "user_principal_name": user.get("userPrincipalName"),
            },
            "site": {
                "hostname": hostname,
                "site_path": normalized_site_path,
            },
            "effective_roles": effective_roles,
            "direct_assignments": direct_matches,
            "group_assignments": via_group_matches,
            "has_access": bool(effective_roles),
        }

    def _headers(self) -> dict[str, str]:
        if not self._access_token:
            self.authenticate()
        return {
            "Authorization": f"Bearer {self._access_token}",
            "Accept": "application/json",
        }

    def _get(self, endpoint: str) -> dict[str, Any]:
        response = self._request("GET", endpoint)
        return response.json()

    def _put(self, endpoint: str, payload: bytes, headers: dict[str, str] | None = None) -> dict[str, Any]:
        response = self._request("PUT", endpoint, data=payload, headers=headers)
        return response.json()

    def _request(
        self,
        method: str,
        endpoint: str,
        data: bytes | None = None,
        headers: dict[str, str] | None = None,
        raw: bool = False,
    ) -> requests.Response:
        merged_headers = self._headers()
        if headers:
            merged_headers.update(headers)

        response = requests.request(
            method=method,
            url=f"{self._base_graph}{endpoint}",
            headers=merged_headers,
            data=data,
            timeout=self.config.timeout_seconds,
        )

        if response.status_code >= 400:
            raise SharePointError(
                f"Errore Graph API su {method} {endpoint} ({response.status_code}): {response.text}"
            )

        if raw:
            return response

        content_type = response.headers.get("Content-Type", "")
        if "application/json" not in content_type and response.text:
            raise SharePointError(f"Risposta inattesa (non JSON): {response.text[:300]}")

        return response

    def authenticate_sharepoint(self, hostname: str) -> str:
        token_url = f"https://login.microsoftonline.com/{self.config.tenant_id}/oauth2/v2.0/token"
        payload = {
            "client_id": self.config.client_id,
            "client_secret": self.config.client_secret,
            "grant_type": "client_credentials",
            "scope": f"https://{hostname}/.default",
        }
        response = requests.post(token_url, data=payload, timeout=self.config.timeout_seconds)
        if response.status_code >= 400:
            raise SharePointError(
                f"Autenticazione SharePoint fallita per {hostname} ({response.status_code}): {response.text}"
            )

        token = response.json().get("access_token")
        if not token:
            raise SharePointError("Token SharePoint non presente nella risposta OAuth2.")

        self._sharepoint_tokens[hostname] = token
        return token

    def _sharepoint_headers(self, hostname: str) -> dict[str, str]:
        if hostname not in self._sharepoint_tokens:
            self.authenticate_sharepoint(hostname)
        return {
            "Authorization": f"Bearer {self._sharepoint_tokens[hostname]}",
            "Accept": "application/json;odata=nometadata",
        }

    def _sharepoint_get(self, hostname: str, site_path: str, endpoint: str) -> list[dict[str, Any]]:
        url = f"https://{hostname}{site_path}{endpoint}"
        response = requests.get(url, headers=self._sharepoint_headers(hostname), timeout=self.config.timeout_seconds)
        if response.status_code >= 400:
            raise SharePointError(f"Errore SharePoint REST GET {url} ({response.status_code}): {response.text}")

        payload = response.json()
        value = payload.get("value")
        if isinstance(value, list):
            return value

        data = payload.get("d", {})
        results = data.get("results")
        if isinstance(results, list):
            return results
        return []

    def _graph_get_paged(self, endpoint: str) -> list[dict[str, Any]]:
        current_url = f"{self._base_graph}{endpoint}"
        all_items: list[dict[str, Any]] = []

        while current_url:
            response = requests.get(
                current_url,
                headers=self._headers(),
                timeout=self.config.timeout_seconds,
            )
            if response.status_code >= 400:
                raise SharePointError(f"Errore Graph API su GET {current_url} ({response.status_code}): {response.text}")

            payload = response.json()
            all_items.extend(payload.get("value", []))
            current_url = payload.get("@odata.nextLink")

        return all_items

    def _get_graph_user(self, user_email: str) -> dict[str, Any]:
        endpoint = f"/users/{user_email}?$select=id,displayName,mail,userPrincipalName"
        return self._get(endpoint)

    def _get_user_transitive_group_ids(self, user_id: str) -> set[str]:
        endpoint = f"/users/{user_id}/transitiveMemberOf/microsoft.graph.group?$select=id"
        groups = self._graph_get_paged(endpoint)
        return {g["id"] for g in groups if "id" in g}

    def _user_in_sharepoint_group(
        self,
        hostname: str,
        site_path: str,
        group_id: int,
        user_email: str,
    ) -> bool:
        members = self._sharepoint_get(
            hostname=hostname,
            site_path=site_path,
            endpoint=(
                f"/_api/web/sitegroups({group_id})/users"
                "?$select=Id,Email,LoginName,Title"
            ),
        )
        for member in members:
            email = (member.get("Email") or "").strip().lower()
            login_name = (member.get("LoginName") or "").strip().lower()
            title = (member.get("Title") or "").strip().lower()
            if email == user_email or user_email in login_name or title == user_email:
                return True
        return False

    @staticmethod
    def _normalize_site_path(site_path: str) -> str:
        raw = site_path.strip()
        if not raw:
            raise SharePointError("site_path non puo' essere vuoto.")
        if not raw.startswith("/"):
            raw = "/" + raw
        return raw.rstrip("/")

    @staticmethod
    def _extract_role_names(assignment: dict[str, Any]) -> list[str]:
        bindings = assignment.get("RoleDefinitionBindings") or []
        names: list[str] = []
        for binding in bindings:
            name = binding.get("Name")
            if name:
                names.append(str(name))
        return names

    @staticmethod
    def _principal_matches_user(member: dict[str, Any], user_email: str) -> bool:
        login_name = (member.get("LoginName") or "").strip().lower()
        title = (member.get("Title") or "").strip().lower()
        return user_email in login_name or title == user_email

    @staticmethod
    def _extract_guid_from_claim(value: str | None) -> str | None:
        if not value:
            return None
        match = re.search(
            r"([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})",
            value,
        )
        if not match:
            return None
        return match.group(1).lower()
