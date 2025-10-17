"""Library API for managing structured licenses."""

from __future__ import annotations

from typing import Any
import os
import json
import toml

from liscopelens.utils.structure import LicenseFeat, load_licenses
from liscopelens.utils.scaffold import get_resource_path
from liscopelens.api.base import regenerate_knowledge_base


__all__ = [
    "add_structured_license",
    "list_structured_licenses",
    "get_structured_license",
]


def add_structured_license(
    license_data: str | dict,
    spdx_id: str | None = None,
    override: bool = True,
    regenerate_kb: bool = False,
) -> dict[str, Any]:
    """Add or update a structured license in the system.

    This function allows users to add new structured licenses or override existing ones.
    The license data can be provided as either a JSON string or a dictionary. After adding
    the license, optionally regenerate the knowledge base to include the new license in
    compatibility inference.

    Args:
        license_data: Structured license data as JSON string or dict. Must follow the
                     LicenseFeat structure with fields like 'can', 'cannot', 'must', etc.
        spdx_id: SPDX ID for the license. If not provided, must be in license_data.
        override: If True, allows overwriting existing licenses. If False, returns error
                 if license already exists. Defaults to True.
        regenerate_kb: If True, regenerates the knowledge base after adding the license
                      to enable compatibility inference. Defaults to False.

    Returns:
        dict: A dictionary containing:
            - status: "success" or "error"
            - message: Description of the result
            - spdx_id: The SPDX ID of the added/updated license
            - file_path: Path where the license was saved
            - overridden: Boolean indicating if an existing license was overridden
            - kb_regenerated: Boolean indicating if knowledge base was regenerated

    Raises:
        ValueError: If license_data format is invalid or required fields are missing

    Example:
        >>> from liscopelens.api import add_structured_license
        >>> license_dict = {
        ...     "can": {
        ...         "modify": {"protect_scope": [], "escape_scope": []},
        ...         "distribute": {"protect_scope": [], "escape_scope": []}
        ...     },
        ...     "must": {
        ...         "include_license": {"protect_scope": [], "escape_scope": []}
        ...     },
        ...     "cannot": {}
        ... }
        >>> result = add_structured_license(license_dict, spdx_id="My-Custom-1.0")
        >>> print(result["status"])
        'success'

        >>> # Using JSON string
        >>> import json
        >>> license_json = json.dumps(license_dict)
        >>> result = add_structured_license(license_json, spdx_id="My-Custom-1.0")
    """
    try:
        # Parse license_data if it's a JSON string
        if isinstance(license_data, str):
            try:
                license_dict = json.loads(license_data)
            except json.JSONDecodeError as e:
                return {
                    "status": "error",
                    "message": f"Invalid JSON format: {str(e)}",
                    "spdx_id": spdx_id or "",
                }
        elif isinstance(license_data, dict):
            license_dict = license_data
        else:
            return {
                "status": "error",
                "message": "license_data must be either a JSON string or a dictionary",
                "spdx_id": spdx_id or "",
            }

        # Determine SPDX ID
        if spdx_id is None:
            spdx_id = license_dict.get("spdx_id")
            if not spdx_id:
                return {
                    "status": "error",
                    "message": "spdx_id must be provided either as parameter or in license_data",
                }

        # Validate SPDX ID format
        if not isinstance(spdx_id, str) or not spdx_id.strip():
            return {
                "status": "error",
                "message": "spdx_id must be a non-empty string",
                "spdx_id": spdx_id,
            }

        # Validate required fields structure
        required_modals = ["can", "cannot", "must"]
        for modal in required_modals:
            if modal not in license_dict:
                license_dict[modal] = {}
            if not isinstance(license_dict[modal], dict):
                return {
                    "status": "error",
                    "message": f"Field '{modal}' must be a dictionary",
                    "spdx_id": spdx_id,
                }

        # Validate action structure
        for modal in required_modals:
            for action_name, action_data in license_dict[modal].items():
                if not isinstance(action_data, dict):
                    return {
                        "status": "error",
                        "message": f"Action '{modal}.{action_name}' must be a dictionary",
                        "spdx_id": spdx_id,
                    }
                if "protect_scope" not in action_data:
                    action_data["protect_scope"] = []
                if "escape_scope" not in action_data:
                    action_data["escape_scope"] = []

        # Check if license already exists
        licenses_path = get_resource_path().joinpath("licenses")
        license_file_path = licenses_path.joinpath(f"{spdx_id}.toml")

        overridden = False
        if license_file_path.exists():
            if not override:
                return {
                    "status": "error",
                    "message": f"License '{spdx_id}' already exists. Set override=True to replace it.",
                    "spdx_id": spdx_id,
                    "overridden": False,
                }
            overridden = True

        # Prepare TOML content  - must use nested dict structure
        toml_data = {}
        for modal in required_modals:
            if license_dict[modal]:  # Only add if not empty
                toml_data[modal] = {}
                for action_name, action_data in license_dict[modal].items():
                    toml_data[modal][action_name] = {
                        "protect_scope": action_data.get("protect_scope", []),
                        "escape_scope": action_data.get("escape_scope", []),
                    }
                    # Add optional fields if present
                    if "target" in action_data:
                        toml_data[modal][action_name]["target"] = action_data["target"]

        # Add special sections if present
        if "special" in license_dict and license_dict["special"]:
            toml_data["special"] = {}
            for special_name, special_data in license_dict["special"].items():
                if isinstance(special_data, dict):
                    toml_data["special"][special_name] = special_data

        # Write to file
        try:
            with open(license_file_path, "w", encoding="utf-8") as f:
                toml.dump(toml_data, f)
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to write license file: {str(e)}",
                "spdx_id": spdx_id,
            }

        # Optionally regenerate knowledge base
        kb_regenerated = False
        if regenerate_kb:
            try:
                regenerate_result, success = regenerate_knowledge_base(force=True)
                kb_regenerated = success
                if not success:
                    return {
                        "status": "warning",
                        "message": f"License '{spdx_id}' added successfully, but knowledge base regeneration failed: {regenerate_result.get('message')}",
                        "spdx_id": spdx_id,
                        "file_path": str(license_file_path),
                        "overridden": overridden,
                        "kb_regenerated": False,
                    }
            except Exception as e:
                return {
                    "status": "warning",
                    "message": f"License '{spdx_id}' added successfully, but knowledge base regeneration failed: {str(e)}",
                    "spdx_id": spdx_id,
                    "file_path": str(license_file_path),
                    "overridden": overridden,
                    "kb_regenerated": False,
                }

        return {
            "status": "success",
            "message": f"License '{spdx_id}' {'updated' if overridden else 'added'} successfully"
                      + (f" and knowledge base regenerated" if kb_regenerated else ""),
            "spdx_id": spdx_id,
            "file_path": str(license_file_path),
            "overridden": overridden,
            "kb_regenerated": kb_regenerated,
        }

    except Exception as e:
        return {
            "status": "error",
            "message": f"An error occurred: {str(e)}",
            "spdx_id": spdx_id if spdx_id else "",
        }


