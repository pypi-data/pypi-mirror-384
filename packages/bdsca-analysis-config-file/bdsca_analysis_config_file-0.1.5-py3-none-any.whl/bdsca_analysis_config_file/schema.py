from __future__ import annotations

from typing import Any

from jsonschema import Draft7Validator
from jsonschema.exceptions import ValidationError

SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "https://example.invalid/bdsca-analysis-config.schema.json",
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "specVersion": {
            "type": "string",
            "const": "1",
            "description": "Schema version; must be '1'",
        },
        "overrides": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "component": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string", "maxLength": 255},
                            "vendor": {"type": "string", "maxLength": 255},
                            "version": {"type": "string", "maxLength": 255},
                            "purl": {"type": "string", "maxLength": 255},
                            "codetype": {"type": "string", "maxLength": 255},
                        },
                        "additionalProperties": False,
                        "oneOf": [
                            {"required": ["name"]},
                            {"required": ["purl"]},
                        ],
                    },
                    "files": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "path": {"type": "string", "maxLength": 5000},
                                "sha1": {"type": "string", "minLength": 40, "maxLength": 40},
                            },
                            "additionalProperties": False,
                            "oneOf": [
                                {"required": ["path"]},
                                {"required": ["sha1"]},
                            ],
                        },
                        "minItems": 1,
                    },
                    "newVersion": {"type": "string", "maxLength": 255},
                    "forceVersion": {"type": "boolean"},
                },
                "required": ["component"],
                "anyOf": [{"required": ["newVersion"]}],
            },
        },
        "vulnerabilityTriages": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "component": {
                        "type": "object",
                        "properties": {
                            "purl": {"type": "string", "maxLength": 255},
                            "name": {"type": "string", "maxLength": 255},
                            "version": {"type": "string", "maxLength": 255},
                            "vendor": {"type": "string", "maxLength": 255},
                            "origin": {"type": "string", "maxLength": 255},
                            "sha": {"type": "string", "maxLength": 255},
                            "codetype": {"type": "string", "maxLength": 255},
                        },
                        "additionalProperties": False,
                        "oneOf": [
                            {"required": ["purl"]},
                            {"required": ["name", "version"]},
                            {"required": ["sha"]},
                        ],
                    },
                    "triages": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "additionalProperties": False,
                            "properties": {
                                "bdsa": {"type": "string"},
                                "cve": {"type": "string"},
                                "resolution": {
                                    "enum": [
                                        "PATCHED",
                                        "NOT_AFFECTED",
                                        "IGNORED",
                                        "MITIGATED",
                                        "NEW",
                                    ]
                                },
                                "comment": {"type": "string", "maxLength": 500},
                            },
                            "oneOf": [
                                {"required": ["bdsa"]},
                                {"required": ["cve"]},
                            ],
                        },
                        "minItems": 1,
                    },
                },
                "required": ["component", "triages"],
            },
        },
        "componentAdditions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "component": {
                        "type": "object",
                        "properties": {
                            "purl": {"type": "string", "maxLength": 255},
                            "name": {"type": "string", "maxLength": 255},
                            "version": {"type": "string", "maxLength": 255},
                            "vendor": {"type": "string", "maxLength": 255},
                        },
                        "oneOf": [
                            {"required": ["purl"]},
                            {"required": ["name"]},
                        ],
                        "additionalProperties": False,
                    }
                },
                "required": ["component"],
                "additionalProperties": False,
            },
            "additionalProperties": False,
        },
        "changeTarget": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "project": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "name": {"type": "string", "maxLength": 255},
                            "version": {"type": "string", "maxLength": 255},
                        },
                        "required": ["name", "version"],
                    }
                },
                "required": ["project"],
            },
            "minItems": 1,
        },
    },
    "required": ["specVersion", "changeTarget"],
}


_validator = Draft7Validator(SCHEMA)


def validate_config(data: Any) -> list[str]:
    """Validate the provided data against the schema.

    Returns a list of error messages; empty list means valid.
    """

    def path_str(err: ValidationError) -> str:
        p = "".join(f"[{i!r}]" if isinstance(i, int) else f".{i}" for i in err.absolute_path)
        return p[1:] if p.startswith(".") else (p or "<root>")

    def join_set(reqs: list[str]) -> str:
        if not reqs:
            return ""
        if len(reqs) == 1:
            return reqs[0]
        return "(" + ", ".join(reqs) + ")"

    def friendly(err: ValidationError) -> str:
        # Expand anyOf/oneOf into explicit required-set messages
        if err.validator in {"anyOf", "oneOf"} and err.context:
            required_sets: list[list[str]] = []
            for sub in err.context:
                if sub.validator == "required":
                    if isinstance(sub.validator_value, list):
                        reqs = [str(x) for x in sub.validator_value]
                    else:
                        reqs = []
                    if reqs:
                        required_sets.append(reqs)
            if required_sets:
                options = ", ".join(join_set(rs) for rs in required_sets)
                kind = "one of" if err.validator == "oneOf" else "any of"
                return f"Must include {kind}: {options}"
            # Fall back to default message
        if err.validator == "required":
            # Prefer the property named in the message
            return err.message.replace(" is a required property", " is missing")
        if err.validator == "additionalProperties":
            # Custom message for extra fields in componentAdditions
            if ".componentAdditions" in str(err.absolute_path):
                return "componentAdditions.component only allows 'purl', 'name', 'version', 'vendor'; additional " f"properties are not permitted: {err.message}"
            return err.message
        return err.message

    errors: list[str] = []
    for err in _validator.iter_errors(data):
        errors.append(str(f"{path_str(err)}: {friendly(err)}"))
    return list(errors)
