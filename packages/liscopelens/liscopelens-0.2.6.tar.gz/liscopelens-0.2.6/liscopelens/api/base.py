"""High-level helpers for running the parser pipeline programmatically."""

from __future__ import annotations

from argparse import Namespace
from typing import Any, Mapping, Sequence
import os
import json
import toml

from liscopelens.parser.scancode import ScancodeParser
from liscopelens.parser.exception import BaseExceptionParser
from liscopelens.parser.decycle import DecycleParser
from liscopelens.parser.propagate import BasePropagateParser
from liscopelens.parser.compatible import BaseCompatiblityParser
from liscopelens.utils.graph import GraphManager
from liscopelens.utils.structure import Config, load_config, Scope, LicenseFeat, load_licenses
from liscopelens.utils.scaffold import get_resource_path
from liscopelens.infer import generate_knowledge_graph
from liscopelens.checker import Checker
from liscopelens.constants import CompatibleType

ParserInitArgs = Namespace | str | Sequence[str] | dict[str, Any] | None

__all__ = [
    "ScancodeParser",
    "BaseExceptionParser",
    "DecycleParser",
    "BasePropagateParser",
    "BaseCompatiblityParser",
    "ParserInitArgs",
    "check_compatibility",
    "regenerate_knowledge_base",
    "check_license_compatibility",
    "query_license_compatibility",
    "add_structured_license",
    "list_structured_licenses",
    "get_structured_license",
]


def check_compatibility(
    license_map: Mapping[str, str],
    graph_input: GraphManager | str | dict[str, Any],
    *,
    config: Config | None = None,
    args: ParserInitArgs = None,
) -> tuple[GraphManager, dict[str, dict]]:
    """Execute the canonical Scancode → Exception → Decycle → Propagate → Compatibility pipeline.

    Args:
        license_map: Mapping from graph node labels ("//path") to SPDX expressions.
        graph_input: Existing graph context, a JSON payload, or a path that resolves to a graph export.
        config: Optional pre-loaded configuration; defaults to :func:`load_config`.
        args: Unified argument set shared across all parser stages.

    Returns:
        tuple: A tuple containing:
            - GraphManager: The graph after compatibility evaluation.
            - dict: The results dictionary containing conflict information.
    """

    if not isinstance(license_map, Mapping):
        raise TypeError(
            "license_map must be a mapping of node labels to SPDX expressions"
        )

    resolved_config = config or load_config()

    scancode_parser = ScancodeParser(args, resolved_config)
    context = scancode_parser(dict(license_map), graph_input)

    exception_parser = BaseExceptionParser(args, resolved_config)
    context = exception_parser(context)

    dag_parser = DecycleParser(args, resolved_config)
    context = dag_parser(context)

    propagate_parser = BasePropagateParser(args, resolved_config)
    context = propagate_parser(context)

    compatible_parser = BaseCompatiblityParser(args, resolved_config)
    context, results = compatible_parser(context)

    return context, results


def regenerate_knowledge_base(force: bool = True) -> tuple[dict[str, Any], bool]:
    """Regenerate the license compatibility knowledge base.

    This function regenerates the knowledge graphs for license properties and
    compatibility relationships. By default, it forces regeneration even if
    existing knowledge graphs are present.

    Args:
        force: If True, regenerate knowledge base even if it already exists.
               Defaults to True.

    Returns:
        dict: A dictionary containing:
            - message: Description of the result
            - properties_graph_nodes: Number of nodes in properties graph
            - properties_graph_edges: Number of edges in properties graph
            - compatible_graph_nodes: Number of nodes in compatible graph
            - compatible_graph_edges: Number of edges in compatible graph

        bool: True if regeneration was successful, False otherwise.

    Example:
        >>> from liscopelens.api import regenerate_knowledge_base
        >>> result, success = regenerate_knowledge_base()
        >>> print(success)
        True
    """
    try:
        infer = generate_knowledge_graph(reinfer=force)

        result = {
            "message": "Knowledge base regenerated successfully",
            "properties_graph_nodes": len(infer.properties_graph.nodes()),
            "properties_graph_edges": len(list(infer.properties_graph.edges())),
            "compatible_graph_nodes": len(infer.compatible_graph.nodes()),
            "compatible_graph_edges": len(list(infer.compatible_graph.edges())),
        }

        return result, True

    except Exception as e:
        return {
            "message": f"Failed to regenerate knowledge base: {str(e)}",
            "properties_graph_nodes": 0,
            "properties_graph_edges": 0,
            "compatible_graph_nodes": 0,
            "compatible_graph_edges": 0,
        }, False


