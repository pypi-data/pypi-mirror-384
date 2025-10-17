from ..utils import parse_response, MyAsyncClient, MyClient
from .. import enums
from typing import List, Optional, Protocol, Dict
from pydantic import BaseModel, Field
import logging


logger = logging.getLogger(__name__)


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


class Term(BaseModel):
    id: int
    is_active: bool = Field(..., alias="isActive")
    number: int


class AcademicYear(BaseModel):
    id: int
    number: int
    term_type: enums.TermType = Field(..., alias="termType")
    terms: List[Term]


class FinalMark(BaseModel):
    value: Optional[enums.MarkValue] = None


class FieldMark(BaseModel):
    value: Optional[enums.MarkValue] = None


class Marks(BaseModel):
    field: Optional[FieldMark] = Field(None, pattern=r"^\d$")
    raw: Dict = Field(default_factory=lambda: dict())

    def __init__(self, **data):
        """Just save original dict"""
        super().__init__(**data)
        self.raw = data


class Subject(BaseModel):
    name: str
    marks: Marks
    final_mark: FinalMark = Field(..., alias='finalMark')


class Attestation(BaseModel):
    academic_years: List[AcademicYear] = Field(..., alias="academicYears")
    subjects: List[Subject]


async def get_attestation_async(client: MyAsyncClient) -> Attestation:
    r = await client.get(f"services/students/{client._SID}/attestation")
    return parse_response(r, Attestation)


def get_attestation_sync(client: MyClient) -> Attestation:
    r = client.get(f"services/students/{client._SID}/attestation")
    return parse_response(r, Attestation)


class AsyncGetAttestationMethod:
    async def get_attestation(self: AsyncASURSO) -> Attestation:
        return await get_attestation_async(self._client)


class GetAttestationMethod:
    def get_attestation(self: ASURSO) -> Attestation:
        return get_attestation_sync(self._client)
