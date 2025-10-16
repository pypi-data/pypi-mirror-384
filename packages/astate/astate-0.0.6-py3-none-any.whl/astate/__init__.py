'''

AST utils


## re_find_in_body

Recursively find elements in an ast body that satisfy a condition

    >>> from astate import re_find_in_body
    >>> def foo(x):
    ...     def bar(y):
    ...         y * 1
    ...     return bar(x)
    >>>
    >>> [x.name for x in re_find_in_body(foo)]
    ['foo', 'bar']
    >>> [x.name for x in re_find_in_body(foo, max_levels=1)]
    ['foo']


## remove_docstrings

Remove docstrings from the given Python code.

    >>> from astate import remove_docstrings
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

from astate.util import is_ast, is_body, ensure_body, re_find_in_body
from astate.misc import remove_docstrings, imported_packages_from_code
