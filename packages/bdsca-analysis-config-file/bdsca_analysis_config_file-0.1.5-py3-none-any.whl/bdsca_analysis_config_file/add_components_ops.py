from __future__ import annotations

from .remediator_base import RemediatorBase


class AddComponentsOps(RemediatorBase):
    def check_component_exists_in_bom(
        self,
        project_name: str,
        project_version_name: str,
        component_name: str,
        component_version_name: str,
    ) -> bool:
        ids = self.get_project_and_version_ids(project_name, project_version_name)
        if not ids:
            self._error(f"Could not resolve project/version IDs for {project_name}/{project_version_name}: {self.last_error}")
            return False
        project_id, project_version_id = ids
        base = self._base_url()
        url = f"{base}/api/projects/{project_id}/versions/{project_version_id}/components"
        headers = self.hub.get_headers()
        headers["Accept"] = "application/vnd.blackducksoftware.bill-of-materials-6+json"
        self._info("Fetching BOM components", {"url": url})
        response = self.session.get(
            url,
            headers=headers,
            verify=not self.hub.config["insecure"],
        )
        if response.status_code == 200:
            try:
                bom_data = response.json()
                for item in bom_data.get("items", []):
                    if item.get("componentName") == component_name and item.get("componentVersion") == component_version_name:
                        return True
                return False
            except Exception:
                self.last_error = "Failed to parse BOM components response JSON"
                return False
        body = getattr(response, "text", "") or getattr(response, "content", b"")
        self.last_error = f"Fetch BOM components failed ({response.status_code}): {body}"
        self._error(self.last_error)
        return False

    def add_missing_components_from_config(
        self,
        project_name: str,
        project_version_name: str,
        component_additions: list[dict],
        dryrun: bool = False,
    ) -> list[dict]:
        ids = self.get_project_and_version_ids(project_name, project_version_name)
        if not ids:
            self._error(f"Could not resolve project/version IDs for {project_name}/{project_version_name}: {self.last_error}")
            return []
        project_id, project_version_id = ids
        results = []
        for entry in component_additions:
            component = entry.get("component", {})
            # Resolve identity (uses PURL or name/version) and check if already present
            name, version_url, versionNumber, origin_url, originId = self.resolve_component_identity(component)

            if name:
                exists = self.check_component_exists_in_bom(project_name, project_version_name, name, versionNumber)
                if exists:
                    self._info(f"Component {name} ({versionNumber or '<any>'}) already exists in BOM, skipping.")
                    results.append({"component": component, "added": False, "result": None})
                    continue

            # Build payload: prefer PURL-derived or name/version-derived version URL; fallback to resolved version string
            version_ref = None
            if isinstance(origin_url, str) and origin_url:
                version_ref = origin_url
            else:
                # No PURL: try resolving from /api/components using name/version
                if name:
                    version_ref = self.get_component_by_name_version(name, versionNumber)
            if not version_ref:
                self._error(f"Could not resolve component version reference for {component}, skipping addition.")
                results.append({"component": component, "added": False, "result": None})
                continue
            self._debug(f"Resolved component version reference: {version_ref}")
            component_payload = {"component": version_ref, "componentModification": "add"}
            if component.get("vendor"):
                status, origin = self.fetch_origins(version_ref, component)
                if origin:
                    component_payload["component"] = origin.get("_meta", {}).get("href", version_ref)
            if dryrun:
                self._info(f"Dry-run: would add component to BOM: {component_payload}")
                results.append({"component": component, "added": True, "result": {"status": "DRY-RUN"}})
            else:
                result = self.add_component_to_bom(project_id, project_version_id, component_payload)
                results.append({"component": component, "added": bool(result), "result": result})
        return results

    def add_component_to_bom(
        self,
        project_id: str,
        project_version_id: str,
        component_payload: dict,
    ) -> dict | None:
        base = self._base_url()
        url = f"{base}/api/projects/{project_id}/versions/{project_version_id}/components"
        headers = self.hub.get_headers()
        headers["Content-Type"] = "application/vnd.blackducksoftware.bill-of-materials-6+json"
        self._info("Adding component to BOM", {"url": url, "payload": component_payload})
        response = self.session.post(
            url,
            headers=headers,
            json=component_payload,
            verify=not self.hub.config["insecure"],
        )
        if response.status_code in (200, 201, 202):
            return {"status": "OK"}
        else:
            body = getattr(response, "text", "") or getattr(response, "content", b"")
            self.last_error = f"Add component to BOM failed ({response.status_code}): {body}"
            self._error(self.last_error)
            return None
