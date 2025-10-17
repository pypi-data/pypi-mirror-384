from . import login
from . import info
from . import dashboard
from . import lessons
from . import attestation
from . import chats
from . import organization
from . import reports
from . import logout


class AsyncMethods(
    login.AsyncLoginMethod,
    info.AsyncGetInfoMethod,
    dashboard.AsyncGetDashboardMethod,
    lessons.AsyncGetLessonsMethod,
    attestation.AsyncGetAttestationMethod,
    chats.AsyncGetChatsMethod,
    organization.AsyncGetOrganizationMethod,
    reports.AsyncGetReportMethods,
    logout.AsyncLogoutMethod,
):
    pass


class Methods(
    login.LoginMethod,
    info.GetInfoMethod,
    dashboard.GetDashboardMethod,
    lessons.GetLessonsMethod,
    attestation.GetAttestationMethod,
    chats.GetChatsMethod,
    organization.GetOrganizationMethod,
    reports.GetReportMethods,
    logout.LogoutMethod,
):
    pass
