"""
Tests for auth service
"""

from unittest.mock import Mock, patch
from trovesuite_auth_service import AuthService
from trovesuite_auth_service.entities.shared_response import Respons


class TestAuthService:
    """Test cases for AuthService"""

    def test_auth_service_initialization(self):
        """Test that AuthService can be initialized"""
        auth_service = AuthService()
        assert auth_service is not None

    @patch('trovesuite_auth_service.auth_service.DatabaseManager')
    def test_authorize_success(self, mock_db_manager):
        """Test successful user authorization"""
        # Mock database responses
        mock_db_manager.execute_query.side_effect = [
            [{'is_verified': True}],  # Tenant verification
            [{'is_suspended': False, 'can_always_login': True, 'working_days': ['MONDAY']}],  # Login settings
            [],  # User groups
            [{'role_id': 'role1', 'org_id': 'org1'}],  # User roles
            [{'permission_id': 'perm1'}]  # Permissions
        ]

        result = AuthService.authorize("user123", "tenant456")

        assert isinstance(result, Respons)
        assert result.success is True
        assert result.status_code == 200
        assert "Authorized" in result.detail

    @patch('trovesuite_auth_service.auth_service.DatabaseManager')
    def test_authorize_tenant_not_verified(self, mock_db_manager):
        """Test authorization failure when tenant is not verified"""
        mock_db_manager.execute_query.return_value = [{'is_verified': False}]

        result = AuthService.authorize("user123", "tenant456")

        assert isinstance(result, Respons)
        assert result.success is False
        assert result.status_code == 403
        assert "tenant not verified" in result.detail

    @patch('trovesuite_auth_service.auth_service.DatabaseManager')
    def test_authorize_user_suspended(self, mock_db_manager):
        """Test authorization failure when user is suspended"""
        mock_db_manager.execute_query.side_effect = [
            [{'is_verified': True}],  # Tenant verification
            [{'is_suspended': True, 'can_always_login': True, 'working_days': ['MONDAY']}]  # Login settings
        ]

        result = AuthService.authorize("user123", "tenant456")

        assert isinstance(result, Respons)
        assert result.success is False
        assert result.status_code == 403
        assert "user suspended" in result.detail

    def test_check_permission_success(self):
        """Test successful permission check"""
        # Mock user roles
        user_roles = [
            Mock(
                org_id="org1",
                bus_id="bus1", 
                app_id="app1",
                loc_id="loc1",
                resource_id="res1",
                permissions=["read", "write"]
            )
        ]

        has_permission = AuthService.check_permission(
            user_roles=user_roles,
            action="read",
            org_id="org1",
            bus_id="bus1",
            app_id="app1",
            loc_id="loc1",
            resource_id="res1"
        )

        assert has_permission is True

    def test_check_permission_failure(self):
        """Test failed permission check"""
        # Mock user roles
        user_roles = [
            Mock(
                org_id="org1",
                bus_id="bus1",
                app_id="app1", 
                loc_id="loc1",
                resource_id="res1",
                permissions=["write"]  # No "read" permission
            )
        ]

        has_permission = AuthService.check_permission(
            user_roles=user_roles,
            action="read",
            org_id="org1",
            bus_id="bus1",
            app_id="app1",
            loc_id="loc1",
            resource_id="res1"
        )

        assert has_permission is False

    def test_check_permission_hierarchy(self):
        """Test permission check with hierarchy (None means all)"""
        # Mock user roles with None values (applies to all)
        user_roles = [
            Mock(
                org_id="org1",
                bus_id=None,  # Applies to all businesses
                app_id=None,  # Applies to all apps
                loc_id=None,  # Applies to all locations
                resource_id=None,  # Applies to all resources
                permissions=["read"]
            )
        ]

        has_permission = AuthService.check_permission(
            user_roles=user_roles,
            action="read",
            org_id="org1",
            bus_id="any_bus",
            app_id="any_app",
            loc_id="any_loc",
            resource_id="any_res"
        )

        assert has_permission is True

    def test_get_user_permissions(self):
        """Test getting all user permissions"""
        # Mock user roles
        user_roles = [
            Mock(permissions=["read", "write"]),
            Mock(permissions=["admin", "delete"]),
            Mock(permissions=["read", "update"])  # Duplicate "read"
        ]

        permissions = AuthService.get_user_permissions(user_roles)
        
        # Should return unique permissions
        assert len(permissions) == 4
        assert "read" in permissions
        assert "write" in permissions
        assert "admin" in permissions
        assert "delete" in permissions
        assert "update" in permissions

    def test_has_any_permission(self):
        """Test checking if user has any of the required permissions"""
        user_roles = [Mock(permissions=["read", "write"])]
        
        # User has one of the required permissions
        has_any = AuthService.has_any_permission(user_roles, ["read", "admin"])
        assert has_any is True
        
        # User has none of the required permissions
        has_any = AuthService.has_any_permission(user_roles, ["admin", "delete"])
        assert has_any is False

    def test_has_all_permissions(self):
        """Test checking if user has all required permissions"""
        user_roles = [Mock(permissions=["read", "write", "admin"])]
        
        # User has all required permissions
        has_all = AuthService.has_all_permissions(user_roles, ["read", "write"])
        assert has_all is True
        
        # User is missing some required permissions
        has_all = AuthService.has_all_permissions(user_roles, ["read", "delete"])
        assert has_all is False

    def test_authorize_input_validation(self):
        """Test input validation for authorize method"""
        # Test empty user_id
        result = AuthService.authorize("", "tenant123")
        assert result.success is False
        assert result.error == "INVALID_USER_ID"
        assert result.status_code == 400
        
        # Test empty tenant_id
        result = AuthService.authorize("user123", "")
        assert result.success is False
        assert result.error == "INVALID_TENANT_ID"
        assert result.status_code == 400
        
        # Test None user_id
        result = AuthService.authorize(None, "tenant123")
        assert result.success is False
        assert result.error == "INVALID_USER_ID"
        assert result.status_code == 400