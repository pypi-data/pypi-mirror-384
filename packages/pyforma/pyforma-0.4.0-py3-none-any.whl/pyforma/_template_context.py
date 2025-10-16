from decimal import Decimal
from itertools import chain, islice, product, starmap
from math import hypot, sin, sqrt, log, cos, tan
import re
from collections import deque, namedtuple
from collections.abc import Sequence, Callable
from datetime import datetime, date, timedelta
from functools import cache
from pathlib import Path
from statistics import mean, median, stdev
from typing import Any

from pyforma._template import Template
from pyforma._util import defaulted


@cache
def _load(canonical_path: Path) -> Template:
    return Template(canonical_path)


class TemplateContext:
    """Maintains defaults and caches loaded templates."""

    def __init__(
        self,
        *,
        default_variables: dict[str, Any] | None = None,
        default_renderers: Sequence[tuple[type, Callable[[Any], str]]] | None = None,
        base_path: Path | None = None,
    ):
        """Constructs a new context

        Args:
            default_variables: Default variables to use for substitution and rendering
            default_renderers: Default renderers to use for substitution and rendering
            base_path: Base path for template loading
        """

        self._variables: dict[str, Any] = defaulted(default_variables, dict[str, Any]())
        self._renderers: set[tuple[type, Callable[[Any], str]]] = set(
            defaulted(default_renderers, set[tuple[type, Callable[[Any], str]]]())
        )
        self._base_path: Path | None = base_path

    def load_template(self, path: Path, /) -> Template:
        """Load a template from file

        The loaded files are cached; every unique file is only retrieved from disk and parsed once.

        Args:
            path: Path to the template file
                  If this path is relative, it is assumed to be relative to the context's base path. If no base path
                  was provided, the cwd is used as reference point.

        Returns:
            The loaded template

        Raises:
            OSError: If the file cannot be opened
        """
        if not path.is_absolute():
            base_path = defaulted(self._base_path, Path.cwd())
            path = base_path / path

        path = path.resolve()
        return _load(path)

    def unresolved_identifiers(self, template: Template) -> set[str]:
        """Provides access to the set of unresolved identifiers in the template

        Args:
            template: The template to find unresolved identifiers in

        Returns:
            A set of unresolved identifiers in the template without identifiers set as variables in this context.
        """

        return template.unresolved_identifiers() - self._variables.keys()

    def substitute(
        self,
        template: Template,
        *,
        variables: dict[str, Any] | None = None,
        keep_comments: bool = True,
        renderers: Sequence[tuple[type, Callable[[Any], str]]] | None = None,
    ) -> Template:
        """Substitute variables into this template and return the result

        Args:
            template: The template to substitute into
            variables: The variables to substitute
            keep_comments: Whether to keep comments in the result
            renderers: Renderers to use for substitution

        Returns:
            The resulting template

        Raises:
            ValueError: If a variable cannot be substituted due to missing renderer
        """
        _variables = self._variables | defaulted(variables, dict[str, Any]())
        _renderers = list({*defaulted(renderers, ()), *self._renderers})
        return template.substitute(
            _variables, keep_comments=keep_comments, renderers=_renderers
        )

    def render(
        self,
        template: Template,
        *,
        variables: dict[str, Any] | None = None,
        renderers: Sequence[tuple[type, Callable[[Any], str]]] | None = None,
    ) -> str:
        """Render the template to string

        Args:
            template: The template to render
            variables: The variables to substitute
            renderers: Renderers to use for substitution

        Returns:
            The rendered template as string

        Raises:
            ValueError: If some variables in the template remain unresolved after substitution
        """
        _variables = self._variables | defaulted(variables, dict[str, Any]())
        _renderers = list({*defaulted(renderers, ()), *self._renderers})
        return template.render(_variables, renderers=_renderers)


def _make_var(fn: Callable[..., Any]) -> tuple[str, Any]:
    return (fn.__name__, fn)


class DefaultTemplateContext(TemplateContext):
    """A template context with sensible defaults."""

    _default_variables: dict[str, Any] = dict(
        (
            # built-ins
            _make_var(abs),
            _make_var(aiter),
            _make_var(all),
            _make_var(anext),
            _make_var(any),
            _make_var(ascii),
            _make_var(bin),
            _make_var(bool),
            _make_var(breakpoint),
            _make_var(bytearray),
            _make_var(bytes),
            _make_var(callable),
            _make_var(chr),
            _make_var(complex),
            _make_var(dict),
            _make_var(divmod),
            _make_var(enumerate),
            _make_var(filter),
            _make_var(float),
            _make_var(format),
            _make_var(frozenset),
            _make_var(getattr),
            _make_var(hasattr),
            _make_var(hash),
            _make_var(hex),
            _make_var(id),
            _make_var(int),
            _make_var(isinstance),
            _make_var(issubclass),
            _make_var(iter),
            _make_var(len),
            _make_var(list),
            _make_var(map),
            _make_var(max),
            _make_var(memoryview),
            _make_var(min),
            _make_var(next),
            _make_var(object),
            _make_var(oct),
            _make_var(open),
            _make_var(ord),
            _make_var(pow),
            _make_var(range),
            _make_var(repr),
            _make_var(reversed),
            _make_var(round),
            _make_var(set),
            _make_var(slice),
            _make_var(sorted),
            _make_var(str),
            _make_var(sum),
            _make_var(tuple),
            _make_var(type),
            _make_var(vars),
            _make_var(zip),
            # common stdlib functionality
            _make_var(Path),
            _make_var(date),
            _make_var(datetime),
            _make_var(timedelta),
            _make_var(deque),
            _make_var(namedtuple),
            _make_var(chain),
            _make_var(islice),
            _make_var(starmap),
            _make_var(product),
            _make_var(sqrt),
            _make_var(log),
            _make_var(sin),
            _make_var(cos),
            _make_var(tan),
            _make_var(hypot),
            _make_var(mean),
            _make_var(median),
            _make_var(stdev),
            _make_var(Decimal),
            ("re", re),
        )
    )
    _default_renderers: tuple[tuple[type, Callable[[Any], str]], ...] = ()

    def __init__(
        self,
        *,
        default_variables: dict[str, Any] | None = None,
        default_renderers: Sequence[tuple[type, Callable[[Any], str]]] | None = None,
        base_path: Path | None = None,
    ):
        """Constructs a new context

        Args:
            default_variables: Additional default variables to use for substitution and rendering
            default_renderers: Additional default renderers to use for substitution and rendering
            base_path: Base path for template loading
        """

        _variables = DefaultTemplateContext._default_variables | defaulted(
            default_variables, dict[str, Any]()
        )
        _renderers = list(
            {
                *defaulted(default_renderers, ()),
                *DefaultTemplateContext._default_renderers,
            }
        )
        super().__init__(
            default_variables=_variables,
            default_renderers=_renderers,
            base_path=base_path,
        )
