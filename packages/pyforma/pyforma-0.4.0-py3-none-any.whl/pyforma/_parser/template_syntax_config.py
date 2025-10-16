from dataclasses import dataclass, asdict
from typing import Annotated

from annotated_types import MinLen


@dataclass(frozen=True)
class BlockSyntaxConfig:
    open: Annotated[str, MinLen(1)]
    close: Annotated[str, MinLen(1)]

    def __post_init__(self):
        if self.open == "" or self.close == "":
            raise ValueError("open and close symbol can't be empty")

        if self.open == self.close:
            raise ValueError("open and close symbol can't be identical")


@dataclass(frozen=True)
class TemplateSyntaxConfig:
    comment: BlockSyntaxConfig = BlockSyntaxConfig("{#", "#}")
    expression: BlockSyntaxConfig = BlockSyntaxConfig("{{", "}}")
    environment: BlockSyntaxConfig = BlockSyntaxConfig("{%", "%}")

    def __post_init__(self):
        if (
            len(
                {
                    *asdict(self.comment).values(),
                    *asdict(self.expression).values(),
                    *asdict(self.environment).values(),
                }
            )
            != 6
        ):
            raise ValueError("symbols must not overlap!")
