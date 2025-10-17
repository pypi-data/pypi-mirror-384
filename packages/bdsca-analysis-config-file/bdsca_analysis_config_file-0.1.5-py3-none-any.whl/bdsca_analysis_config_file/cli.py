from __future__ import annotations

import argparse
import json
import shutil
import sys
import textwrap
from pathlib import Path

import yaml

from . import __version__
from .remediator import BlackDuckRemediator
from .schema import validate_config


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="bdsca-config",
        description="BDSCA analysis configuration file utilities.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"bdsca-analysis-config-file {__version__}",
        help="Show version and exit.",
    )

    sub = parser.add_subparsers(dest="command", required=True)

    p_add_components = sub.add_parser("add-components", help="Add missing components from componentAdditions to BOM for each project in the config.")
    p_add_components.add_argument("config", type=Path, help="Path to YAML config file.")
    p_add_components.add_argument("--base-url", dest="base_url", help="Black Duck base URL")
    p_add_components.add_argument("--api-token", dest="api_token", help="Black Duck API token")
    p_add_components.add_argument(
        "--insecure",
        action="store_true",
        help="Disable TLS verification when connecting to Black Duck",
    )
    p_add_components.add_argument(
        "--verbosity",
        choices=["info", "debug"],
        default="info",
        help="Output level: info (default) or debug",
    )
    p_add_components.add_argument(
        "--dryrun",
        action="store_true",
        help="Do not make changes; print current vs new values that would be applied",
    )

    p_validate = sub.add_parser("validate", help="Validate a YAML configuration file exists and is parseable.")
    p_validate.add_argument("config", type=Path, help="Path to YAML config file.")
    p_validate.add_argument(
        "--output",
        choices=["yaml", "json", "summary"],
        help=("If provided and the file is valid, prints the content in the chosen format: " "yaml|json|summary. Printed to stdout."),
    )
    p_validate.add_argument(
        "--target",
        action="store_true",
        help=("If set and the file is valid, prints the effective change target (Project)"),
    )

    p_remediate = sub.add_parser(
        "remediate",
        help=("Validate a YAML configuration file and perform remediation using BlackDuckRemediator."),
    )
    p_remediate.add_argument("config", type=Path, help="Path to YAML config file.")
    # Optional connection parameters for constructing a Hub when not injecting one
    p_remediate.add_argument("--base-url", dest="base_url", help="Black Duck base URL")
    p_remediate.add_argument("--api-token", dest="api_token", help="Black Duck API token")
    p_remediate.add_argument(
        "--insecure",
        action="store_true",
        help="Disable TLS verification when connecting to Black Duck",
    )
    p_remediate.add_argument(
        "--verbosity",
        choices=["info", "debug"],
        default="info",
        help="Output level for remediation: info (default) or debug",
    )
    p_remediate.add_argument(
        "--dryrun",
        action="store_true",
        help="Do not make changes; print current vs new values that would be applied",
    )

    p_overwrite = sub.add_parser(
        "overwrite",
        help=("Validate a YAML configuration file and overwrite remediation for matching vulnerabilities " "(ignores vendor/origin/sha constraints)."),
    )
    p_overwrite.add_argument("config", type=Path, help="Path to YAML config file.")
    p_overwrite.add_argument("--base-url", dest="base_url", help="Black Duck base URL")
    p_overwrite.add_argument("--api-token", dest="api_token", help="Black Duck API token")
    p_overwrite.add_argument(
        "--insecure",
        action="store_true",
        help="Disable TLS verification when connecting to Black Duck",
    )
    p_overwrite.add_argument(
        "--verbosity",
        choices=["info", "debug"],
        default="info",
        help="Output level for overwrite: info (default) or debug",
    )
    p_overwrite.add_argument(
        "--dryrun",
        action="store_true",
        help="Do not make changes; print current vs new values that would be applied",
    )

    return parser


