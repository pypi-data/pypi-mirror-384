from .enums import LessonsPeriod
from .exceptions import UnauthorizedError
from typing import (
    List,
    Tuple,
    Dict,
    Callable,
    Optional,
    Union,
    TypeVar,
    Type,
    cast,
    overload,
)
import hashlib
import logging
import datetime
import base64
import httpx
from json import JSONDecodeError


logger = logging.getLogger(__name__)
T = TypeVar("T")


def range_to_dates(
    start: Optional[Union[datetime.date, datetime.datetime, LessonsPeriod]] = None,
    end: Optional[Union[datetime.date, datetime.datetime]] = None,
    offset: Optional[int] = None,
) -> Tuple[datetime.date, datetime.date]:
    """Get two datetime.date from some range"""
    cur = datetime.datetime.now()
    if isinstance(start, datetime.date):
        start = datetime.datetime.combine(start, cur.time())

    if isinstance(end, datetime.date):
        end = datetime.datetime.combine(end, cur.time())

    for_enum: Dict[LessonsPeriod, Tuple[datetime.datetime, datetime.datetime]] = {
        # days
        LessonsPeriod.PREVIOUS_DAY: (
            cur - datetime.timedelta(days=1),
            cur - datetime.timedelta(days=1),
        ),
        LessonsPeriod.TODAY: (cur, cur),
        LessonsPeriod.NEXT_DAY: (
            cur + datetime.timedelta(days=1),
            cur + datetime.timedelta(days=1),
        ),
        # weeks
        LessonsPeriod.PREVIOUS_WEEK: (
            cur - datetime.timedelta(days=cur.weekday(), weeks=1),
            cur - datetime.timedelta(days=cur.weekday() - 6, weeks=1),
        ),
        LessonsPeriod.THIS_WEEK: (
            cur - datetime.timedelta(days=cur.weekday()),
            cur - datetime.timedelta(days=cur.weekday() - 6),
        ),
        LessonsPeriod.NEXT_WEEK: (
            cur - datetime.timedelta(days=cur.weekday(), weeks=-1),
            cur - datetime.timedelta(days=cur.weekday() - 6, weeks=-1),
        ),
        # months
        LessonsPeriod.PREVIOUS_MONTH: (
            datetime.datetime(cur.year, cur.month - 1, 1),
            datetime.datetime(cur.year, cur.month, 1) - datetime.timedelta(days=1),
        ),
        LessonsPeriod.THIS_MONTH: (
            datetime.datetime(cur.year, cur.month, 1),
            datetime.datetime(cur.year, cur.month + 1, 1) - datetime.timedelta(days=1),
        ),
        LessonsPeriod.NEXT_MONTH: (
            datetime.datetime(cur.year, cur.month + 1, 1),
            datetime.datetime(cur.year, cur.month + 2, 1) - datetime.timedelta(days=1),
        ),
    }

    if isinstance(start, LessonsPeriod):
        return for_enum[start][0].date(), for_enum[start][1].date()

    N = type(None)
    D = datetime.datetime

    start = cast(datetime.datetime, start)
    offset = cast(int, offset)
    end = cast(datetime.datetime, end)

    for_dates: Dict[
        Tuple[
            Union[Type[None], Type[datetime.datetime]],
            Union[Type[None], Type[int]],
            Union[Type[None], Type[datetime.datetime]],
        ],
        Callable[[], Union[Tuple[datetime.date, datetime.date], Exception]],
    ] = {
        (N, N, N): lambda: (cur.date(), (cur + datetime.timedelta(days=7)).date()),
        (N, N, D): lambda: (cur.date(), end.date()),
        (N, int, N): lambda: (
            cur.date(),
            (cur + datetime.timedelta(days=offset)).date(),
        ),
        (N, int, D): lambda: (
            (end - datetime.timedelta(days=offset)).date(),
            end.date(),
        ),
        (D, N, N): lambda: (start.date(), (start + datetime.timedelta(days=7)).date()),
        (D, N, D): lambda: (start.date(), end.date()),
        (D, int, N): lambda: (start.date(), (start + datetime.timedelta(days=offset))),
        (D, int, D): lambda: ValueError(
            "Use only (start+end, start+offset, offset+end) pair"
        ),
    }

    result = for_dates[type(start), type(offset), type(end)]()
    if isinstance(result, Exception):
        raise result
    return result


def hash_password(password: str) -> str:
    p1 = hashlib.sha256(password.encode()).digest()
    r = base64.b64encode(p1).decode()
    return r


@overload
def parse_response(r: httpx.Response, my_type: Type[T]) -> T: ...
@overload
def parse_response(r: httpx.Response, my_type: List[Type[T]]) -> List[T]: ...
def parse_response(
    r: httpx.Response,
    my_type: Union[Type[T], List[Type[T]]],
) -> Union[T, List[T]]:
    check_for_errors(r)
    data = r.json()
    for (cookie_name, cookie_value) in dict(r.cookies).items():
        data[f"__cookie__{cookie_name}"] = cookie_value
    logger.debug(f"{r.url=}, {data=}")

    if isinstance(my_type, list) and isinstance(my_type[0], type):
        return [my_type[0](**d) for d in data]

    elif isinstance(my_type, list):
        raise ValueError(
            f"You need to provide something like list[MyClass], not {my_type}..."
        )

    elif isinstance(my_type, (bool, float, int, str, list, tuple, set, dict)):
        result = data

    else:
        result = my_type(**data)
    return result


def check_for_errors(r: httpx.Response) -> None:
    if r.status_code == 401:
        try:
            d = r.json()
        except JSONDecodeError:
            raise UnauthorizedError("without message")
        if "responseStatus" not in d or "message" not in d["responseStatus"]:
            raise UnauthorizedError("without message")
        raise UnauthorizedError(d["responseStatus"]["message"])
    return


class MyAsyncClient(httpx.AsyncClient):
    _SID: str = ""


class MyClient(httpx.Client):
    _SID: str = ""