def check_license_compatibility(
    license_a: str,
    license_b: str,
    scope: Scope | dict[str, list[str]] | str | None = None,
) -> dict[str, Any]:
    """Query the compatibility between two licenses.

    This function checks whether two licenses are compatible with each other,
    optionally within a specific usage scope.

    Args:
        license_a: SPDX ID of the first license (e.g., "MIT", "GPL-3.0")
        license_b: SPDX ID of the second license (e.g., "Apache-2.0")
        scope: Optional usage scope for conditional compatibility check.
               Can be a Scope object, dict, or JSON string.
               Defaults to None.

    Returns:
        dict: A dictionary containing:
            - status: "success" or "error"
            - license_a: The first license SPDX ID
            - license_b: The second license SPDX ID
            - compatibility: Compatibility type (UNCONDITIONAL_COMPATIBLE,
                           CONDITIONAL_COMPATIBLE, INCOMPATIBLE, or UNKNOWN)
            - message: Detailed description of the compatibility result
            - scope: The applicable scope (only for conditional compatibility)

    Raises:
        ValueError: If license names are invalid or scope format is incorrect

    Example:
        >>> from liscopelens.api import check_license_compatibility
        >>> result = check_license_compatibility("MIT", "GPL-3.0")
        >>> print(result["compatibility"])
        'UNCONDITIONAL_COMPATIBLE'

        >>> # Check with specific scope
        >>> result = check_license_compatibility(
        ...     "GPL-3.0",
        ...     "Apache-2.0",
        ...     scope={"dynamic_linking": []}
        ... )
    """
    try:
        # Input validation
        if not license_a or not isinstance(license_a, str):
            raise ValueError("license_a must be a non-empty string")
        if not license_b or not isinstance(license_b, str):
            raise ValueError("license_b must be a non-empty string")

        # Initialize the checker
        checker = Checker()

        # Check if licenses exist
        if not checker.is_license_exist(license_a):
            return {
                "status": "error",
                "license_a": license_a,
                "license_b": license_b,
                "compatibility": CompatibleType.UNKNOWN,
                "message": f"License '{license_a}' does not exist in the knowledge base",
            }

        if not checker.is_license_exist(license_b):
            return {
                "status": "error",
                "license_a": license_a,
                "license_b": license_b,
                "compatibility": CompatibleType.UNKNOWN,
                "message": f"License '{license_b}' does not exist in the knowledge base",
            }

        # Parse scope if provided
        parsed_scope = None
        if scope is not None:
            if isinstance(scope, Scope):
                parsed_scope = scope
            elif isinstance(scope, dict):
                parsed_scope = Scope.from_dict(scope)
            elif isinstance(scope, str):
                parsed_scope = Scope.from_str(scope)
            else:
                raise ValueError(
                    "scope must be a Scope object, dict, or JSON string"
                )

        # Check compatibility
        compatibility_type = checker.check_compatibility(
            license_a, license_b, parsed_scope
        )

        # Build result dictionary
        result = {
            "status": "success",
            "license_a": license_a,
            "license_b": license_b,
            "compatibility": compatibility_type.value,
        }

        # Add appropriate message based on compatibility type
        if compatibility_type == CompatibleType.UNCONDITIONAL_COMPATIBLE:
            result["message"] = (
                f"License '{license_a}' is unconditionally compatible "
                f"with '{license_b}'"
            )
        elif compatibility_type == CompatibleType.CONDITIONAL_COMPATIBLE:
            # Get the edge data to retrieve scope information
            edge_index = checker.compatible_graph.query_edge_by_label(
                license_a, license_b
            )
            if edge_index:
                edge_data = checker.compatible_graph.get_edge_data(edge_index[0])
                if edge_data and "scope" in edge_data:
                    result["scope"] = edge_data["scope"]
                    result["message"] = (
                        f"License '{license_a}' is conditionally compatible "
                        f"with '{license_b}' within the specified scope"
                    )
                else:
                    result["message"] = (
                        f"License '{license_a}' is conditionally compatible "
                        f"with '{license_b}'"
                    )
            else:
                result["message"] = (
                    f"License '{license_a}' is conditionally compatible "
                    f"with '{license_b}'"
                )
        elif compatibility_type == CompatibleType.INCOMPATIBLE:
            result["message"] = (
                f"License '{license_a}' is incompatible with '{license_b}'"
            )
        else:  # UNKNOWN
            result["message"] = (
                f"Compatibility between '{license_a}' and '{license_b}' "
                f"is unknown"
            )

        return result

    except ValueError as e:
        return {
            "status": "error",
            "license_a": license_a if license_a else "",
            "license_b": license_b if license_b else "",
            "compatibility": CompatibleType.UNKNOWN,
            "message": str(e),
        }
    except Exception as e:
        return {
            "status": "error",
            "license_a": license_a if license_a else "",
            "license_b": license_b if license_b else "",
            "compatibility": CompatibleType.UNKNOWN,
            "message": f"An error occurred: {str(e)}",
        }


