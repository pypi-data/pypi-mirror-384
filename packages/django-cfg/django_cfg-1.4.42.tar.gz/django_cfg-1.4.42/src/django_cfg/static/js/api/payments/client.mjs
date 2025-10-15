import { BaseAPIClient } from '../base.mjs';

/**
 * Payments API Client
 * Auto-generated from OpenAPI schema
 * @module payments
 * @extends BaseAPIClient
 */
export class PaymentsAPI extends BaseAPIClient {
    /**
     * Initialize payments API client
     * @param {string} [baseURL] - Optional base URL
     */
    constructor(baseURL) {
        super(baseURL);
    }

    /**
     * paymentsAdminApiPaymentsList     * Admin ViewSet for payment management.

Provides full CRUD operations for payments with admin-specific features.     * @param {Object} [params={}] - Query parameters     * @param {string} [params.currency__code]     * @param {string} [params.ordering] - Which field to use when ordering the results.     * @param {number} [params.page] - A page number within the paginated result set.     * @param {number} [params.page_size] - Number of results to return per page.     * @param {"nowpayments"} [params.provider] - Payment provider

* `nowpayments` - NowPayments     * @param {string} [params.search] - A search term.     * @param {"cancelled" | "completed" | "confirmed" | "confirming" | "expired" | "failed" | "pending" | "refunded"} [params.status] - Current payment status

* `pending` - Pending
* `confirming` - Confirming
* `confirmed` - Confirmed
* `completed` - Completed
* `failed` - Failed
* `expired` - Expired
* `cancelled` - Cancelled
* `refunded` - Refunded     * @param {number} [params.user]     * @returns {Promise<PaginatedAdminPaymentListList>} Response data
     */
    async paymentsAdminApiPaymentsList(params = {}) {
        const path = `/cfg/payments/admin/api/payments/`;        return this.get(path, params);    }
    /**
     * paymentsAdminApiPaymentsCreate     * Create payment with enhanced error handling.     * @param {AdminPaymentCreateRequest} data - Request body     * @returns {Promise<AdminPaymentCreate>} Response data
     */
    async paymentsAdminApiPaymentsCreate(data) {
        const path = `/cfg/payments/admin/api/payments/`;        return this.post(path, data);    }
    /**
     * paymentsAdminApiPaymentsRetrieve     * Admin ViewSet for payment management.

Provides full CRUD operations for payments with admin-specific features.     * @param {string} id     * @returns {Promise<AdminPaymentDetail>} Response data
     */
    async paymentsAdminApiPaymentsRetrieve(id) {
        const path = `/cfg/payments/admin/api/payments/${id}/`;        return this.get(path);    }
    /**
     * paymentsAdminApiPaymentsUpdate     * Admin ViewSet for payment management.

Provides full CRUD operations for payments with admin-specific features.     * @param {string} id     * @param {AdminPaymentUpdateRequest} data - Request body     * @returns {Promise<AdminPaymentUpdate>} Response data
     */
    async paymentsAdminApiPaymentsUpdate(id, data) {
        const path = `/cfg/payments/admin/api/payments/${id}/`;        return this.put(path, data);    }
    /**
     * paymentsAdminApiPaymentsPartialUpdate     * Admin ViewSet for payment management.

Provides full CRUD operations for payments with admin-specific features.     * @param {string} id     * @param {PatchedAdminPaymentUpdateRequest} data - Request body     * @returns {Promise<AdminPaymentUpdate>} Response data
     */
    async paymentsAdminApiPaymentsPartialUpdate(id, data) {
        const path = `/cfg/payments/admin/api/payments/${id}/`;        return this.patch(path, data);    }
    /**
     * paymentsAdminApiPaymentsDestroy     * Admin ViewSet for payment management.

Provides full CRUD operations for payments with admin-specific features.     * @param {string} id     * @returns {Promise<void>} No content
     */
    async paymentsAdminApiPaymentsDestroy(id) {
        const path = `/cfg/payments/admin/api/payments/${id}/`;        return this.delete(path);    }
    /**
     * paymentsAdminApiPaymentsCancelCreate     * Cancel a payment.     * @param {string} id     * @returns {Promise<AdminPaymentDetail>} Response data
     */
    async paymentsAdminApiPaymentsCancelCreate(id) {
        const path = `/cfg/payments/admin/api/payments/${id}/cancel/`;        return this.post(path, {});    }
    /**
     * paymentsAdminApiPaymentsRefreshStatusCreate     * Refresh payment status from provider via AJAX.     * @param {string} id     * @returns {Promise<AdminPaymentDetail>} Response data
     */
    async paymentsAdminApiPaymentsRefreshStatusCreate(id) {
        const path = `/cfg/payments/admin/api/payments/${id}/refresh_status/`;        return this.post(path, {});    }
    /**
     * paymentsAdminApiPaymentsRefundCreate     * Refund a payment.     * @param {string} id     * @returns {Promise<AdminPaymentDetail>} Response data
     */
    async paymentsAdminApiPaymentsRefundCreate(id) {
        const path = `/cfg/payments/admin/api/payments/${id}/refund/`;        return this.post(path, {});    }
    /**
     * paymentsAdminApiPaymentsStatsRetrieve     * Get comprehensive payment statistics.     * @returns {Promise<AdminPaymentStats>} Response data
     */
    async paymentsAdminApiPaymentsStatsRetrieve() {
        const path = `/cfg/payments/admin/api/payments/stats/`;        return this.get(path);    }
    /**
     * paymentsAdminApiStatsList     * Get overview statistics.     * @param {Object} [params={}] - Query parameters     * @param {string} [params.ordering] - Which field to use when ordering the results.     * @param {number} [params.page] - A page number within the paginated result set.     * @param {number} [params.page_size] - Number of results to return per page.     * @param {string} [params.search] - A search term.     * @returns {Promise<PaginatedAdminPaymentStatsList>} Response data
     */
    async paymentsAdminApiStatsList(params = {}) {
        const path = `/cfg/payments/admin/api/stats/`;        return this.get(path, params);    }
    /**
     * paymentsAdminApiStatsRetrieve     * Admin ViewSet for comprehensive system statistics.

Provides aggregated statistics across all system components.     * @param {string} id     * @returns {Promise<AdminPaymentStats>} Response data
     */
    async paymentsAdminApiStatsRetrieve(id) {
        const path = `/cfg/payments/admin/api/stats/${id}/`;        return this.get(path);    }
    /**
     * paymentsAdminApiStatsPaymentsRetrieve     * Get detailed payment statistics.     * @returns {Promise<AdminPaymentStats>} Response data
     */
    async paymentsAdminApiStatsPaymentsRetrieve() {
        const path = `/cfg/payments/admin/api/stats/payments/`;        return this.get(path);    }
    /**
     * paymentsAdminApiStatsSystemRetrieve     * Get system health and performance statistics.     * @returns {Promise<AdminPaymentStats>} Response data
     */
    async paymentsAdminApiStatsSystemRetrieve() {
        const path = `/cfg/payments/admin/api/stats/system/`;        return this.get(path);    }
    /**
     * paymentsAdminApiStatsWebhooksRetrieve     * Get detailed webhook statistics.     * @returns {Promise<AdminPaymentStats>} Response data
     */
    async paymentsAdminApiStatsWebhooksRetrieve() {
        const path = `/cfg/payments/admin/api/stats/webhooks/`;        return this.get(path);    }
    /**
     * paymentsAdminApiUsersList     * Override list to limit results for dropdown.     * @param {Object} [params={}] - Query parameters     * @param {boolean} [params.is_active]     * @param {boolean} [params.is_staff]     * @param {boolean} [params.is_superuser]     * @param {string} [params.ordering] - Which field to use when ordering the results.     * @param {number} [params.page] - A page number within the paginated result set.     * @param {number} [params.page_size] - Number of results to return per page.     * @param {string} [params.search] - A search term.     * @returns {Promise<PaginatedAdminUserList>} Response data
     */
    async paymentsAdminApiUsersList(params = {}) {
        const path = `/cfg/payments/admin/api/users/`;        return this.get(path, params);    }
    /**
     * paymentsAdminApiUsersRetrieve     * Admin ViewSet for user management.

Provides read-only access to users for admin interface.     * @param {number} id - A unique integer value identifying this User.     * @returns {Promise<AdminUser>} Response data
     */
    async paymentsAdminApiUsersRetrieve(id) {
        const path = `/cfg/payments/admin/api/users/${id}/`;        return this.get(path);    }
    /**
     * paymentsAdminApiWebhookTestTestCreate     * Test webhook endpoint.

Sends a test webhook to the specified URL with the given event type.
Useful for developers to test their webhook implementations.     * @param {WebhookStatsRequest} data - Request body     * @returns {Promise<WebhookStats>} Response data
     */
    async paymentsAdminApiWebhookTestTestCreate(data) {
        const path = `/cfg/payments/admin/api/webhook-test/test/`;        return this.post(path, data);    }
    /**
     * paymentsAdminApiWebhooksList     * List webhook providers and configurations with real ngrok URLs.     * @param {Object} [params={}] - Query parameters     * @param {string} [params.ordering] - Which field to use when ordering the results.     * @param {number} [params.page] - A page number within the paginated result set.     * @param {number} [params.page_size] - Number of results to return per page.     * @param {string} [params.search] - A search term.     * @returns {Promise<PaginatedWebhookStatsList>} Response data
     */
    async paymentsAdminApiWebhooksList(params = {}) {
        const path = `/cfg/payments/admin/api/webhooks/`;        return this.get(path, params);    }
    /**
     * paymentsAdminApiWebhooksRetrieve     * Admin ViewSet for webhook configuration management.

Read-only view for webhook configurations and provider info.
Requires admin permissions.     * @param {string} id     * @returns {Promise<WebhookStats>} Response data
     */
    async paymentsAdminApiWebhooksRetrieve(id) {
        const path = `/cfg/payments/admin/api/webhooks/${id}/`;        return this.get(path);    }
    /**
     * paymentsAdminApiWebhooksEventsList     * List webhook events with filtering and pagination.     * @param {string} webhook_pk     * @param {Object} [params={}] - Query parameters     * @param {string} [params.ordering] - Which field to use when ordering the results.     * @param {number} [params.page] - A page number within the paginated result set.     * @param {number} [params.page_size] - Number of results to return per page.     * @param {string} [params.search] - A search term.     * @returns {Promise<PaginatedWebhookEventListList>} Response data
     */
    async paymentsAdminApiWebhooksEventsList(webhook_pk, params = {}) {
        const path = `/cfg/payments/admin/api/webhooks/${webhook_pk}/events/`;        return this.get(path, params);    }
    /**
     * paymentsAdminApiWebhooksEventsRetrieve     * Admin ViewSet for webhook events management.

Provides listing, filtering, and actions for webhook events.
Requires admin permissions.     * @param {string} id     * @param {string} webhook_pk     * @returns {Promise<WebhookEventList>} Response data
     */
    async paymentsAdminApiWebhooksEventsRetrieve(id, webhook_pk) {
        const path = `/cfg/payments/admin/api/webhooks/${webhook_pk}/events/${id}/`;        return this.get(path);    }
    /**
     * paymentsAdminApiWebhooksEventsRetryCreate     * Retry a failed webhook event.     * @param {string} id     * @param {string} webhook_pk     * @param {WebhookEventListRequest} data - Request body     * @returns {Promise<WebhookEventList>} Response data
     */
    async paymentsAdminApiWebhooksEventsRetryCreate(id, webhook_pk, data) {
        const path = `/cfg/payments/admin/api/webhooks/${webhook_pk}/events/${id}/retry/`;        return this.post(path, data);    }
    /**
     * paymentsAdminApiWebhooksEventsClearAllCreate     * Clear all webhook events.     * @param {string} webhook_pk     * @param {WebhookEventListRequest} data - Request body     * @returns {Promise<WebhookEventList>} Response data
     */
    async paymentsAdminApiWebhooksEventsClearAllCreate(webhook_pk, data) {
        const path = `/cfg/payments/admin/api/webhooks/${webhook_pk}/events/clear_all/`;        return this.post(path, data);    }
    /**
     * paymentsAdminApiWebhooksEventsRetryFailedCreate     * Retry all failed webhook events.     * @param {string} webhook_pk     * @param {WebhookEventListRequest} data - Request body     * @returns {Promise<WebhookEventList>} Response data
     */
    async paymentsAdminApiWebhooksEventsRetryFailedCreate(webhook_pk, data) {
        const path = `/cfg/payments/admin/api/webhooks/${webhook_pk}/events/retry_failed/`;        return this.post(path, data);    }
    /**
     * paymentsAdminApiWebhooksStatsRetrieve     * Get webhook statistics.     * @returns {Promise<WebhookStats>} Response data
     */
    async paymentsAdminApiWebhooksStatsRetrieve() {
        const path = `/cfg/payments/admin/api/webhooks/stats/`;        return this.get(path);    }
    /**
     * paymentsApiKeysList     * Global API Key ViewSet: /api/api-keys/

Provides admin-level access to all API keys with filtering and stats.     * @param {Object} [params={}] - Query parameters     * @param {boolean} [params.is_active]     * @param {string} [params.ordering] - Which field to use when ordering the results.     * @param {number} [params.page] - A page number within the paginated result set.     * @param {number} [params.page_size] - Number of results to return per page.     * @param {string} [params.search] - A search term.     * @param {number} [params.user]     * @returns {Promise<PaginatedAPIKeyListList>} Response data
     */
    async paymentsApiKeysList(params = {}) {
        const path = `/cfg/payments/api-keys/`;        return this.get(path, params);    }
    /**
     * paymentsApiKeysCreate     * Global API Key ViewSet: /api/api-keys/

Provides admin-level access to all API keys with filtering and stats.     * @param {APIKeyCreateRequest} data - Request body     * @returns {Promise<APIKeyCreate>} Response data
     */
    async paymentsApiKeysCreate(data) {
        const path = `/cfg/payments/api-keys/`;        return this.post(path, data);    }
    /**
     * paymentsApiKeysRetrieve     * Global API Key ViewSet: /api/api-keys/

Provides admin-level access to all API keys with filtering and stats.     * @param {string} id     * @returns {Promise<APIKeyDetail>} Response data
     */
    async paymentsApiKeysRetrieve(id) {
        const path = `/cfg/payments/api-keys/${id}/`;        return this.get(path);    }
    /**
     * paymentsApiKeysUpdate     * Global API Key ViewSet: /api/api-keys/

Provides admin-level access to all API keys with filtering and stats.     * @param {string} id     * @param {APIKeyUpdateRequest} data - Request body     * @returns {Promise<APIKeyUpdate>} Response data
     */
    async paymentsApiKeysUpdate(id, data) {
        const path = `/cfg/payments/api-keys/${id}/`;        return this.put(path, data);    }
    /**
     * paymentsApiKeysPartialUpdate     * Global API Key ViewSet: /api/api-keys/

Provides admin-level access to all API keys with filtering and stats.     * @param {string} id     * @param {PatchedAPIKeyUpdateRequest} data - Request body     * @returns {Promise<APIKeyUpdate>} Response data
     */
    async paymentsApiKeysPartialUpdate(id, data) {
        const path = `/cfg/payments/api-keys/${id}/`;        return this.patch(path, data);    }
    /**
     * paymentsApiKeysDestroy     * Global API Key ViewSet: /api/api-keys/

Provides admin-level access to all API keys with filtering and stats.     * @param {string} id     * @returns {Promise<void>} No content
     */
    async paymentsApiKeysDestroy(id) {
        const path = `/cfg/payments/api-keys/${id}/`;        return this.delete(path);    }
    /**
     * paymentsApiKeysPerformActionCreate     * Perform action on API key.

POST /api/api-keys/{id}/perform_action/     * @param {string} id     * @returns {Promise<APIKeyDetail>} Response data
     */
    async paymentsApiKeysPerformActionCreate(id) {
        const path = `/cfg/payments/api-keys/${id}/perform_action/`;        return this.post(path, {});    }
    /**
     * paymentsApiKeysAnalyticsRetrieve     * Get API key analytics.

GET /api/api-keys/analytics/?days=30     * @returns {Promise<APIKeyDetail>} Response data
     */
    async paymentsApiKeysAnalyticsRetrieve() {
        const path = `/cfg/payments/api-keys/analytics/`;        return this.get(path);    }
    /**
     * paymentsApiKeysByUserRetrieve     * Get API keys grouped by user.

GET /api/api-keys/by_user/     * @returns {Promise<APIKeyDetail>} Response data
     */
    async paymentsApiKeysByUserRetrieve() {
        const path = `/cfg/payments/api-keys/by_user/`;        return this.get(path);    }
    /**
     * paymentsApiKeysCreateCreate     * Standalone API key creation endpoint: /api/api-keys/create/

Simplified endpoint for API key creation.     * @param {APIKeyCreateRequest} data - Request body     * @returns {Promise<APIKeyCreate>} Response data
     */
    async paymentsApiKeysCreateCreate(data) {
        const path = `/cfg/payments/api-keys/create/`;        return this.post(path, data);    }
    /**
     * paymentsApiKeysExpiringSoonRetrieve     * Get API keys expiring soon.

GET /api/api-keys/expiring_soon/?days=7     * @returns {Promise<APIKeyDetail>} Response data
     */
    async paymentsApiKeysExpiringSoonRetrieve() {
        const path = `/cfg/payments/api-keys/expiring_soon/`;        return this.get(path);    }
    /**
     * paymentsApiKeysHealthRetrieve     * Health check for the ViewSet and related services.

Returns service status and basic metrics.     * @returns {Promise<APIKeyDetail>} Response data
     */
    async paymentsApiKeysHealthRetrieve() {
        const path = `/cfg/payments/api-keys/health/`;        return this.get(path);    }
    /**
     * paymentsApiKeysStatsRetrieve     * Get statistics for the current queryset.

Returns counts, aggregates, and breakdowns.     * @returns {Promise<APIKeyDetail>} Response data
     */
    async paymentsApiKeysStatsRetrieve() {
        const path = `/cfg/payments/api-keys/stats/`;        return this.get(path);    }
    /**
     * Validate API Key (Standalone)     * Standalone endpoint to validate an API key and return key information     * @param {APIKeyValidationRequest} data - Request body     * @returns {Promise<APIKeyValidationResponse>} Response data
     */
    async paymentsApiKeysValidateCreate(data) {
        const path = `/cfg/payments/api-keys/validate/`;        return this.post(path, data);    }
    /**
     * Validate API Key     * Validate an API key and return key information     * @param {APIKeyValidationRequest} data - Request body     * @returns {Promise<APIKeyValidationResponse>} Response data
     */
    async paymentsApiKeysValidateKeyCreate(data) {
        const path = `/cfg/payments/api-keys/validate_key/`;        return this.post(path, data);    }
    /**
     * paymentsBalancesList     * User balance ViewSet: /api/balances/

Read-only access to user balances with statistics.     * @param {Object} [params={}] - Query parameters     * @param {string} [params.ordering] - Which field to use when ordering the results.     * @param {number} [params.page] - A page number within the paginated result set.     * @param {number} [params.page_size] - Number of results to return per page.     * @param {string} [params.search] - A search term.     * @param {number} [params.user]     * @returns {Promise<PaginatedUserBalanceList>} Response data
     */
    async paymentsBalancesList(params = {}) {
        const path = `/cfg/payments/balances/`;        return this.get(path, params);    }
    /**
     * paymentsBalancesRetrieve     * User balance ViewSet: /api/balances/

Read-only access to user balances with statistics.     * @param {number} id - A unique integer value identifying this User Balance.     * @returns {Promise<UserBalance>} Response data
     */
    async paymentsBalancesRetrieve(id) {
        const path = `/cfg/payments/balances/${id}/`;        return this.get(path);    }
    /**
     * paymentsBalancesAnalyticsRetrieve     * Get balance analytics.

GET /api/balances/analytics/?days=30     * @returns {Promise<UserBalance>} Response data
     */
    async paymentsBalancesAnalyticsRetrieve() {
        const path = `/cfg/payments/balances/analytics/`;        return this.get(path);    }
    /**
     * paymentsBalancesHealthRetrieve     * Health check for the ViewSet and related services.

Returns service status and basic metrics.     * @returns {Promise<UserBalance>} Response data
     */
    async paymentsBalancesHealthRetrieve() {
        const path = `/cfg/payments/balances/health/`;        return this.get(path);    }
    /**
     * paymentsBalancesStatsRetrieve     * Get statistics for the current queryset.

Returns counts, aggregates, and breakdowns.     * @returns {Promise<UserBalance>} Response data
     */
    async paymentsBalancesStatsRetrieve() {
        const path = `/cfg/payments/balances/stats/`;        return this.get(path);    }
    /**
     * paymentsBalancesSummaryRetrieve     * Get balance summary for all users.

GET /api/balances/summary/     * @returns {Promise<UserBalance>} Response data
     */
    async paymentsBalancesSummaryRetrieve() {
        const path = `/cfg/payments/balances/summary/`;        return this.get(path);    }
    /**
     * paymentsCurrenciesList     * Currency ViewSet: /api/currencies/

Read-only access to currency information with conversion capabilities.     * @param {Object} [params={}] - Query parameters     * @param {"crypto" | "fiat"} [params.currency_type] - Type of currency

* `fiat` - Fiat Currency
* `crypto` - Cryptocurrency     * @param {boolean} [params.is_active]     * @param {string} [params.ordering] - Which field to use when ordering the results.     * @param {number} [params.page] - A page number within the paginated result set.     * @param {number} [params.page_size] - Number of results to return per page.     * @param {string} [params.search] - A search term.     * @returns {Promise<PaginatedCurrencyListList>} Response data
     */
    async paymentsCurrenciesList(params = {}) {
        const path = `/cfg/payments/currencies/`;        return this.get(path, params);    }
    /**
     * paymentsCurrenciesCreate     * Disable create action.     * @returns {Promise<Currency>} Response data
     */
    async paymentsCurrenciesCreate() {
        const path = `/cfg/payments/currencies/`;        return this.post(path, {});    }
    /**
     * paymentsCurrenciesRetrieve     * Currency ViewSet: /api/currencies/

Read-only access to currency information with conversion capabilities.     * @param {number} id - A unique integer value identifying this Currency.     * @returns {Promise<Currency>} Response data
     */
    async paymentsCurrenciesRetrieve(id) {
        const path = `/cfg/payments/currencies/${id}/`;        return this.get(path);    }
    /**
     * paymentsCurrenciesNetworksRetrieve     * Get networks for specific currency.

GET /api/currencies/{id}/networks/     * @param {number} id - A unique integer value identifying this Currency.     * @returns {Promise<Currency>} Response data
     */
    async paymentsCurrenciesNetworksRetrieve(id) {
        const path = `/cfg/payments/currencies/${id}/networks/`;        return this.get(path);    }
    /**
     * paymentsCurrenciesProvidersRetrieve     * Get providers supporting specific currency.

GET /api/currencies/{id}/providers/     * @param {number} id - A unique integer value identifying this Currency.     * @returns {Promise<Currency>} Response data
     */
    async paymentsCurrenciesProvidersRetrieve(id) {
        const path = `/cfg/payments/currencies/${id}/providers/`;        return this.get(path);    }
    /**
     * paymentsCurrenciesConvertCreate     * Convert between currencies.

POST /api/currencies/convert/     * @returns {Promise<Currency>} Response data
     */
    async paymentsCurrenciesConvertCreate() {
        const path = `/cfg/payments/currencies/convert/`;        return this.post(path, {});    }
    /**
     * paymentsCurrenciesCryptoRetrieve     * Get only cryptocurrencies.

GET /api/currencies/crypto/     * @returns {Promise<Currency>} Response data
     */
    async paymentsCurrenciesCryptoRetrieve() {
        const path = `/cfg/payments/currencies/crypto/`;        return this.get(path);    }
    /**
     * paymentsCurrenciesFiatRetrieve     * Get only fiat currencies.

GET /api/currencies/fiat/     * @returns {Promise<Currency>} Response data
     */
    async paymentsCurrenciesFiatRetrieve() {
        const path = `/cfg/payments/currencies/fiat/`;        return this.get(path);    }
    /**
     * paymentsCurrenciesHealthRetrieve     * Health check for the ViewSet and related services.

Returns service status and basic metrics.     * @returns {Promise<Currency>} Response data
     */
    async paymentsCurrenciesHealthRetrieve() {
        const path = `/cfg/payments/currencies/health/`;        return this.get(path);    }
    /**
     * Get exchange rates     * Get current exchange rates for specified currencies     * @param {Object} [params={}] - Query parameters     * @param {string} [params.base_currency] - Base currency code (e.g., USD)     * @param {string} [params.currencies] - Comma-separated list of target currency codes (e.g., BTC,ETH,USDT)     * @returns {Promise<Currency>} Response data
     */
    async paymentsCurrenciesRatesRetrieve(params = {}) {
        const path = `/cfg/payments/currencies/rates/`;        return this.get(path, params);    }
    /**
     * paymentsCurrenciesStableRetrieve     * Get only stablecoins.

GET /api/currencies/stable/     * @returns {Promise<Currency>} Response data
     */
    async paymentsCurrenciesStableRetrieve() {
        const path = `/cfg/payments/currencies/stable/`;        return this.get(path);    }
    /**
     * paymentsCurrenciesStatsRetrieve     * Get statistics for the current queryset.

Returns counts, aggregates, and breakdowns.     * @returns {Promise<Currency>} Response data
     */
    async paymentsCurrenciesStatsRetrieve() {
        const path = `/cfg/payments/currencies/stats/`;        return this.get(path);    }
    /**
     * Get supported currencies     * Get list of supported currencies from payment providers     * @param {Object} [params={}] - Query parameters     * @param {"crypto" | "fiat" | "stablecoin"} [params.currency_type] - Currency type filter: crypto, fiat, or stablecoin     * @param {string} [params.provider] - Payment provider name (e.g., nowpayments)     * @returns {Promise<Currency>} Response data
     */
    async paymentsCurrenciesSupportedRetrieve(params = {}) {
        const path = `/cfg/payments/currencies/supported/`;        return this.get(path, params);    }
    /**
     * paymentsEndpointGroupsList     * Endpoint Group ViewSet: /api/endpoint-groups/

Read-only access to endpoint group information.     * @param {Object} [params={}] - Query parameters     * @param {boolean} [params.is_enabled]     * @param {string} [params.ordering] - Which field to use when ordering the results.     * @param {number} [params.page] - A page number within the paginated result set.     * @param {number} [params.page_size] - Number of results to return per page.     * @param {string} [params.search] - A search term.     * @returns {Promise<PaginatedEndpointGroupList>} Response data
     */
    async paymentsEndpointGroupsList(params = {}) {
        const path = `/cfg/payments/endpoint-groups/`;        return this.get(path, params);    }
    /**
     * paymentsEndpointGroupsRetrieve     * Endpoint Group ViewSet: /api/endpoint-groups/

Read-only access to endpoint group information.     * @param {number} id - A unique integer value identifying this Endpoint Group.     * @returns {Promise<EndpointGroup>} Response data
     */
    async paymentsEndpointGroupsRetrieve(id) {
        const path = `/cfg/payments/endpoint-groups/${id}/`;        return this.get(path);    }
    /**
     * paymentsEndpointGroupsAvailableRetrieve     * Get available endpoint groups for subscription.

GET /api/endpoint-groups/available/     * @returns {Promise<EndpointGroup>} Response data
     */
    async paymentsEndpointGroupsAvailableRetrieve() {
        const path = `/cfg/payments/endpoint-groups/available/`;        return this.get(path);    }
    /**
     * paymentsEndpointGroupsHealthRetrieve     * Health check for the ViewSet and related services.

Returns service status and basic metrics.     * @returns {Promise<EndpointGroup>} Response data
     */
    async paymentsEndpointGroupsHealthRetrieve() {
        const path = `/cfg/payments/endpoint-groups/health/`;        return this.get(path);    }
    /**
     * paymentsEndpointGroupsStatsRetrieve     * Get statistics for the current queryset.

Returns counts, aggregates, and breakdowns.     * @returns {Promise<EndpointGroup>} Response data
     */
    async paymentsEndpointGroupsStatsRetrieve() {
        const path = `/cfg/payments/endpoint-groups/stats/`;        return this.get(path);    }
    /**
     * paymentsHealthRetrieve     * Health check for the ViewSet and related services.

Returns service status and basic metrics.     * @returns {Promise<Payment>} Response data
     */
    async paymentsHealthRetrieve() {
        const path = `/cfg/payments/health/`;        return this.get(path);    }
    /**
     * paymentsNetworksList     * Network ViewSet: /api/networks/

Read-only access to blockchain network information.     * @param {Object} [params={}] - Query parameters     * @param {boolean} [params.is_active]     * @param {string} [params.native_currency__code]     * @param {string} [params.ordering] - Which field to use when ordering the results.     * @param {number} [params.page] - A page number within the paginated result set.     * @param {number} [params.page_size] - Number of results to return per page.     * @param {string} [params.search] - A search term.     * @returns {Promise<PaginatedNetworkList>} Response data
     */
    async paymentsNetworksList(params = {}) {
        const path = `/cfg/payments/networks/`;        return this.get(path, params);    }
    /**
     * paymentsNetworksRetrieve     * Network ViewSet: /api/networks/

Read-only access to blockchain network information.     * @param {number} id - A unique integer value identifying this Network.     * @returns {Promise<Network>} Response data
     */
    async paymentsNetworksRetrieve(id) {
        const path = `/cfg/payments/networks/${id}/`;        return this.get(path);    }
    /**
     * paymentsNetworksByCurrencyRetrieve     * Get networks grouped by currency.

GET /api/networks/by_currency/     * @returns {Promise<Network>} Response data
     */
    async paymentsNetworksByCurrencyRetrieve() {
        const path = `/cfg/payments/networks/by_currency/`;        return this.get(path);    }
    /**
     * paymentsNetworksHealthRetrieve     * Health check for the ViewSet and related services.

Returns service status and basic metrics.     * @returns {Promise<Network>} Response data
     */
    async paymentsNetworksHealthRetrieve() {
        const path = `/cfg/payments/networks/health/`;        return this.get(path);    }
    /**
     * paymentsNetworksStatsRetrieve     * Get statistics for the current queryset.

Returns counts, aggregates, and breakdowns.     * @returns {Promise<Network>} Response data
     */
    async paymentsNetworksStatsRetrieve() {
        const path = `/cfg/payments/networks/stats/`;        return this.get(path);    }
    /**
     * API Keys Overview     * Get API keys overview     * @returns {Promise<APIKeysOverview>} Response data
     */
    async paymentsOverviewDashboardApiKeysOverviewRetrieve() {
        const path = `/cfg/payments/overview/dashboard/api_keys_overview/`;        return this.get(path);    }
    /**
     * Balance Overview     * Get user balance overview     * @returns {Promise<BalanceOverview>} Response data
     */
    async paymentsOverviewDashboardBalanceOverviewRetrieve() {
        const path = `/cfg/payments/overview/dashboard/balance_overview/`;        return this.get(path);    }
    /**
     * Payments Chart Data     * Get chart data for payments visualization     * @param {Object} [params={}] - Query parameters     * @param {"1y" | "30d" | "7d" | "90d"} [params.period] - Time period for chart data     * @returns {Promise<PaymentsChartResponse>} Response data
     */
    async paymentsOverviewDashboardChartDataRetrieve(params = {}) {
        const path = `/cfg/payments/overview/dashboard/chart_data/`;        return this.get(path, params);    }
    /**
     * Payments Dashboard Metrics     * Get payments dashboard metrics including balance, subscriptions, API keys, and payments     * @returns {Promise<PaymentsMetrics>} Response data
     */
    async paymentsOverviewDashboardMetricsRetrieve() {
        const path = `/cfg/payments/overview/dashboard/metrics/`;        return this.get(path);    }
    /**
     * Payments Dashboard Overview     * Get complete payments dashboard overview with metrics, recent payments, and analytics     * @returns {Promise<PaymentsDashboardOverview>} Response data
     */
    async paymentsOverviewDashboardOverviewRetrieve() {
        const path = `/cfg/payments/overview/dashboard/overview/`;        return this.get(path);    }
    /**
     * Payment Analytics     * Get analytics for payments by currency and provider     * @param {Object} [params={}] - Query parameters     * @param {number} [params.limit] - Number of analytics items to return     * @returns {Promise<PaymentAnalyticsResponse>} Response data
     */
    async paymentsOverviewDashboardPaymentAnalyticsRetrieve(params = {}) {
        const path = `/cfg/payments/overview/dashboard/payment_analytics/`;        return this.get(path, params);    }
    /**
     * Recent Payments     * Get recent payments for the user     * @param {Object} [params={}] - Query parameters     * @param {number} [params.limit] - Number of payments to return     * @param {number} [params.page] - A page number within the paginated result set.     * @param {number} [params.page_size] - Number of results to return per page.     * @returns {Promise<PaginatedRecentPaymentList>} Response data
     */
    async paymentsOverviewDashboardRecentPaymentsList(params = {}) {
        const path = `/cfg/payments/overview/dashboard/recent_payments/`;        return this.get(path, params);    }
    /**
     * Recent Transactions     * Get recent balance transactions for the user     * @param {Object} [params={}] - Query parameters     * @param {number} [params.limit] - Number of transactions to return     * @param {number} [params.page] - A page number within the paginated result set.     * @param {number} [params.page_size] - Number of results to return per page.     * @returns {Promise<PaginatedRecentTransactionList>} Response data
     */
    async paymentsOverviewDashboardRecentTransactionsList(params = {}) {
        const path = `/cfg/payments/overview/dashboard/recent_transactions/`;        return this.get(path, params);    }
    /**
     * Subscription Overview     * Get current subscription overview     * @returns {Promise<SubscriptionOverview>} Response data
     */
    async paymentsOverviewDashboardSubscriptionOverviewRetrieve() {
        const path = `/cfg/payments/overview/dashboard/subscription_overview/`;        return this.get(path);    }
    /**
     * paymentsPaymentList     * Global payment ViewSet: /api/v1/payments/

Provides admin-level access to all payments with filtering and stats.     * @param {Object} [params={}] - Query parameters     * @param {string} [params.currency__code]     * @param {string} [params.ordering] - Which field to use when ordering the results.     * @param {number} [params.page] - A page number within the paginated result set.     * @param {number} [params.page_size] - Number of results to return per page.     * @param {"nowpayments"} [params.provider] - Payment provider

* `nowpayments` - NowPayments     * @param {string} [params.search] - A search term.     * @param {"cancelled" | "completed" | "confirmed" | "confirming" | "expired" | "failed" | "pending" | "refunded"} [params.status] - Current payment status

* `pending` - Pending
* `confirming` - Confirming
* `confirmed` - Confirmed
* `completed` - Completed
* `failed` - Failed
* `expired` - Expired
* `cancelled` - Cancelled
* `refunded` - Refunded     * @param {number} [params.user]     * @returns {Promise<PaginatedPaymentListList>} Response data
     */
    async paymentsPaymentList(params = {}) {
        const path = `/cfg/payments/payment/`;        return this.get(path, params);    }
    /**
     * paymentsPaymentCreate     * Global payment ViewSet: /api/v1/payments/

Provides admin-level access to all payments with filtering and stats.     * @param {PaymentCreateRequest} data - Request body     * @returns {Promise<PaymentCreate>} Response data
     */
    async paymentsPaymentCreate(data) {
        const path = `/cfg/payments/payment/`;        return this.post(path, data);    }
    /**
     * paymentsPaymentRetrieve     * Global payment ViewSet: /api/v1/payments/

Provides admin-level access to all payments with filtering and stats.     * @param {string} id     * @returns {Promise<Payment>} Response data
     */
    async paymentsPaymentRetrieve(id) {
        const path = `/cfg/payments/payment/${id}/`;        return this.get(path);    }
    /**
     * paymentsPaymentUpdate     * Global payment ViewSet: /api/v1/payments/

Provides admin-level access to all payments with filtering and stats.     * @param {string} id     * @param {PaymentRequest} data - Request body     * @returns {Promise<Payment>} Response data
     */
    async paymentsPaymentUpdate(id, data) {
        const path = `/cfg/payments/payment/${id}/`;        return this.put(path, data);    }
    /**
     * paymentsPaymentPartialUpdate     * Global payment ViewSet: /api/v1/payments/

Provides admin-level access to all payments with filtering and stats.     * @param {string} id     * @param {PatchedPaymentRequest} data - Request body     * @returns {Promise<Payment>} Response data
     */
    async paymentsPaymentPartialUpdate(id, data) {
        const path = `/cfg/payments/payment/${id}/`;        return this.patch(path, data);    }
    /**
     * paymentsPaymentDestroy     * Global payment ViewSet: /api/v1/payments/

Provides admin-level access to all payments with filtering and stats.     * @param {string} id     * @returns {Promise<void>} No content
     */
    async paymentsPaymentDestroy(id) {
        const path = `/cfg/payments/payment/${id}/`;        return this.delete(path);    }
    /**
     * paymentsPaymentCancelCreate     * Cancel payment.

POST /api/v1/payments/{id}/cancel/     * @param {string} id     * @param {PaymentRequest} data - Request body     * @returns {Promise<Payment>} Response data
     */
    async paymentsPaymentCancelCreate(id, data) {
        const path = `/cfg/payments/payment/${id}/cancel/`;        return this.post(path, data);    }
    /**
     * paymentsPaymentCheckStatusCreate     * Check payment status with provider.

POST /api/v1/payments/{id}/check_status/     * @param {string} id     * @param {PaymentRequest} data - Request body     * @returns {Promise<Payment>} Response data
     */
    async paymentsPaymentCheckStatusCreate(id, data) {
        const path = `/cfg/payments/payment/${id}/check_status/`;        return this.post(path, data);    }
    /**
     * paymentsPaymentAnalyticsRetrieve     * Get payment analytics.

GET /api/v1/payments/analytics/?days=30     * @returns {Promise<Payment>} Response data
     */
    async paymentsPaymentAnalyticsRetrieve() {
        const path = `/cfg/payments/payment/analytics/`;        return this.get(path);    }
    /**
     * paymentsPaymentByProviderRetrieve     * Get payments grouped by provider.

GET /api/v1/payments/by_provider/     * @returns {Promise<Payment>} Response data
     */
    async paymentsPaymentByProviderRetrieve() {
        const path = `/cfg/payments/payment/by_provider/`;        return this.get(path);    }
    /**
     * paymentsPaymentCreateCreate     * Standalone payment creation endpoint: /api/v1/payments/create/

Simplified endpoint for payment creation without full ViewSet overhead.     * @param {PaymentCreateRequest} data - Request body     * @returns {Promise<PaymentCreate>} Response data
     */
    async paymentsPaymentCreateCreate(data) {
        const path = `/cfg/payments/payment/create/`;        return this.post(path, data);    }
    /**
     * paymentsPaymentHealthRetrieve     * Health check for the ViewSet and related services.

Returns service status and basic metrics.     * @returns {Promise<Payment>} Response data
     */
    async paymentsPaymentHealthRetrieve() {
        const path = `/cfg/payments/payment/health/`;        return this.get(path);    }
    /**
     * paymentsPaymentStatsRetrieve     * Get statistics for the current queryset.

Returns counts, aggregates, and breakdowns.     * @returns {Promise<Payment>} Response data
     */
    async paymentsPaymentStatsRetrieve() {
        const path = `/cfg/payments/payment/stats/`;        return this.get(path);    }
    /**
     * paymentsPaymentStatusRetrieve     * Standalone payment status endpoint: /api/v1/payments/{id}/status/

Quick status check without full ViewSet overhead.     * @param {string} id     * @returns {Promise<Payment>} Response data
     */
    async paymentsPaymentStatusRetrieve(id) {
        const path = `/cfg/payments/payment/status/${id}/`;        return this.get(path);    }
    /**
     * paymentsProviderCurrenciesList     * Provider Currency ViewSet: /api/provider-currencies/

Read-only access to provider-specific currency information.     * @param {Object} [params={}] - Query parameters     * @param {string} [params.currency__code]     * @param {boolean} [params.is_enabled]     * @param {string} [params.network__code]     * @param {string} [params.ordering] - Which field to use when ordering the results.     * @param {number} [params.page] - A page number within the paginated result set.     * @param {number} [params.page_size] - Number of results to return per page.     * @param {string} [params.provider]     * @param {string} [params.search] - A search term.     * @returns {Promise<PaginatedProviderCurrencyList>} Response data
     */
    async paymentsProviderCurrenciesList(params = {}) {
        const path = `/cfg/payments/provider-currencies/`;        return this.get(path, params);    }
    /**
     * paymentsProviderCurrenciesRetrieve     * Provider Currency ViewSet: /api/provider-currencies/

Read-only access to provider-specific currency information.     * @param {number} id - A unique integer value identifying this Provider Currency.     * @returns {Promise<ProviderCurrency>} Response data
     */
    async paymentsProviderCurrenciesRetrieve(id) {
        const path = `/cfg/payments/provider-currencies/${id}/`;        return this.get(path);    }
    /**
     * Get provider currencies grouped by provider     * Get provider currencies grouped by provider     * @param {Object} [params={}] - Query parameters     * @param {string} [params.provider] - Filter by payment provider (e.g., nowpayments)     * @returns {Promise<ProviderCurrency>} Response data
     */
    async paymentsProviderCurrenciesByProviderRetrieve(params = {}) {
        const path = `/cfg/payments/provider-currencies/by_provider/`;        return this.get(path, params);    }
    /**
     * paymentsProviderCurrenciesHealthRetrieve     * Health check for the ViewSet and related services.

Returns service status and basic metrics.     * @returns {Promise<ProviderCurrency>} Response data
     */
    async paymentsProviderCurrenciesHealthRetrieve() {
        const path = `/cfg/payments/provider-currencies/health/`;        return this.get(path);    }
    /**
     * paymentsProviderCurrenciesLimitsRetrieve     * Get currency limits by provider.

GET /api/provider-currencies/limits/?provider=nowpayments     * @returns {Promise<ProviderCurrency>} Response data
     */
    async paymentsProviderCurrenciesLimitsRetrieve() {
        const path = `/cfg/payments/provider-currencies/limits/`;        return this.get(path);    }
    /**
     * paymentsProviderCurrenciesStatsRetrieve     * Get statistics for the current queryset.

Returns counts, aggregates, and breakdowns.     * @returns {Promise<ProviderCurrency>} Response data
     */
    async paymentsProviderCurrenciesStatsRetrieve() {
        const path = `/cfg/payments/provider-currencies/stats/`;        return this.get(path);    }
    /**
     * paymentsSubscriptionsList     * Global subscription ViewSet: /api/subscriptions/

Provides admin-level access to all subscriptions with filtering and stats.     * @param {Object} [params={}] - Query parameters     * @param {string} [params.ordering] - Which field to use when ordering the results.     * @param {number} [params.page] - A page number within the paginated result set.     * @param {number} [params.page_size] - Number of results to return per page.     * @param {string} [params.search] - A search term.     * @param {"active" | "cancelled" | "expired" | "inactive" | "suspended"} [params.status] - Subscription status

* `active` - Active
* `inactive` - Inactive
* `suspended` - Suspended
* `cancelled` - Cancelled
* `expired` - Expired     * @param {"basic" | "enterprise" | "free" | "pro"} [params.tier] - Subscription tier

* `free` - Free Tier
* `basic` - Basic Tier
* `pro` - Pro Tier
* `enterprise` - Enterprise Tier     * @param {number} [params.user]     * @returns {Promise<PaginatedSubscriptionListList>} Response data
     */
    async paymentsSubscriptionsList(params = {}) {
        const path = `/cfg/payments/subscriptions/`;        return this.get(path, params);    }
    /**
     * paymentsSubscriptionsCreate     * Global subscription ViewSet: /api/subscriptions/

Provides admin-level access to all subscriptions with filtering and stats.     * @param {SubscriptionCreateRequest} data - Request body     * @returns {Promise<SubscriptionCreate>} Response data
     */
    async paymentsSubscriptionsCreate(data) {
        const path = `/cfg/payments/subscriptions/`;        return this.post(path, data);    }
    /**
     * paymentsSubscriptionsRetrieve     * Global subscription ViewSet: /api/subscriptions/

Provides admin-level access to all subscriptions with filtering and stats.     * @param {string} id     * @returns {Promise<Subscription>} Response data
     */
    async paymentsSubscriptionsRetrieve(id) {
        const path = `/cfg/payments/subscriptions/${id}/`;        return this.get(path);    }
    /**
     * paymentsSubscriptionsUpdate     * Global subscription ViewSet: /api/subscriptions/

Provides admin-level access to all subscriptions with filtering and stats.     * @param {string} id     * @param {SubscriptionRequest} data - Request body     * @returns {Promise<Subscription>} Response data
     */
    async paymentsSubscriptionsUpdate(id, data) {
        const path = `/cfg/payments/subscriptions/${id}/`;        return this.put(path, data);    }
    /**
     * paymentsSubscriptionsPartialUpdate     * Global subscription ViewSet: /api/subscriptions/

Provides admin-level access to all subscriptions with filtering and stats.     * @param {string} id     * @param {PatchedSubscriptionRequest} data - Request body     * @returns {Promise<Subscription>} Response data
     */
    async paymentsSubscriptionsPartialUpdate(id, data) {
        const path = `/cfg/payments/subscriptions/${id}/`;        return this.patch(path, data);    }
    /**
     * paymentsSubscriptionsDestroy     * Global subscription ViewSet: /api/subscriptions/

Provides admin-level access to all subscriptions with filtering and stats.     * @param {string} id     * @returns {Promise<void>} No content
     */
    async paymentsSubscriptionsDestroy(id) {
        const path = `/cfg/payments/subscriptions/${id}/`;        return this.delete(path);    }
    /**
     * paymentsSubscriptionsIncrementUsageCreate     * Increment subscription usage.

POST /api/subscriptions/{id}/increment_usage/     * @param {string} id     * @param {SubscriptionRequest} data - Request body     * @returns {Promise<Subscription>} Response data
     */
    async paymentsSubscriptionsIncrementUsageCreate(id, data) {
        const path = `/cfg/payments/subscriptions/${id}/increment_usage/`;        return this.post(path, data);    }
    /**
     * paymentsSubscriptionsUpdateStatusCreate     * Update subscription status.

POST /api/subscriptions/{id}/update_status/     * @param {string} id     * @param {SubscriptionRequest} data - Request body     * @returns {Promise<Subscription>} Response data
     */
    async paymentsSubscriptionsUpdateStatusCreate(id, data) {
        const path = `/cfg/payments/subscriptions/${id}/update_status/`;        return this.post(path, data);    }
    /**
     * paymentsSubscriptionsAnalyticsRetrieve     * Get subscription analytics.

GET /api/subscriptions/analytics/?days=30     * @returns {Promise<Subscription>} Response data
     */
    async paymentsSubscriptionsAnalyticsRetrieve() {
        const path = `/cfg/payments/subscriptions/analytics/`;        return this.get(path);    }
    /**
     * paymentsSubscriptionsByStatusRetrieve     * Get subscriptions grouped by status.

GET /api/subscriptions/by_status/     * @returns {Promise<Subscription>} Response data
     */
    async paymentsSubscriptionsByStatusRetrieve() {
        const path = `/cfg/payments/subscriptions/by_status/`;        return this.get(path);    }
    /**
     * paymentsSubscriptionsByTierRetrieve     * Get subscriptions grouped by tier.

GET /api/subscriptions/by_tier/     * @returns {Promise<Subscription>} Response data
     */
    async paymentsSubscriptionsByTierRetrieve() {
        const path = `/cfg/payments/subscriptions/by_tier/`;        return this.get(path);    }
    /**
     * paymentsSubscriptionsHealthRetrieve     * Health check for the ViewSet and related services.

Returns service status and basic metrics.     * @returns {Promise<Subscription>} Response data
     */
    async paymentsSubscriptionsHealthRetrieve() {
        const path = `/cfg/payments/subscriptions/health/`;        return this.get(path);    }
    /**
     * paymentsSubscriptionsStatsRetrieve     * Get statistics for the current queryset.

Returns counts, aggregates, and breakdowns.     * @returns {Promise<Subscription>} Response data
     */
    async paymentsSubscriptionsStatsRetrieve() {
        const path = `/cfg/payments/subscriptions/stats/`;        return this.get(path);    }
    /**
     * paymentsTariffsList     * Tariff ViewSet: /api/tariffs/

Read-only access to tariff information for subscription selection.     * @param {Object} [params={}] - Query parameters     * @param {boolean} [params.is_active]     * @param {string} [params.ordering] - Which field to use when ordering the results.     * @param {number} [params.page] - A page number within the paginated result set.     * @param {number} [params.page_size] - Number of results to return per page.     * @param {string} [params.search] - A search term.     * @returns {Promise<PaginatedTariffList>} Response data
     */
    async paymentsTariffsList(params = {}) {
        const path = `/cfg/payments/tariffs/`;        return this.get(path, params);    }
    /**
     * paymentsTariffsRetrieve     * Tariff ViewSet: /api/tariffs/

Read-only access to tariff information for subscription selection.     * @param {number} id - A unique integer value identifying this Tariff.     * @returns {Promise<Tariff>} Response data
     */
    async paymentsTariffsRetrieve(id) {
        const path = `/cfg/payments/tariffs/${id}/`;        return this.get(path);    }
    /**
     * paymentsTariffsEndpointGroupsRetrieve     * Get endpoint groups for specific tariff.

GET /api/tariffs/{id}/endpoint_groups/     * @param {number} id - A unique integer value identifying this Tariff.     * @returns {Promise<Tariff>} Response data
     */
    async paymentsTariffsEndpointGroupsRetrieve(id) {
        const path = `/cfg/payments/tariffs/${id}/endpoint_groups/`;        return this.get(path);    }
    /**
     * paymentsTariffsFreeRetrieve     * Get free tariffs.

GET /api/tariffs/free/     * @returns {Promise<Tariff>} Response data
     */
    async paymentsTariffsFreeRetrieve() {
        const path = `/cfg/payments/tariffs/free/`;        return this.get(path);    }
    /**
     * paymentsTariffsHealthRetrieve     * Health check for the ViewSet and related services.

Returns service status and basic metrics.     * @returns {Promise<Tariff>} Response data
     */
    async paymentsTariffsHealthRetrieve() {
        const path = `/cfg/payments/tariffs/health/`;        return this.get(path);    }
    /**
     * paymentsTariffsPaidRetrieve     * Get paid tariffs.

GET /api/tariffs/paid/     * @returns {Promise<Tariff>} Response data
     */
    async paymentsTariffsPaidRetrieve() {
        const path = `/cfg/payments/tariffs/paid/`;        return this.get(path);    }
    /**
     * paymentsTariffsStatsRetrieve     * Get statistics for the current queryset.

Returns counts, aggregates, and breakdowns.     * @returns {Promise<Tariff>} Response data
     */
    async paymentsTariffsStatsRetrieve() {
        const path = `/cfg/payments/tariffs/stats/`;        return this.get(path);    }
    /**
     * paymentsTransactionsList     * Transaction ViewSet: /api/transactions/

Read-only access to transaction history with filtering.     * @param {Object} [params={}] - Query parameters     * @param {string} [params.ordering] - Which field to use when ordering the results.     * @param {number} [params.page] - A page number within the paginated result set.     * @param {number} [params.page_size] - Number of results to return per page.     * @param {string} [params.payment_id]     * @param {string} [params.search] - A search term.     * @param {"adjustment" | "bonus" | "deposit" | "fee" | "payment" | "refund" | "withdrawal"} [params.transaction_type] - Type of transaction

* `deposit` - Deposit
* `withdrawal` - Withdrawal
* `payment` - Payment
* `refund` - Refund
* `fee` - Fee
* `bonus` - Bonus
* `adjustment` - Adjustment     * @param {number} [params.user]     * @returns {Promise<PaginatedTransactionList>} Response data
     */
    async paymentsTransactionsList(params = {}) {
        const path = `/cfg/payments/transactions/`;        return this.get(path, params);    }
    /**
     * paymentsTransactionsRetrieve     * Transaction ViewSet: /api/transactions/

Read-only access to transaction history with filtering.     * @param {string} id     * @returns {Promise<Transaction>} Response data
     */
    async paymentsTransactionsRetrieve(id) {
        const path = `/cfg/payments/transactions/${id}/`;        return this.get(path);    }
    /**
     * paymentsTransactionsByTypeRetrieve     * Get transactions grouped by type.

GET /api/transactions/by_type/     * @returns {Promise<Transaction>} Response data
     */
    async paymentsTransactionsByTypeRetrieve() {
        const path = `/cfg/payments/transactions/by_type/`;        return this.get(path);    }
    /**
     * paymentsTransactionsHealthRetrieve     * Health check for the ViewSet and related services.

Returns service status and basic metrics.     * @returns {Promise<Transaction>} Response data
     */
    async paymentsTransactionsHealthRetrieve() {
        const path = `/cfg/payments/transactions/health/`;        return this.get(path);    }
    /**
     * paymentsTransactionsRecentRetrieve     * Get recent transactions.

GET /api/transactions/recent/?limit=10     * @returns {Promise<Transaction>} Response data
     */
    async paymentsTransactionsRecentRetrieve() {
        const path = `/cfg/payments/transactions/recent/`;        return this.get(path);    }
    /**
     * paymentsTransactionsStatsRetrieve     * Get statistics for the current queryset.

Returns counts, aggregates, and breakdowns.     * @returns {Promise<Transaction>} Response data
     */
    async paymentsTransactionsStatsRetrieve() {
        const path = `/cfg/payments/transactions/stats/`;        return this.get(path);    }
    /**
     * paymentsUsersList     * User-specific payment ViewSet: /api/v1/users/{user_id}/payments/

Provides user-scoped access to payments with full CRUD operations.     * @param {Object} [params={}] - Query parameters     * @param {string} [params.currency__code]     * @param {string} [params.ordering] - Which field to use when ordering the results.     * @param {number} [params.page] - A page number within the paginated result set.     * @param {number} [params.page_size] - Number of results to return per page.     * @param {"nowpayments"} [params.provider] - Payment provider

* `nowpayments` - NowPayments     * @param {string} [params.search] - A search term.     * @param {"cancelled" | "completed" | "confirmed" | "confirming" | "expired" | "failed" | "pending" | "refunded"} [params.status] - Current payment status

* `pending` - Pending
* `confirming` - Confirming
* `confirmed` - Confirmed
* `completed` - Completed
* `failed` - Failed
* `expired` - Expired
* `cancelled` - Cancelled
* `refunded` - Refunded     * @returns {Promise<PaginatedPaymentListList>} Response data
     */
    async paymentsUsersList(params = {}) {
        const path = `/cfg/payments/users/`;        return this.get(path, params);    }
    /**
     * paymentsUsersCreate     * User-specific payment ViewSet: /api/v1/users/{user_id}/payments/

Provides user-scoped access to payments with full CRUD operations.     * @param {PaymentCreateRequest} data - Request body     * @returns {Promise<PaymentCreate>} Response data
     */
    async paymentsUsersCreate(data) {
        const path = `/cfg/payments/users/`;        return this.post(path, data);    }
    /**
     * paymentsUsersRetrieve     * User-specific payment ViewSet: /api/v1/users/{user_id}/payments/

Provides user-scoped access to payments with full CRUD operations.     * @param {string} id     * @returns {Promise<Payment>} Response data
     */
    async paymentsUsersRetrieve(id) {
        const path = `/cfg/payments/users/${id}/`;        return this.get(path);    }
    /**
     * paymentsUsersUpdate     * User-specific payment ViewSet: /api/v1/users/{user_id}/payments/

Provides user-scoped access to payments with full CRUD operations.     * @param {string} id     * @param {PaymentRequest} data - Request body     * @returns {Promise<Payment>} Response data
     */
    async paymentsUsersUpdate(id, data) {
        const path = `/cfg/payments/users/${id}/`;        return this.put(path, data);    }
    /**
     * paymentsUsersPartialUpdate     * User-specific payment ViewSet: /api/v1/users/{user_id}/payments/

Provides user-scoped access to payments with full CRUD operations.     * @param {string} id     * @param {PatchedPaymentRequest} data - Request body     * @returns {Promise<Payment>} Response data
     */
    async paymentsUsersPartialUpdate(id, data) {
        const path = `/cfg/payments/users/${id}/`;        return this.patch(path, data);    }
    /**
     * paymentsUsersDestroy     * User-specific payment ViewSet: /api/v1/users/{user_id}/payments/

Provides user-scoped access to payments with full CRUD operations.     * @param {string} id     * @returns {Promise<void>} No content
     */
    async paymentsUsersDestroy(id) {
        const path = `/cfg/payments/users/${id}/`;        return this.delete(path);    }
    /**
     * paymentsUsersCancelCreate     * Cancel payment.

POST /api/v1/users/{user_id}/payments/{id}/cancel/     * @param {string} id     * @param {PaymentRequest} data - Request body     * @returns {Promise<Payment>} Response data
     */
    async paymentsUsersCancelCreate(id, data) {
        const path = `/cfg/payments/users/${id}/cancel/`;        return this.post(path, data);    }
    /**
     * paymentsUsersCheckStatusCreate     * Check payment status with provider.

POST /api/v1/users/{user_id}/payments/{id}/check_status/     * @param {string} id     * @param {PaymentRequest} data - Request body     * @returns {Promise<Payment>} Response data
     */
    async paymentsUsersCheckStatusCreate(id, data) {
        const path = `/cfg/payments/users/${id}/check_status/`;        return this.post(path, data);    }
    /**
     * paymentsUsersApiKeysList     * User-specific API Key ViewSet: /api/users/{user_id}/api-keys/

Provides user-scoped access to API keys with full CRUD operations.     * @param {number} user_pk     * @param {Object} [params={}] - Query parameters     * @param {boolean} [params.is_active]     * @param {string} [params.ordering] - Which field to use when ordering the results.     * @param {number} [params.page] - A page number within the paginated result set.     * @param {number} [params.page_size] - Number of results to return per page.     * @param {string} [params.search] - A search term.     * @returns {Promise<PaginatedAPIKeyListList>} Response data
     */
    async paymentsUsersApiKeysList(user_pk, params = {}) {
        const path = `/cfg/payments/users/${user_pk}/api-keys/`;        return this.get(path, params);    }
    /**
     * paymentsUsersApiKeysCreate     * User-specific API Key ViewSet: /api/users/{user_id}/api-keys/

Provides user-scoped access to API keys with full CRUD operations.     * @param {number} user_pk     * @param {APIKeyCreateRequest} data - Request body     * @returns {Promise<APIKeyCreate>} Response data
     */
    async paymentsUsersApiKeysCreate(user_pk, data) {
        const path = `/cfg/payments/users/${user_pk}/api-keys/`;        return this.post(path, data);    }
    /**
     * paymentsUsersApiKeysRetrieve     * User-specific API Key ViewSet: /api/users/{user_id}/api-keys/

Provides user-scoped access to API keys with full CRUD operations.     * @param {string} id     * @param {number} user_pk     * @returns {Promise<APIKeyDetail>} Response data
     */
    async paymentsUsersApiKeysRetrieve(id, user_pk) {
        const path = `/cfg/payments/users/${user_pk}/api-keys/${id}/`;        return this.get(path);    }
    /**
     * paymentsUsersApiKeysUpdate     * User-specific API Key ViewSet: /api/users/{user_id}/api-keys/

Provides user-scoped access to API keys with full CRUD operations.     * @param {string} id     * @param {number} user_pk     * @param {APIKeyUpdateRequest} data - Request body     * @returns {Promise<APIKeyUpdate>} Response data
     */
    async paymentsUsersApiKeysUpdate(id, user_pk, data) {
        const path = `/cfg/payments/users/${user_pk}/api-keys/${id}/`;        return this.put(path, data);    }
    /**
     * paymentsUsersApiKeysPartialUpdate     * User-specific API Key ViewSet: /api/users/{user_id}/api-keys/

Provides user-scoped access to API keys with full CRUD operations.     * @param {string} id     * @param {number} user_pk     * @param {PatchedAPIKeyUpdateRequest} data - Request body     * @returns {Promise<APIKeyUpdate>} Response data
     */
    async paymentsUsersApiKeysPartialUpdate(id, user_pk, data) {
        const path = `/cfg/payments/users/${user_pk}/api-keys/${id}/`;        return this.patch(path, data);    }
    /**
     * paymentsUsersApiKeysDestroy     * User-specific API Key ViewSet: /api/users/{user_id}/api-keys/

Provides user-scoped access to API keys with full CRUD operations.     * @param {string} id     * @param {number} user_pk     * @returns {Promise<void>} No content
     */
    async paymentsUsersApiKeysDestroy(id, user_pk) {
        const path = `/cfg/payments/users/${user_pk}/api-keys/${id}/`;        return this.delete(path);    }
    /**
     * paymentsUsersApiKeysPerformActionCreate     * Perform action on API key.

POST /api/users/{user_id}/api-keys/{id}/perform_action/     * @param {string} id     * @param {number} user_pk     * @returns {Promise<APIKeyDetail>} Response data
     */
    async paymentsUsersApiKeysPerformActionCreate(id, user_pk) {
        const path = `/cfg/payments/users/${user_pk}/api-keys/${id}/perform_action/`;        return this.post(path, {});    }
    /**
     * paymentsUsersApiKeysActiveRetrieve     * Get user's active API keys.

GET /api/users/{user_id}/api-keys/active/     * @param {number} user_pk     * @returns {Promise<APIKeyDetail>} Response data
     */
    async paymentsUsersApiKeysActiveRetrieve(user_pk) {
        const path = `/cfg/payments/users/${user_pk}/api-keys/active/`;        return this.get(path);    }
    /**
     * paymentsUsersApiKeysHealthRetrieve     * Health check for the ViewSet and related services.

Returns service status and basic metrics.     * @param {number} user_pk     * @returns {Promise<APIKeyDetail>} Response data
     */
    async paymentsUsersApiKeysHealthRetrieve(user_pk) {
        const path = `/cfg/payments/users/${user_pk}/api-keys/health/`;        return this.get(path);    }
    /**
     * paymentsUsersApiKeysStatsRetrieve     * Get statistics for the current queryset.

Returns counts, aggregates, and breakdowns.     * @param {number} user_pk     * @returns {Promise<APIKeyDetail>} Response data
     */
    async paymentsUsersApiKeysStatsRetrieve(user_pk) {
        const path = `/cfg/payments/users/${user_pk}/api-keys/stats/`;        return this.get(path);    }
    /**
     * paymentsUsersApiKeysSummaryRetrieve     * Get user API key summary.

GET /api/users/{user_id}/api-keys/summary/     * @param {number} user_pk     * @returns {Promise<APIKeyDetail>} Response data
     */
    async paymentsUsersApiKeysSummaryRetrieve(user_pk) {
        const path = `/cfg/payments/users/${user_pk}/api-keys/summary/`;        return this.get(path);    }
    /**
     * paymentsUsersPaymentList     * User-specific payment ViewSet: /api/v1/users/{user_id}/payments/

Provides user-scoped access to payments with full CRUD operations.     * @param {number} user_pk     * @param {Object} [params={}] - Query parameters     * @param {string} [params.currency__code]     * @param {string} [params.ordering] - Which field to use when ordering the results.     * @param {number} [params.page] - A page number within the paginated result set.     * @param {number} [params.page_size] - Number of results to return per page.     * @param {"nowpayments"} [params.provider] - Payment provider

* `nowpayments` - NowPayments     * @param {string} [params.search] - A search term.     * @param {"cancelled" | "completed" | "confirmed" | "confirming" | "expired" | "failed" | "pending" | "refunded"} [params.status] - Current payment status

* `pending` - Pending
* `confirming` - Confirming
* `confirmed` - Confirmed
* `completed` - Completed
* `failed` - Failed
* `expired` - Expired
* `cancelled` - Cancelled
* `refunded` - Refunded     * @returns {Promise<PaginatedPaymentListList>} Response data
     */
    async paymentsUsersPaymentList(user_pk, params = {}) {
        const path = `/cfg/payments/users/${user_pk}/payment/`;        return this.get(path, params);    }
    /**
     * paymentsUsersPaymentCreate     * User-specific payment ViewSet: /api/v1/users/{user_id}/payments/

Provides user-scoped access to payments with full CRUD operations.     * @param {number} user_pk     * @param {PaymentCreateRequest} data - Request body     * @returns {Promise<PaymentCreate>} Response data
     */
    async paymentsUsersPaymentCreate(user_pk, data) {
        const path = `/cfg/payments/users/${user_pk}/payment/`;        return this.post(path, data);    }
    /**
     * paymentsUsersPaymentRetrieve     * User-specific payment ViewSet: /api/v1/users/{user_id}/payments/

Provides user-scoped access to payments with full CRUD operations.     * @param {string} id     * @param {number} user_pk     * @returns {Promise<Payment>} Response data
     */
    async paymentsUsersPaymentRetrieve(id, user_pk) {
        const path = `/cfg/payments/users/${user_pk}/payment/${id}/`;        return this.get(path);    }
    /**
     * paymentsUsersPaymentUpdate     * User-specific payment ViewSet: /api/v1/users/{user_id}/payments/

Provides user-scoped access to payments with full CRUD operations.     * @param {string} id     * @param {number} user_pk     * @param {PaymentRequest} data - Request body     * @returns {Promise<Payment>} Response data
     */
    async paymentsUsersPaymentUpdate(id, user_pk, data) {
        const path = `/cfg/payments/users/${user_pk}/payment/${id}/`;        return this.put(path, data);    }
    /**
     * paymentsUsersPaymentPartialUpdate     * User-specific payment ViewSet: /api/v1/users/{user_id}/payments/

Provides user-scoped access to payments with full CRUD operations.     * @param {string} id     * @param {number} user_pk     * @param {PatchedPaymentRequest} data - Request body     * @returns {Promise<Payment>} Response data
     */
    async paymentsUsersPaymentPartialUpdate(id, user_pk, data) {
        const path = `/cfg/payments/users/${user_pk}/payment/${id}/`;        return this.patch(path, data);    }
    /**
     * paymentsUsersPaymentDestroy     * User-specific payment ViewSet: /api/v1/users/{user_id}/payments/

Provides user-scoped access to payments with full CRUD operations.     * @param {string} id     * @param {number} user_pk     * @returns {Promise<void>} No content
     */
    async paymentsUsersPaymentDestroy(id, user_pk) {
        const path = `/cfg/payments/users/${user_pk}/payment/${id}/`;        return this.delete(path);    }
    /**
     * paymentsUsersPaymentCancelCreate     * Cancel payment.

POST /api/v1/users/{user_id}/payments/{id}/cancel/     * @param {string} id     * @param {number} user_pk     * @param {PaymentRequest} data - Request body     * @returns {Promise<Payment>} Response data
     */
    async paymentsUsersPaymentCancelCreate(id, user_pk, data) {
        const path = `/cfg/payments/users/${user_pk}/payment/${id}/cancel/`;        return this.post(path, data);    }
    /**
     * paymentsUsersPaymentCheckStatusCreate     * Check payment status with provider.

POST /api/v1/users/{user_id}/payments/{id}/check_status/     * @param {string} id     * @param {number} user_pk     * @param {PaymentRequest} data - Request body     * @returns {Promise<Payment>} Response data
     */
    async paymentsUsersPaymentCheckStatusCreate(id, user_pk, data) {
        const path = `/cfg/payments/users/${user_pk}/payment/${id}/check_status/`;        return this.post(path, data);    }
    /**
     * paymentsUsersPaymentHealthRetrieve     * Health check for the ViewSet and related services.

Returns service status and basic metrics.     * @param {number} user_pk     * @returns {Promise<Payment>} Response data
     */
    async paymentsUsersPaymentHealthRetrieve(user_pk) {
        const path = `/cfg/payments/users/${user_pk}/payment/health/`;        return this.get(path);    }
    /**
     * paymentsUsersPaymentStatsRetrieve     * Get statistics for the current queryset.

Returns counts, aggregates, and breakdowns.     * @param {number} user_pk     * @returns {Promise<Payment>} Response data
     */
    async paymentsUsersPaymentStatsRetrieve(user_pk) {
        const path = `/cfg/payments/users/${user_pk}/payment/stats/`;        return this.get(path);    }
    /**
     * paymentsUsersPaymentSummaryRetrieve     * Get user payment summary.

GET /api/v1/users/{user_id}/payments/summary/     * @param {number} user_pk     * @returns {Promise<Payment>} Response data
     */
    async paymentsUsersPaymentSummaryRetrieve(user_pk) {
        const path = `/cfg/payments/users/${user_pk}/payment/summary/`;        return this.get(path);    }
    /**
     * paymentsUsersSubscriptionsList     * User-specific subscription ViewSet: /api/users/{user_id}/subscriptions/

Provides user-scoped access to subscriptions with full CRUD operations.     * @param {number} user_pk     * @param {Object} [params={}] - Query parameters     * @param {string} [params.ordering] - Which field to use when ordering the results.     * @param {number} [params.page] - A page number within the paginated result set.     * @param {number} [params.page_size] - Number of results to return per page.     * @param {string} [params.search] - A search term.     * @param {"active" | "cancelled" | "expired" | "inactive" | "suspended"} [params.status] - Subscription status

* `active` - Active
* `inactive` - Inactive
* `suspended` - Suspended
* `cancelled` - Cancelled
* `expired` - Expired     * @param {"basic" | "enterprise" | "free" | "pro"} [params.tier] - Subscription tier

* `free` - Free Tier
* `basic` - Basic Tier
* `pro` - Pro Tier
* `enterprise` - Enterprise Tier     * @returns {Promise<PaginatedSubscriptionListList>} Response data
     */
    async paymentsUsersSubscriptionsList(user_pk, params = {}) {
        const path = `/cfg/payments/users/${user_pk}/subscriptions/`;        return this.get(path, params);    }
    /**
     * paymentsUsersSubscriptionsCreate     * User-specific subscription ViewSet: /api/users/{user_id}/subscriptions/

Provides user-scoped access to subscriptions with full CRUD operations.     * @param {number} user_pk     * @param {SubscriptionCreateRequest} data - Request body     * @returns {Promise<SubscriptionCreate>} Response data
     */
    async paymentsUsersSubscriptionsCreate(user_pk, data) {
        const path = `/cfg/payments/users/${user_pk}/subscriptions/`;        return this.post(path, data);    }
    /**
     * paymentsUsersSubscriptionsRetrieve     * User-specific subscription ViewSet: /api/users/{user_id}/subscriptions/

Provides user-scoped access to subscriptions with full CRUD operations.     * @param {string} id     * @param {number} user_pk     * @returns {Promise<Subscription>} Response data
     */
    async paymentsUsersSubscriptionsRetrieve(id, user_pk) {
        const path = `/cfg/payments/users/${user_pk}/subscriptions/${id}/`;        return this.get(path);    }
    /**
     * paymentsUsersSubscriptionsUpdate     * User-specific subscription ViewSet: /api/users/{user_id}/subscriptions/

Provides user-scoped access to subscriptions with full CRUD operations.     * @param {string} id     * @param {number} user_pk     * @param {SubscriptionRequest} data - Request body     * @returns {Promise<Subscription>} Response data
     */
    async paymentsUsersSubscriptionsUpdate(id, user_pk, data) {
        const path = `/cfg/payments/users/${user_pk}/subscriptions/${id}/`;        return this.put(path, data);    }
    /**
     * paymentsUsersSubscriptionsPartialUpdate     * User-specific subscription ViewSet: /api/users/{user_id}/subscriptions/

Provides user-scoped access to subscriptions with full CRUD operations.     * @param {string} id     * @param {number} user_pk     * @param {PatchedSubscriptionRequest} data - Request body     * @returns {Promise<Subscription>} Response data
     */
    async paymentsUsersSubscriptionsPartialUpdate(id, user_pk, data) {
        const path = `/cfg/payments/users/${user_pk}/subscriptions/${id}/`;        return this.patch(path, data);    }
    /**
     * paymentsUsersSubscriptionsDestroy     * User-specific subscription ViewSet: /api/users/{user_id}/subscriptions/

Provides user-scoped access to subscriptions with full CRUD operations.     * @param {string} id     * @param {number} user_pk     * @returns {Promise<void>} No content
     */
    async paymentsUsersSubscriptionsDestroy(id, user_pk) {
        const path = `/cfg/payments/users/${user_pk}/subscriptions/${id}/`;        return this.delete(path);    }
    /**
     * paymentsUsersSubscriptionsIncrementUsageCreate     * Increment subscription usage.

POST /api/users/{user_id}/subscriptions/{id}/increment_usage/     * @param {string} id     * @param {number} user_pk     * @param {SubscriptionRequest} data - Request body     * @returns {Promise<Subscription>} Response data
     */
    async paymentsUsersSubscriptionsIncrementUsageCreate(id, user_pk, data) {
        const path = `/cfg/payments/users/${user_pk}/subscriptions/${id}/increment_usage/`;        return this.post(path, data);    }
    /**
     * paymentsUsersSubscriptionsUpdateStatusCreate     * Update subscription status.

POST /api/users/{user_id}/subscriptions/{id}/update_status/     * @param {string} id     * @param {number} user_pk     * @param {SubscriptionRequest} data - Request body     * @returns {Promise<Subscription>} Response data
     */
    async paymentsUsersSubscriptionsUpdateStatusCreate(id, user_pk, data) {
        const path = `/cfg/payments/users/${user_pk}/subscriptions/${id}/update_status/`;        return this.post(path, data);    }
    /**
     * paymentsUsersSubscriptionsActiveRetrieve     * Get user's active subscription.

GET /api/users/{user_id}/subscriptions/active/     * @param {number} user_pk     * @returns {Promise<Subscription>} Response data
     */
    async paymentsUsersSubscriptionsActiveRetrieve(user_pk) {
        const path = `/cfg/payments/users/${user_pk}/subscriptions/active/`;        return this.get(path);    }
    /**
     * paymentsUsersSubscriptionsHealthRetrieve     * Health check for the ViewSet and related services.

Returns service status and basic metrics.     * @param {number} user_pk     * @returns {Promise<Subscription>} Response data
     */
    async paymentsUsersSubscriptionsHealthRetrieve(user_pk) {
        const path = `/cfg/payments/users/${user_pk}/subscriptions/health/`;        return this.get(path);    }
    /**
     * paymentsUsersSubscriptionsStatsRetrieve     * Get statistics for the current queryset.

Returns counts, aggregates, and breakdowns.     * @param {number} user_pk     * @returns {Promise<Subscription>} Response data
     */
    async paymentsUsersSubscriptionsStatsRetrieve(user_pk) {
        const path = `/cfg/payments/users/${user_pk}/subscriptions/stats/`;        return this.get(path);    }
    /**
     * paymentsUsersSubscriptionsSummaryRetrieve     * Get user subscription summary.

GET /api/users/{user_id}/subscriptions/summary/     * @param {number} user_pk     * @returns {Promise<Subscription>} Response data
     */
    async paymentsUsersSubscriptionsSummaryRetrieve(user_pk) {
        const path = `/cfg/payments/users/${user_pk}/subscriptions/summary/`;        return this.get(path);    }
    /**
     * paymentsUsersHealthRetrieve     * Health check for the ViewSet and related services.

Returns service status and basic metrics.     * @returns {Promise<Payment>} Response data
     */
    async paymentsUsersHealthRetrieve() {
        const path = `/cfg/payments/users/health/`;        return this.get(path);    }
    /**
     * paymentsUsersStatsRetrieve     * Get statistics for the current queryset.

Returns counts, aggregates, and breakdowns.     * @returns {Promise<Payment>} Response data
     */
    async paymentsUsersStatsRetrieve() {
        const path = `/cfg/payments/users/stats/`;        return this.get(path);    }
    /**
     * paymentsUsersSummaryRetrieve     * Get user payment summary.

GET /api/v1/users/{user_id}/payments/summary/     * @returns {Promise<Payment>} Response data
     */
    async paymentsUsersSummaryRetrieve() {
        const path = `/cfg/payments/users/summary/`;        return this.get(path);    }
    /**
     * Webhook Endpoint Info     * Get webhook endpoint information for debugging and configuration     * @param {string} provider - Payment provider name     * @returns {Promise<WebhookResponse>} Response data
     */
    async paymentsWebhooksRetrieve(provider) {
        const path = `/cfg/payments/webhooks/${provider}/`;        return this.get(path);    }
    /**
     * Process Webhook     * Process incoming webhook from payment provider     * @param {string} provider - Payment provider name (nowpayments, stripe, etc.)     * @param {WebhookResponseRequest} data - Request body     * @returns {Promise<WebhookResponse>} Response data
     */
    async paymentsWebhooksCreate(provider, data) {
        const path = `/cfg/payments/webhooks/${provider}/`;        return this.post(path, data);    }
    /**
     * Webhook Health Check     * Check webhook service health status and recent activity metrics     * @returns {Promise<WebhookHealth>} Response data
     */
    async paymentsWebhooksHealthRetrieve() {
        const path = `/cfg/payments/webhooks/health/`;        return this.get(path);    }
    /**
     * Supported Webhook Providers     * Get list of supported webhook providers with configuration details     * @returns {Promise<SupportedProviders>} Response data
     */
    async paymentsWebhooksProvidersRetrieve() {
        const path = `/cfg/payments/webhooks/providers/`;        return this.get(path);    }
    /**
     * Webhook Statistics     * Get webhook processing statistics for a given time period     * @param {Object} [params={}] - Query parameters     * @param {number} [params.days] - Number of days to analyze (1-365)     * @returns {Promise<WebhookStats>} Response data
     */
    async paymentsWebhooksStatsRetrieve(params = {}) {
        const path = `/cfg/payments/webhooks/stats/`;        return this.get(path, params);    }
}

// Default instance for convenience
export const paymentsAPI = new PaymentsAPI();

// Default export
export default PaymentsAPI;