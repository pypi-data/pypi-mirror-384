from ..utils import parse_response, MyAsyncClient, MyClient
from typing import Protocol, List
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


class TitleItem(BaseModel):
    language_code: str
    value: str


class LessonsMenu(BaseModel):
    is_enabled: bool = Field(..., alias="isEnabled")
    session_table_enabled: bool = Field(..., alias="sessionTableEnabled")
    examination_enabled: bool = Field(..., alias="examinationEnabled")
    prof_module_examination_enabled: bool = Field(
        ..., alias="profModuleExaminationEnabled"
    )
    courseworks_enabled: bool = Field(..., alias="courseworksEnabled")


class EducationMenu(BaseModel):
    is_enabled: bool = Field(..., alias="isEnabled")
    working_programs_enabled: bool = Field(..., alias="workingProgramsEnabled")


class UsersMenu(BaseModel):
    is_enabled: bool = Field(..., alias="isEnabled")
    enrollees_enabled: bool = Field(..., alias="enrolleesEnabled")
    parents_enabled: bool = Field(..., alias="parentsEnabled")
    expelled_students_enabled: bool = Field(..., alias="expelledStudentsEnabled")
    departments_enabled: bool = Field(..., alias="departmentsEnabled")


class ForeignInstallation(BaseModel):
    is_enabled: bool = Field(..., alias="isEnabled")


class AvailableLanguage(BaseModel):
    key: str
    value: str


class Info(BaseModel):
    title: List[TitleItem]
    is_file_storage_available: bool = Field(..., alias="isFileStorageAvailable")
    is_supplementary_education_certificates_available: bool = Field(
        ..., alias="isSupplementaryEducationCertificatesAvailable"
    )
    is_edit_student_factual_hours_available_for_organization: bool = Field(
        ..., alias="isEditStudentFactualHoursAvailableForOrganization"
    )
    is_factual_hours_available_systemwide: bool = Field(
        ..., alias="isFactualHoursAvailableSystemwide"
    )
    are_chats_enabled: bool = Field(..., alias="areChatsEnabled")
    is_ern_enabled: bool = Field(..., alias="isErnEnabled")
    is_employment_enabled: bool = Field(..., alias="isEmploymentEnabled")
    is_reports_menu_enabled: bool = Field(..., alias="isReportsMenuEnabled")
    is_portfolio_menu_enabled: bool = Field(..., alias="isPortfolioMenuEnabled")
    is_administration_menu_enabled: bool = Field(
        ..., alias="isAdministrationMenuEnabled"
    )
    is_org_license_enabled: bool = Field(..., alias="isOrgLicenseEnabled")
    is_org_details_enabled: bool = Field(..., alias="isOrgDetailsEnabled")
    lessons_menu: LessonsMenu = Field(..., alias="lessonsMenu")
    education_menu: EducationMenu = Field(..., alias="educationMenu")
    users_menu: UsersMenu = Field(..., alias="usersMenu")
    foreign_installation: ForeignInstallation = Field(..., alias="foreignInstallation")
    default_language: str = Field(..., alias="defaultLanguage")
    available_languages: List[AvailableLanguage] = Field(
        ..., alias="availableLanguages"
    )
    import_encoding: str = Field(..., alias="importEncoding")


async def get_info_async(client: MyAsyncClient) -> Info:
    r = await client.get("/services/people/system/info")
    return parse_response(r, Info)


def get_info_sync(client: MyClient) -> Info:
    r = client.get("/services/people/system/info")
    return parse_response(r, Info)


class AsyncGetInfoMethod:
    async def get_info(self: AsyncASURSO) -> Info:
        return await get_info_async(self._client)


class GetInfoMethod:
    def get_info(self: ASURSO) -> Info:
        return get_info_sync(self._client)
