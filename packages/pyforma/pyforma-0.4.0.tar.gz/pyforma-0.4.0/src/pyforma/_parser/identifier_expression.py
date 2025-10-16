from pyforma._ast.expression import ValueExpression
from .parser import parser
from .identifier import identifier
from .parse_context import ParseContext
from .parse_result import ParseResult
from pyforma._ast import IdentifierExpression, Expression


@parser
def identifier_expression(context: ParseContext) -> ParseResult[Expression]:
    """Parse an identifier expression."""

    r = identifier(context)
    if r.is_failure:
        return ParseResult.make_failure(
            expected=identifier.name,
            context=context,
            cause=r,
        )
    match r.success.result:
        case "True":
            return ParseResult.make_success(
                result=ValueExpression(True),
                context=r.context,
            )
        case "False":
            return ParseResult.make_success(
                result=ValueExpression(False),
                context=r.context,
            )
        case "None":
            return ParseResult.make_success(
                result=ValueExpression(None),
                context=r.context,
            )
        case _:
            return ParseResult.make_success(
                result=IdentifierExpression(r.success.result),
                context=r.context,
            )
