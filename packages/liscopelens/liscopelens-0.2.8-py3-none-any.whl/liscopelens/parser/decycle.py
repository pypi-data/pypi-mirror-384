#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# Copyright (c) 2024 Lanzhou University
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

"""
DAG Parser module for cycle resolution in dependency graphs.

This parser detects and resolves cycles in the dependency graph by merging
nodes that form cycles. It specifically handles cycles where all nodes in
the cycle path are 'code' type nodes.
"""

import argparse
from pathlib import Path
from typing import Optional, List, Set, Tuple
from collections import defaultdict

import networkx as nx

from liscopelens.utils import GraphManager
from liscopelens.utils.structure import Config, DualLicense, DualUnit

from .base import BaseParser


class DecycleParser(BaseParser):
    """
    Parser for resolving cycles in dependency graphs to ensure DAG structure.

    This parser detects cycles in the graph and resolves them by merging all
    nodes in a cycle into a single node when all nodes in the cycle are of
    type 'code'. The merged node combines licenses from all original nodes
    using AND aggregation.

    Properties:
        cycle_counter: Counter for generating unique IDs for merged cycle nodes
    """

    arg_table = {
        "--merge-cycles": {
            "action": "store_true",
            "help": "Merge cycles where all nodes are code type",
            "default": True,
        },
        "--node-type": {
            "type": str,
            "help": "Node type to consider for cycle merging (default: code)",
            "default": "code",
        },
    }

    def __init__(self, args: argparse.Namespace, config: Config):
        super().__init__(args, config)
        self.cycle_counter = 0

    def _detect_cycles(self, graph: nx.MultiDiGraph) -> List[List[str]]:
        """
        Detect all simple cycles in the graph.

        Args:
            graph: The directed graph to analyze

        Returns:
            List of cycles, where each cycle is a list of node labels
        """
        try:
            cycles = list(nx.simple_cycles(graph))
            return cycles
        except Exception:
            return []

    def _is_code_cycle(self, cycle: List[str], context: GraphManager) -> bool:
        """
        Check if all nodes in a cycle are of the specified node type.

        Args:
            cycle: List of node labels forming a cycle
            context: GraphManager containing the graph

        Returns:
            True if all nodes in the cycle are of the target type, False otherwise
        """
        target_type = getattr(self.args, "node_type", "code")

        for node_label in cycle:
            node_data = context.get_node_data(node_label)
            if not node_data:
                return False

            node_type = node_data.get("type", None)
            if node_type != target_type:
                return False

        return True

    def _aggregate_licenses(self, node_labels: List[str], context: GraphManager) -> DualLicense:
        """
        Aggregate licenses from multiple nodes using AND operation.

        Args:
            node_labels: List of node labels to aggregate licenses from
            context: GraphManager containing the graph

        Returns:
            Aggregated DualLicense object
        """
        aggregated_license = None

        for node_label in node_labels:
            node_data = context.get_node_data(node_label)
            if not node_data:
                continue

            # Try to get licenses from different possible attributes
            node_license = node_data.get("licenses", None)
            if not node_license:
                node_license = node_data.get("outbound", None)

            if not node_license:
                continue

            # Ensure it's a DualLicense object
            if isinstance(node_license, str):
                node_license = DualLicense.from_str(node_license)
            elif isinstance(node_license, list):
                node_license = DualLicense.from_list(node_license)
            elif not isinstance(node_license, DualLicense):
                continue

            # Aggregate using AND operation
            if aggregated_license is None:
                aggregated_license = node_license
            else:
                aggregated_license = aggregated_license & node_license

        return aggregated_license if aggregated_license else DualLicense([frozenset()])

    def _create_merged_node_id(self) -> str:
        """
        Generate a unique ID for a merged cycle node.

        Returns:
            Unique node ID in the format 'cycle_{counter}'
        """
        node_id = f"cycle_{self.cycle_counter}"
        self.cycle_counter += 1
        return node_id

    def _merge_cycle_nodes(
        self,
        cycle: List[str],
        context: GraphManager
    ) -> Tuple[str, dict]:
        """
        Merge all nodes in a cycle into a single node.

        Args:
            cycle: List of node labels forming the cycle
            context: GraphManager containing the graph

        Returns:
            Tuple of (merged_node_id, merged_node_attributes)
        """
        merged_node_id = self._create_merged_node_id()

        # Aggregate licenses from all nodes in the cycle
        aggregated_license = self._aggregate_licenses(cycle, context)

        # Collect metadata from all nodes
        original_nodes = []
        original_metadata = {}

        for node_label in cycle:
            node_data = context.get_node_data(node_label)
            if node_data:
                original_nodes.append(node_label)
                original_metadata[node_label] = dict(node_data)

        # Create merged node attributes
        merged_attributes = {
            "type": getattr(self.args, "node_type", "code"),
            "merged_from_cycle": True,
            "original_nodes": original_nodes,
            "original_metadata": original_metadata,
            "licenses": aggregated_license,
            "outbound": aggregated_license,
        }

        return merged_node_id, merged_attributes

    def _get_external_edges(
        self,
        cycle_nodes: Set[str],
        context: GraphManager
    ) -> Tuple[List[Tuple], List[Tuple]]:
        """
        Get edges connecting cycle nodes to external nodes.

        Args:
            cycle_nodes: Set of node labels in the cycle
            context: GraphManager containing the graph

        Returns:
            Tuple of (incoming_edges, outgoing_edges) where each edge is
            (source, target, key, data)
        """
        incoming_edges = []
        outgoing_edges = []

        for u, v, key, data in context.graph.edges(keys=True, data=True):
            # Incoming edges: from external to cycle
            if u not in cycle_nodes and v in cycle_nodes:
                incoming_edges.append((u, v, key, data))

            # Outgoing edges: from cycle to external
            elif u in cycle_nodes and v not in cycle_nodes:
                outgoing_edges.append((u, v, key, data))

        return incoming_edges, outgoing_edges

    def _resolve_cycle(self, cycle: List[str], context: GraphManager) -> GraphManager:
        """
        Resolve a single cycle by merging its nodes.

        Args:
            cycle: List of node labels forming the cycle
            context: GraphManager containing the graph

        Returns:
            Updated GraphManager with cycle resolved
        """
        cycle_nodes = set(cycle)

        # Create merged node
        merged_node_id, merged_attributes = self._merge_cycle_nodes(cycle, context)

        # Get external edges
        incoming_edges, outgoing_edges = self._get_external_edges(cycle_nodes, context)

        # Add merged node to graph
        from liscopelens.utils.graph import Vertex
        merged_vertex = Vertex(merged_node_id, **merged_attributes)
        context.add_node(merged_vertex)

        # Recreate external edges pointing to/from the merged node
        from liscopelens.utils.graph import Edge

        # Handle incoming edges
        incoming_sources = defaultdict(list)
        for u, v, key, data in incoming_edges:
            incoming_sources[u].append(data)

        for source, edge_data_list in incoming_sources.items():
            # Merge edge attributes if multiple edges from same source
            merged_edge_data = edge_data_list[0].copy() if edge_data_list else {}
            edge = Edge(source, merged_node_id, **merged_edge_data)
            context.add_edge(edge)

        # Handle outgoing edges
        outgoing_targets = defaultdict(list)
        for u, v, key, data in outgoing_edges:
            outgoing_targets[v].append(data)

        for target, edge_data_list in outgoing_targets.items():
            # Merge edge attributes if multiple edges to same target
            merged_edge_data = edge_data_list[0].copy() if edge_data_list else {}
            edge = Edge(merged_node_id, target, **merged_edge_data)
            context.add_edge(edge)

        # Remove original cycle nodes and their edges
        for node_label in cycle_nodes:
            if node_label in context.graph:
                context.graph.remove_node(node_label)

        return context

    def parse(
        self,
        project_path: Path,
        context: Optional[GraphManager] = None
    ) -> GraphManager:
        """
        Parse the graph and resolve cycles to ensure DAG structure.

        Args:
            project_path: The path of the project
            context: The context (GraphManager) of the project

        Returns:
            The updated GraphManager with cycles resolved
        """
        if context is None:
            context = GraphManager()

        # Check if cycle merging is enabled
        if not getattr(self.args, "merge_cycles", True):
            return context

        # Iteratively detect and resolve cycles until no more cycles exist
        max_iterations = 1000  # Prevent infinite loops
        iteration = 0

        while iteration < max_iterations:
            # Detect cycles
            cycles = self._detect_cycles(context.graph)

            if not cycles:
                # No more cycles, we're done
                break

            # Process each cycle
            cycles_to_resolve = []
            for cycle in cycles:
                if self._is_code_cycle(cycle, context):
                    cycles_to_resolve.append(cycle)

            if not cycles_to_resolve:
                # No code cycles to resolve, we're done
                break

            # Resolve cycles one at a time to avoid conflicts
            # After each resolution, we'll re-detect cycles in the next iteration
            for cycle in cycles_to_resolve[:1]:  # Resolve one cycle at a time
                # Check if all nodes in cycle still exist (might have been merged already)
                if all(node in context.graph for node in cycle):
                    context = self._resolve_cycle(cycle, context)
                    break  # Resolve only one cycle per iteration

            iteration += 1

        if iteration >= max_iterations:
            import warnings
            warnings.warn(
                f"DecycleParser reached maximum iterations ({max_iterations}). "
                f"The graph may still contain cycles."
            )

        return context

    def __call__(
        self,
        context: GraphManager | str | dict | None = None,
        *,
        project_path: str | Path | None = None,
    ) -> GraphManager:
        """
        Execute DAG resolution directly on a context object.

        This method allows the parser to be used as a callable library function.

        Args:
            context: GraphManager, path to graph file, or graph dict
            project_path: Optional project path

        Returns:
            Updated GraphManager with cycles resolved

        Example:
            ```python
            from liscopelens.parser.decycle import DecycleParser
            from liscopelens.utils.structure import load_config

            config = load_config()
            parser = DecycleParser(args=None, config=config)

            # Use as library
            resolved_graph = parser(context="path/to/graph.json")
            ```
        """
        gm = self._normalize_context(context, allow_none=True)
        proj = Path(project_path) if project_path is not None else Path(".")
        return self.parse(proj, gm)