def cmd_validate(config: Path, output: str | None = None, target: bool = False) -> int:
    if not config.exists():
        print(f"Error: file not found: {config}", file=sys.stderr)
        return 2
    try:
        with config.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        print(f"Invalid YAML: {e}", file=sys.stderr)
        return 3
    except OSError as e:
        print(f"Error reading file: {e}", file=sys.stderr)
        return 4
    # Schema validation
    errors = validate_config(data)
    if errors:
        print("Schema validation failed:", file=sys.stderr)

        def format_table(rows: list[tuple[str, str]]) -> str:
            # Determine target width
            total = shutil.get_terminal_size(fallback=(100, 24)).columns
            total = max(60, min(total, 120))
            header_loc, header_err = "Location", "Error"
            # Compute column widths
            max_loc_len = max([len(header_loc)] + [len(r[0]) for r in rows])
            loc_w = min(max(12, max_loc_len), int(total * 0.35))
            err_w = total - (3 + 2 + loc_w + 3)  # separators and spaces
            err_w = max(20, err_w)

            def wrap_cell(text: str, width: int) -> list[str]:
                return textwrap.wrap(text, width=width) or [""]

            sep = "+" + "-" * (loc_w + 2) + "+" + "-" * (err_w + 2) + "+"
            out = [sep, f"| {header_loc:<{loc_w}} | {header_err:<{err_w}} |", sep]
            for loc, msg in rows:
                loc_lines = wrap_cell(loc, loc_w)
                msg_lines = wrap_cell(msg, err_w)
                lines = max(len(loc_lines), len(msg_lines))
                for i in range(lines):
                    loc_part = loc_lines[i] if i < len(loc_lines) else ""
                    msg_part = msg_lines[i] if i < len(msg_lines) else ""
                    out.append(f"| {loc_part:<{loc_w}} | {msg_part:<{err_w}} |")
            out.append(sep)
            return "\n".join(out)

        # Split "path: message" pairs
        table_rows: list[tuple[str, str]] = []
        for error in errors:
            if ": " in error:
                loc, msg = error.split(": ", 1)
            else:
                loc, msg = "<unknown>", error
            table_rows.append((loc, msg))

        print(format_table(table_rows), file=sys.stderr)
        return 5
    print(f"Valid YAML (schema v1): {config}")

    # Optional pretty output
    if output:
        if output == "yaml":
            text = yaml.safe_dump(data, sort_keys=False, allow_unicode=True)
            print(text, end="")
        elif output == "json":
            print(json.dumps(data, indent=2, ensure_ascii=False))
        elif output == "summary":
            print(render_summary(data, include_target=target))
    elif target:
        print(compute_target_line(data))
    return 0


def _load_and_validate_config(path: Path) -> tuple[dict, list[str]]:
    try:
        with path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as exc:
        return ({}, [f"Invalid YAML: {exc}"])
    except OSError as exc:
        return ({}, [f"Error reading file: {exc}"])
    errors = validate_config(data)
    return (data, errors)


def cmd_remediate(
    config: Path,
    base_url: str | None,
    api_token: str | None,
    insecure: bool,
    verbosity: str,
    dryrun: bool = False,
) -> int:
    if not config.exists():
        print(f"Error: file not found: {config}", file=sys.stderr)
        return 2
    data, errors = _load_and_validate_config(config)
    if errors:
        print("Schema validation failed:", file=sys.stderr)
        for e in errors:
            print(f"- {e}", file=sys.stderr)
        return 5

    # Build change target context (now an array of {project:{name,version}})
    ct_list = data.get("changeTarget") or []
    projects = []
    for entry in ct_list:
        if not isinstance(entry, dict):
            continue
        proj = entry.get("project") or {}
        projects.append({"name": proj.get("name"), "version": proj.get("version")})

    if not (base_url and api_token):
        print(
            "Remediation requires credentials: provide --base-url and --api-token",
            file=sys.stderr,
        )
        return 7
    try:
        remediator = BlackDuckRemediator(
            base_url=base_url,
            api_token=api_token,
            insecure=insecure,
            output_level=verbosity,
        )
    except Exception as ex:
        print(f"Failed to initialize remediator: {ex}", file=sys.stderr)
        return 7

    vts = data.get("vulnerabilityTriages") or []
    overall_ok = True
    for target in projects:
        project_name = str(target.get("name") or "")
        project_version = str(target.get("version") or "")

        # Only remediate vulnerabilities
        for tri in vts:
            comp = tri.get("component") or {}
            triages = tri.get("triages") or []
            ok = remediator.remediate_component_vulnerabilities(
                project_name,
                project_version,
                comp,
                triages,
                changed_by="bdsca-cli",
                dryrun=dryrun,
            )
            if not ok:
                overall_ok = False

    if overall_ok:
        if dryrun:
            print("Dry-run completed: no changes were made. Displayed what would be updated.")
        else:
            print("Remediation completed successfully.")
        return 0
    reason = getattr(remediator, "last_error", None)
    if reason:
        print(f"Remediation failed: {reason}", file=sys.stderr)
    else:
        print("Remediation did not complete successfully.", file=sys.stderr)
    return 8


