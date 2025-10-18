from enum import Enum, auto


class LessonsPeriod(Enum):
    # days
    TODAY = auto()
    NEXT_DAY = auto()
    PREVIOUS_DAY = auto()

    # weeks
    NEXT_WEEK = auto()
    THIS_WEEK = auto()
    PREVIOUS_WEEK = auto()

    # months
    NEXT_MONTH = auto()
    THIS_MONTH = auto()
    PREVIOUS_MONTH = auto()
