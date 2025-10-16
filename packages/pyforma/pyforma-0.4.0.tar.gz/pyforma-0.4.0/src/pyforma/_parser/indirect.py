from functools import cache
import importlib
from .parser import Parser, parser
from .parse_context import ParseContext
from .parse_result import ParseResult
from pyforma._util import defaulted


class indirect[T]:
    """Indirectly calls another parser"""

    @cache
    def __new__(cls, module_path: str, name: str | None = None) -> Parser[T]:
        """Indirectly calls the parser in the given module

        Args:
            module_path: Module and symbol path, e.g. "some.module.variable_name"
            name: Optional name for the parser

        Returns:
            The parser instance
        """

        @parser(name=defaulted(name, f"indirect({module_path})"))
        def indirect_parser(context: ParseContext) -> ParseResult[T]:
            module_name, attr_name = module_path.rsplit(".", 1)
            module = importlib.import_module(module_name)
            parser = getattr(module, attr_name)
            result = parser(context)
            return result

        return indirect_parser