def render_summary(data: dict, include_target: bool = False) -> str:
    lines: list[str] = []
    spec = data.get("specVersion")
    if spec:
        lines.append(f"specVersion: {spec}")
    if include_target:
        # lowercase to match summary style
        lines.append(compute_summary_target_line(data))
    # overrides
    overrides = data.get("overrides") or []
    lines.append(f"overrides: {len(overrides)}")
    for i, ov in enumerate(overrides, 1):
        comp = ov.get("component", {}) if isinstance(ov, dict) else {}
        ident = comp.get("purl") or comp.get("name") or "<unknown>"
        change = ov.get("newVersion")
        files = ov.get("files") or []
        lines.append(f"  {i}. component: {ident} | change: {change or '-'} | files: {len(files)}")
    # vulnerabilityTriages
    vts = data.get("vulnerabilityTriages") or []
    lines.append(f"vulnerabilityTriages: {len(vts)}")
    for i, tri in enumerate(vts, 1):
        comp = tri.get("component", {}) if isinstance(tri, dict) else {}
        ident = comp.get("purl") or comp.get("name") or "<unknown>"
        triages = tri.get("triages") or []
        lines.append(f"  {i}. component: {ident} | triages: {len(triages)}")
    # componentAdditions
    adds = data.get("componentAdditions") or []
    lines.append(f"componentAdditions: {len(adds)}")
    for i, add in enumerate(adds, 1):
        comp = add.get("component", {}) if isinstance(add, dict) else {}
        ident = comp.get("purl") or comp.get("name") or "<unknown>"
        files = add.get("files") or []
        lines.append(f"  {i}. component: {ident} | files: {len(files)}")
    return "\n".join(lines) + ("\n" if lines else "")


def compute_target_line(data: dict) -> str:
    # Title case for default output line
    ct_list = data.get("changeTarget") or []
    if not ct_list:
        return "Target: not specified"
    parts = []
    for entry in ct_list:
        proj = (entry or {}).get("project") or {}
        parts.append(f"Project '{proj.get('name')}' version '{proj.get('version')}'")
    return "Target: " + "; ".join(parts)


def compute_summary_target_line(data: dict) -> str:
    # Lowercase variant for summary block
    ct_list = data.get("changeTarget") or []
    if not ct_list:
        return "target: not specified"
    if len(ct_list) == 1:
        proj = (ct_list[0] or {}).get("project") or {}
        return f"target: project name='{proj.get('name')}' version='{proj.get('version')}'"
    # Multiple projects: list each on its own line
    lines = ["target:"]
    for _, entry in enumerate(ct_list, 1):
        proj = (entry or {}).get("project") or {}
        lines.append(f"  - project name='{proj.get('name')}' version='{proj.get('version')}'")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "validate":
        return cmd_validate(args.config, getattr(args, "output", None), getattr(args, "target", False))
    if args.command == "remediate":
        return cmd_remediate(args.config, args.base_url, args.api_token, args.insecure, args.verbosity, args.dryrun)
    if args.command == "overwrite":
        return cmd_overwrite(args.config, args.base_url, args.api_token, args.insecure, args.verbosity, args.dryrun)
    if args.command == "add-components":
        return cmd_add_components(args.config, args.base_url, args.api_token, args.insecure, args.verbosity, args.dryrun)

    parser.print_help()
    return 0


