import re
from enum import StrEnum
from maleo.types.string import ListOfStrs


class CaseFormatter:
    class Case(StrEnum):
        CAMEL = "camel"
        PASCAL = "pascal"
        SNAKE = "snake"

        @classmethod
        def choices(cls) -> ListOfStrs:
            return [e.value for e in cls]

    @staticmethod
    def to_camel(text: str) -> str:
        """Converts snake_case or PascalCase to camelCase."""
        words = re.split(r"[_\s]", text)  # Handle snake_case and spaces
        return words[0].lower() + "".join(word.capitalize() for word in words[1:])

    @staticmethod
    def to_pascal(text: str) -> str:
        """Converts snake_case or camelCase to PascalCase."""
        words = re.split(r"[_\s]", text)
        return "".join(word.capitalize() for word in words)

    @staticmethod
    def to_snake(text: str) -> str:
        """Converts camelCase or PascalCase to snake_case."""
        return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", text).lower()

    @staticmethod
    def convert(text: str, target: Case) -> str:
        """Converts text to the specified case format."""
        if target is CaseFormatter.Case.CAMEL:
            return CaseFormatter.to_camel(text)
        elif target is CaseFormatter.Case.PASCAL:
            return CaseFormatter.to_pascal(text)
        elif target is CaseFormatter.Case.SNAKE:
            return CaseFormatter.to_snake(text)
