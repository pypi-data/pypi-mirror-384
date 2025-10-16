"""Miscellenous tools using ast"""

import ast


def remove_docstrings(code: str) -> str:
    '''
    Remove docstrings from the given Python code.

    Args:
        code (str): A string containing Python code.

    Returns:
        str: The same code with docstrings removed.

    Examples:
        >>> code = \'\'\'
        ... def foo():
        ...     """This is a docstring."""
        ...     print("Hello")
        ...
        ... class Bar:
        ...     """Class docstring."""
        ...     def baz(self):
        ...         """Method docstring."""
        ...         pass
        ... \'\'\'
        >>> print(remove_docstrings(code))
        def foo():
            print('Hello')
        <BLANKLINE>
        class Bar:
        <BLANKLINE>
            def baz(self):
                pass
    '''

    class DocstringRemover(ast.NodeTransformer):
        def visit_FunctionDef(self, node):
            self.generic_visit(node)
            if (
                node.body
                and isinstance(node.body[0], ast.Expr)
                and isinstance(node.body[0].value, ast.Str)
            ):
                node.body = node.body[
                    1:
                ]  # Remove the first expression if it's a docstring
            return node

        def visit_ClassDef(self, node):
            self.generic_visit(node)
            if (
                node.body
                and isinstance(node.body[0], ast.Expr)
                and isinstance(node.body[0].value, ast.Str)
            ):
                node.body = node.body[
                    1:
                ]  # Remove the first expression if it's a docstring
            return node

        def visit_Module(self, node):
            self.generic_visit(node)
            if (
                node.body
                and isinstance(node.body[0], ast.Expr)
                and isinstance(node.body[0].value, ast.Str)
            ):
                node.body = node.body[
                    1:
                ]  # Remove the first expression if it's a docstring
            return node

    parsed_ast = ast.parse(code)
    transformer = DocstringRemover()
    cleaned_ast = transformer.visit(parsed_ast)
    return ast.unparse(cleaned_ast)


"""Extract dependencies from setup.cfg files and Python source code.

This module provides functionality to parse setup.cfg files and extract
their required dependencies, as well as extract imported packages from Python code.
"""

import ast
from typing import Callable, Set


def _return_none(error: Exception) -> None:
    """Default error handler that returns None."""
    return None


def imported_packages_from_code(
    code: str, *, on_parsing_error: Callable[[Exception], None] = _return_none
) -> Set[str]:
    """Extract top-level package names from Python code using AST parsing.

    Args:
        code: Python source code as a string
        on_parsing_error: Callable to handle parsing errors. By default, returns None.
                         Can be set to raise the error, e.g., `lambda e: (_ for _ in ()).throw(e)`

    Returns:
        Set of top-level package names imported in the code

    Example:
        >>> code = '''
        ... import os
        ... import numpy as np
        ... from collections import defaultdict
        ... from pkg.submodule import something
        ... '''
        >>> sorted(imported_packages_from_code(code))
        ['collections', 'numpy', 'os', 'pkg']

        >>> invalid_code = 'import os\\nthis is not valid python'
        >>> result = imported_packages_from_code(invalid_code)
        >>> result is None
        True

        >>> imported_packages_from_code(invalid_code, on_parsing_error=lambda e: (_ for _ in ()).throw(e))
        Traceback (most recent call last):
        ...
        SyntaxError: invalid syntax...
    """
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return on_parsing_error(e)

    packages = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                # Extract the top-level package name
                package = alias.name.split(".")[0]
                packages.add(package)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                # Extract the top-level package name
                package = node.module.split(".")[0]
                packages.add(package)

    return packages
