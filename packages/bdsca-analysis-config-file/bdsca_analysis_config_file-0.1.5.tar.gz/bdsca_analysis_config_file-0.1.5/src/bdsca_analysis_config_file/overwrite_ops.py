from __future__ import annotations

from typing import Any

from .remediator_base import RemediatorBase


class OverwriteOps(RemediatorBase):
    def overwrite_component_version(
        self,
        project_name: str,
        project_version: str,
        component: dict,
        new_version: str | None = None,
        *,
        changed_by: str = "bdsca-cli",
        dryrun: bool = False,
    ) -> bool:
        self.last_error = None
        if not project_name or not project_version:
            self.last_error = "Project name/version required"
            return False
        if not isinstance(component, dict):
            self.last_error = "Component must be a dict"
            return False

        comp_name, comp_version_url, comp_version_number, comp_origin_url, comp_origin_id = self.resolve_component_identity(component)

        ids = self.get_project_and_version_ids(project_name, project_version)
        if not ids:
            self._error(f"Could not resolve project/version IDs for {project_name}/{project_version}: {self.last_error}")
            return False
        project_id, version_id = ids

        headers = self.hub.get_headers()
        headers["Accept"] = "application/vnd.blackducksoftware.bill-of-materials-6+json"
        base = self._base_url()
        q = f"componentOrVersionName:{comp_name}"
        comp_url = f"{base}/api/projects/{project_id}/versions/{version_id}/components?q={q}"
        self._debug(f"Fetching BOM components for overwrite check: {comp_url}")
        comp_resp = self.session.get(comp_url, headers=headers, verify=not self.hub.config["insecure"])
        if comp_resp.status_code != 200:
            self.last_error = f"Fetch BOM components failed ({comp_resp.status_code})"
            return False
        bom = comp_resp.json() or {}
        bom_items = bom.get("items") or []
        matched_comps: list[dict[str, Any]] = []
        for i in bom_items:
            self._debug(f"Checking BOM component: {i.get('componentName')} (version: {i.get('componentVersionName')})")
            if i.get("componentName") == comp_name:
                self._debug(f"{i.get('componentVersionName')} == {comp_version_number}")
                if i.get("componentVersionName") is None and comp_version_number == "":
                    matched_comps.append(i)
                else:
                    if comp_version_number and i.get("componentVersionName") == comp_version_number:
                        matched_comps.append(i)
        if not matched_comps:
            self.last_error = f"Component '{comp_name}'" f"{(' version ' + comp_version_number) if comp_version_number else ' with empty version'} " f"not found in BOM of project {project_name} and version {project_version}"
            return False

        for mc in matched_comps:
            comp_href: str | None = None
            comp_field = mc.get("component")
            if isinstance(comp_field, dict):
                comp_href = comp_field.get("_meta", {}).get("href") if isinstance(comp_field.get("_meta"), dict) else comp_field.get("href")
            elif isinstance(comp_field, str):
                comp_href = comp_field

            comp_id: str | None = None
            if isinstance(comp_href, str) and "/api/components/" in comp_href:
                try:
                    parts = comp_href.strip("/").split("/")
                    comp_id = parts[parts.index("components") + 1]
                except Exception:
                    comp_id = None
            if not comp_id:
                self._debug("Could not extract componentId from component href", {"href": comp_href})
                continue

            q_param = f"versionName:{new_version}" if new_version else None
            self._debug("Fetching versions for component", {"componentId": comp_id, "q": q_param})
            versions_payload = self.get_component_versions(
                comp_id,
                limit=50,
                sort="versionname asc",
                q=q_param,
            )
            if versions_payload:
                self._debug(f"Fetched {versions_payload.get('totalCount', 0)} versions for component ID {comp_id}")
                if versions_payload.get("totalCount", 0) == 0:
                    self.last_error = f"No component versions found for component '{comp_name}'" f"{(' with version ' + new_version) if new_version else ''}"
                    return False
                items = versions_payload.get("items") if isinstance(versions_payload, dict) else None
                if not items or not isinstance(items, list) or not items:
                    self.last_error = "Unexpected component versions payload format"
                    return False
                first_item = items[0]
                meta = first_item.get("_meta") if isinstance(first_item, dict) else None
                ver_href = meta.get("href") if isinstance(meta, dict) else None
                status, origins_resp = self.fetch_origins(ver_href or "", component)
                if status == 200 and first_item:
                    if origins_resp and isinstance(origins_resp, dict):
                        modComponent: dict[str, Any] = {}
                        modComponent["component"] = mc.get("component")
                        modComponent["componentModified"] = False
                        modComponent["componentVersion"] = ver_href
                        origin: dict[str, Any] = {}
                        origin["externalId"] = origins_resp.get("externalId")
                        origin["externalNamespace"] = origins_resp.get("externalNamespace")
                        origin["name"] = origins_resp.get("versionName")
                        origin["origin"] = origins_resp.get("_meta", {}).get("href")
                        modComponent["origins"] = [origin]
                        modComponent["usages"] = mc.get("usages", [])
                        parts = mc.get("componentVersion", "").strip("/").split("/")
                        comp_version_id = parts[parts.index("versions") + 1] if "versions" in parts else None
                        if dryrun:
                            self._info(
                                "DRY-RUN: Would overwrite component version",
                                {
                                    "project": project_name,
                                    "version": project_version,
                                    "component": comp_name,
                                    "currentVersion": comp_version_number or "<any>",
                                    "newVersion": origin.get("name") or "<unchanged>",
                                    "vendor": origin.get("externalNamespace") or "<unchanged>",
                                    "modComponent": modComponent,
                                },
                            )
                            return True
                        else:
                            headers_put = self.hub.get_headers()
                            headers_put["Content-Type"] = "application/vnd.blackducksoftware.bill-of-materials-5+json"
                            if comp_version_id is not None:
                                post_url = f"{base}/api/projects/{project_id}/versions/{version_id}/components/" f"{comp_id}/versions/{comp_version_id}"
                            else:
                                post_url = f"{base}/api/projects/{project_id}/versions/{version_id}/components/{comp_id}"
                            self._debug("Overwriting component version", {"url": post_url, "data": modComponent})
                            updateResponse = self.hub.execute_put(
                                post_url,
                                data=modComponent,
                                custom_headers=headers_put,
                            )
                            if updateResponse is not None and getattr(updateResponse, "status_code", None) in (200, 202):
                                updatedComponent = updateResponse.json() or {}
                                self._info(
                                    "Component overwrite successfully done.",
                                    {
                                        "project": project_name,
                                        "version": project_version,
                                        "component": updatedComponent.get("componentName") or comp_name,
                                        "newVersion": (updatedComponent.get("origins", [{}]) or [{}])[0].get("name") if isinstance(updatedComponent.get("origins", [{}]), list) else (new_version or "<unchanged>"),
                                        "vendor": (updatedComponent.get("origins", [{}]) or [{}])[0].get("externalNamespace") if isinstance(updatedComponent.get("origins", [{}]), list) else (new_version or "<unchanged>"),
                                    },
                                )
                                return True
                            else:
                                msg = "Component version overwrite failed (" f"{getattr(updateResponse, 'status_code', 'no-response')}" "): " f"{getattr(updateResponse, 'text', '') or getattr(updateResponse, 'content', b'')}"
                                self._error(msg)
                                self.last_error = msg
                                return False
                    else:
                        self._debug(
                            "Component vendor does not match; skipping origin",
                            {
                                "componentVendor": component.get("vendor"),
                                "originName": origins_resp.get("originName") if isinstance(origins_resp, dict) else getattr(origins_resp, "status_code", None),
                            },
                        )
                else:
                    self._debug(
                        "Failed to fetch component versions origins",
                        {"status": getattr(origins_resp, "status_code", None)},
                    )
        return True
