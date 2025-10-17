from ..utils import parse_response, MyAsyncClient, MyClient
from pydantic import BaseModel, Field
from typing import Protocol
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
    region: str
    settlement: str
    mail_address: str = Field(..., alias='mailAddress')
    kladr: str


class BankingDetails(BaseModel):
    okved: str
    inn: str
    kpp: str
    ogrn: str
    oktmo: str
    okopth: str
    okths: str
    okpo: str
    others: str
    okogu: str
    founder_type: str = Field(..., alias='founderType')
    founders: str
    okato: str


class EService(BaseModel):
    url: str
    is_enabled: bool = Field(..., alias='isEnabled')
    cache_enrollee_list_timeout: int = Field(..., alias='cacheEnrolleeListTimeout')
    cache_specialty_list_timeout: int = Field(..., alias='cacheSpecialtyListTimeout')
    cache_enrollee_timeout: int = Field(..., alias='cacheEnrolleeTimeout')
    use_rest_integration: bool = Field(..., alias='useRestIntegration')


class Attestation(BaseModel):
    is_enabled: bool = Field(..., alias='isEnabled')


class FactHours(BaseModel):
    is_enabled: bool = Field(..., alias='isEnabled')


class VkChats(BaseModel):
    community_id: str = Field(..., alias='communityId')
    community_token: str = Field(..., alias='communityToken')


class Administration(BaseModel):
    e_service: EService = Field(..., alias='eService')
    organization_id: str = Field(..., alias='organizationId')
    attestation: Attestation
    fact_hours: FactHours = Field(..., alias='factHours')
    vk_chats: VkChats = Field(..., alias='vkChats')


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


async def get_organization_async(client: MyAsyncClient) -> Organization:
    r = await client.get("/services/people/organization")
    return parse_response(r, Organization)


def get_organization_sync(client: MyClient) -> Organization:
    r = client.get("/services/people/organization")
    return parse_response(r, Organization)


class AsyncGetOrganizationMethod:
    async def get_organization(self: AsyncASURSO):
        return await get_organization_async(self._client)


class GetOrganizationMethod:
    def get_organization(self: ASURSO):
        return get_organization_sync(self._client)
