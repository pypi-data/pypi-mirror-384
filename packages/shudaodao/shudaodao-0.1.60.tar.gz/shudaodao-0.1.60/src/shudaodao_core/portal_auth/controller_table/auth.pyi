from .. import get_engine_name as get_engine_name
from ...auth.auth_router import AuthRouter as AuthRouter
from ...config.app_config import AppConfig as AppConfig
from ...exception.service_exception import (
    ServiceErrorException as ServiceErrorException,
)
from ...schemas.response import TokenRefreshModel as TokenRefreshModel
from ...services.auth_service import AuthService as AuthService
from ...services.data_service import DataService as DataService
from ...tools.tenant_checker import TenantManager as TenantManager
from ...utils.response_utils import ResponseUtil as ResponseUtil
from ..entity_table.auth_user import (
    AuthLogin as AuthLogin,
    AuthPassword as AuthPassword,
    AuthUser as AuthUser,
    AuthUserRegister as AuthUserRegister,
    AuthUserResponse as AuthUserResponse,
)
from _typeshed import Incomplete
from fastapi.security import OAuth2PasswordRequestForm as OAuth2PasswordRequestForm
from sqlmodel.ext.asyncio.session import AsyncSession as AsyncSession

Auth_Controller: Incomplete

async def auth_register(register_model: AuthUserRegister, db: AsyncSession = ...): ...
async def auth_login(login_model: AuthLogin, db: AsyncSession = ...): ...
async def auth_token(
    form_data: OAuth2PasswordRequestForm = ..., db: AsyncSession = ...
): ...
async def auth_refresh(refresh_model: TokenRefreshModel, db: AsyncSession = ...): ...
async def auth_logout(): ...
async def auth_me(current_user: AuthUserResponse = ...): ...
async def auth_me_password(
    password_model: AuthPassword,
    db: AsyncSession = ...,
    current_user: AuthUserResponse = ...,
): ...
