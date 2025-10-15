"""
Sweet Potato Authentication & Payment Service Python client.

This package exposes modules for authentication, session management,
payments, and supporting utilities as implementation progresses.
"""

from .auth import (
    AuthClient,
    AuthError,
    NonceResponse,
    TokenPair,
    TokenUser,
    UserProfile,
    UserWallet,
    PasswordResetRequestResponse,
)
from .sessions import (
    SessionError,
    SessionSummary,
    SessionValidationResult,
    SessionListResult,
    SessionRecord,
    SessionTouchResult,
    SessionRevokeResult,
    SessionsClient,
)
from .payments import (
    PaymentsClient,
    PaymentsError,
    CheckoutSession,
    PaymentIntent,
    WalletDeposit,
    WalletTransaction,
    SubscriptionPlan,
    SubscriptionDetail,
    SubscriptionCancellation,
    BalanceOverview,
    BalanceAmounts,
    UsageSummary,
    PaymentMethodUpdateResult,
    ProductPrice,
    Product,
    ProductList,
)
from .whitelist import (
    WhitelistClient,
    WhitelistError,
    WhitelistEntry,
    WhitelistCheckResult,
    WhitelistListResult,
    WhitelistMessage,
)
from .config import Settings, create_http_client
from .crypto import (
    CryptoPaymentsClient,
    CryptoPaymentsError,
    CryptoInvoice,
    CryptoInvoiceStatus,
    CryptoReconcileJob,
    verify_crypto_webhook_signature,
)
from .usage import (
    UsageClient,
    UsageError,
    UsagePeriod,
    UsageFeature,
    UsageFeaturesResponse,
    UsageRecordUsage,
    UsageRecordResult,
    UsageHistoryEntry,
    UsageHistoryResponse,
)
from .secure_messages import (
    SecureMessagesClient,
    SecureMessagesError,
    SecureMessage,
)
from .permissions import (
    AdminConfig,
    PermissionChecker,
    PermissionCheckResult,
    DEFAULT_ADMIN_ACCOUNTS,
    can_access_admin,
    create_permission_checker,
    default_permission_checker,
    get_role_aware_error_message,
    get_user_display,
    get_user_role,
    has_permission,
    is_admin_account,
)
from .metrics import MetricsClient
from .auth_async import AsyncAuthClient
from .sessions_async import AsyncSessionsClient
from .payments_async import AsyncPaymentsClient
from .usage_async import AsyncUsageClient
from .whitelist_async import AsyncWhitelistClient
from .secure_messages_async import AsyncSecureMessagesClient
from .metrics_async import AsyncMetricsClient
from .crypto_async import AsyncCryptoPaymentsClient
from .async_client import AsyncSpapsClient
from .http_async import RetryAsyncClient
from .client import SpapsClient
from .storage import (
    StoredTokens,
    TokenStorage,
    InMemoryTokenStorage,
    FileTokenStorage,
)
from .http import RetryConfig, LoggingHooks, default_logging_hooks

__all__ = [
    "__version__",
    "AuthClient",
    "AuthError",
    "NonceResponse",
    "TokenPair",
    "TokenUser",
    "UserProfile",
    "UserWallet",
    "PasswordResetRequestResponse",
    "SessionsClient",
    "SessionListResult",
    "SessionRecord",
    "SessionTouchResult",
    "SessionRevokeResult",
    "PaymentsClient",
    "PaymentsError",
    "CheckoutSession",
    "CheckoutSessionDetails",
    "CheckoutSessionSummary",
    "CheckoutSessionList",
    "ExpireCheckoutSessionResult",
    "PaymentIntent",
    "WalletDeposit",
    "WalletTransaction",
    "SubscriptionPlan",
    "SubscriptionItemPriceRecurring",
    "SubscriptionItemPrice",
    "SubscriptionItem",
    "SubscriptionDetail",
    "SubscriptionCancellation",
    "SubscriptionList",
    "BalanceOverview",
    "BalanceAmounts",
    "UsageSummary",
    "PaymentMethodUpdateResult",
    "ProductPrice",
    "Product",
    "ProductList",
    "GuestCheckoutSession",
    "GuestCheckoutSessionSummary",
    "GuestCheckoutSessionList",
    "GuestCheckoutConversionResult",
    "PaymentRecord",
    "PaymentHistory",
    "WhitelistClient",
    "WhitelistError",
    "WhitelistEntry",
    "WhitelistCheckResult",
    "WhitelistListResult",
    "WhitelistMessage",
    "Settings",
    "create_http_client",
    "SessionError",
    "SessionSummary",
    "SessionValidationResult",
    "CryptoPaymentsClient",
    "CryptoPaymentsError",
    "CryptoInvoice",
    "CryptoInvoiceStatus",
    "CryptoReconcileJob",
    "verify_crypto_webhook_signature",
    "UsageClient",
    "UsageError",
    "UsagePeriod",
    "UsageFeature",
    "UsageFeaturesResponse",
    "UsageRecordUsage",
    "UsageRecordResult",
    "UsageHistoryEntry",
    "UsageHistoryResponse",
    "SecureMessagesClient",
    "SecureMessagesError",
    "SecureMessage",
    "MetricsClient",
    "SpapsClient",
    "AsyncSpapsClient",
    "AsyncAuthClient",
    "AsyncSessionsClient",
    "AsyncPaymentsClient",
    "AsyncUsageClient",
    "AsyncWhitelistClient",
    "AsyncSecureMessagesClient",
    "AsyncMetricsClient",
    "AsyncCryptoPaymentsClient",
    "RetryAsyncClient",
    "AdminConfig",
    "PermissionChecker",
    "PermissionCheckResult",
    "DEFAULT_ADMIN_ACCOUNTS",
    "is_admin_account",
    "get_user_role",
    "has_permission",
    "can_access_admin",
    "get_role_aware_error_message",
    "get_user_display",
    "create_permission_checker",
    "default_permission_checker",
    "StoredTokens",
    "TokenStorage",
    "InMemoryTokenStorage",
    "FileTokenStorage",
    "RetryConfig",
    "LoggingHooks",
    "default_logging_hooks",
]

# Temporary development version; replaced during release automation.
__version__ = "0.1.3"
