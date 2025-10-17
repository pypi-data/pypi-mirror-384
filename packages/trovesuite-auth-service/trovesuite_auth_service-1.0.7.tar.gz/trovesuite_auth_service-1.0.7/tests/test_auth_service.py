"""
Tests for auth service
"""

import pytest
from unittest.mock import Mock, patch
from trovesuite_auth_service import AuthService, AuthServiceReadDto
from trovesuite_auth_service.entities.shared_response import Respons


class TestAuthService:
    """Test cases for AuthService"""

    def test_auth_service_initialization(self):
        """Test that AuthService can be initialized"""
        auth_service = AuthService()
        assert auth_service is not None

    @patch('auth_service.auth_service.DatabaseManager')
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

    @patch('auth_service.auth_service.DatabaseManager')
    def test_authorize_tenant_not_verified(self, mock_db_manager):
        """Test authorization failure when tenant is not verified"""
        mock_db_manager.execute_query.return_value = [{'is_verified': False}]

        result = AuthService.authorize("user123", "tenant456")

        assert isinstance(result, Respons)
        assert result.success is False
        assert result.status_code == 403
        assert "tenant not verified" in result.detail

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