def list_structured_licenses(
    only_custom: bool = False,
    include_metadata: bool = False,
) -> list[str] | dict[str, Any]:
    """Query and return a list of all structured licenses in the system.

    This function retrieves all available structured licenses from the license
    directory. Optionally filter to show only custom (user-added) licenses.

    Args:
        only_custom: If True, only returns custom licenses (not native ones).
                    Defaults to False.
        include_metadata: If True, returns a dict with additional metadata.
                         Defaults to False (returns simple list).

    Returns:
        list[str] or dict: If include_metadata is False, returns a list of SPDX IDs.
                          If include_metadata is True, returns a dictionary with:
                              - status: "success" or "error"
                              - licenses: List of SPDX IDs
                              - count: Number of licenses
                              - custom_count: Number of custom licenses (if applicable)

    Example:
        >>> from liscopelens.api import list_structured_licenses
        >>> licenses = list_structured_licenses()
        >>> print(type(licenses))
        <class 'list'>
        >>> print(licenses[:3])
        ['MIT', 'Apache-2.0', 'GPL-3.0-only']

        >>> # With metadata
        >>> result = list_structured_licenses(include_metadata=True)
        >>> print(result["count"])
        150
    """
    try:
        # Load all licenses
        all_licenses = load_licenses()
        license_ids = sorted(all_licenses.keys())

        # TODO: Implement custom license tracking
        # For now, we return all licenses since there's no built-in way
        # to distinguish custom from native licenses
        if only_custom:
            # This would require maintaining a registry of custom licenses
            # For now, return empty list
            custom_licenses = []
            if include_metadata:
                return {
                    "status": "success",
                    "licenses": custom_licenses,
                    "count": 0,
                    "message": "Custom license tracking not yet implemented. All licenses returned.",
                }
            return custom_licenses

        if include_metadata:
            return {
                "status": "success",
                "licenses": license_ids,
                "count": len(license_ids),
                "message": f"Found {len(license_ids)} structured licenses",
            }

        return license_ids

    except Exception as e:
        if include_metadata:
            return {
                "status": "error",
                "licenses": [],
                "count": 0,
                "message": f"An error occurred: {str(e)}",
            }
        return []