def cmd_add_components(
    config: Path,
    base_url: str | None,
    api_token: str | None,
    insecure: bool,
    verbosity: str,
    dryrun: bool = False,
) -> int:
    if not config.exists():
        print(f"Error: file not found: {config}", file=sys.stderr)
        return 2
    data, errors = _load_and_validate_config(config)
    if errors:
        print("Schema validation failed:", file=sys.stderr)
        for e in errors:
            print(f"- {e}", file=sys.stderr)
        return 5

    ct_list = data.get("changeTarget") or []
    projects = []
    for entry in ct_list:
        if not isinstance(entry, dict):
            continue
        proj = entry.get("project") or {}
        projects.append({"name": proj.get("name"), "version": proj.get("version")})

    if not (base_url and api_token):
        print(
            "Add-components requires credentials: provide --base-url and --api-token",
            file=sys.stderr,
        )
        return 7
    try:
        remediator = BlackDuckRemediator(
            base_url=base_url,
            api_token=api_token,
            insecure=insecure,
            output_level=verbosity,
        )
    except Exception as ex:
        print(f"Failed to initialize remediator: {ex}", file=sys.stderr)
        return 7

    component_additions = data.get("componentAdditions") or []
    if not component_additions:
        print("No componentAdditions found; nothing to add.")
        return 0

    overall_ok = True
    for target in projects:
        project_name = str(target.get("name") or "")
        project_version = str(target.get("version") or "")
        add_results = remediator.add_missing_components_from_config(
            project_name,
            project_version,
            component_additions,
            dryrun=dryrun,
        )
        for res in add_results:
            comp = res.get("component", {})
            ident = comp.get("purl") or comp.get("name") or "<unknown>"
            if res.get("added"):
                if res.get("result") and res["result"].get("status") == "DRY-RUN":
                    print(f"Dry-run: would add component to BOM: {comp}")
                else:
                    print(f"Added component to BOM: {ident}")
            else:
                print(f"Component already exists or failed to add: {ident}")
            if res.get("result") is None and getattr(remediator, "last_error", None):
                print(f"  Error: {remediator.last_error}", file=sys.stderr)
            if not res.get("added"):
                overall_ok = False

    if overall_ok:
        print("All components added successfully.")
        return 0
    else:
        print("Some components failed to add or already existed.", file=sys.stderr)
        return 8


def cmd_overwrite(
    config: Path,
    base_url: str | None,
    api_token: str | None,
    insecure: bool,
    verbosity: str,
    dryrun: bool = False,
) -> int:
    if not config.exists():
        print(f"Error: file not found: {config}", file=sys.stderr)
        return 2
    data, errors = _load_and_validate_config(config)
    if errors:
        print("Schema validation failed:", file=sys.stderr)
        for e in errors:
            print(f"- {e}", file=sys.stderr)
        return 5

    ct_list = data.get("changeTarget") or []
    projects = []
    for entry in ct_list:
        if not isinstance(entry, dict):
            continue
        proj = entry.get("project") or {}
        projects.append({"name": proj.get("name"), "version": proj.get("version")})

    if not (base_url and api_token):
        print(
            "Overwrite requires credentials: provide --base-url and --api-token",
            file=sys.stderr,
        )
        return 7
    try:
        remediator = BlackDuckRemediator(
            base_url=base_url,
            api_token=api_token,
            insecure=insecure,
            output_level=verbosity,
        )
    except Exception as ex:
        print(f"Failed to initialize remediator: {ex}", file=sys.stderr)
        return 7

    vts = data.get("overrides") or []
    overall_ok = True
    reasons = []
    for target in projects:
        project_name = str(target.get("name") or "")
        project_version = str(target.get("version") or "")
        for tri in vts:
            comp = tri.get("component") or {}
            new_version = tri.get("newVersion")
            ok = remediator.overwrite_component_version(
                project_name,
                project_version,
                comp,
                new_version,
                changed_by="bdsca-cli",
                dryrun=dryrun,
            )
            if not ok:
                overall_ok = False
                reasons.append(getattr(remediator, "last_error", None))

    if overall_ok:
        if dryrun:
            print("Dry-run completed: no changes were made. Displayed what would be updated.")
        else:
            print("Overwrite completed successfully.")
        return 0
    if reasons:
        for r in reasons:
            print(f"Overwrite failed: {r}", file=sys.stderr)
    return 8
