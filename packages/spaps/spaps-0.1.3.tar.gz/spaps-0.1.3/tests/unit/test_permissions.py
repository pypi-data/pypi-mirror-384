from spaps_client.permissions import (
    DEFAULT_ADMIN_ACCOUNTS,
    PermissionChecker,
    can_access_admin,
    get_role_aware_error_message,
    get_user_display,
    get_user_role,
    has_permission,
    is_admin_account,
)


def test_is_admin_account_matches_default_email() -> None:
    assert is_admin_account(DEFAULT_ADMIN_ACCOUNTS.email)
    assert is_admin_account(DEFAULT_ADMIN_ACCOUNTS.wallets["ethereum"])
    assert not is_admin_account("not-admin@example.com")


def test_is_admin_account_with_custom_admins() -> None:
    custom = [
        "admin@example.com",
        {"email": "owner@example.com", "wallets": {"ethereum": "0xabc", "solana": "So1Ana"}},
    ]
    assert is_admin_account("admin@example.com", custom)
    assert is_admin_account("0xabc", custom)
    assert not is_admin_account("user@example.com", custom)


def test_get_user_role_defaults_to_guest() -> None:
    assert get_user_role() == "guest"
    assert get_user_role("user@example.com") == "user"
    assert get_user_role(DEFAULT_ADMIN_ACCOUNTS.email) == "admin"


def test_has_permission_considers_roles() -> None:
    admin_user = {"email": DEFAULT_ADMIN_ACCOUNTS.email, "permissions": []}
    limited_user = {"email": "user@example.com", "permissions": ["read:docs"]}

    assert has_permission(admin_user, "manage:billing") is True
    assert has_permission(limited_user, "read:docs") is True
    assert has_permission(limited_user, ["read:docs", "write:docs"]) is False
    assert has_permission(None, "read:docs") is False


def test_can_access_admin_reports_missing_auth() -> None:
    result = can_access_admin(None)
    assert result.allowed is False
    assert result.userRole == "guest"
    assert result.requiredRole == "admin"

    result_admin = can_access_admin({"email": DEFAULT_ADMIN_ACCOUNTS.email})
    assert result_admin.allowed is True
    assert result_admin.userRole == "admin"


def test_get_role_aware_error_message() -> None:
    message = get_role_aware_error_message("admin", "user", action="update billing settings")
    assert "Admin privileges required" in message

    fallback = get_role_aware_error_message("superadmin", "guest")
    assert "superadmin" in fallback


def test_get_user_display_formats_wallet() -> None:
    user = {"wallet_address": "0xabcdef1234567890", "email": None}
    display = get_user_display(user)
    assert display["displayName"].startswith("0xabcd")
    assert display["role"] == "user"


def test_permission_checker_helpers() -> None:
    checker = PermissionChecker(customAdmins=["founder@example.com"])
    assert checker.isAdmin("founder@example.com")
    assert checker.getRole("founder@example.com") == "admin"
    assert checker.requiresAuth({"email": "user@example.com"}) is False
    assert checker.requiresAdmin({"email": "user@example.com"}) is True

    checker.addCustomAdmin("new-admin@example.com")
    assert checker.isAdmin("new-admin@example.com") is True

    checker.removeCustomAdmin("new-admin@example.com")
    assert checker.isAdmin("new-admin@example.com") is False
