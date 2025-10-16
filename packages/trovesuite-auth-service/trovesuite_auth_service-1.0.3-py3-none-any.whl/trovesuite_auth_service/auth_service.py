"""Auth Service - Business logic for user authentication and authorization"""
from datetime import datetime, timezone
from typing import Annotated
from fastapi import HTTPException
from fastapi.params import Depends
from fastapi.security import OAuth2PasswordBearer
import jwt
from .utils.helper import Helper
from .auth_read_dto import AuthServiceReadDto
from .configs.settings import db_settings
from .configs.database import DatabaseManager
from .configs.logging import get_logger
from .entities.shared_response import Respons

logger = get_logger("auth_service")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class AuthService:
    """Service class for authentication and authorization operations"""

    def __init__(self) -> any:
        """Initialize the service"""
        pass
    
    @staticmethod
    def decode_token(token: Annotated[str, Depends(oauth2_scheme)]) -> any:
        credentials_exception = HTTPException(
            status_code=401,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        try:
            payload = jwt.decode(token, db_settings.SECRET_KEY, algorithms=[db_settings.ALGORITHM])
            user_id = payload.get("user_id")
            tenant_id = payload.get("tenant_id")

            if user_id is None or tenant_id is None:
                raise credentials_exception

            return {"user_id": user_id, "tenant_id": tenant_id}

        except jwt.InvalidTokenError:
            raise credentials_exception
        
    @staticmethod
    def authorize(user_id: str, tenant_id: str) -> Respons[AuthServiceReadDto]:
        """Check if a user is authorized based on login settings and roles"""
        try:

            is_tenant_verified = DatabaseManager.execute_query(
                f"SELECT is_verified FROM {db_settings.TENANTS_TABLE} WHERE delete_status = 'NOT_DELETED' AND id = %s",
                (tenant_id,),
            )

            if not is_tenant_verified or len(is_tenant_verified) == 0 or not is_tenant_verified[0]['is_verified']:
                logger.warning(f"Login failed - tenant not verified for user: {user_id}")
                return Respons[AuthServiceReadDto](
                    detail="Unauthorized, tenant not verified",
                    data=[],
                    success=False,
                    status_code=403,
                    error=None
                )

            login_settings_details = DatabaseManager.execute_query(
                f"""SELECT user_id, group_id, is_suspended, can_always_login,
                is_multi_factor_enabled, is_login_before, working_days,
                login_on, logout_on FROM "{tenant_id}".{db_settings.LOGIN_SETTINGS_TABLE} 
                WHERE (delete_status = 'NOT_DELETED' AND is_active = true ) AND user_id = %s""",
                (user_id,),
            )

            if login_settings_details[0]['is_suspended']:
                logger.warning(f"Authorization failed - user suspended: {user_id}")
                return Respons[AuthServiceReadDto](
                    detail="Unauthorized, user suspended",
                    data=[],
                    success=False,
                    status_code=403,
                    error=None
                )

            if not login_settings_details[0]['can_always_login']:
                current_day = datetime.now().strftime("%A").upper()
                
                if current_day not in login_settings_details[0]['working_days']:
                    logger.warning(f"Authorization failed - outside working days for user: {user_id} checking custom login period")
              
                    # Get current datetime (full date and time) with timezone
                    current_datetime = datetime.now(timezone.utc).replace(microsecond=0, second=0)
                    
                    # Get from database (should already be datetime objects)
                    login_on = login_settings_details[0]['login_on']
                    logout_on = login_settings_details[0]['logout_on']
                    
                    # Set defaults if None (with timezone awareness)
                    if not login_on:
                        login_on = datetime.min.replace(tzinfo=timezone.utc)
                    if not logout_on:
                        logout_on = datetime.max.replace(tzinfo=timezone.utc)

                    # Compare full datetime objects (both date and time)
                    if not (login_on <= current_datetime <= logout_on):
                        logger.warning(f"Authorization failed - outside allowed period for user: {user_id}")
                        return Respons[AuthServiceReadDto](
                            detail="Unauthorized, login not allowed at this time",
                            data=[],
                            success=False,
                            status_code=403,
                            error=None
                        )
            
            # 1️⃣ Get all groups the user belongs to
            user_groups = DatabaseManager.execute_query(
                f"""SELECT group_id FROM "{tenant_id}".{db_settings.USER_GROUPS_TABLE}
                    WHERE delete_status = 'NOT_DELETED' AND is_active = true AND user_id = %s""",(user_id,),
            )

            # 2️⃣ Prepare list of group_ids
            group_ids = [g["group_id"] for g in user_groups] if user_groups else []

            # 3️⃣ Build query dynamically to include groups (if any) + user
            if group_ids:
                get_user_roles = DatabaseManager.execute_query(
                    f"""
                        SELECT DISTINCT ON (role_id)
                            org_id, bus_id, app_id, loc_id, shared_resource_id, resource_id, user_id, role_id
                        FROM "{tenant_id}".{db_settings.ASSIGN_ROLES_TABLE}
                        WHERE delete_status = 'NOT_DELETED'
                        AND is_active = true
                        AND (user_id = %s OR group_id = ANY(%s))
                        ORDER BY role_id;
                    """,
                    (user_id, group_ids),
                )
            else:
                # No groups, just check roles for user
                get_user_roles = DatabaseManager.execute_query(
                    f"""
                        SELECT DISTINCT ON (role_id)
                            org_id, bus_id, app_id, loc_id, shared_resource_id, resource_id, user_id, role_id
                        FROM "{tenant_id}".{db_settings.ASSIGN_ROLES_TABLE}
                        WHERE delete_status = 'NOT_DELETED'
                        AND is_active = true
                        AND user_id = %s
                        ORDER BY role_id;
                    """,
                    (user_id,),
                )

            # GET permissions and Append to Role
            get_user_roles_with_tenant_and_permissions = []
            for role in get_user_roles:
                permissions = DatabaseManager.execute_query(
                    f"""SELECT permission_id FROM {db_settings.ROLE_PERMISSIONS_TABLE} WHERE role_id = %s""",
                    params=(role["role_id"],),)

                role_dict = {**role, "tenant_id": tenant_id, "permissions": [p['permission_id'] for p in permissions]}
                get_user_roles_with_tenant_and_permissions.append(role_dict)

            roles_dto = Helper.map_to_dto(get_user_roles_with_tenant_and_permissions, AuthServiceReadDto)

            return Respons[AuthServiceReadDto](
                detail="Authorized",
                data=roles_dto,
                success=True,
                status_code=200,
                error=None,
            )

        except HTTPException as http_ex:
            raise http_ex

        except Exception as e:
            logger.error(f"Authorization check failed for user: {str(e)}")
            return Respons[AuthServiceReadDto](
                detail="Authorization check failed due to an internal error",
                data=[],
                success=False,
                status_code=500,
                error=str(e)
            )
        
    @staticmethod
    def check_permission(user_roles: list, action=None, org_id=None, bus_id=None, app_id=None,
                     loc_id=None, resource_id=None, shared_resource_id=None) -> bool:
        """
        Check if user has a given permission (action) for a specific target.
        
        Hierarchy: organization > business > app > location > resource/shared_resource
        If a field in role is None, it applies to all under that level.
        """
        for role in user_roles:
            # Check hierarchy: None means "all"
            if role.org_id not in (None, org_id):
                continue
            if role.bus_id not in (None, bus_id):
                continue
            if role.app_id not in (None, app_id):
                continue
            if role.loc_id not in (None, loc_id):
                continue
            if role.resource_id not in (None, resource_id):
                continue
            if role.shared_resource_id not in (None, shared_resource_id):
                continue

            # Check if the permission exists
            if action in role.permissions:
                return True

        return False
