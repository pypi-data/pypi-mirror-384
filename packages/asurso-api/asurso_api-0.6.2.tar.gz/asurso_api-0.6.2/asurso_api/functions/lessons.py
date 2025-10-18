from ..utils import parse_response, MyAsyncClient, MyClient, range_to_dates
from typing import (
    List,
    Optional,
    Protocol,
    Union,
    TypeVar,
)
from pydantic import BaseModel, Field, computed_field, field_validator, ValidationInfo
from .. import enums
import datetime
import logging


logger = logging.getLogger(__name__)
T = TypeVar("T", datetime.datetime, None)


class AsyncASURSO(Protocol):
    _SID: str
    _login: str
    _password: str
    _client: MyAsyncClient


class ASURSO(Protocol):
    _SID: str
    _login: str
    _password: str
    _client: MyClient


class Classroom(BaseModel):
    raw_buildingName: Optional[str] = Field(None, alias="buildingName")
    raw_buildingId: Optional[int] = Field(None, alias="buildingId")
    raw_building: Optional[str] = Field(None, alias="building")
    name: str
    id: int

    @computed_field
    def building(self) -> str:
        if self.raw_building:
            return self.raw_building
        elif self.raw_buildingName:
            return self.raw_buildingName
        raise ValueError("???")

    @field_validator("raw_building", "raw_buildingName", "raw_buildingId")
    def mutually_exclusive1(cls, value: Union[str, int], info: ValidationInfo):
        if info.field_name == "raw_building":
            if (
                info.data.get("buildingName", None)
                and info.data.get("buildingId", None)
            ) is None:
                return value
            elif (
                info.data.get("buildingName", None) or info.data.get("buildingId", None)
            ) is not None:
                raise ValueError(
                    "Fields buildingName and buildingId is already provided! "
                    "Only use fields 'buildingName' and 'buildingID' or 'building'"
                )

        elif info.field_name in {"raw_buildingName", "raw_buildingId"}:
            if info.data.get("building", None) is None:
                return value
            raise ValueError(
                "Field building is already provided! "
                "Only use fields 'buildingName' and 'buildingID' or 'building'"
            )

        raise ValueError(
            f"Didn't found other fields with building, current field_name={info.field_name!r}"
        )

    def humanize(self):
        return f"<Кабинет {self.name} в корпусе {self.building}>"


class Teacher(BaseModel):
    first_name: str = Field(..., alias="firstName")
    last_name: str = Field(..., alias="lastName")
    middle_name: str = Field(..., alias="middleName")
    id: int

    @computed_field  # type: ignore[prop-decorator]
    @property
    def full_name(self) -> str:
        return " ".join([self.last_name, self.first_name, self.middle_name])


class Timetable(BaseModel):
    classroom: Classroom
    teacher: Teacher


class Task(BaseModel):
    id: int
    type: enums.EducationTaskType
    topic: str
    condition: Optional[str] = None
    is_required: bool = Field(..., alias="isRequired")
    attachments: List
    mark: Optional[str] = None

    @property
    def ru_type(self) -> str:
        if self.type == enums.EducationTaskType.HOME:
            return "Домашняя работа"
        return self.type.name.title().replace("_", "")


class Gradebook(BaseModel):
    id: int
    themes: List[str]
    lesson_type: enums.ThematicPlanLessonType = Field(..., alias="lessonType")
    tasks: List[Task]
    absence_type: Optional[enums.AbsenceType] = Field(None, alias="absenceType")

    @property
    def ru_lesson_type(self):
        if self.lesson_type == "Lesson":
            return "Лекция"
        elif self.lesson_type == "PracticalTraining":
            return "Практическая работа"
        return self.lesson_type


class Lesson(BaseModel):
    start_time: Optional[str] = Field(None, alias="startTime")
    end_time: Optional[str] = Field(None, alias="endTime")
    name: Optional[str] = None
    timetable: Optional[Timetable] = None
    gradebook: Optional[Gradebook] = None


class LessonsDay(BaseModel):
    date_raw: str = Field("", validation_alias="date")
    lessons: List[Lesson]
    is_holiday: bool = Field(..., alias="isHoliday")
    is_short: bool = Field(..., alias="isShort")

    @computed_field  # type: ignore[prop-decorator]
    @property
    def date(self) -> datetime.date:
        _d = datetime.date.fromisoformat(self.date_raw.split("T")[0])
        return _d

    @property
    def ru_date(self) -> str:
        """something like "01.01.2021" """
        return format(self.date, rus=True)


def format(date: Union[datetime.date, datetime.datetime], rus=False) -> str:
    if rus:
        return date.strftime("%d.%m.%Y")
    return date.strftime("%Y-%m-%d")


async def get_lessons_async(
    client: MyAsyncClient,
    start: Union[
        datetime.date, datetime.datetime, enums.LessonsPeriod
    ] = enums.LessonsPeriod.THIS_WEEK,
    end: Optional[Union[datetime.date, datetime.datetime]] = None,
    offset: Optional[int] = None,
) -> List[LessonsDay]:
    start_, end_ = range_to_dates(start, end, offset)

    r = await client.get(
        f"services/students/{client._SID}/lessons/{format(start_, rus=False)}/{format(end_, rus=False)}"
    )
    return parse_response(r, [LessonsDay])


def get_lessons_sync(
    client: MyClient,
    start: Union[
        datetime.date, datetime.datetime, enums.LessonsPeriod
    ] = enums.LessonsPeriod.THIS_WEEK,
    end: Optional[Union[datetime.date, datetime.datetime]] = None,
    offset: Optional[int] = None,
) -> List[LessonsDay]:
    start_, end_ = range_to_dates(start, end, offset)

    r = client.get(
        f"services/students/{client._SID}/lessons/{format(start_, rus=False)}/{format(end_, rus=False)}"
    )
    return parse_response(r, [LessonsDay])


class AsyncGetLessonsMethod:
    async def get_lessons(
        self: AsyncASURSO,
        start: Union[
            datetime.date, datetime.datetime, enums.LessonsPeriod
        ] = enums.LessonsPeriod.THIS_WEEK,
        end: Optional[Union[datetime.date, datetime.datetime]] = None,
        offset: Optional[int] = None,
    ):
        return await get_lessons_async(
            self._client, start=start, end=end, offset=offset
        )


class GetLessonsMethod:
    def get_lessons(
        self: ASURSO,
        start: Union[
            datetime.date, datetime.datetime, enums.LessonsPeriod
        ] = enums.LessonsPeriod.THIS_WEEK,
        end: Optional[Union[datetime.date, datetime.datetime]] = None,
        offset: Optional[int] = None,
    ):
        return get_lessons_sync(self._client, start=start, end=end, offset=offset)
