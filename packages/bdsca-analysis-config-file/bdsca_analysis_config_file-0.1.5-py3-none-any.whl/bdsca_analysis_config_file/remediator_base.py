from __future__ import annotations

import sys
from typing import Any


class RemediatorBase:
    """Base class providing hub/session setup, logging, and shared helpers."""

    last_error: str | None
    _purl_cache: dict[str, Any]
    # Caches store resolved identity as 5-tuple: (name, version_url, version_name, origin_url, originId)
    _purl_component_cache: dict[str, tuple[str, str, str, str, str]]
    _nv_component_cache: dict[tuple[str, str, str, str, str], tuple[str, str, str, str, str]]

    def __init__(
        self,
        log_level: int = 10,
        *,
        hub: Any | None = None,
        base_url: str | None = None,
        api_token: str | None = None,
        insecure: bool = False,
        session: Any | None = None,
        output_level: str = "info",
    ) -> None:
        # Logging was replaced with print statements; preserving parameter for compatibility
        lvl = (output_level or "info").lower()
        self._level = "debug" if lvl == "debug" else "info"

        def _make_debug() -> Any:
            if self._level == "debug":
                return lambda *a, **k: print("[DEBUG]", *a, **k)
            return lambda *a, **k: None

        self._debug = _make_debug()
        self._info = lambda *a, **k: print("[INFO]", *a, **k)
        self._error = lambda *a, **k: print("[ERROR]", *a, file=sys.stderr, **k)

        # Session dependency (requests-like)
        if session is None:
            try:
                import requests as _requests  # type: ignore
            except Exception as ex:  # pragma: no cover
                raise RuntimeError("Provide a session or install 'requests'") from ex
            self.session = _requests
        else:
            self.session = session

        # Hub dependency
        if hub is not None:
            self.hub = hub
        else:
            if not base_url or not api_token:
                raise ValueError("base_url and api_token are required when no hub is provided")
            # Normalize base_url, remove trailing slash
            url = base_url[:-1] if base_url.endswith("/") else base_url
            # Lazy import to avoid hard dependency during tests
            try:
                from blackduck.HubRestApi import HubInstance  # type: ignore
            except Exception as ex:  # pragma: no cover
                raise RuntimeError("Black Duck SDK not installed; pass a 'hub' instance instead") from ex
            self.hub = HubInstance(url, api_token=api_token, insecure=insecure)

        # Detailed failure reason (for CLI display)
        self.last_error = None
        # Simple in-memory caches
        self._purl_cache = {}
        self._purl_component_cache = {}
        self._nv_component_cache = {}

    # ------------------------- Common helpers -------------------------
    def _base_url(self) -> str:
        base: str | None = None
        if hasattr(self.hub, "base_url") and self.hub.base_url:
            base = str(self.hub.base_url).rstrip("/")
        elif isinstance(getattr(self.hub, "config", None), dict):
            cfg = self.hub.config
            base = (cfg.get("baseurl") or cfg.get("url") or "").rstrip("/")
        return base or ""

    def get_project_and_version_ids(self, project_name: str, project_version_name: str) -> tuple[str, str] | None:
        parameters = {"q": f"name:{project_name}"}
        projects = self.hub.get_projects(limit=1, parameters=parameters)
        if not projects or not projects.get("items"):
            self.last_error = f"Project not found: {project_name}"
            return None
        project = projects["items"][0]
        versions = self._call_project_versions(project, project_version_name)
        if not versions or not versions.get("items"):
            self.last_error = f"Version not found: {project_version_name} (project {project_name})"
            return None
        version = versions["items"][0]
        project_id = project.get("_meta", {}).get("href", "").split("/")[-1]
        version_id = version.get("_meta", {}).get("href", "").split("/")[-1]
        if not project_id or not version_id:
            self.last_error = f"Could not extract project/version IDs for {project_name}/{project_version_name}"
            return None
        return (project_id, version_id)

    def _get_project_versions(self, project: dict, projectVersionName: str) -> dict[str, Any]:
        parameters = {"q": f"versionName:{projectVersionName}", "limit": "1"}
        url = project["_meta"]["href"] + "/versions" + self.hub._get_parameter_string(parameters)
        headers = self.hub.get_headers()
        headers["Accept"] = "application/vnd.blackducksoftware.internal-1+json"
        response = self.session.get(url, headers=headers, verify=not self.hub.config["insecure"])
        if response.status_code != 200:
            self.last_error = f"Fetch project versions failed ({response.status_code}) for URL: {url}"
            self._error(self.last_error)
            return {}
        try:
            jsondata = response.json()
            if isinstance(jsondata, dict):
                return jsondata
            self.last_error = "Unexpected project versions response type"
            return {}
        except Exception:
            self.last_error = "Failed to parse project versions response JSON"
            self._error(self.last_error)
            return {}

    def _call_project_versions(self, project: dict, projectVersionName: str) -> dict[str, Any]:
        return self._get_project_versions(project, projectVersionName)

    def get_component_by_purl(self, purl: str) -> dict[str, Any] | None:
        if not purl:
            self.last_error = "purl must be provided"
            return None
        base = self._base_url()
        if not base:
            self.last_error = "Could not determine Black Duck base URL from hub"
            return None
        endpoint = f"{base}/api/search/kb-purl-component"
        # Build query string
        params = {"purl": purl}
        if hasattr(self.hub, "_get_parameter_string"):
            endpoint = endpoint + self.hub._get_parameter_string(params)
        else:
            from urllib.parse import urlencode

            endpoint = endpoint + "?" + urlencode(params)

        headers = self.hub.get_headers()
        headers["Accept"] = "application/vnd.blackducksoftware.component-detail-5+json"

        self._info("Fetching component by purl", {"purl": purl})
        resp = self.session.get(endpoint, headers=headers, verify=not self.hub.config["insecure"])
        if resp.status_code == 200:
            try:
                result = resp.json()
                if isinstance(result, dict):
                    return result
                return None
            except Exception:
                self.last_error = "Failed to parse component response JSON"
                return None
        if resp.status_code == 404:
            self.last_error = f"Component not found for purl: {purl}"
            return None
        self.last_error = f"Component lookup failed ({resp.status_code}): " f"{getattr(resp, 'text', '') or getattr(resp, 'content', b'')}"
        self._error(self.last_error)
        return None

    def get_component_versions(
        self,
        component_id: str,
        *,
        offset: int = 0,
        limit: int = 100,
        sort: str | None = None,
        q: str | None = None,
        filter: object | None = None,
    ) -> dict[str, Any] | None:
        if not component_id:
            self.last_error = "component_id must be provided"
            return None
        base = self._base_url()
        if not base:
            self.last_error = "Could not determine Black Duck base URL from hub"
            return None
        endpoint = f"{base}/api/components/{component_id}/versions"
        params: dict[str, Any] = {"offset": offset, "limit": limit}
        if sort:
            params["sort"] = sort
        if q:
            params["q"] = q
        if filter:
            if isinstance(filter, (list, tuple)):
                params["filter"] = list(filter)
            else:
                params["filter"] = [str(filter)]

        from urllib.parse import urlencode

        qs = urlencode(params, doseq=True)
        url = endpoint + ("?" + qs if qs else "")

        headers = self.hub.get_headers()
        headers["Accept"] = "application/vnd.blackducksoftware.component-detail-5+json"

        self._info("Fetching component versions", {"componentId": component_id, "url": url})
        resp = self.session.get(url, headers=headers, verify=not bool(self.hub.config.get("insecure", False)))
        if resp.status_code == 200:
            try:
                data = resp.json()
                if isinstance(data, dict):
                    return data
            except Exception:
                self.last_error = "Failed to parse component versions response JSON"
                return None
            self.last_error = "Unexpected response type for component versions"
            return None
        if resp.status_code == 404:
            self.last_error = f"Component not found: {component_id}"
            return None
        self.last_error = f"Component versions fetch failed ({resp.status_code}): " f"{getattr(resp, 'text', '') or getattr(resp, 'content', b'')}"
        self._error(self.last_error)
        return None

    def get_component_by_name_version(
        self,
        name: str,
        version: str,
        *,
        limit: int = 30,
    ) -> str | None:
        """Resolve a component version by name/version using search API.

        Returns the component version href string if found, else None.
        """
        if not name or not isinstance(name, str):
            self.last_error = "name must be provided"
            return None
        if not isinstance(version, str):
            self.last_error = "version must be a string"
            return None

        base = self._base_url()
        if not base:
            self.last_error = "Could not determine Black Duck base URL from hub"
            return None

        endpoint = f"{base}/api/search/components-in-use"
        # Attempt to filter by componentname and versionname; also set a small limit
        # Note: On some installations, only external IDs are searchable. We still include
        # the filter to improve hit probability and fallback to client-side filtering.
        params: dict[str, Any] = {"limit": limit}
        params["q"] = f"{name}"

        from urllib.parse import urlencode

        # Build initial URL without offset to preserve existing behavior/tests
        url = endpoint + "?" + urlencode(params)

        headers = self.hub.get_headers()
        # Use the component-detail v4 media type as requested
        headers["Accept"] = "application/vnd.blackducksoftware.internal-1+json, application/json"

        self._info("Fetching component by name/version", {"name": name, "url": url})
        resp = self.session.get(url, headers=headers, verify=not self.hub.config["insecure"])
        if resp.status_code == 404:
            self.last_error = f"Component not found: {name} {version}"
            return None

        # Iterate through pages until match is found or items exhausted
        offset = 0
        while resp.status_code == 200:
            try:
                data = resp.json()
            except Exception:
                self.last_error = "Failed to parse components response JSON"
                return None
            if isinstance(data, dict):
                items_node = data.get("items")
                items_list: list[Any] = items_node if isinstance(items_node, list) else []
                for item in items_list:
                    if not isinstance(item, dict):
                        continue
                    if not version:
                        href_any = item.get("_meta", {}).get("href")
                        href = href_any if isinstance(href_any, str) else None
                        return href
                    component_version = item.get("componentVersion")
                    if component_version == version:
                        href = item.get("_meta", {}).get("href")
                        return href if isinstance(href, str) and href else None
                    else:
                        self._debug(
                            "Component version does not match; skipping item",
                            {"found": component_version, "expected": version},
                        )

                # Determine if more pages exist
                total = data.get("totalCount")
                item_count = len(items_list)
                if not isinstance(total, int):
                    break
                offset += item_count
                if item_count == 0 or offset >= total:
                    break
                # Fetch next page: include offset; keep same limit/q
                paged_params = {"limit": limit, "q": name, "offset": offset}
                next_url = endpoint + "?" + urlencode(paged_params)
                self._debug("Paging components-in-use search", {"offset": offset, "limit": limit})
                resp = self.session.get(next_url, headers=headers, verify=not self.hub.config["insecure"])
            else:
                break
        return None

    def _extract_component_from_purl_payload(self, payload: Any) -> tuple[str, str, str, str, str]:
        d = payload or {}
        self._debug("Extracting component identity from payload", {"payload": d})
        if isinstance(d, dict) and d.get("items") and isinstance(d["items"], list):
            d = d["items"][0] or {}

        def first(*keys: str) -> str:
            for k in keys:
                v = d.get(k)
                if isinstance(v, str) and v:
                    return v
            comp = d.get("component") or {}
            if isinstance(comp, dict):
                for k in keys:
                    v = comp.get(k)
                    if isinstance(v, str) and v:
                        return v
            compver = d.get("version") or {}
            if isinstance(compver, dict):
                for k in keys:
                    v = compver.get(k)
                    if isinstance(v, str) and v:
                        return v
            return ""

        name = first("componentName", "name")
        versionNumber = first("versionName", "name")
        version = first("version")

        origin_url = first("variant")
        originId = first("originId")

        return (str(name or ""), str(version or ""), str(versionNumber or ""), str(origin_url or ""), str(originId or ""))

    def _component_version_matches_sha(self, vuln_comp: dict[str, Any], sha: str, project_version_href: str) -> bool:
        try:
            details_url: str | None = None
            cv = vuln_comp.get("componentVersion")
            comp_id: str | None = None
            comp_ver_id: str | None = None
            comp_ver_href: str | None = None
            if isinstance(cv, str):
                comp_ver_href = cv
            elif isinstance(cv, dict):
                comp_ver_href = cv.get("_meta", {}).get("href") if isinstance(cv.get("_meta"), dict) else cv.get("href")
            if isinstance(comp_ver_href, str) and "/api/components/" in comp_ver_href and "/versions/" in comp_ver_href:
                try:
                    parts = comp_ver_href.strip("/").split("/")
                    comp_id = parts[parts.index("components") + 1]
                    comp_ver_id = parts[parts.index("versions") + 1]
                except Exception:
                    comp_id = None
                    comp_ver_id = None

            if not (comp_id and comp_ver_id and isinstance(project_version_href, str) and project_version_href):
                return False

            pv_href = project_version_href
            if not pv_href.lower().startswith("http"):
                base = self._base_url()
                if base:
                    if pv_href.startswith("/"):
                        pv_href = base + pv_href
                    else:
                        pv_href = base + "/" + pv_href

            details_url = f"{pv_href}/components/{comp_id}/versions/{comp_ver_id}/sbom-fields"
            headers_ver = self.hub.get_headers()
            headers_ver["Accept"] = "application/vnd.blackducksoftware.bill-of-materials-7+json"
            headers_ver["Content-Type"] = "application/vnd.blackducksoftware.bill-of-materials-7+json"
            resp_ver = self.session.get(
                details_url,
                headers=headers_ver,
                verify=not self.hub.config["insecure"],
            )
            if resp_ver.status_code != 200:
                return False

            try:
                ver_json = resp_ver.json() or {}
            except Exception:
                ver_json = {}

            if not isinstance(ver_json, dict):
                return False

            items = ver_json.get("items")
            if isinstance(items, list):
                for it in items:
                    if not isinstance(it, dict):
                        continue
                    label = str(it.get("label") or "").lower()
                    field_name = str(it.get("fieldName") or "").lower()
                    if label == "component hash" or field_name == "componenthash":
                        val = it.get("value")
                        if isinstance(val, dict):
                            if "componentHash" in val and val["componentHash"] == sha:
                                return True
            return False
        except Exception:
            return False

    # ----------------------- Identity resolution -----------------------
    def resolve_component_identity(self, component: dict[str, Any]) -> tuple[str, str, str, str, str]:
        """
        Given a component dict (may contain purl, name/version/origin), resolve and return
        (name, version, originId) using caches and, if needed, a purl lookup.

        Caches are updated for both purl and (name,version,origin) keys.
        """
        name = str(component.get("name") or "")
        versionNumber = str(component.get("version") or "")
        version_url = ""
        origin_url = ""
        originId = ""

        purl = component.get("purl")
        if isinstance(purl, str) and purl:
            cached_ident = self._purl_component_cache.get(purl)
            if cached_ident:
                self._debug("Using cached PURL component identity", {"purl": purl})
                name, version_url, versionNumber, origin_url, originId = cached_ident
            else:
                payload = self._purl_cache.get(purl)
                if payload is None:
                    payload = self.get_component_by_purl(purl)
                    if payload is not None:
                        self._purl_cache[purl] = payload
                if payload:
                    n2, v2, vn2, ou2, oi2 = self._extract_component_from_purl_payload(payload)
                    self._debug("Extracted component identity from PURL payload", {"name": n2, "version": vn2, "version_url": v2, "origin_url": ou2, "originId": oi2})
                    if n2:
                        name = n2
                    if v2:
                        version_url = v2
                    if vn2:
                        versionNumber = vn2
                    if ou2:
                        origin_url = ou2
                    if oi2:
                        originId = oi2
                else:
                    self._debug("PURL lookup failed; falling back to provided fields", {"purl": purl})
                self._debug("Resolved component identity", {"name": name, "version": versionNumber, "origin": origin_url, "originId": originId})
                self._purl_component_cache[purl] = (str(name), str(version_url), str(versionNumber), str(origin_url), str(originId))
        else:
            key = (str(name), str(version_url), str(versionNumber), str(origin_url), str(originId))
            cached_ident2 = self._nv_component_cache.get(key)
            if cached_ident2:
                self._debug("Using cached NV component identity", {"key": key})
                name, version_url, versionNumber, origin_url, originId = cached_ident2
            else:
                self._nv_component_cache[key] = (str(name), str(version_url), str(versionNumber), str(origin_url), str(originId))

        return (str(name), str(version_url), str(versionNumber), str(origin_url), str(originId))

    def fetch_origins(self, href: str, component: dict[str, Any], limit: int = 100, offset: int = 0) -> tuple[int, dict[str, Any] | None]:
        """
        Fetch origins for a component version given a link href.
        Returns a tuple of (status_code, origin_item_dict|None).
        """
        headers = self.hub.get_headers()
        sep = "&" if "?" in href else "?"
        url = f"{href}{sep}limit={limit}&offset={offset}"
        resp = self.session.get(url, headers=headers, verify=not self.hub.config.get("insecure", False))
        status = getattr(resp, "status_code", 0) or 0
        if status == 200:
            try:
                payload = resp.json() or {}
                if not isinstance(payload, dict):
                    self.last_error = "Invalid component version payload"
                    return status, None
                meta = payload.get("_meta")
                if not isinstance(meta, dict):
                    self.last_error = "Missing _meta in component version payload"
                    return status, None
                links_node = meta.get("links")
                if not isinstance(links_node, list):
                    self.last_error = "Missing links in component version payload"
                    return status, None
                origins_href: str | None = None
                for link in links_node:
                    if isinstance(link, dict) and link.get("rel") == "origins":
                        href_val = link.get("href")
                        if isinstance(href_val, str):
                            origins_href = href_val
                            break
                if not origins_href:
                    self.last_error = "Origins link not found in component version payload"
                    return status, None

                resp = self.session.get(origins_href, headers=headers, verify=not self.hub.config.get("insecure", False))
                status = getattr(resp, "status_code", 0) or 0
                if status != 200:
                    return status, None
                origins_resp = resp.json() or {}
                if not isinstance(origins_resp, dict):
                    return status, None
                items_node = origins_resp.get("items")
                items_list: list[Any] = items_node if isinstance(items_node, list) else []
                first_item: dict[str, Any] | None = None
                for item in items_list:
                    if not isinstance(item, dict):
                        continue
                    if first_item is None:
                        first_item = item
                    # If vendor is specified, match it against originName (case-insensitive)
                    vendor = component.get("vendor")
                    if isinstance(vendor, str) and vendor:
                        origin_name = item.get("originName")
                        if isinstance(origin_name, str) and origin_name.lower() == vendor.lower():
                            return status, item
                # No vendor provided or no match found; fall back to first origin if available
                return status, first_item
            except Exception:
                self._debug("Failed to parse origins response", {"href": href})
                self.last_error = "Failed to parse origins response"
        else:
            self._debug("Failed to fetch origins", {"href": href})
            self.last_error = "Failed to fetch origins"
        return status, None
