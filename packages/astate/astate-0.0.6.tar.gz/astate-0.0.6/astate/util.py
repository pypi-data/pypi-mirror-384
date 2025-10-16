"""Utils for astate"""

import ast
import inspect
from functools import partial
from typing import Iterable, Union, Callable, Optional


def is_ast(obj):
    return isinstance(obj, ast.AST)


def is_body(obj):
    return isinstance(obj, list) and all(map(is_ast, obj))


def ensure_body(obj):
    if is_body(obj):
        return obj
    elif isinstance(obj, ast.AST):
        return obj.body
    elif isinstance(obj, str):
        return ast.parse(obj)
    else:
        return ensure_body(inspect.getsource(obj))


def _isinstance(obj, typ):
    return isinstance(obj, typ)


def re_find_in_body(
    body,
    cond: Union[Callable, type] = ast.FunctionDef,
    max_levels: Optional[int] = None,
):
    """
    Recursively find elements in an ast body that satisfy a condition

    :param body: A list of ast nodes or object that can be resolved to it.
        See ``ensure_body`` to see what objects can be resolved to a body.
    :param cond: The condition to apply to ast elements of body to determine whether to
        yield or not
    :param max_levels: Maximum levels of recursion desired
    :return: A generator of filtered ast nodes

    >>> def foo(x):
    ...     def bar(y):
    ...         y * 1
    ...     return bar(x)
    >>>
    >>> [x.name for x in re_find_in_body(foo)]
    ['foo', 'bar']
    >>> [x.name for x in re_find_in_body(foo, max_levels=1)]
    ['foo']


    """
    if max_levels is None:
        max_levels = float("infinity")
    if isinstance(cond, type):
        cond_type = cond
        cond = partial(_isinstance, typ=cond_type)
    body = ensure_body(body)
    if not isinstance(body, Iterable) and (body_ := getattr(body, "body", None)):
        yield from re_find_in_body(body_, cond, max_levels)
    else:
        for t in body:
            if cond(t):
                yield t
            if hasattr(t, "body"):
                max_levels -= 1
                if max_levels > 0:
                    yield from re_find_in_body(t.body, cond, max_levels)
