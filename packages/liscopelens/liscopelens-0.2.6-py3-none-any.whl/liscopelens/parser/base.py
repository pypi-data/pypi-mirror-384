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
The base classes of Parsers.
"""
import argparse
import json
import os
import shlex
import warnings
from pathlib import Path
from typing import Any, Dict, Tuple, Optional, Type, Sequence, Union

from abc import ABC, abstractmethod
from liscopelens.utils.graph import GraphManager, Vertex, Edge
from liscopelens.utils.structure import Config


class BaseParser(ABC):
    """
    Properties:
        - arg_table: A dictionary that contains the arguments for the parser. The key is the argument name.
          Supported meta-keys in each arg item:
            - 'group': build a required mutually exclusive group with same name
            - 'arg_group': add to a normal argument group with this name
            - 'parser_only': if True, excluded from build_parser (default False)
        - args: The parsed arguments. When Entry is initialized, the args will be passed to the parser.
        - config: The configuration of the parser. The configuration will be passed to the parser.

    Methods:
        - normalize_path: Normalize the given path to ensure it is absolute and properly formatted.
        - path2gnlike: Convert a normalized path to a GNLike format path.
        - gnlike2path: Convert a GNLike format path back to a normalized path.

    Abstract Methods:
        - parse: Parse the arguments and update the context (GraphManager) of the project.
        This method should be implemented by subclasses to define how the parser processes the input arguments
        and updates the graph context.
    """

    arg_table: Dict[str, Dict[str, Any]]

    @classmethod
    def build_parser(cls) -> argparse.ArgumentParser:
        """
        Build an ArgumentParser from the class arg_table.

        Supports both normal argument groups and mutually exclusive groups.
        If an entry in arg_table has 'group', all arguments with the same group
        will be added into one mutually exclusive group.
        """

        parser = argparse.ArgumentParser(prog=cls.__name__)
        normal_groups: dict[str, argparse._ArgumentGroup] = {}
        exclusive_groups: dict[str, argparse._MutuallyExclusiveGroup] = {}

        for opt, args_setting in cls.arg_table.items():
            # Copy to avoid mutating the class-level definition
            args_setting = dict(args_setting)

            # Filter parser-only options
            # If an arg item declares `parser_only=True`, it is intended to be
            # consumed by higher-level orchestrators and should not be part of
            # the parser constructed here.
            if args_setting.pop("parser_only", False):
                continue

            # If group is defined, create/get a mutually exclusive group
            if "group" in args_setting:
                group_name = args_setting.pop("group")
                if group_name not in exclusive_groups:
                    # required=True 表示该组至少要有一个生效参数
                    exclusive_groups[group_name] = parser.add_mutually_exclusive_group(
                        required=True
                    )
                target = exclusive_groups[group_name]
            else:
                # fallback: use main parser or normal argument groups
                group_name = args_setting.pop("arg_group", None)
                if group_name:
                    if group_name not in normal_groups:
                        normal_groups[group_name] = parser.add_argument_group(
                            group_name
                        )
                    target = normal_groups[group_name]
                else:
                    target = parser

            # add_argument 支持多个 option string，例如 ("-f", "--foo")
            if isinstance(opt, (tuple, list)):
                opt_strings = list(opt)
            else:
                opt_strings = [opt]

            target.add_argument(*opt_strings, **args_setting)

        return parser

    def __init__(self, args: argparse.Namespace | str | list | tuple, config: Config):
        parser = self.build_parser()
        if isinstance(args, str):
            self.args = parser.parse_args(shlex.split(args))
            print(self.args)
        elif isinstance(args, (list, tuple)):
            self.args = parser.parse_args(list(args))
        elif isinstance(args, dict):
            # dict → namespace, 但仍可以 parser.parse_args([]) 来触发默认值
            ns = parser.parse_args([])
            for k, v in args.items():
                setattr(ns, k, v)
            self.args = ns
        elif isinstance(args, argparse.Namespace):
            self.args = args
        elif args is None:
            self.args = parser.parse_args([])
        else:
            raise TypeError(f"Unsupported args type: {type(args)}")

        self.config = config

    def _normalize_context(
        self,
        context: Optional[GraphManager | str | dict],
        *,
        allow_none: bool = False,
    ) -> GraphManager:
        """Normalize arbitrary inputs into a GraphManager instance."""

        if context is None:
            if allow_none:
                return GraphManager()
            raise ValueError(f"Context cannot be None in {self.__class__.__name__}.")

        if hasattr(context, "nodes") and hasattr(context, "modify_node_attribute"):
            return context  # type: ignore[return-value]

        gm_cls = GraphManager

        if isinstance(context, str):
            if os.path.exists(context):
                for meth in (
                    "load",
                    "from_file",
                    "from_json_file",
                    "from_path",
                    "deserialize",
                ):
                    fn = getattr(gm_cls, meth, None)
                    if callable(fn):
                        try:
                            return fn(context)  # type: ignore[misc]
                        except Exception:
                            continue

                with open(context, "r", encoding="utf-8") as f:
                    data = json.load(f)

                return self._normalize_context(data, allow_none=allow_none)

            try:
                data = json.loads(context)
            except json.JSONDecodeError as exc:
                raise FileNotFoundError(
                    f"Context path not found and provided string is not valid JSON: {context!r}"
                ) from exc

            return self._normalize_context(data, allow_none=allow_none)

        if isinstance(context, dict):
            for meth in ("from_json", "from_dict", "deserialize"):
                fn = getattr(gm_cls, meth, None)
                if callable(fn):
                    try:
                        return fn(context)  # type: ignore[misc]
                    except Exception:
                        continue

            raise ValueError(
                "Unable to construct GraphManager from dict using known constructors."
            )

        raise TypeError(f"Unsupported context type: {type(context)}")

    def path2gnlike(self, target_path: Path, root_path: Path) -> str:
        """
        Convert a normalized path to a GNLike format path.

        Args:
            target_path (Path): The normalized path to be converted.
            root_path (Path): The root path to be used as the base for conversion.

        Returns:
            str: The GNLike format path.
        """
        return "//" + target_path.resolve().relative_to(root_path.resolve()).as_posix()

    def gnlike2path(self, gnlike_path: str, root_path: Path) -> Path:
        """
        Convert a GNLike format path back to a normalized path.

        Args:
            gnlike_path (str): The GNLike format path to be converted.
            root_path (Path): The root path to be used as the base for conversion.

        Returns:
            Path: The normalized path.
        """
        if not gnlike_path.startswith("//"):
            raise ValueError(f"Invalid GNLike path: {gnlike_path}")

        relative_path = Path(gnlike_path[2:])
        return root_path / relative_path

    @abstractmethod
    def parse(
        self, project_path: Path, context: Optional[GraphManager] = None
    ) -> GraphManager:
        """
        Parse the arguments and update the context

        Args:
            - project_path: The path of the project
            - context: The context (GraphManager) of the project

        Returns:
            - The updated context
        """
        raise NotImplementedError


class BaseParserEntry:
    """
    Properties:
        - parsers: A tuple of the parsers that will be used in this entry
        - entry_help: The help message of this entry
        - arg_parser: The argument parser of this entry
    """

    parsers: Tuple[Type[BaseParser], ...]
    entry_help: str = ""
    arg_parser: argparse.ArgumentParser | None = None

    def __init__(self, args: argparse.Namespace, config: Config):
        """
        when user input the command liscopelens [entry_name] hit the enter key, the parser will be initialized.
        """
        self.args = args
        self.config = config
        if self.parsers is None:
            raise NotImplementedError("No parsers found")

        if self.entry_help == "":
            warnings.warn("No entry help provided")

        self._parsers = (p(args, config) for p in self.parsers)

    def parse(self, project_path: Path, context: Optional[GraphManager] = None):
        """
        Parse the arguments and update the context

        Args:
            - project_path: The path of the project
            - context: The context (GraphManager) of the project

        Returns:
            - None, but any return could add when inheriting this class.

            ! Attention: you should add the return type in the subclass. If there is output file or cli
            ! output, you should implement that logic in the subclass parse method.
        """

        for p in self._parsers:
            context = p.parse(project_path, context)
        # Add arguments to arg_parser here if needed
