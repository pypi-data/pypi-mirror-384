from __future__ import annotations

from typing import Any

from .remediator_base import RemediatorBase


class RemediateOps(RemediatorBase):
    def __createComment(self, reason: str, comment: str, dismissedBy: str) -> str:  # noqa: N802 (keep name for compatibility)
        policyComment = ""
        if reason:
            policyComment = f"Reason to dismiss: {reason}\n"
        if comment:
            policyComment = f"{policyComment}Comments: {comment}\n"
        if dismissedBy:
            policyComment = f"{policyComment}Changed by: {dismissedBy}"
        return policyComment

    def __remediate(  # noqa: N802 (private name used in tests)
        self,
        projectName: str,
        projectVersionName: str,
        componentName: str,
        componentVersionName: str,
        componentOriginID: str | None,
        vulnerabilityName: str,
        remediatedBy: str,
        dismissStatus: str,
        remediationStatus: str,
        remediationComment: str,
        vendor: str | None = None,
        sha: str | None = None,
        *,
        dryrun: bool = False,
    ) -> bool:
        self._debug(
            "remediate with params:",
            projectName,
            projectVersionName,
            componentName,
            componentVersionName,
            sha,
            vulnerabilityName,
            remediationStatus,
            remediationComment,
        )
        parameters = {"q": f"name:{projectName}"}
        projects = self.hub.get_projects(limit=1, parameters=parameters)
        if not projects or not projects.get("items"):
            self.last_error = f"Project not found: {projectName}"
            return False
        for project in projects["items"]:
            versions = self._call_project_versions(project, projectVersionName)
            if not versions or not versions.get("items"):
                self.last_error = f"Version not found: {projectVersionName} (project {projectName})"
                continue
            for version in versions["items"]:
                headers = self.hub.get_headers()
                headers["Accept"] = "application/vnd.blackducksoftware.bill-of-materials-6+json"
                parameters = {"q": f"componentName:{componentName},vulnerabilityName:{vulnerabilityName}"}
                url = version["_meta"]["href"] + "/vulnerable-bom-components" + self.hub._get_parameter_string(parameters)
                response = self.session.get(
                    url,
                    headers=headers,
                    verify=not self.hub.config["insecure"],
                )
                if response.status_code == 200:
                    vulnComps = response.json()
                    if vulnComps["totalCount"] > 0:
                        matched = False
                        for vulnComp in vulnComps["items"]:
                            if sha:
                                if not self._component_version_matches_sha(vulnComp, sha, version["_meta"]["href"]):
                                    self._debug("SHA mismatch; skipping item", {"expected": sha})
                                    continue
                                else:
                                    # SHA matched; no need to check name/version/origin
                                    url = vulnComp["_meta"]["href"]
                            else:
                                if vulnComp["componentName"] == componentName and vulnComp["componentVersionName"] == componentVersionName:
                                    if componentOriginID and vulnComp["componentVersionOriginId"] == componentOriginID:
                                        if vendor:
                                            if vulnComp.get("componentVersionOriginName") != vendor:
                                                self._debug(f"Vendor mismatch: expected {vendor}, got {vulnComp.get('componentVersionOriginName')}")
                                                continue
                                        url = vulnComp["_meta"]["href"]
                                    elif not componentOriginID:
                                        url = vulnComp["_meta"]["href"]
                                    else:
                                        continue
                            matched = True
                            if url:
                                response = self.session.get(
                                    url,
                                    headers=headers,
                                    verify=not self.hub.config["insecure"],
                                )
                                if response.status_code == 200:
                                    current: dict[str, Any] = {}
                                    try:
                                        current = response.json() or {}
                                    except Exception:
                                        current = {}
                                    remediationData: dict[str, Any] = {}
                                    remediationData["comment"] = self.__createComment(dismissStatus, remediationComment, remediatedBy)
                                    remediationData["remediationStatus"] = remediationStatus

                                    if dryrun:
                                        cur_status = current.get("remediationStatus", "<unknown>")
                                        cur_comment = current.get("comment", "<none>")
                                        new_status = remediationData["remediationStatus"]
                                        new_comment = remediationData["comment"]

                                        status_changed = cur_status != new_status
                                        comment_changed = cur_comment != new_comment

                                        lines = [
                                            "DRY-RUN: Would update remediation",
                                            f"  Project:     {projectName}",
                                            f"  Version:     {projectVersionName}",
                                            (f"  Component:   {vulnComp.get('componentName', '')} " f"({vulnComp.get('componentVersionName', '')})"),
                                            f"  Vulnerability: {vulnerabilityName}",
                                            "  Current:",
                                            f"    - status:  {cur_status}",
                                            f"    - comment: {cur_comment}",
                                            "  New:",
                                            f"    - status:  {new_status}",
                                            f"    - comment: {new_comment}",
                                        ]
                                        if not status_changed and not comment_changed:
                                            lines.append("  Note: No change needed (already up-to-date).")
                                        self._info("\n".join(lines))
                                        return True

                                    self._info(
                                        "Updating remediation status",
                                        {
                                            "project": projectName,
                                            "version": projectVersionName,
                                            "component": vulnComp.get("componentName", ""),
                                            "componentVersion": vulnComp.get("componentVersionName", ""),
                                            "vulnerability": vulnerabilityName,
                                            "status": remediationStatus,
                                        },
                                    )
                                    response = self.session.put(
                                        url,
                                        headers=headers,
                                        json=remediationData,
                                        verify=not self.hub.config["insecure"],
                                    )
                                    if response.status_code == 202:
                                        self._info(
                                            "Remediation succeeded",
                                            {
                                                "component": vulnComp.get("componentName", ""),
                                                "componentVersion": vulnComp.get("componentVersionName", ""),
                                                "vulnerability": vulnerabilityName,
                                            },
                                        )
                                        return True
                                    else:
                                        body = getattr(response, "text", "") or getattr(response, "content", b"")
                                        msg = "Remediation status update failed " f"({response.status_code}): {body}"
                                        self._error(msg)
                                        self.last_error = msg
                                else:
                                    msg = "Failed to fetch vulnerable BOM item " f"({response.status_code})"
                                    self._error(msg)
                                    self.last_error = msg
                        if not matched:
                            if sha:
                                self._error(
                                    "No matching vulnerable component found with the specified sha",
                                )
                            else:
                                self._error(
                                    "No matching vulnerable component found with the specified " "name, version, and origin",
                                )
                    else:
                        if sha:
                            msg = f"No vulnerable component found with sha: {sha} " f"and vulnerability: {vulnerabilityName}"
                        else:
                            msg = f"No vulnerable component found with name: {componentName} " f"and vulnerability: {vulnerabilityName}"
                        self._error(msg)
                        self.last_error = msg
                else:
                    self.last_error = f"Query vulnerable components failed ({response.status_code})"
        return False

    def remediate_component_vulnerabilities(
        self,
        project_name: str,
        project_version: str,
        component: dict,
        triages: list[dict],
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
        if not triages:
            self._info("No triages to remediate for component", component)
            return True

        comp_vendor = component.get("vendor") or None
        comp_sha = component.get("sha") or None

        comp_name, comp_version_url, comp_version, comp_origin_url, comp_origin_id = self.resolve_component_identity(component)

        if not comp_sha:
            if not comp_name or not comp_version:
                self.last_error = "Component name/version could not be determined"
                return False

        overall = True
        for t in triages:
            if not isinstance(t, dict):
                continue
            vuln = t.get("cve") or t.get("bdsa")
            if not vuln:
                continue
            resolution = t.get("resolution") or ""
            comment = t.get("comment") or ""
            ok = self.__remediate(
                project_name,
                project_version,
                comp_name,
                comp_version,
                comp_origin_id,
                vuln,
                changed_by,
                resolution,
                resolution,
                comment,
                vendor=comp_vendor,
                sha=comp_sha,
                dryrun=dryrun,
            )
            if not ok:
                overall = False

        return overall
