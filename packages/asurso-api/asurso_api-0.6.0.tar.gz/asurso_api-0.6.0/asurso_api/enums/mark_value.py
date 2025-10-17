from enum import Enum


class MarkValue(Enum):
    TWO = "Two"
    THREE = "Three"
    FOUR = "Four"
    FIVE = "Five"

    def to_value(self):
        return {
            MarkValue.TWO: "2",
            MarkValue.THREE: "3",
            MarkValue.FOUR: "4",
            MarkValue.FIVE: "5",
        }[self]
