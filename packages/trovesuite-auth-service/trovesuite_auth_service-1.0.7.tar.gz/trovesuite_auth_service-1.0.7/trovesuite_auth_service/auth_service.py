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

    def __init__(self) -> None:
        """Initialize the service"""
        pass
    
    @staticmethod
    def decode_token(token: Annotated[str, Depends(oauth2_scheme)]) -> dict:
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

        except jwt.InvalidTokenError as exc:
            raise credentials_exception from exc
        
    @staticmethod
    def authorize(user_id: str, tenant_id: str) -> Respons[AuthServiceReadDto]:
        """Check if a user is authorized based on login settings and roles"""
        # Input validation
        if not user_id or not isinstance(user_id, str):
            return Respons[AuthServiceReadDto](
                detail="Invalid user_id: must be a non-empty string",
                data=[],
                success=False,
                status_code=400,
                error="INVALID_USER_ID"
            )
        
        if not tenant_id or not isinstance(tenant_id, str):
            return Respons[AuthServiceReadDto](
                detail="Invalid tenant_id: must be a non-empty string",
                data=[],
                success=False,
                status_code=400,
                error="INVALID_TENANT_ID"
            )
        
        try:

            is_tenant_verified = DatabaseManager.execute_query(
                f"SELECT is_verified FROM {db_settings.TENANTS_TABLE} WHERE delete_status = 'NOT_DELETED' AND id = %s",
                (tenant_id,),
            )

            if not is_tenant_verified or len(is_tenant_verified) == 0:
                logger.warning("Login failed - tenant not found: %s", tenant_id)
                return Respons[AuthServiceReadDto](
                    detail=f"Tenant '{tenant_id}' not found or has been deleted",
                    data=[],
                    success=False,
                    status_code=404,
                    error="TENANT_NOT_FOUND"
                )
            
            if not is_tenant_verified[0]['is_verified']:
                logger.warning("Login failed - tenant not verified for user: %s, tenant: %s", user_id, tenant_id)
                return Respons[AuthServiceReadDto](
                    detail=f"Tenant '{tenant_id}' is not verified. Please contact your administrator.",
                    data=[],
                    success=False,
                    status_code=403,
                    error="TENANT_NOT_VERIFIED"
                )

            login_settings_details = DatabaseManager.execute_query(
                f"""SELECT user_id, group_id, is_suspended, can_always_login,
                is_multi_factor_enabled, is_login_before, working_days,
                login_on, logout_on FROM "{tenant_id}".{db_settings.LOGIN_SETTINGS_TABLE} 
                WHERE (delete_status = 'NOT_DELETED' AND is_active = true ) AND user_id = %s""",
                (user_id,),
            )

            if not login_settings_details or len(login_settings_details) == 0:
                logger.warning("Authorization failed - user not found: %s in tenant: %s", user_id, tenant_id)
                return Respons[AuthServiceReadDto](
                    detail=f"User '{user_id}' not found in tenant '{tenant_id}' or account is inactive",
                    data=[],
                    success=False,
                    status_code=404,
                    error="USER_NOT_FOUND"
                )

            if login_settings_details[0]['is_suspended']:
                logger.warning("Authorization failed - user suspended: %s", user_id)
                return Respons[AuthServiceReadDto](
                    detail="Your account has been suspended. Please contact your administrator.",
                    data=[],
                    success=False,
                    status_code=403,
                    error="USER_SUSPENDED"
                )

            if not login_settings_details[0]['can_always_login']:
                current_day = datetime.now().strftime("%A").upper()
                
                if current_day not in login_settings_details[0]['working_days']:
                    logger.warning("Authorization failed - outside working days for user: %s checking custom login period", user_id)
              
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
                        logger.warning("Authorization failed - outside allowed period for user: %s", user_id)
                        return Respons[AuthServiceReadDto](
                            detail="Login is not allowed at this time. Please check your access schedule.",
                            data=[],
                            success=False,
                            status_code=403,
                            error="LOGIN_TIME_RESTRICTED"
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
                            org_id, bus_id, app_id, shared_resource_id, resource_id, user_id, role_id
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
                            org_id, bus_id, app_id, shared_resource_id, resource_id, user_id, role_id
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
            logger.error("Authorization check failed for user: %s", str(e))
            return Respons[AuthServiceReadDto](
                detail="Authorization check failed due to an internal error",
                data=[],
                success=False,
                status_code=500,
                error=str(e)
            )
        
    @staticmethod
    def check_permission(user_roles: list, action=None, org_id=None, bus_id=None, app_id=None,
                     resource_id=None, shared_resource_id=None) -> bool:
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
            if role.resource_id not in (None, resource_id):
                continue
            if role.shared_resource_id not in (None, shared_resource_id):
                continue

            # Check if the permission exists
            if action in role.permissions:
                return True

        return False
    
    @staticmethod
    def get_user_info_from_token(token: str) -> dict:
        """
        Convenience method to get user information from a JWT token.
        
        Args:
            token: JWT token string
            
        Returns:
            dict: User information including user_id and tenant_id
            
        Raises:
            HTTPException: If token is invalid
        """
        return AuthService.decode_token(token)
    
    @staticmethod
    def authorize_user_from_token(token: str) -> Respons[AuthServiceReadDto]:
        """
        Convenience method to authorize a user directly from a JWT token.
        
        Args:
            token: JWT token string
            
        Returns:
            Respons[AuthServiceReadDto]: Authorization result with user roles and permissions
            
        Raises:
            HTTPException: If token is invalid
        """
        user_info = AuthService.decode_token(token)
        return AuthService.authorize(user_info["user_id"], user_info["tenant_id"])
    
    @staticmethod
    def get_user_permissions(user_roles: list) -> list:
        """
        Get all unique permissions for a user across all their roles.
        
        Args:
            user_roles: List of user roles from authorization
            
        Returns:
            list: Unique list of permissions
        """
        permissions = set()
        for role in user_roles:
            if role.permissions:
                permissions.update(role.permissions)
        return list(permissions)
    
    @staticmethod
    def has_any_permission(user_roles: list, required_permissions: list) -> bool:
        """
        Check if user has any of the required permissions.
        
        Args:
            user_roles: List of user roles from authorization
            required_permissions: List of permissions to check for
            
        Returns:
            bool: True if user has any of the required permissions
        """
        user_permissions = AuthService.get_user_permissions(user_roles)
        return any(perm in user_permissions for perm in required_permissions)
    
    @staticmethod
    def has_all_permissions(user_roles: list, required_permissions: list) -> bool:
        """
        Check if user has all of the required permissions.
        
        Args:
            user_roles: List of user roles from authorization
            required_permissions: List of permissions to check for
            
        Returns:
            bool: True if user has all of the required permissions
        """
        user_permissions = AuthService.get_user_permissions(user_roles)
        return all(perm in user_permissions for perm in required_permissions)