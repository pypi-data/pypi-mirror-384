from ..utils import hash_password, parse_response, MyAsyncClient, MyClient
from pydantic import BaseModel, Field, field_validator, ValidationInfo
from typing import Protocol, List, Union, overload, Literal, Dict
from httpx import Response
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


class Address(BaseModel):
    kladr: str
    mail_address: str = Field(..., alias="mailAddress")
    region: str
    settlement: str


class Attestation(BaseModel):
    is_enabled: bool = Field(..., alias="isEnabled")


class EService(BaseModel):
    cache_enrollee_list_timeout: int = Field(..., alias="cacheEnrolleeListTimeout")
    cache_enrollee_timeout: int = Field(..., alias="cacheEnrolleeTimeout")
    cache_specialty_list_timeout: int = Field(..., alias="cacheSpecialtyListTimeout")
    is_enabled: bool = Field(..., alias="isEnabled")
    url: str
    use_rest_integration: bool = Field(..., alias="useRestIntegration")


class FactHours(BaseModel):
    is_enabled: bool = Field(..., alias="isEnabled")


class VkChats(BaseModel):
    community_id: str = Field(..., alias="communityId")
    community_token: str = Field(..., alias="communityToken")


class Administration(BaseModel):
    attestation: Attestation
    e_service: EService = Field(..., alias="eService")
    fact_hours: FactHours = Field(..., alias="factHours")
    organization_id: str = Field(..., alias="organizationId")
    vk_chats: VkChats = Field(..., alias="vkChats")


class BankingDetails(BaseModel):
    founder_type: str = Field(..., alias="founderType")
    founders: str
    inn: str
    kpp: str
    ogrn: str
    okato: str
    okogu: str
    okopth: str
    okpo: str
    okths: str
    oktmo: str
    okved: str
    others: str


class Organization(BaseModel):
    abbreviation: str
    actual_address: str = Field(..., alias="actualAddress")
    additional_name: str = Field(..., alias="additionalName")
    address: Address
    administration: Administration
    banking_details: BankingDetails = Field(..., alias="bankingDetails")
    director_name: str = Field(..., alias="directorName")
    director_position: str = Field(..., alias="directorPosition")
    email: str
    entrepreneur_name: str = Field(..., alias="entrepreneurName")
    fax: str
    head_organization_name: str = Field(..., alias="headOrganizationName")
    is_entrepreneur_owned: bool = Field(..., alias="isEntrepreneurOwned")
    is_subdepartment: bool = Field(..., alias="isSubdepartment")
    legal_address: str = Field(..., alias="legalAddress")
    legal_status: str = Field(..., alias="legalStatus")
    name: str
    occupancy: int
    organization_dept_id: int = Field(..., alias="organizationDeptId")
    organization_id: str = Field(..., alias="organizationId")
    organization_status: str = Field(..., alias="organizationStatus")
    organization_type: str = Field(..., alias="organizationType")
    phone: str
    rosobr_id: str = Field(..., alias="rosobrId")
    shift_count: int = Field(..., alias="shiftCount")
    short_name: str = Field(..., alias="shortName")
    site: str
    study_unit_number: str = Field(..., alias="studyUnitNumber")
    type: str


class Settings(BaseModel):
    organization: Organization


class Student(BaseModel):
    first_name: str = Field(..., alias="firstName")
    group_id: int = Field(..., alias="groupId")
    group_name: str = Field(..., alias="groupName")
    id: int
    last_name: str = Field(..., alias="lastName")
    middle_name: str = Field(..., alias="middleName")


class StudentRole(BaseModel):
    id: int
    student_group_id: int = Field(..., alias="studentGroupId")
    students: List[Student]


class Spo(BaseModel):
    first_name: str = Field(..., alias="firstName")
    is_trusted: bool = Field(..., alias="isTrusted")
    last_name: str = Field(..., alias="lastName")
    middle_name: str = Field(..., alias="middleName")
    settings: Settings
    student_role: StudentRole = Field(..., alias="studentRole")


class LoginInfo(BaseModel):
    cookies_UID: str = Field(..., alias="__cookie__UID")
    install_name: str = Field(..., alias="installName")
    local_network: bool = Field(..., alias="localNetwork")
    tenant_name: str = Field(..., alias="tenantName")
    tenants: Dict[str, Spo] = Field(...)
    """Dict with key(s) matching `spo_\\d+`. 
    Its better to use with `tenant_name` to get `Spo` object """

    @field_validator("tenants")
    def validate_tenants(cls, tenants):
        if any(not(x.startswith("spo_") and x[4:].isdigit()) for x in tenants):
            raise ValueError(f"Found not \"spo_\\d+\" key in tenants")
        return tenants


class LoginInfoPerm(LoginInfo):
    cookies_AspNetCoreCookies: str = Field(..., alias="__cookie__.AspNetCore.Cookies")
    cookies_AspNetCoreSession: None = None


class LoginInfoTemp(LoginInfo):
    cookies_AspNetCoreCookies: None = None
    cookies_AspNetCoreSession: str = Field(..., alias="__cookie__.AspNetCore.Session")


def _format_output(client: Union[MyAsyncClient, MyClient], result: LoginInfo) -> None:
    tenant_name = result.tenant_name
    tenant = result.tenants[tenant_name]
    SID = tenant.student_role.id
    client._SID = str(SID)


def _parse(client: Union[MyClient, MyAsyncClient], r: Response, is_remember: bool):
    client.cookies.update(r.cookies)
    result = parse_response(r, LoginInfoPerm if is_remember else LoginInfoTemp)
    _format_output(client, result)
    return result


async def login_async(
    client: MyAsyncClient,
    login: str,
    password: str,
    is_remember=False,
    need_to_hash=True,
):
    if need_to_hash:
        password = hash_password(password)

    r = await client.post(
        "/services/security/login",
        json=dict(login=login, password=password, isRemember=is_remember),
    )
    return _parse(client, r, is_remember=is_remember)


def login_sync(
    client: MyClient,
    login: str,
    password: str,
    is_remember=False,
    need_to_hash=True,
) -> Union[LoginInfoTemp, LoginInfoPerm]:
    if need_to_hash:
        password = hash_password(password)

    r = client.post(
        "/services/security/login",
        json=dict(login=login, password=password, isRemember=is_remember),
    )
    return _parse(client, r, is_remember=is_remember)


class AsyncLoginMethod:
    @overload
    async def login(self: AsyncASURSO) -> LoginInfoTemp: ...
    @overload
    async def login(self: AsyncASURSO, is_remember: Literal[False]) -> LoginInfoTemp: ...
    @overload
    async def login(self: AsyncASURSO, is_remember: Literal[True]) -> LoginInfoPerm: ...
    async def login(self: AsyncASURSO, is_remember=False):
        result = await login_async(
            self._client, self._login, self._password, is_remember, need_to_hash=False
        )
        return result


class LoginMethod:
    @overload
    def login(self: ASURSO) -> LoginInfoTemp: ...
    @overload
    def login(self: ASURSO, is_remember: Literal[False]) -> LoginInfoTemp: ...
    @overload
    def login(self: ASURSO, is_remember: Literal[True]) -> LoginInfoPerm: ...
    def login(self: ASURSO, is_remember=False):
        result = login_sync(
            self._client, self._login, self._password, is_remember, need_to_hash=False
        )
        return result
