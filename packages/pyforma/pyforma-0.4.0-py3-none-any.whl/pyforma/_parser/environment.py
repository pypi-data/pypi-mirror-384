from functools import cache

from pyforma._ast.environment import (
    Environment,
    IfEnvironment,
    TemplateEnvironment,
    WithEnvironment,
    ForEnvironment,
)
from pyforma._ast.comment import Comment
from pyforma._ast.expression import Expression
from .parse_context import ParseContext
from .parse_result import ParseResult
from .until import until
from .delimited import delimited
from .identifier import identifier
from .repetition import repetition
from .option import option
from .alternation import alternation
from .non_empty import non_empty
from .sequence import sequence
from .literal import literal
from .whitespace import whitespace
from .transform_result import transform_success
from .expression import expression
from .parser import Parser, parser
from .template_syntax_config import TemplateSyntaxConfig

_destructuring = delimited(
    delim=sequence(whitespace, literal(","), whitespace),
    content=identifier,
    allow_trailing_delim=False,
)


@cache
def literal_environment(syntax: TemplateSyntaxConfig) -> Parser[TemplateEnvironment]:
    parse_open = transform_success(
        sequence(
            literal(syntax.environment.open),
            whitespace,
            literal("literal"),
            option(
                transform_success(
                    sequence(non_empty(whitespace), identifier),
                    transform=lambda s: s[1],
                )
            ),
            whitespace,
            literal(syntax.environment.close),
        ),
        transform=lambda s: s[3],
    )

    @parser
    def parse_literal_env(context: ParseContext) -> ParseResult[TemplateEnvironment]:
        iden = parse_open(context)
        if iden.is_failure:
            return ParseResult[TemplateEnvironment].make_failure(
                context=context,
                expected="literal environment",
                cause=iden,
            )

        if iden.success.result:
            iden_parser = sequence(whitespace, literal(iden.success.result))
        else:
            iden_parser = parser(
                lambda context: ParseResult[str].make_success(
                    context=context, result=""
                )
            )

        parse_close = transform_success(
            sequence(
                literal(syntax.environment.open),
                whitespace,
                literal("endliteral"),
                iden_parser,
                whitespace,
                literal(syntax.environment.close),
            ),
            transform=lambda s: None,
        )
        parse_content = until(parse_close)

        parse = sequence(parse_content, parse_close, name="literal-environment")
        result = parse(iden.context)

        return ParseResult[TemplateEnvironment].make_success(
            context=result.context,
            result=TemplateEnvironment(
                content=(result.success.result[0],),
            ),
        )

    return parse_literal_env


@cache
def with_environment(
    syntax: TemplateSyntaxConfig,
    template_parser: Parser[tuple[str | Comment | Expression | Environment, ...]],
) -> Parser[WithEnvironment]:
    parse_open = transform_success(
        sequence(
            literal(syntax.environment.open),
            whitespace,
            literal("with"),
            non_empty(whitespace),
            delimited(
                delim=sequence(whitespace, literal(";"), whitespace),
                content=transform_success(
                    sequence(
                        _destructuring, whitespace, literal("="), whitespace, expression
                    ),
                    transform=lambda s: (s[0], s[4]),
                ),
                allow_trailing_delim=True,
            ),
            whitespace,
            literal(syntax.environment.close),
        ),
        transform=lambda s: s[4],
    )
    parse_close = transform_success(
        sequence(
            literal(syntax.environment.open),
            whitespace,
            literal("endwith"),
            whitespace,
            literal(syntax.environment.close),
        ),
        transform=lambda s: None,
    )

    parse = sequence(parse_open, template_parser, parse_close, name="with-environment")

    return transform_success(
        parse,
        transform=lambda s: WithEnvironment(
            variables=tuple(WithEnvironment.Destructuring(e[0], e[1]) for e in s[0]),
            content=TemplateEnvironment(s[1]),
        ),
    )


@cache
def if_environment(
    syntax: TemplateSyntaxConfig,
    template_parser: Parser[tuple[str | Comment | Expression | Environment, ...]],
) -> Parser[IfEnvironment]:
    parse_if = transform_success(
        sequence(
            literal(syntax.environment.open),
            whitespace,
            literal("if"),
            non_empty(whitespace),
            expression,
            whitespace,
            literal(syntax.environment.close),
        ),
        transform=lambda s: s[4],
    )
    parse_elif = transform_success(
        sequence(
            literal(syntax.environment.open),
            whitespace,
            literal("elif"),
            non_empty(whitespace),
            expression,
            whitespace,
            literal(syntax.environment.close),
        ),
        transform=lambda s: s[4],
    )
    parse_else = transform_success(
        sequence(
            literal(syntax.environment.open),
            whitespace,
            literal("else"),
            whitespace,
            literal(syntax.environment.close),
        ),
        transform=lambda s: None,
    )
    parse_close = transform_success(
        sequence(
            literal(syntax.environment.open),
            whitespace,
            literal("endif"),
            whitespace,
            literal(syntax.environment.close),
        ),
        transform=lambda s: None,
    )

    parse = transform_success(
        sequence(
            parse_if,
            template_parser,
            repetition(sequence(parse_elif, template_parser)),
            transform_success(
                option(sequence(parse_else, template_parser)),
                transform=lambda s: TemplateEnvironment(())
                if s is None
                else TemplateEnvironment(s[1]),
            ),
            parse_close,
        ),
        transform=lambda s: (
            tuple(
                (expr, TemplateEnvironment(templ))
                for expr, templ in ((s[0], s[1]), *s[2])
            ),
            s[3],
        ),
        name="if-environment",
    )

    return transform_success(
        parse,
        transform=lambda s: IfEnvironment(
            ifs=s[0],
            else_content=s[1],
        ),
    )


@cache
def for_environment(
    syntax: TemplateSyntaxConfig,
    template_parser: Parser[tuple[str | Comment | Expression | Environment, ...]],
) -> Parser[ForEnvironment]:
    parse_open = transform_success(
        sequence(
            literal(syntax.environment.open),
            whitespace,
            literal("for"),
            non_empty(whitespace),
            _destructuring,
            non_empty(whitespace),
            literal("in"),
            non_empty(whitespace),
            expression,
            whitespace,
            literal(syntax.environment.close),
        ),
        transform=lambda s: (s[4], s[8]),
    )
    parse_close = transform_success(
        sequence(
            literal(syntax.environment.open),
            whitespace,
            literal("endfor"),
            whitespace,
            literal(syntax.environment.close),
        ),
        transform=lambda s: None,
    )

    parse = sequence(parse_open, template_parser, parse_close, name="for-environment")

    return transform_success(
        parse,
        transform=lambda s: ForEnvironment(
            identifier=s[0][0],
            expression=s[0][1],
            content=TemplateEnvironment(s[1]),
        ),
    )


@cache
def environment(
    syntax: TemplateSyntaxConfig,
    template_parser: Parser[tuple[str | Comment | Expression | Environment, ...]],
) -> Parser[Environment]:
    """Creates an environment parser using the provided template syntax

    Args:
        syntax: The syntax config to use

    Returns:
        The environment parser.
    """

    result = alternation(
        with_environment(syntax, template_parser),
        if_environment(syntax, template_parser),
        for_environment(syntax, template_parser),
        literal_environment(syntax),
        name="environment",
    )
    return result
