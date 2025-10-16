from abc import ABC, abstractmethod
from collections.abc import Sized, Iterable
from dataclasses import dataclass
from typing import Any, override, Annotated

from annotated_types import MinLen

from .expression import Expression, ValueExpression
from .comment import Comment


def _destructure_value(identifiers: tuple[str, ...], value: Any) -> dict[str, Any]:
    if len(identifiers) > 1:
        if not isinstance(value, Sized):
            raise TypeError(f"Can't unpack {value}: not sized")
        elif len(identifiers) != len(value):
            raise TypeError(
                f"Can't unpack {value}: has length {len(identifiers)} instead of {len(identifiers)}"
            )
        if not isinstance(value, Iterable):
            raise TypeError(f"Can't unpack {value}: not iterable")
        vs = {k: v for k, v in zip(identifiers, value)}
    else:
        vs = {identifiers[0]: value}  # pyright: ignore[reportGeneralTypeIssues]

    return vs


class Environment(ABC):
    """Environment base class"""

    @abstractmethod
    def identifiers(self) -> set[str]: ...

    @abstractmethod
    def substitute(self, variables: dict[str, Any]) -> "Environment": ...


@dataclass(frozen=True)
class TemplateEnvironment(Environment):
    """Template Environment class"""

    content: tuple[str | Comment | Expression | Environment, ...]

    @override
    def identifiers(self) -> set[str]:
        return set[str]().union(
            *(
                e.identifiers()
                for e in self.content
                if isinstance(e, Expression) or isinstance(e, Environment)
            )
        )

    @override
    def substitute(self, variables: dict[str, Any]) -> "TemplateEnvironment":
        def subs(
            e: str | Comment | Expression | Environment,
        ) -> str | Comment | Expression | Environment:
            match e:
                case str() | Comment():
                    return e
                case Expression() | Environment():  # pragma: no branch
                    return e.substitute(variables)

        return TemplateEnvironment(tuple(subs(e) for e in self.content))


@dataclass(frozen=True)
class WithEnvironment(Environment):
    """With-Environment"""

    @dataclass(frozen=True)
    class Destructuring:
        identifiers: tuple[str, ...]
        expression: Expression

    variables: tuple[Destructuring, ...]
    content: TemplateEnvironment

    @override
    def identifiers(self) -> set[str]:
        content_ids = self.content.identifiers() - set[str]().union(
            *[d.identifiers for d in self.variables]
        )
        var_ids = set[str]().union(
            *[d.expression.identifiers() for d in self.variables]
        )
        return content_ids | var_ids

    @override
    def substitute(self, variables: dict[str, Any]) -> Environment:
        _variables = tuple(
            WithEnvironment.Destructuring(
                destructuring.identifiers,
                destructuring.expression.substitute(variables),
            )
            for destructuring in self.variables
        )
        relevant_variables = {
            key: val
            for key, val in variables.items()
            if key not in set[str]().union(*[d.identifiers for d in self.variables])
        }
        for destructuring in _variables:
            if isinstance(destructuring.expression, ValueExpression):
                relevant_variables |= _destructure_value(
                    destructuring.identifiers, destructuring.expression.value
                )

        _content = self.content.substitute(relevant_variables)
        _remaining_identifiers = _content.identifiers()
        _variables = tuple(
            destructuring
            for destructuring in _variables
            if any(iden in _remaining_identifiers for iden in destructuring.identifiers)
        )

        if len(_variables) == 0:
            return _content

        return WithEnvironment(_variables, _content)


@dataclass(frozen=True)
class IfEnvironment(Environment):
    """If-Environment"""

    ifs: tuple[tuple[Expression, TemplateEnvironment], ...]
    else_content: TemplateEnvironment

    @override
    def identifiers(self) -> set[str]:
        return (
            set[str]().union(
                *[expr.identifiers() | env.identifiers() for expr, env in self.ifs]
            )
            | self.else_content.identifiers()
        )

    @override
    def substitute(self, variables: dict[str, Any]) -> "Environment":
        _ifs: tuple[tuple[Expression, TemplateEnvironment], ...] = ()

        for expr, env in self.ifs:
            _expr = expr.substitute(variables)

            if isinstance(_expr, ValueExpression):
                if _expr.value:
                    if len(_ifs) == 0:
                        return env.substitute(variables)
                    else:
                        _ifs += ((_expr, env.substitute(variables)),)
            else:
                _ifs += ((_expr, env.substitute(variables)),)

        _else_content = self.else_content.substitute(variables)

        if len(_ifs) == 0:
            return _else_content
        return IfEnvironment(_ifs, _else_content)


@dataclass(frozen=True)
class ForEnvironment(Environment):
    """For-Environment"""

    identifier: Annotated[tuple[str, ...], MinLen(1)]
    expression: Expression
    content: TemplateEnvironment

    @override
    def identifiers(self) -> set[str]:
        content_ids = self.content.identifiers() - set(self.identifier)
        return self.expression.identifiers() | content_ids

    @override
    def substitute(self, variables: dict[str, Any]) -> "Environment":
        _expression = self.expression.substitute(variables)
        _content = self.content.substitute(
            {k: v for k, v in variables.items() if k not in self.identifier}
        )

        if isinstance(_expression, ValueExpression):
            _contents: list[TemplateEnvironment] = []
            for value in _expression.value:
                vs = _destructure_value(self.identifier, value)
                c = _content.substitute(vs)
                _contents.append(c)
            return TemplateEnvironment(tuple(_contents)).substitute({})
        else:
            return ForEnvironment(self.identifier, _expression, _content)