def query_license_compatibility(
    license_a: str,
    license_b: str,
) -> dict[str, Any]:
    """Get detailed compatibility information between two licenses from the knowledge base.

    This function directly queries the knowledge base to retrieve the compatibility edge
    data between two licenses, including the compatibility type and scope information.
    Unlike check_license_compatibility, this function returns the raw edge attributes
    from the knowledge graph without evaluation.

    Args:
        license_a: SPDX ID of the first license (e.g., "MIT", "GPL-3.0")
        license_b: SPDX ID of the second license (e.g., "Apache-2.0")

    Returns:
        dict: A dictionary containing:
            - status: "success" or "error"
            - license_a: The first license SPDX ID
            - license_b: The second license SPDX ID
            - compatibility_type: The compatibility type (UNCONDITIONAL_COMPATIBLE,
                                CONDITIONAL_COMPATIBLE, INCOMPATIBLE, or UNKNOWN)
            - scope: The scope object from the edge (for conditional compatibility).
                    This indicates under what conditions the licenses are compatible.
            - message: Detailed description of the result

    Raises:
        ValueError: If license names are invalid

    Example:
        >>> from liscopelens.api import query_license_compatibility
        >>> result = query_license_compatibility("MIT", "GPL-3.0")
        >>> print(result["compatibility_type"])
        'UNCONDITIONAL_COMPATIBLE'

        >>> # Get detailed compatibility with scope information
        >>> result = query_license_compatibility("GPL-3.0", "Apache-2.0")
        >>> if result["compatibility_type"] == "CONDITIONAL_COMPATIBLE":
        ...     print(result["scope"])  # Shows the scope conditions
    """
    try:
        # Input validation
        if not license_a or not isinstance(license_a, str):
            raise ValueError("license_a must be a non-empty string")
        if not license_b or not isinstance(license_b, str):
            raise ValueError("license_b must be a non-empty string")

        # Initialize the checker
        checker = Checker()

        # Check if licenses exist
        if not checker.is_license_exist(license_a):
            return {
                "status": "error",
                "license_a": license_a,
                "license_b": license_b,
                "compatibility_type": CompatibleType.UNKNOWN.name,
                "message": f"License '{license_a}' does not exist in the knowledge base",
            }

        if not checker.is_license_exist(license_b):
            return {
                "status": "error",
                "license_a": license_a,
                "license_b": license_b,
                "compatibility_type": CompatibleType.UNKNOWN.name,
                "message": f"License '{license_b}' does not exist in the knowledge base",
            }

        # Query the edge from the compatibility graph
        edge_index = checker.compatible_graph.query_edge_by_label(
            license_a, license_b
        )

        if not edge_index:
            return {
                "status": "success",
                "license_a": license_a,
                "license_b": license_b,
                "compatibility_type": CompatibleType.UNKNOWN.name,
                "message": f"No compatibility relationship found between '{license_a}' and '{license_b}'",
            }

        # Get edge data
        edge_data = checker.compatible_graph.get_edge_data(edge_index[0])
        if not edge_data:
            return {
                "status": "error",
                "license_a": license_a,
                "license_b": license_b,
                "compatibility_type": CompatibleType.UNKNOWN.name,
                "message": f"Failed to retrieve edge data for '{license_a}' -> '{license_b}'",
            }

        # Extract compatibility information
        compatibility_type = CompatibleType(
            edge_data.get("compatibility", CompatibleType.UNKNOWN)
        )

        # Build result dictionary
        result = {
            "status": "success",
            "license_a": license_a,
            "license_b": license_b,
            "compatibility_type": compatibility_type.name,
        }

        # Add scope information for conditional compatibility
        if "scope" in edge_data:
            scope_data = edge_data["scope"]
            # Convert scope string to Scope object for better usability
            if isinstance(scope_data, str):
                result["scope"] = Scope.from_str(scope_data)
            else:
                result["scope"] = scope_data
        else:
            result["scope"] = None

        # Generate appropriate message
        if compatibility_type == CompatibleType.UNCONDITIONAL_COMPATIBLE:
            result["message"] = (
                f"License '{license_a}' is unconditionally compatible with '{license_b}'"
            )
        elif compatibility_type == CompatibleType.CONDITIONAL_COMPATIBLE:
            result["message"] = (
                f"License '{license_a}' is conditionally compatible with '{license_b}'. "
                f"Check the 'scope' field for compatibility conditions."
            )
        elif compatibility_type == CompatibleType.INCOMPATIBLE:
            result["message"] = (
                f"License '{license_a}' is incompatible with '{license_b}'"
            )
        else:  # UNKNOWN
            result["message"] = (
                f"Compatibility between '{license_a}' and '{license_b}' is unknown"
            )

        return result

    except ValueError as e:
        return {
            "status": "error",
            "license_a": license_a if license_a else "",
            "license_b": license_b if license_b else "",
            "compatibility_type": CompatibleType.UNKNOWN.name,
            "message": str(e),
        }
    except Exception as e:
        return {
            "status": "error",
            "license_a": license_a if license_a else "",
            "license_b": license_b if license_b else "",
            "compatibility_type": CompatibleType.UNKNOWN.name,
            "message": f"An error occurred: {str(e)}",
        }
