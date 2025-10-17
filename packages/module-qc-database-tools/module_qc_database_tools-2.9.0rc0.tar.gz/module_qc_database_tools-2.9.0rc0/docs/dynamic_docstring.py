from __future__ import annotations

import ast
from typing import Any

import griffe


class InspectSpecificObjects(griffe.Extension):
    """An extension to inspect just a few specific objects."""

    def __init__(self, functions: list[str]) -> None:
        # defined in mkdocs.yml
        self.functions = functions

    def on_function_instance(
        self,
        *,
        node: ast.AST | griffe.ObjectNode,  # noqa: ARG002
        func: griffe.Function,
        **kwargs: Any,  # noqa: ARG002
    ) -> None:
        """
        Post-process Griffe functions to dynamically update docstrings.
        """
        if func.path in self.functions:
            func.docstring = griffe.Docstring(griffe.dynamic_import(func.path).__doc__)
