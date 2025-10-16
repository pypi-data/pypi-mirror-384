from collections.abc import Iterator
from dataclasses import dataclass
from typing import override


@dataclass(frozen=True)
class ParseContext:
    """Maintains the input for parsing"""

    source: str  # Complete input string
    index: int = 0  # Index of the next character to consume

    def __post_init__(self):
        """Makes sure that the index is valid"""
        if self.index < 0 or self.index > len(self.source):
            raise ValueError(
                f"index {self.index} out of range 0 ... {len(self.source)}"
            )

    def __getitem__(self, item: int | slice) -> str:
        """Provides indexing and slicing of the remaining input"""
        return self.source[self.index :].__getitem__(item)

    def __len__(self) -> int:
        """Provides the length of the remaining input"""
        return len(self.source) - self.index

    def __iter__(self) -> Iterator[str]:
        """Provides an iterator over the remaining input"""
        for i in range(self.__len__()):
            yield self.__getitem__(i)

    @override
    def __str__(self) -> str:
        """Provides a string representation of the remaining input"""
        return self.source[self.index :].__str__()

    def peek(self, count: int = 1) -> str:
        """Provides lookahead for n characters.

        Args:
            count: The lookahead size

        Raises:
            ValueError: The count is negative or greater than the remaining input.
        """
        if count < 0:
            raise ValueError("count cannot be negative")
        if self.__len__() < count:
            raise ValueError(
                f"remaining input too short: requested {count} but is {self.__len__()}"
            )
        return self.source[self.index : self.index + count]

    def consume(self, count: int = 1) -> "ParseContext":
        """Consumes some of the remaining input.

        Args:
            count: The number of characters to consume

        Raises:
            ValueError: The count is negative or greater than the remaining input.
        """
        if count < 0:
            raise ValueError("count cannot be negative")
        if self.__len__() < count:
            raise ValueError(
                f"remaining input too short: requested {count} but is {self.__len__()}"
            )
        return ParseContext(self.source, self.index + count)

    def at_eof(self) -> bool:
        """Checks if no remaining input is left."""
        return self.__len__() == 0

    def at_bof(self) -> bool:
        """Checks if no input has been consumed yet."""
        return self.index == 0

    def line_and_column(self) -> tuple[int, int]:
        """Computes the 1-based line and column of the current index in the input string"""
        line = 1
        column = 1
        for char in self.source[0 : self.index]:
            if char == "\n":
                line += 1
                column = 1
            else:
                column += 1
        return line, column