def get_structured_license(
    spdx_id: str,
    format: str = "json",
) -> str | dict[str, Any]:
    """Query and return structured license data by SPDX ID.

    This function retrieves the detailed structured data for a specific license
    identified by its SPDX ID. The data can be returned as a JSON string or
    as a dictionary.

    Args:
        spdx_id: The SPDX ID of the license to query (e.g., "MIT", "GPL-3.0-only")
        format: Output format - "json" (JSON string) or "dict" (Python dict).
               Defaults to "json".

    Returns:
        str or dict: If format is "json", returns a JSON string representation.
                    If format is "dict", returns a dictionary with:
                        - status: "success" or "error"
                        - spdx_id: The queried SPDX ID
                        - data: The structured license data
                        - message: Description

    Raises:
        ValueError: If spdx_id is invalid or format is not supported

    Example:
        >>> from liscopelens.api import get_structured_license
        >>> license_json = get_structured_license("MIT", format="json")
        >>> print(type(license_json))
        <class 'str'>

        >>> import json
        >>> license_data = json.loads(license_json)
        >>> print("can" in license_data)
        True

        >>> # Get as dictionary
        >>> result = get_structured_license("MIT", format="dict")
        >>> print(result["status"])
        'success'
        >>> print("can" in result["data"])
        True
    """
    try:
        # Validate input
        if not spdx_id or not isinstance(spdx_id, str):
            error_result = {
                "status": "error",
                "spdx_id": spdx_id if spdx_id else "",
                "message": "spdx_id must be a non-empty string",
            }
            if format == "json":
                return json.dumps(error_result)
            return error_result

        if format not in ["json", "dict"]:
            error_result = {
                "status": "error",
                "spdx_id": spdx_id,
                "message": f"Unsupported format '{format}'. Use 'json' or 'dict'.",
            }
            if format == "json":
                return json.dumps(error_result)
            return error_result

        # Load all licenses
        all_licenses = load_licenses()

        # Check if license exists
        if spdx_id not in all_licenses:
            error_result = {
                "status": "error",
                "spdx_id": spdx_id,
                "message": f"License '{spdx_id}' not found in the system",
            }
            if format == "json":
                return json.dumps(error_result)
            return error_result

        # Get the license
        license_feat = all_licenses[spdx_id]

        # Convert LicenseFeat to dictionary
        license_data = {
            "spdx_id": license_feat.spdx_id,
            "can": {},
            "cannot": {},
            "must": {},
            "special": {},
            "human_review": license_feat.human_review,
        }

        # Process each modal
        for modal_name in ["can", "cannot", "must", "special"]:
            modal_dict = getattr(license_feat, modal_name)
            for action_name, action_feat in modal_dict.items():
                license_data[modal_name][action_name] = {
                    "name": action_feat.name,
                    "modal": action_feat.modal,
                    "protect_scope": action_feat.protect_scope,
                    "escape_scope": action_feat.escape_scope,
                    "scope": dict(action_feat.scope),  # Convert Scope to dict
                    "target": action_feat.target,
                }

        # Add scope information if available
        if license_feat.scope:
            license_data["scope"] = license_feat.scope

        # Prepare result
        if format == "json":
            return json.dumps(license_data, indent=2, ensure_ascii=False)
        else:  # format == "dict"
            return {
                "status": "success",
                "spdx_id": spdx_id,
                "data": license_data,
                "message": f"Successfully retrieved structured data for license '{spdx_id}'",
            }

    except Exception as e:
        error_result = {
            "status": "error",
            "spdx_id": spdx_id if spdx_id else "",
            "message": f"An error occurred: {str(e)}",
        }
        if format == "json":
            return json.dumps(error_result)
        return error_result
