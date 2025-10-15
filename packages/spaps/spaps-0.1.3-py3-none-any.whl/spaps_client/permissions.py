"""
Client-side permission helpers mirroring the TypeScript SDK utilities.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Sequence, Union

Identifier = Optional[str]
AdminEntry = Union[str, "AdminConfig"]


@dataclass(frozen=True)
class AdminConfig:
    email: str
    wallets: Dict[str, str]


@dataclass
class PermissionCheckResult:
    allowed: bool
    reason: Optional[str]
    userRole: str
    requiredRole: Optional[str] = None


DEFAULT_ADMIN_ACCOUNTS = AdminConfig(
    email="buildooor@gmail.com",
    wallets={
        "ethereum": "0xa72bb7CeF1e4B2Cc144373d8dE0Add7CCc8DF4Ba",
        "solana": "HVEbdiYU3Rr34NHBSgKs7q8cvdTeZLqNL77Z1FB2vjLy",
    },
)

PERMISSION_MESSAGES: Dict[str, Dict[str, str]] = {
    "admin": {
        "user": "🔒 Admin privileges required to {action}. Please authenticate with an admin account.",
        "guest": "🔐 Authentication required. Please sign in with an admin account to {action}.",
    },
    "user": {
        "guest": "🔐 Authentication required. Please sign in to {action}.",
    },
}


def _normalize(identifier: Identifier) -> Optional[str]:
    return identifier.lower() if identifier else None


def _iter_admin_entries(custom_admins: Optional[Sequence[AdminEntry]]) -> Iterable[AdminEntry]:
    return custom_admins or ()


def is_admin_account(identifier: Identifier, custom_admins: Optional[Sequence[AdminEntry]] = None) -> bool:
    normalized = _normalize(identifier)
    if not normalized:
        return False

    defaults = {
        DEFAULT_ADMIN_ACCOUNTS.email.lower(),
        DEFAULT_ADMIN_ACCOUNTS.wallets["ethereum"].lower(),
        DEFAULT_ADMIN_ACCOUNTS.wallets["solana"].lower(),
    }
    if normalized in defaults:
        return True

    for entry in _iter_admin_entries(custom_admins):
        if isinstance(entry, str):
            if normalized == entry.lower():
                return True
            continue

        if isinstance(entry, AdminConfig):
            email_candidate = entry.email
            wallet_iter = entry.wallets.values()
        elif isinstance(entry, dict):
            email_candidate = entry.get("email")
            wallet_iter = (entry.get("wallets") or {}).values()
        else:
            continue

        if email_candidate and normalized == email_candidate.lower():
            return True
        if any(wallet and normalized == wallet.lower() for wallet in wallet_iter):
            return True
    return False


def get_user_role(identifier: Identifier = None, custom_admins: Optional[Sequence[AdminEntry]] = None) -> str:
    if not identifier:
        return "guest"
    if is_admin_account(identifier, custom_admins):
        return "admin"
    return "user"


def has_permission(
    user: Optional[Dict[str, Any]],
    required_permissions: Union[str, Sequence[str]],
    custom_admins: Optional[Sequence[AdminEntry]] = None,
) -> bool:
    if not user:
        return False
    identifier = user.get("email") or user.get("wallet_address")
    role = get_user_role(identifier, custom_admins)
    if role == "admin":
        return True

    permissions: List[str] = list(user.get("permissions") or [])
    if isinstance(required_permissions, str):
        return required_permissions in permissions
    return all(permission in permissions for permission in required_permissions)


def can_access_admin(
    user: Optional[Dict[str, Any]],
    custom_admins: Optional[Sequence[AdminEntry]] = None,
) -> PermissionCheckResult:
    if not user:
        return PermissionCheckResult(
            allowed=False,
            reason="Authentication required",
            userRole="guest",
            requiredRole="admin",
        )
    identifier = user.get("email") or user.get("wallet_address")
    role = get_user_role(identifier, custom_admins)
    allowed = role == "admin"
    reason = None if allowed else "Admin privileges required"
    return PermissionCheckResult(
        allowed=allowed,
        reason=reason,
        userRole=role,
        requiredRole="admin",
    )


def get_role_aware_error_message(required_role: str, user_role: str, action: str = "perform this action") -> str:
    template = PERMISSION_MESSAGES.get(required_role, {}).get(user_role)
    if template:
        return template.format(action=action)
    return f"Access denied. Required role: {required_role}, current role: {user_role}"


def get_user_display(
    user: Optional[Dict[str, Any]],
    custom_admins: Optional[Sequence[AdminEntry]] = None,
) -> Dict[str, Any]:
    if not user:
        return {
            "displayName": "Guest",
            "role": "guest",
            "badge": None,
            "isAdmin": False,
        }

    identifier = user.get("email") or user.get("wallet_address")
    role = get_user_role(identifier, custom_admins)
    is_admin = role == "admin"
    display_name = user.get("email")
    if not display_name:
        wallet = user.get("wallet_address") or ""
        if wallet:
            display_name = f"{wallet[:6]}...{wallet[-4:]}"
        else:
            display_name = "User"

    return {
        "displayName": display_name,
        "role": role,
        "badge": "👑 Admin" if is_admin else None,
        "isAdmin": is_admin,
    }


class PermissionChecker:
    """Stateful helper that caches custom admin entries."""

    def __init__(self, customAdmins: Optional[Sequence[AdminEntry]] = None) -> None:
        self.custom_admins: List[AdminEntry] = list(customAdmins or [])

    def isAdmin(self, identifier: Identifier) -> bool:  # noqa: N802
        return is_admin_account(identifier, self.custom_admins)

    def getRole(self, identifier: Identifier = None) -> str:  # noqa: N802
        return get_user_role(identifier, self.custom_admins)

    def hasPermission(self, user: Optional[Dict[str, Any]], permissions: Union[str, Sequence[str]]) -> bool:  # noqa: N802
        return has_permission(user, permissions, self.custom_admins)

    def canAccessAdmin(self, user: Optional[Dict[str, Any]]) -> PermissionCheckResult:  # noqa: N802
        return can_access_admin(user, self.custom_admins)

    def getErrorMessage(self, requiredRole: str, userRole: str, action: Optional[str] = None) -> str:  # noqa: N802
        return get_role_aware_error_message(requiredRole, userRole, action or "perform this action")

    def getUserDisplay(self, user: Optional[Dict[str, Any]]) -> Dict[str, Any]:  # noqa: N802
        return get_user_display(user, self.custom_admins)

    def requiresAuth(self, user: Optional[Dict[str, Any]]) -> bool:  # noqa: N802
        return user is None

    def requiresAdmin(self, user: Optional[Dict[str, Any]]) -> bool:  # noqa: N802
        return not self.canAccessAdmin(user).allowed

    def addCustomAdmin(self, admin: AdminEntry) -> None:  # noqa: N802
        self.custom_admins.append(admin)

    def removeCustomAdmin(self, admin: AdminEntry) -> None:  # noqa: N802
        self.custom_admins = [entry for entry in self.custom_admins if entry != admin]


def create_permission_checker(custom_admins: Optional[Sequence[AdminEntry]] = None) -> PermissionChecker:
    return PermissionChecker(custom_admins)


default_permission_checker = PermissionChecker()


__all__ = [
    "AdminConfig",
    "PermissionChecker",
    "PermissionCheckResult",
    "DEFAULT_ADMIN_ACCOUNTS",
    "can_access_admin",
    "create_permission_checker",
    "default_permission_checker",
    "get_role_aware_error_message",
    "get_user_display",
    "get_user_role",
    "has_permission",
    "is_admin_account",
]
