/**
 * Type definitions for django-cfg API
 * Auto-generated from OpenAPI schema
 * @module types
 */

// This file contains JSDoc type definitions generated from the OpenAPI schema
// These types can be used for better IDE support and documentation

/**
 * @typedef {Object} APIKeyCreate * @description API key creation serializer with service integration.

Creates new API keys and returns the full key value (only once). * @property {string} name - Descriptive name for the API key * @property {number} [expires_in_days] - Expiration in days (optional, null for no expiration) */

/**
 * @typedef {Object} APIKeyCreateRequest * @description API key creation serializer with service integration.

Creates new API keys and returns the full key value (only once). * @property {string} name - Descriptive name for the API key * @property {number} [expires_in_days] - Expiration in days (optional, null for no expiration) */

/**
 * @typedef {Object} APIKeyDetail * @description Complete API key serializer with full details.

Used for API key detail views (no key value for security). * @property {string} id - Unique identifier for this record * @property {string} user * @property {string} name - Human-readable name for this API key * @property {string} key_preview * @property {boolean} is_active - Whether this API key is active * @property {boolean} is_expired * @property {boolean} is_valid * @property {number} days_until_expiry * @property {number} total_requests - Total number of requests made with this key * @property {string} last_used_at - When this API key was last used * @property {string} expires_at - When this API key expires (null = never expires) * @property {string} created_at - When this record was created * @property {string} updated_at - When this record was last updated */

/**
 * @typedef {Object} APIKeyList * @description Lightweight API key serializer for lists.

Optimized for API key lists with minimal data (no key value). * @property {string} id - Unique identifier for this record * @property {string} user * @property {string} name - Human-readable name for this API key * @property {boolean} is_active - Whether this API key is active * @property {boolean} is_expired * @property {boolean} is_valid * @property {number} total_requests - Total number of requests made with this key * @property {string} last_used_at - When this API key was last used * @property {string} expires_at - When this API key expires (null = never expires) * @property {string} created_at - When this record was created */

/**
 * @typedef {Object} APIKeyUpdate * @description API key update serializer for modifying API key properties.

Allows updating name and active status only. * @property {string} name - Human-readable name for this API key * @property {boolean} [is_active] - Whether this API key is active */

/**
 * @typedef {Object} APIKeyUpdateRequest * @description API key update serializer for modifying API key properties.

Allows updating name and active status only. * @property {string} name - Human-readable name for this API key * @property {boolean} [is_active] - Whether this API key is active */

/**
 * @typedef {Object} APIKeyValidationRequest * @description API key validation serializer.

Validates API key and returns key information. * @property {string} key - API key to validate */

/**
 * @typedef {Object} APIKeyValidationResponse * @description API key validation response serializer.

Defines the structure of API key validation response for OpenAPI schema. * @property {boolean} success - Whether the validation was successful * @property {boolean} valid - Whether the API key is valid * @property {any} api_key - API key details if valid * @property {string} message - Validation message * @property {string} [error] - Error message if validation failed * @property {string} [error_code] - Error code if validation failed */

/**
 * @typedef {Object} APIKeysOverview * @description API keys overview metrics * @property {number} total_keys - Total number of API keys * @property {number} active_keys - Number of active API keys * @property {number} expired_keys - Number of expired API keys * @property {number} total_requests - Total requests across all keys * @property {string} last_used_at - When any key was last used * @property {string} most_used_key_name - Name of most used API key * @property {number} most_used_key_requests - Requests count for most used key * @property {number} expiring_soon_count - Number of keys expiring within 7 days */

/**
 * @typedef {Object} APIResponse * @description Standard API response serializer. * @property {boolean} success - Operation success status * @property {string} [message] - Success message * @property {string} [error] - Error message * @property {Record<string, any>} [data] - Response data */

/**
 * @typedef {Object} APIResponseRequest * @description Standard API response serializer. * @property {boolean} success - Operation success status * @property {string} [message] - Success message * @property {string} [error] - Error message * @property {Record<string, any>} [data] - Response data */

/**
 * @typedef {Object} AdminPaymentCreate * @description Serializer for creating payments in admin interface.
Uses UniversalPayment only for data creation. * @property {number} user * @property {number} amount_usd * @property {string} provider * @property {string} [description] * @property {string} [callback_url] * @property {string} [cancel_url] */

/**
 * @typedef {Object} AdminPaymentCreateRequest * @description Serializer for creating payments in admin interface.
Uses UniversalPayment only for data creation. * @property {number} user * @property {number} amount_usd * @property {string} currency_code - Provider currency code (e.g., BTC, ZROERC20) * @property {string} provider * @property {string} [description] * @property {string} [callback_url] * @property {string} [cancel_url] */

/**
 * @typedef {Object} AdminPaymentDetail * @description Detailed serializer for individual payment in admin interface.
Uses UniversalPayment only for data extraction. * @property {string} id * @property {any} user * @property {string} internal_payment_id * @property {number} amount_usd * @property {number} actual_amount_usd * @property {number} fee_amount_usd * @property {string} currency_code * @property {string} currency_name * @property {string} provider * @property {string} provider_display * @property {string} status * @property {string} status_display * @property {string} pay_amount * @property {string} pay_address * @property {string} payment_url * @property {string} transaction_hash * @property {number} confirmations_count * @property {string} security_nonce * @property {string} expires_at * @property {string} completed_at * @property {string} status_changed_at * @property {string} description * @property {string} callback_url * @property {string} cancel_url * @property {any} provider_data * @property {any} webhook_data * @property {string} created_at * @property {string} updated_at * @property {string} age */

/**
 * @typedef {Object} AdminPaymentList * @description Serializer for payment list in admin interface.
Uses UniversalPayment only for data extraction. * @property {string} id * @property {string} internal_payment_id * @property {any} user * @property {number} amount_usd * @property {string} currency_code * @property {string} currency_name * @property {string} provider * @property {string} provider_display * @property {string} status * @property {string} status_display * @property {string} pay_amount * @property {string} pay_address * @property {string} transaction_hash * @property {string} created_at * @property {string} updated_at * @property {string} description * @property {string} age */

/**
 * @typedef {Object} AdminPaymentStats * @description Serializer for payment statistics in admin interface. * @property {number} total_payments * @property {number} total_amount_usd * @property {number} successful_payments * @property {number} failed_payments * @property {number} pending_payments * @property {number} success_rate * @property {Record<string, Record<string, any>>} by_provider - Statistics by provider * @property {Record<string, Record<string, any>>} by_currency - Statistics by currency * @property {Record<string, number>} last_24h - Payments in last 24 hours * @property {Record<string, number>} last_7d - Payments in last 7 days * @property {Record<string, number>} last_30d - Payments in last 30 days */

/**
 * @typedef {Object} AdminPaymentUpdate * @description Serializer for updating payments in admin interface. * @property {"pending" | "confirming" | "confirmed" | "completed" | "failed" | "expired" | "cancelled" | "refunded"} [status] - Current payment status

* `pending` - Pending
* `confirming` - Confirming
* `confirmed` - Confirmed
* `completed` - Completed
* `failed` - Failed
* `expired` - Expired
* `cancelled` - Cancelled
* `refunded` - Refunded * @property {string} [description] - Payment description * @property {string} [callback_url] - Success callback URL * @property {string} [cancel_url] - Cancellation URL * @property {any} [provider_data] - Provider-specific data (validated by Pydantic) * @property {any} [webhook_data] - Webhook data (validated by Pydantic) */

/**
 * @typedef {Object} AdminPaymentUpdateRequest * @description Serializer for updating payments in admin interface. * @property {"pending" | "confirming" | "confirmed" | "completed" | "failed" | "expired" | "cancelled" | "refunded"} [status] - Current payment status

* `pending` - Pending
* `confirming` - Confirming
* `confirmed` - Confirmed
* `completed` - Completed
* `failed` - Failed
* `expired` - Expired
* `cancelled` - Cancelled
* `refunded` - Refunded * @property {string} [description] - Payment description * @property {string} [callback_url] - Success callback URL * @property {string} [cancel_url] - Cancellation URL * @property {any} [provider_data] - Provider-specific data (validated by Pydantic) * @property {any} [webhook_data] - Webhook data (validated by Pydantic) */

/**
 * @typedef {Object} AdminUser * @description Simplified user serializer for admin interface. * @property {number} id * @property {string} username - Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only. * @property {string} email * @property {string} first_name * @property {string} last_name * @property {boolean} is_active - Designates whether this user should be treated as active. Unselect this instead of deleting accounts. */

/**
 * @typedef {Object} BalanceOverview * @description User balance overview metrics * @property {number} current_balance - Current balance in USD * @property {string} balance_display - Formatted balance display * @property {number} total_deposited - Total amount deposited (lifetime) * @property {number} total_spent - Total amount spent (lifetime) * @property {string} last_transaction_at - Last transaction timestamp * @property {boolean} has_transactions - Whether user has any transactions * @property {boolean} is_empty - Whether balance is zero */

/**
 * @typedef {Object} BulkEmailRequest * @description Simple serializer for bulk email. * @property {string[]} recipients * @property {string} subject * @property {string} email_title * @property {string} main_text * @property {string} [main_html_content] * @property {string} [button_text] * @property {string} [button_url] * @property {string} [secondary_text] */

/**
 * @typedef {Object} BulkEmailResponse * @description Response for bulk email sending. * @property {boolean} success * @property {number} sent_count * @property {number} failed_count * @property {number} total_recipients * @property {string} [error] */

/**
 * @typedef {Object} ChartDataPoint * @description Chart data point for payments analytics * @property {string} x - X-axis value (date) * @property {number} y - Y-axis value (amount or count) */

/**
 * @typedef {Object} ChartSeries * @description Chart series data for payments visualization * @property {string} name - Series name * @property {ChartDataPoint[]} data - Data points * @property {string} color - Series color */

/**
 * @typedef {Object} Currency * @description Complete currency serializer with full details.

Used for currency information and management. * @property {number} id * @property {string} code - Currency code (e.g., BTC, USD, ETH) * @property {string} name - Full currency name (e.g., Bitcoin, US Dollar) * @property {string} symbol - Currency symbol (e.g., $, ₿, Ξ) * @property {"fiat" | "crypto"} currency_type - Type of currency

* `fiat` - Fiat Currency
* `crypto` - Cryptocurrency * @property {string} type_display * @property {number} decimal_places - Number of decimal places for this currency * @property {boolean} is_active - Whether this currency is available for payments * @property {boolean} is_crypto - Check if this is a cryptocurrency. * @property {boolean} is_fiat - Check if this is a fiat currency. * @property {string} created_at - When this record was created * @property {string} updated_at - When this record was last updated */

/**
 * @typedef {Object} CurrencyAnalyticsItem * @description Analytics data for a single currency * @property {string} currency_code - Currency code (e.g., BTC) * @property {string} currency_name - Currency name (e.g., Bitcoin) * @property {number} total_payments - Total number of payments * @property {number} total_amount - Total amount in USD * @property {number} completed_payments - Number of completed payments * @property {number} average_amount - Average payment amount in USD * @property {number} success_rate - Success rate percentage */

/**
 * @typedef {Object} CurrencyList * @description Lightweight currency serializer for lists.

Optimized for currency selection and lists. * @property {number} id * @property {string} code - Currency code (e.g., BTC, USD, ETH) * @property {string} name - Full currency name (e.g., Bitcoin, US Dollar) * @property {string} symbol - Currency symbol (e.g., $, ₿, Ξ) * @property {"fiat" | "crypto"} currency_type - Type of currency

* `fiat` - Fiat Currency
* `crypto` - Cryptocurrency * @property {string} type_display * @property {boolean} is_active - Whether this currency is available for payments */

/**
 * @typedef {Object} EmailLog * @description Serializer for EmailLog model. * @property {string} id * @property {number} user * @property {string} user_email * @property {number} newsletter * @property {string} newsletter_title * @property {string} recipient - Comma-separated email addresses * @property {string} subject * @property {string} body * @property {"pending" | "sent" | "failed"} status - * `pending` - Pending
* `sent` - Sent
* `failed` - Failed * @property {string} created_at * @property {string} sent_at * @property {string} error_message */

/**
 * @typedef {Object} Endpoint * @description Serializer for single endpoint status. * @property {string} url - Resolved URL (for parametrized URLs) or URL pattern * @property {string} [url_pattern] - Original URL pattern (for parametrized URLs) * @property {string} [url_name] - Django URL name (if available) * @property {string} [namespace] - URL namespace * @property {string} group - URL group (up to 3 depth) * @property {string} [view] - View function/class name * @property {string} status - Status: healthy, unhealthy, warning, error, skipped, pending * @property {number} [status_code] - HTTP status code * @property {number} [response_time_ms] - Response time in milliseconds * @property {boolean} [is_healthy] - Whether endpoint is healthy * @property {string} [error] - Error message if check failed * @property {string} [error_type] - Error type: database, general, etc. * @property {string} [reason] - Reason for warning/skip * @property {string} [last_checked] - Timestamp of last check * @property {boolean} [has_parameters] - Whether URL has parameters that were resolved with test values * @property {boolean} [required_auth] - Whether endpoint required JWT authentication * @property {boolean} [rate_limited] - Whether endpoint returned 429 (rate limited) */

/**
 * @typedef {Object} EndpointGroup * @description Endpoint group serializer for API access management.

Used for subscription endpoint group configuration. * @property {number} id * @property {string} name - Endpoint group name (e.g., 'Payment API', 'Balance API') * @property {string} description - Description of what this endpoint group provides * @property {boolean} is_enabled - Whether this endpoint group is available * @property {string} created_at * @property {string} updated_at */

/**
 * @typedef {Object} EndpointsStatus * @description Serializer for overall endpoints status response. * @property {string} status - Overall status: healthy, degraded, or unhealthy * @property {string} timestamp - Timestamp of the check * @property {number} total_endpoints - Total number of endpoints checked * @property {number} healthy - Number of healthy endpoints * @property {number} unhealthy - Number of unhealthy endpoints * @property {number} warnings - Number of endpoints with warnings * @property {number} errors - Number of endpoints with errors * @property {number} skipped - Number of skipped endpoints * @property {Endpoint[]} endpoints - List of all endpoints with their status */

/**
 * @typedef {Object} ErrorResponse * @description Generic error response. * @property {boolean} [success] * @property {string} message */

/**
 * @typedef {Object} HealthCheck * @description Serializer for health check response. * @property {string} status - Overall health status: healthy, degraded, or unhealthy * @property {string} timestamp - Timestamp of the health check * @property {string} service - Service name * @property {string} version - Django-CFG version * @property {Record<string, any>} checks - Detailed health checks for databases, cache, and system * @property {Record<string, any>} environment - Environment information */

/**
 * @typedef {Object} LeadSubmission * @description Serializer for lead form submission from frontend. * @property {string} name * @property {string} email * @property {string} [company] * @property {string} [company_site] * @property {"email" | "whatsapp" | "telegram" | "phone" | "other"} [contact_type] - * `email` - Email
* `whatsapp` - WhatsApp
* `telegram` - Telegram
* `phone` - Phone
* `other` - Other * @property {string} [contact_value] * @property {string} [subject] * @property {string} message * @property {any} [extra] * @property {string} site_url - Frontend URL where form was submitted */

/**
 * @typedef {Object} LeadSubmissionError * @description Response serializer for lead submission errors. * @property {boolean} success * @property {string} error * @property {Record<string, any>} [details] */

/**
 * @typedef {Object} LeadSubmissionRequest * @description Serializer for lead form submission from frontend. * @property {string} name * @property {string} email * @property {string} [company] * @property {string} [company_site] * @property {"email" | "whatsapp" | "telegram" | "phone" | "other"} [contact_type] - * `email` - Email
* `whatsapp` - WhatsApp
* `telegram` - Telegram
* `phone` - Phone
* `other` - Other * @property {string} [contact_value] * @property {string} [subject] * @property {string} message * @property {any} [extra] * @property {string} site_url - Frontend URL where form was submitted */

/**
 * @typedef {Object} LeadSubmissionResponse * @description Response serializer for successful lead submission. * @property {boolean} success * @property {string} message * @property {number} lead_id */

/**
 * @typedef {Object} Message * @property {string} uuid * @property {string} ticket * @property {any} sender * @property {boolean} is_from_author - Check if this message is from the ticket author. * @property {string} text * @property {string} created_at */

/**
 * @typedef {Object} MessageCreate * @property {string} text */

/**
 * @typedef {Object} MessageCreateRequest * @property {string} text */

/**
 * @typedef {Object} MessageRequest * @property {string} text */

/**
 * @typedef {Object} MethodStat * @description Serializer for individual method statistics. * @property {string} method - RPC method name * @property {number} count - Number of calls * @property {number} percentage - Percentage of total calls * @property {number} [avg_time_ms] - Average execution time in milliseconds * @property {number} [avg_time] - Average execution time (alternative field) * @property {number} [success_rate] - Success rate percentage * @property {string} [last_called] - ISO timestamp of last call */

/**
 * @typedef {Object} MethodStats * @description Serializer for method statistics response. * @property {MethodStat[]} methods - List of method statistics * @property {number} count - Total number of methods * @property {number} total_calls - Total calls across all methods */

/**
 * @typedef {Object} Network * @description Network serializer for blockchain networks.

Used for network information and selection. * @property {number} id * @property {any} currency * @property {string} name - Network name (e.g., Ethereum, Bitcoin, Polygon) * @property {string} code - Network code (e.g., ETH, BTC, MATIC) * @property {boolean} is_active - Whether this network is available for payments * @property {string} created_at - When this record was created * @property {string} updated_at - When this record was last updated */

/**
 * @typedef {Object} Newsletter * @description Serializer for Newsletter model. * @property {number} id * @property {string} title * @property {string} [description] * @property {boolean} [is_active] * @property {boolean} [auto_subscribe] - Automatically subscribe new users to this newsletter * @property {string} created_at * @property {string} updated_at * @property {number} subscribers_count */

/**
 * @typedef {Object} NewsletterCampaign * @description Serializer for NewsletterCampaign model. * @property {number} id * @property {number} newsletter * @property {string} newsletter_title * @property {string} subject * @property {string} email_title * @property {string} main_text * @property {string} [main_html_content] * @property {string} [button_text] * @property {string} [button_url] * @property {string} [secondary_text] * @property {"draft" | "sending" | "sent" | "failed"} status - * `draft` - Draft
* `sending` - Sending
* `sent` - Sent
* `failed` - Failed * @property {string} created_at * @property {string} sent_at * @property {number} recipient_count */

/**
 * @typedef {Object} NewsletterCampaignRequest * @description Serializer for NewsletterCampaign model. * @property {number} newsletter * @property {string} subject * @property {string} email_title * @property {string} main_text * @property {string} [main_html_content] * @property {string} [button_text] * @property {string} [button_url] * @property {string} [secondary_text] */

/**
 * @typedef {Object} NewsletterSubscription * @description Serializer for NewsletterSubscription model. * @property {number} id * @property {number} newsletter * @property {string} newsletter_title * @property {number} [user] * @property {string} user_email * @property {string} email * @property {boolean} [is_active] * @property {string} subscribed_at * @property {string} unsubscribed_at */

/**
 * @typedef {Object} NotificationStats * @description Serializer for notification statistics. * @property {number} total_sent - Total notifications sent * @property {number} delivery_rate - Delivery success rate percentage * @property {Record<string, any>} [by_type] - Breakdown by notification type * @property {any[]} [recent] - Recent notifications * @property {string} [last_sent] - ISO timestamp of last notification * @property {string} [timestamp] - ISO timestamp of the stats * @property {string} [error] - Error message if any */

/**
 * @typedef {Object} OTPErrorResponse * @description Error response for OTP operations. * @property {string} error - Error message */

/**
 * @typedef {Object} OTPRequestRequest * @description Serializer for OTP request. * @property {string} identifier - Email address or phone number for OTP delivery * @property {"email" | "phone"} [channel] - Delivery channel: 'email' or 'phone'. Auto-detected if not provided.

* `email` - Email
* `phone` - Phone * @property {string} [source_url] - Source URL for tracking registration (e.g., https://dashboard.unrealon.com) */

/**
 * @typedef {Object} OTPRequestResponse * @description OTP request response. * @property {string} message - Success message */

/**
 * @typedef {Object} OTPVerifyRequest * @description Serializer for OTP verification. * @property {string} identifier - Email address or phone number used for OTP request * @property {string} otp * @property {"email" | "phone"} [channel] - Delivery channel: 'email' or 'phone'. Auto-detected if not provided.

* `email` - Email
* `phone` - Phone * @property {string} [source_url] - Source URL for tracking login (e.g., https://dashboard.unrealon.com) */

/**
 * @typedef {Object} OTPVerifyResponse * @description OTP verification response. * @property {string} refresh - JWT refresh token * @property {string} access - JWT access token * @property {any} user - User information */

/**
 * @typedef {Object} OverviewStats * @description Serializer for overview statistics. * @property {boolean} [redis_connected] - Whether Redis is connected * @property {number} total_requests_today - Total requests processed today * @property {number} [total_requests_hour] - Total requests in the last hour * @property {string[]} active_methods - List of active RPC methods * @property {string} top_method - Most frequently called method * @property {Record<string, any>} [method_counts] - Count of requests per method * @property {number} avg_response_time_ms - Average response time in milliseconds * @property {number} success_rate - Success rate percentage * @property {number} [error_rate] - Error rate percentage * @property {string} [timestamp] - ISO timestamp of the stats * @property {string} [error] - Error message if any */

/**
 * @typedef {Object} PaginatedAPIKeyListList * @property {number} count - Total number of items across all pages * @property {number} page - Current page number (1-based) * @property {number} pages - Total number of pages * @property {number} page_size - Number of items per page * @property {boolean} has_next - Whether there is a next page * @property {boolean} has_previous - Whether there is a previous page * @property {number} [next_page] - Next page number (null if no next page) * @property {number} [previous_page] - Previous page number (null if no previous page) * @property {APIKeyList[]} results - Array of items for current page */

/**
 * @typedef {Object} PaginatedAdminPaymentListList * @property {number} count - Total number of items across all pages * @property {number} page - Current page number (1-based) * @property {number} pages - Total number of pages * @property {number} page_size - Number of items per page * @property {boolean} has_next - Whether there is a next page * @property {boolean} has_previous - Whether there is a previous page * @property {number} [next_page] - Next page number (null if no next page) * @property {number} [previous_page] - Previous page number (null if no previous page) * @property {AdminPaymentList[]} results - Array of items for current page */

/**
 * @typedef {Object} PaginatedAdminPaymentStatsList * @property {number} count - Total number of items across all pages * @property {number} page - Current page number (1-based) * @property {number} pages - Total number of pages * @property {number} page_size - Number of items per page * @property {boolean} has_next - Whether there is a next page * @property {boolean} has_previous - Whether there is a previous page * @property {number} [next_page] - Next page number (null if no next page) * @property {number} [previous_page] - Previous page number (null if no previous page) * @property {AdminPaymentStats[]} results - Array of items for current page */

/**
 * @typedef {Object} PaginatedAdminUserList * @property {number} count - Total number of items across all pages * @property {number} page - Current page number (1-based) * @property {number} pages - Total number of pages * @property {number} page_size - Number of items per page * @property {boolean} has_next - Whether there is a next page * @property {boolean} has_previous - Whether there is a previous page * @property {number} [next_page] - Next page number (null if no next page) * @property {number} [previous_page] - Previous page number (null if no previous page) * @property {AdminUser[]} results - Array of items for current page */

/**
 * @typedef {Object} PaginatedCurrencyListList * @property {number} count - Total number of items across all pages * @property {number} page - Current page number (1-based) * @property {number} pages - Total number of pages * @property {number} page_size - Number of items per page * @property {boolean} has_next - Whether there is a next page * @property {boolean} has_previous - Whether there is a previous page * @property {number} [next_page] - Next page number (null if no next page) * @property {number} [previous_page] - Previous page number (null if no previous page) * @property {CurrencyList[]} results - Array of items for current page */

/**
 * @typedef {Object} PaginatedEmailLogList * @property {number} count - Total number of items across all pages * @property {number} page - Current page number (1-based) * @property {number} pages - Total number of pages * @property {number} page_size - Number of items per page * @property {boolean} has_next - Whether there is a next page * @property {boolean} has_previous - Whether there is a previous page * @property {number} [next_page] - Next page number (null if no next page) * @property {number} [previous_page] - Previous page number (null if no previous page) * @property {EmailLog[]} results - Array of items for current page */

/**
 * @typedef {Object} PaginatedEndpointGroupList * @property {number} count - Total number of items across all pages * @property {number} page - Current page number (1-based) * @property {number} pages - Total number of pages * @property {number} page_size - Number of items per page * @property {boolean} has_next - Whether there is a next page * @property {boolean} has_previous - Whether there is a previous page * @property {number} [next_page] - Next page number (null if no next page) * @property {number} [previous_page] - Previous page number (null if no previous page) * @property {EndpointGroup[]} results - Array of items for current page */

/**
 * @typedef {Object} PaginatedLeadSubmissionList * @property {number} count - Total number of items across all pages * @property {number} page - Current page number (1-based) * @property {number} pages - Total number of pages * @property {number} page_size - Number of items per page * @property {boolean} has_next - Whether there is a next page * @property {boolean} has_previous - Whether there is a previous page * @property {number} [next_page] - Next page number (null if no next page) * @property {number} [previous_page] - Previous page number (null if no previous page) * @property {LeadSubmission[]} results - Array of items for current page */

/**
 * @typedef {Object} PaginatedMessageList * @property {number} count - Total number of items across all pages * @property {number} page - Current page number (1-based) * @property {number} pages - Total number of pages * @property {number} page_size - Number of items per page * @property {boolean} has_next - Whether there is a next page * @property {boolean} has_previous - Whether there is a previous page * @property {number} [next_page] - Next page number (null if no next page) * @property {number} [previous_page] - Previous page number (null if no previous page) * @property {Message[]} results - Array of items for current page */

/**
 * @typedef {Object} PaginatedNetworkList * @property {number} count - Total number of items across all pages * @property {number} page - Current page number (1-based) * @property {number} pages - Total number of pages * @property {number} page_size - Number of items per page * @property {boolean} has_next - Whether there is a next page * @property {boolean} has_previous - Whether there is a previous page * @property {number} [next_page] - Next page number (null if no next page) * @property {number} [previous_page] - Previous page number (null if no previous page) * @property {Network[]} results - Array of items for current page */

/**
 * @typedef {Object} PaginatedNewsletterCampaignList * @property {number} count - Total number of items across all pages * @property {number} page - Current page number (1-based) * @property {number} pages - Total number of pages * @property {number} page_size - Number of items per page * @property {boolean} has_next - Whether there is a next page * @property {boolean} has_previous - Whether there is a previous page * @property {number} [next_page] - Next page number (null if no next page) * @property {number} [previous_page] - Previous page number (null if no previous page) * @property {NewsletterCampaign[]} results - Array of items for current page */

/**
 * @typedef {Object} PaginatedNewsletterList * @property {number} count - Total number of items across all pages * @property {number} page - Current page number (1-based) * @property {number} pages - Total number of pages * @property {number} page_size - Number of items per page * @property {boolean} has_next - Whether there is a next page * @property {boolean} has_previous - Whether there is a previous page * @property {number} [next_page] - Next page number (null if no next page) * @property {number} [previous_page] - Previous page number (null if no previous page) * @property {Newsletter[]} results - Array of items for current page */

/**
 * @typedef {Object} PaginatedNewsletterSubscriptionList * @property {number} count - Total number of items across all pages * @property {number} page - Current page number (1-based) * @property {number} pages - Total number of pages * @property {number} page_size - Number of items per page * @property {boolean} has_next - Whether there is a next page * @property {boolean} has_previous - Whether there is a previous page * @property {number} [next_page] - Next page number (null if no next page) * @property {number} [previous_page] - Previous page number (null if no previous page) * @property {NewsletterSubscription[]} results - Array of items for current page */

/**
 * @typedef {Object} PaginatedPaymentListList * @property {number} count - Total number of items across all pages * @property {number} page - Current page number (1-based) * @property {number} pages - Total number of pages * @property {number} page_size - Number of items per page * @property {boolean} has_next - Whether there is a next page * @property {boolean} has_previous - Whether there is a previous page * @property {number} [next_page] - Next page number (null if no next page) * @property {number} [previous_page] - Previous page number (null if no previous page) * @property {PaymentList[]} results - Array of items for current page */

/**
 * @typedef {Object} PaginatedProviderCurrencyList * @property {number} count - Total number of items across all pages * @property {number} page - Current page number (1-based) * @property {number} pages - Total number of pages * @property {number} page_size - Number of items per page * @property {boolean} has_next - Whether there is a next page * @property {boolean} has_previous - Whether there is a previous page * @property {number} [next_page] - Next page number (null if no next page) * @property {number} [previous_page] - Previous page number (null if no previous page) * @property {ProviderCurrency[]} results - Array of items for current page */

/**
 * @typedef {Object} PaginatedRecentPaymentList * @property {number} count - Total number of items across all pages * @property {number} page - Current page number (1-based) * @property {number} pages - Total number of pages * @property {number} page_size - Number of items per page * @property {boolean} has_next - Whether there is a next page * @property {boolean} has_previous - Whether there is a previous page * @property {number} [next_page] - Next page number (null if no next page) * @property {number} [previous_page] - Previous page number (null if no previous page) * @property {RecentPayment[]} results - Array of items for current page */

/**
 * @typedef {Object} PaginatedRecentTransactionList * @property {number} count - Total number of items across all pages * @property {number} page - Current page number (1-based) * @property {number} pages - Total number of pages * @property {number} page_size - Number of items per page * @property {boolean} has_next - Whether there is a next page * @property {boolean} has_previous - Whether there is a previous page * @property {number} [next_page] - Next page number (null if no next page) * @property {number} [previous_page] - Previous page number (null if no previous page) * @property {RecentTransaction[]} results - Array of items for current page */

/**
 * @typedef {Object} PaginatedSubscriptionListList * @property {number} count - Total number of items across all pages * @property {number} page - Current page number (1-based) * @property {number} pages - Total number of pages * @property {number} page_size - Number of items per page * @property {boolean} has_next - Whether there is a next page * @property {boolean} has_previous - Whether there is a previous page * @property {number} [next_page] - Next page number (null if no next page) * @property {number} [previous_page] - Previous page number (null if no previous page) * @property {SubscriptionList[]} results - Array of items for current page */

/**
 * @typedef {Object} PaginatedTariffList * @property {number} count - Total number of items across all pages * @property {number} page - Current page number (1-based) * @property {number} pages - Total number of pages * @property {number} page_size - Number of items per page * @property {boolean} has_next - Whether there is a next page * @property {boolean} has_previous - Whether there is a previous page * @property {number} [next_page] - Next page number (null if no next page) * @property {number} [previous_page] - Previous page number (null if no previous page) * @property {Tariff[]} results - Array of items for current page */

/**
 * @typedef {Object} PaginatedTicketList * @property {number} count - Total number of items across all pages * @property {number} page - Current page number (1-based) * @property {number} pages - Total number of pages * @property {number} page_size - Number of items per page * @property {boolean} has_next - Whether there is a next page * @property {boolean} has_previous - Whether there is a previous page * @property {number} [next_page] - Next page number (null if no next page) * @property {number} [previous_page] - Previous page number (null if no previous page) * @property {Ticket[]} results - Array of items for current page */

/**
 * @typedef {Object} PaginatedTransactionList * @property {number} count - Total number of items across all pages * @property {number} page - Current page number (1-based) * @property {number} pages - Total number of pages * @property {number} page_size - Number of items per page * @property {boolean} has_next - Whether there is a next page * @property {boolean} has_previous - Whether there is a previous page * @property {number} [next_page] - Next page number (null if no next page) * @property {number} [previous_page] - Previous page number (null if no previous page) * @property {Transaction[]} results - Array of items for current page */

/**
 * @typedef {Object} PaginatedUserBalanceList * @property {number} count - Total number of items across all pages * @property {number} page - Current page number (1-based) * @property {number} pages - Total number of pages * @property {number} page_size - Number of items per page * @property {boolean} has_next - Whether there is a next page * @property {boolean} has_previous - Whether there is a previous page * @property {number} [next_page] - Next page number (null if no next page) * @property {number} [previous_page] - Previous page number (null if no previous page) * @property {UserBalance[]} results - Array of items for current page */

/**
 * @typedef {Object} PaginatedWebhookEventListList * @property {number} count - Total number of items across all pages * @property {number} page - Current page number (1-based) * @property {number} pages - Total number of pages * @property {number} page_size - Number of items per page * @property {boolean} has_next - Whether there is a next page * @property {boolean} has_previous - Whether there is a previous page * @property {number} [next_page] - Next page number (null if no next page) * @property {number} [previous_page] - Previous page number (null if no previous page) * @property {WebhookEventList[]} results - Array of items for current page */

/**
 * @typedef {Object} PaginatedWebhookStatsList * @property {number} count - Total number of items across all pages * @property {number} page - Current page number (1-based) * @property {number} pages - Total number of pages * @property {number} page_size - Number of items per page * @property {boolean} has_next - Whether there is a next page * @property {boolean} has_previous - Whether there is a previous page * @property {number} [next_page] - Next page number (null if no next page) * @property {number} [previous_page] - Previous page number (null if no previous page) * @property {WebhookStats[]} results - Array of items for current page */

/**
 * @typedef {Object} PatchedAPIKeyUpdateRequest * @description API key update serializer for modifying API key properties.

Allows updating name and active status only. * @property {string} [name] - Human-readable name for this API key * @property {boolean} [is_active] - Whether this API key is active */

/**
 * @typedef {Object} PatchedAdminPaymentUpdateRequest * @description Serializer for updating payments in admin interface. * @property {"pending" | "confirming" | "confirmed" | "completed" | "failed" | "expired" | "cancelled" | "refunded"} [status] - Current payment status

* `pending` - Pending
* `confirming` - Confirming
* `confirmed` - Confirmed
* `completed` - Completed
* `failed` - Failed
* `expired` - Expired
* `cancelled` - Cancelled
* `refunded` - Refunded * @property {string} [description] - Payment description * @property {string} [callback_url] - Success callback URL * @property {string} [cancel_url] - Cancellation URL * @property {any} [provider_data] - Provider-specific data (validated by Pydantic) * @property {any} [webhook_data] - Webhook data (validated by Pydantic) */

/**
 * @typedef {Object} PatchedLeadSubmissionRequest * @description Serializer for lead form submission from frontend. * @property {string} [name] * @property {string} [email] * @property {string} [company] * @property {string} [company_site] * @property {"email" | "whatsapp" | "telegram" | "phone" | "other"} [contact_type] - * `email` - Email
* `whatsapp` - WhatsApp
* `telegram` - Telegram
* `phone` - Phone
* `other` - Other * @property {string} [contact_value] * @property {string} [subject] * @property {string} [message] * @property {any} [extra] * @property {string} [site_url] - Frontend URL where form was submitted */

/**
 * @typedef {Object} PatchedMessageRequest * @property {string} [text] */

/**
 * @typedef {Object} PatchedNewsletterCampaignRequest * @description Serializer for NewsletterCampaign model. * @property {number} [newsletter] * @property {string} [subject] * @property {string} [email_title] * @property {string} [main_text] * @property {string} [main_html_content] * @property {string} [button_text] * @property {string} [button_url] * @property {string} [secondary_text] */

/**
 * @typedef {Object} PatchedPaymentRequest * @description Complete payment serializer with full details.

Used for detail views and updates. * @property {number} [amount_usd] - Payment amount in USD (float for performance) * @property {number} [currency] - Payment currency * @property {number} [network] - Blockchain network (for crypto payments) * @property {"nowpayments"} [provider] - Payment provider

* `nowpayments` - NowPayments * @property {"pending" | "confirming" | "confirmed" | "completed" | "failed" | "expired" | "cancelled" | "refunded"} [status] - Current payment status

* `pending` - Pending
* `confirming` - Confirming
* `confirmed` - Confirmed
* `completed` - Completed
* `failed` - Failed
* `expired` - Expired
* `cancelled` - Cancelled
* `refunded` - Refunded * @property {string} [callback_url] - Success callback URL * @property {string} [cancel_url] - Cancellation URL * @property {string} [description] - Payment description * @property {string} [expires_at] - When this payment expires */

/**
 * @typedef {Object} PatchedSubscriptionRequest * @description Complete subscription serializer with full details.

Used for subscription detail views and updates. * @property {"active" | "inactive" | "suspended" | "cancelled" | "expired"} [status] - Subscription status

* `active` - Active
* `inactive` - Inactive
* `suspended` - Suspended
* `cancelled` - Cancelled
* `expired` - Expired * @property {"free" | "basic" | "pro" | "enterprise"} [tier] - Subscription tier

* `free` - Free Tier
* `basic` - Basic Tier
* `pro` - Pro Tier
* `enterprise` - Enterprise Tier * @property {string} [expires_at] - When this subscription expires */

/**
 * @typedef {Object} PatchedTicketRequest * @property {number} [user] * @property {string} [subject] * @property {"open" | "waiting_for_user" | "waiting_for_admin" | "resolved" | "closed"} [status] - * `open` - Open
* `waiting_for_user` - Waiting for User
* `waiting_for_admin` - Waiting for Admin
* `resolved` - Resolved
* `closed` - Closed */

/**
 * @typedef {Object} PatchedUnsubscribeRequest * @description Simple serializer for unsubscribe. * @property {number} [subscription_id] */

/**
 * @typedef {Object} PatchedUserProfileUpdateRequest * @description Serializer for updating user profile. * @property {string} [first_name] * @property {string} [last_name] * @property {string} [company] * @property {string} [phone] * @property {string} [position] */

/**
 * @typedef {Object} Payment * @description Complete payment serializer with full details.

Used for detail views and updates. * @property {string} id - Unique identifier for this record * @property {string} user * @property {number} amount_usd - Payment amount in USD (float for performance) * @property {number} currency - Payment currency * @property {number} [network] - Blockchain network (for crypto payments) * @property {"nowpayments"} [provider] - Payment provider

* `nowpayments` - NowPayments * @property {"pending" | "confirming" | "confirmed" | "completed" | "failed" | "expired" | "cancelled" | "refunded"} [status] - Current payment status

* `pending` - Pending
* `confirming` - Confirming
* `confirmed` - Confirmed
* `completed` - Completed
* `failed` - Failed
* `expired` - Expired
* `cancelled` - Cancelled
* `refunded` - Refunded * @property {string} status_display * @property {string} amount_display - Get formatted amount display. * @property {string} provider_payment_id - Provider's payment ID * @property {string} payment_url - Payment page URL * @property {string} pay_address - Cryptocurrency payment address * @property {string} [callback_url] - Success callback URL * @property {string} [cancel_url] - Cancellation URL * @property {string} [description] - Payment description * @property {string} transaction_hash - Blockchain transaction hash * @property {number} confirmations_count - Number of blockchain confirmations * @property {string} created_at - When this record was created * @property {string} updated_at - When this record was last updated * @property {string} [expires_at] - When this payment expires * @property {string} completed_at - When this payment was completed * @property {boolean} is_pending - Check if payment is pending. * @property {boolean} is_completed - Check if payment is completed. * @property {boolean} is_failed - Check if payment is failed. * @property {boolean} is_expired - Check if payment is expired. */

/**
 * @typedef {Object} PaymentAnalyticsResponse * @description Payment analytics response with currency and provider breakdown * @property {CurrencyAnalyticsItem[]} currency_analytics - Analytics by currency * @property {ProviderAnalyticsItem[]} provider_analytics - Analytics by provider */

/**
 * @typedef {Object} PaymentCreate * @description Payment creation serializer with Pydantic integration.

Validates input and delegates to PaymentService. * @property {number} amount_usd - Amount in USD (1.00 - 50,000.00) * @property {"BTC" | "ETH" | "LTC" | "XMR" | "USDT" | "USDC" | "ADA" | "DOT"} currency_code - Cryptocurrency to receive

* `BTC` - Bitcoin
* `ETH` - Ethereum
* `LTC` - Litecoin
* `XMR` - Monero
* `USDT` - Tether
* `USDC` - USD Coin
* `ADA` - Cardano
* `DOT` - Polkadot * @property {"nowpayments"} [provider] - Payment provider

* `nowpayments` - NowPayments * @property {string} [callback_url] - Success callback URL * @property {string} [cancel_url] - Cancellation URL * @property {string} [description] - Payment description * @property {any} [metadata] - Additional metadata */

/**
 * @typedef {Object} PaymentCreateRequest * @description Payment creation serializer with Pydantic integration.

Validates input and delegates to PaymentService. * @property {number} amount_usd - Amount in USD (1.00 - 50,000.00) * @property {"BTC" | "ETH" | "LTC" | "XMR" | "USDT" | "USDC" | "ADA" | "DOT"} currency_code - Cryptocurrency to receive

* `BTC` - Bitcoin
* `ETH` - Ethereum
* `LTC` - Litecoin
* `XMR` - Monero
* `USDT` - Tether
* `USDC` - USD Coin
* `ADA` - Cardano
* `DOT` - Polkadot * @property {"nowpayments"} [provider] - Payment provider

* `nowpayments` - NowPayments * @property {string} [callback_url] - Success callback URL * @property {string} [cancel_url] - Cancellation URL * @property {string} [description] - Payment description * @property {any} [metadata] - Additional metadata */

/**
 * @typedef {Object} PaymentList * @description Lightweight serializer for payment lists.

Optimized for list views with minimal data. * @property {string} id - Unique identifier for this record * @property {number} amount_usd - Payment amount in USD (float for performance) * @property {number} currency - Payment currency * @property {"nowpayments"} provider - Payment provider

* `nowpayments` - NowPayments * @property {"pending" | "confirming" | "confirmed" | "completed" | "failed" | "expired" | "cancelled" | "refunded"} status - Current payment status

* `pending` - Pending
* `confirming` - Confirming
* `confirmed` - Confirmed
* `completed` - Completed
* `failed` - Failed
* `expired` - Expired
* `cancelled` - Cancelled
* `refunded` - Refunded * @property {string} status_display * @property {string} amount_display - Get formatted amount display. * @property {string} created_at - When this record was created * @property {string} expires_at - When this payment expires */

/**
 * @typedef {Object} PaymentOverview * @description Payments overview metrics * @property {number} total_payments - Total number of payments * @property {number} completed_payments - Number of completed payments * @property {number} pending_payments - Number of pending payments * @property {number} failed_payments - Number of failed payments * @property {number} total_amount_usd - Total payment amount in USD * @property {number} completed_amount_usd - Total completed amount in USD * @property {number} average_payment_usd - Average payment amount in USD * @property {number} success_rate - Payment success rate percentage * @property {string} last_payment_at - Last payment timestamp * @property {number} payments_this_month - Number of payments this month * @property {number} amount_this_month - Total amount this month * @property {string} top_currency - Most used currency * @property {number} top_currency_count - Usage count for top currency */

/**
 * @typedef {Object} PaymentRequest * @description Complete payment serializer with full details.

Used for detail views and updates. * @property {number} amount_usd - Payment amount in USD (float for performance) * @property {number} currency - Payment currency * @property {number} [network] - Blockchain network (for crypto payments) * @property {"nowpayments"} [provider] - Payment provider

* `nowpayments` - NowPayments * @property {"pending" | "confirming" | "confirmed" | "completed" | "failed" | "expired" | "cancelled" | "refunded"} [status] - Current payment status

* `pending` - Pending
* `confirming` - Confirming
* `confirmed` - Confirmed
* `completed` - Completed
* `failed` - Failed
* `expired` - Expired
* `cancelled` - Cancelled
* `refunded` - Refunded * @property {string} [callback_url] - Success callback URL * @property {string} [cancel_url] - Cancellation URL * @property {string} [description] - Payment description * @property {string} [expires_at] - When this payment expires */

/**
 * @typedef {Object} PaymentsChartResponse * @description Complete chart response for payments analytics * @property {ChartSeries[]} series - Chart series data * @property {string} period - Time period * @property {number} total_amount - Total amount for period * @property {number} total_payments - Total payments for period * @property {number} success_rate - Success rate for period */

/**
 * @typedef {Object} PaymentsDashboardOverview * @description Complete payments dashboard overview response * @property {any} metrics - Dashboard metrics * @property {RecentPayment[]} recent_payments - Recent payments * @property {RecentTransaction[]} recent_transactions - Recent transactions * @property {any} chart_data - Chart data for analytics */

/**
 * @typedef {Object} PaymentsMetrics * @description Complete payments dashboard metrics * @property {any} balance - Balance overview * @property {any} subscription - Subscription overview * @property {any} api_keys - API keys overview * @property {any} payments - Payments overview */

/**
 * @typedef {Object} ProviderAnalyticsItem * @description Analytics data for a single payment provider * @property {string} provider - Provider code * @property {string} provider_display - Provider display name * @property {number} total_payments - Total number of payments * @property {number} total_amount - Total amount in USD * @property {number} completed_payments - Number of completed payments * @property {number} success_rate - Success rate percentage */

/**
 * @typedef {Object} ProviderCurrency * @description Provider currency serializer for provider-specific currency info.

Used for provider currency management and rates. * @property {number} id * @property {any} currency * @property {any} network * @property {string} provider - Payment provider name (e.g., nowpayments) * @property {string} provider_currency_code - Currency code as used by the provider * @property {number} provider_min_amount_usd - Get minimum amount from provider configuration. * @property {number} provider_max_amount_usd - Get maximum amount from provider configuration. * @property {number} provider_fee_percentage - Get fee percentage from provider configuration. * @property {number} provider_fixed_fee_usd - Get fixed fee from provider configuration. * @property {boolean} is_enabled - Whether this currency is enabled for this provider * @property {string} created_at - When this record was created * @property {string} updated_at - When this record was last updated */

/**
 * @typedef {Object} QueueAction * @description Serializer for queue management actions. * @property {"clear" | "clear_all" | "purge" | "purge_failed" | "flush"} action - Action to perform on queues

* `clear` - clear
* `clear_all` - clear_all
* `purge` - purge
* `purge_failed` - purge_failed
* `flush` - flush * @property {string[]} [queue_names] - Specific queues to target (empty = all queues) */

/**
 * @typedef {Object} QueueActionRequest * @description Serializer for queue management actions. * @property {"clear" | "clear_all" | "purge" | "purge_failed" | "flush"} action - Action to perform on queues

* `clear` - clear
* `clear_all` - clear_all
* `purge` - purge
* `purge_failed` - purge_failed
* `flush` - flush * @property {string[]} [queue_names] - Specific queues to target (empty = all queues) */

/**
 * @typedef {Object} QueueStatus * @description Serializer for queue status data. * @property {Record<string, Record<string, number>>} queues - Queue information with pending/failed counts * @property {number} workers - Number of active workers * @property {boolean} redis_connected - Redis connection status * @property {string} timestamp - Current timestamp * @property {string} [error] - Error message if any */

/**
 * @typedef {Object} QuickHealth * @description Serializer for quick health check response. * @property {string} status - Quick health status: ok or error * @property {string} timestamp - Timestamp of the health check * @property {string} [error] - Error message if health check failed */

/**
 * @typedef {Object} RPCRequest * @description Serializer for individual RPC request. * @property {string} [id] - Stream entry ID * @property {string} [request_id] - Unique request ID * @property {string} timestamp - ISO timestamp of the request * @property {string} method - RPC method name * @property {Record<string, any>} [params] - Request parameters * @property {string} [correlation_id] - Correlation ID for tracking * @property {string} [source] - Source of the request */

/**
 * @typedef {Object} RecentPayment * @description Recent payment item * @property {string} id - Payment ID * @property {string} internal_payment_id - Internal payment ID * @property {number} amount_usd - Payment amount in USD * @property {string} amount_display - Formatted amount display * @property {string} currency_code - Currency code * @property {string} status - Payment status * @property {string} status_display - Human-readable status * @property {string} status_color - Color for status display * @property {string} provider - Payment provider * @property {string} created_at - Payment creation timestamp * @property {string} completed_at - Payment completion timestamp * @property {boolean} is_pending - Whether payment is pending * @property {boolean} is_completed - Whether payment is completed * @property {boolean} is_failed - Whether payment failed */

/**
 * @typedef {Object} RecentRequests * @description Serializer for recent requests response. * @property {RPCRequest[]} requests - List of recent RPC requests * @property {number} count - Number of requests returned * @property {number} total_available - Total number of requests available */

/**
 * @typedef {Object} RecentTransaction * @description Recent transaction item * @property {string} id - Transaction ID * @property {string} transaction_type - Transaction type * @property {number} amount_usd - Transaction amount in USD * @property {string} amount_display - Formatted amount display * @property {number} balance_after - Balance after transaction * @property {string} description - Transaction description * @property {string} created_at - Transaction timestamp * @property {string} payment_id - Related payment ID * @property {boolean} is_credit - Whether this is a credit transaction * @property {boolean} is_debit - Whether this is a debit transaction * @property {string} type_color - Color for transaction type display */

/**
 * @typedef {Object} SendCampaignRequest * @description Simple serializer for sending campaign. * @property {number} campaign_id */

/**
 * @typedef {Object} SendCampaignResponse * @description Response for sending campaign. * @property {boolean} success * @property {string} [message] * @property {number} [sent_count] * @property {string} [error] */

/**
 * @typedef {Object} Sender * @property {number} id * @property {string} display_username - Get formatted username for display. * @property {string} email * @property {string} avatar * @property {string} initials - Get user's initials for avatar fallback. * @property {boolean} is_staff - Designates whether the user can log into this admin site. * @property {boolean} is_superuser - Designates that this user has all permissions without explicitly assigning them. */

/**
 * @typedef {Object} SubscribeRequest * @description Simple serializer for newsletter subscription. * @property {number} newsletter_id * @property {string} email */

/**
 * @typedef {Object} SubscribeResponse * @description Response for subscription. * @property {boolean} success * @property {string} message * @property {number} [subscription_id] */

/**
 * @typedef {Object} Subscription * @description Complete subscription serializer with full details.

Used for subscription detail views and updates. * @property {string} id - Unique identifier for this record * @property {string} user * @property {any} tariff * @property {any} endpoint_group * @property {"active" | "inactive" | "suspended" | "cancelled" | "expired"} [status] - Subscription status

* `active` - Active
* `inactive` - Inactive
* `suspended` - Suspended
* `cancelled` - Cancelled
* `expired` - Expired * @property {string} status_display * @property {string} status_color - Get color for status display. * @property {"free" | "basic" | "pro" | "enterprise"} [tier] - Subscription tier

* `free` - Free Tier
* `basic` - Basic Tier
* `pro` - Pro Tier
* `enterprise` - Enterprise Tier * @property {number} total_requests - Total API requests made with this subscription * @property {number} usage_percentage - Get usage percentage for current period. * @property {string} last_request_at - When the last API request was made * @property {string} expires_at - When this subscription expires * @property {boolean} is_active - Check if subscription is active and not expired. * @property {boolean} is_expired - Check if subscription is expired. * @property {string} created_at - When this record was created * @property {string} updated_at - When this record was last updated */

/**
 * @typedef {Object} SubscriptionCreate * @description Subscription creation serializer with service integration.

Validates input and delegates to SubscriptionService. * @property {number} tariff_id - Tariff ID for the subscription * @property {number} [endpoint_group_id] - Endpoint group ID (optional) * @property {number} [duration_days] - Subscription duration in days */

/**
 * @typedef {Object} SubscriptionCreateRequest * @description Subscription creation serializer with service integration.

Validates input and delegates to SubscriptionService. * @property {number} tariff_id - Tariff ID for the subscription * @property {number} [endpoint_group_id] - Endpoint group ID (optional) * @property {number} [duration_days] - Subscription duration in days */

/**
 * @typedef {Object} SubscriptionList * @description Lightweight subscription serializer for lists.

Optimized for subscription lists with minimal data. * @property {string} id - Unique identifier for this record * @property {string} user * @property {string} tariff_name * @property {"active" | "inactive" | "suspended" | "cancelled" | "expired"} status - Subscription status

* `active` - Active
* `inactive` - Inactive
* `suspended` - Suspended
* `cancelled` - Cancelled
* `expired` - Expired * @property {string} status_display * @property {boolean} is_active - Check if subscription is active and not expired. * @property {boolean} is_expired - Check if subscription is expired. * @property {string} expires_at - When this subscription expires * @property {string} created_at - When this record was created */

/**
 * @typedef {Object} SubscriptionOverview * @description Current subscription overview * @property {string} tier - Subscription tier * @property {string} tier_display - Human-readable tier name * @property {string} status - Subscription status * @property {string} status_display - Human-readable status * @property {string} status_color - Color for status display * @property {boolean} is_active - Whether subscription is active * @property {boolean} is_expired - Whether subscription is expired * @property {number} days_remaining - Days until expiration * @property {number} requests_per_hour - Hourly request limit * @property {number} requests_per_day - Daily request limit * @property {number} total_requests - Total requests made * @property {number} usage_percentage - Usage percentage for current period * @property {number} monthly_cost_usd - Monthly cost in USD * @property {string} cost_display - Formatted cost display * @property {string} starts_at - Subscription start date * @property {string} expires_at - Subscription expiration date * @property {string} last_request_at - Last API request timestamp * @property {number} endpoint_groups_count - Number of accessible endpoint groups * @property {string[]} endpoint_groups - List of accessible endpoint group names */

/**
 * @typedef {Object} SubscriptionRequest * @description Complete subscription serializer with full details.

Used for subscription detail views and updates. * @property {"active" | "inactive" | "suspended" | "cancelled" | "expired"} [status] - Subscription status

* `active` - Active
* `inactive` - Inactive
* `suspended` - Suspended
* `cancelled` - Cancelled
* `expired` - Expired * @property {"free" | "basic" | "pro" | "enterprise"} [tier] - Subscription tier

* `free` - Free Tier
* `basic` - Basic Tier
* `pro` - Pro Tier
* `enterprise` - Enterprise Tier * @property {string} expires_at - When this subscription expires */

/**
 * @typedef {Object} SuccessResponse * @description Generic success response. * @property {boolean} success * @property {string} message */

/**
 * @typedef {Object} SupportedProviders * @description Serializer for supported providers response. * @property {boolean} success - Request success status * @property {any} providers - List of supported providers * @property {number} total_count - Total number of providers * @property {string} timestamp - Response timestamp */

/**
 * @typedef {Object} Tariff * @description Tariff serializer for subscription pricing.

Used for tariff information and selection. * @property {number} id * @property {string} name - Tariff name (e.g., 'Free', 'Basic', 'Pro') * @property {string} description - Detailed description of what this tariff includes * @property {number} monthly_price_usd - Monthly price in USD * @property {number} requests_per_month - API requests allowed per month * @property {number} requests_per_hour - API requests allowed per hour * @property {boolean} is_active - Whether this tariff is available for new subscriptions * @property {EndpointGroup[]} endpoint_groups * @property {number} endpoint_groups_count * @property {string} created_at - When this record was created * @property {string} updated_at - When this record was last updated */

/**
 * @typedef {Object} TaskStatistics * @description Serializer for task statistics data. * @property {Record<string, number>} statistics - Task count statistics * @property {Record<string, any>[]} recent_tasks - List of recent tasks * @property {string} timestamp - Current timestamp * @property {string} [error] - Error message if any */

/**
 * @typedef {Object} TestEmailRequest * @description Simple serializer for test email. * @property {string} email * @property {string} [subject] * @property {string} [message] */

/**
 * @typedef {Object} Ticket * @property {string} uuid * @property {number} user * @property {string} subject * @property {"open" | "waiting_for_user" | "waiting_for_admin" | "resolved" | "closed"} [status] - * `open` - Open
* `waiting_for_user` - Waiting for User
* `waiting_for_admin` - Waiting for Admin
* `resolved` - Resolved
* `closed` - Closed * @property {string} created_at * @property {number} unanswered_messages_count - Get count of unanswered messages for this specific ticket. */

/**
 * @typedef {Object} TicketRequest * @property {number} user * @property {string} subject * @property {"open" | "waiting_for_user" | "waiting_for_admin" | "resolved" | "closed"} [status] - * `open` - Open
* `waiting_for_user` - Waiting for User
* `waiting_for_admin` - Waiting for Admin
* `resolved` - Resolved
* `closed` - Closed */

/**
 * @typedef {Object} TokenRefresh * @property {string} access * @property {string} refresh */

/**
 * @typedef {Object} TokenRefreshRequest * @property {string} refresh */

/**
 * @typedef {Object} Transaction * @description Transaction serializer with full details.

Used for transaction history and details. * @property {string} id - Unique identifier for this record * @property {string} user * @property {number} amount_usd - Transaction amount in USD (positive=credit, negative=debit) * @property {string} amount_display * @property {"deposit" | "withdrawal" | "payment" | "refund" | "fee" | "bonus" | "adjustment"} transaction_type - Type of transaction

* `deposit` - Deposit
* `withdrawal` - Withdrawal
* `payment` - Payment
* `refund` - Refund
* `fee` - Fee
* `bonus` - Bonus
* `adjustment` - Adjustment * @property {string} type_color * @property {string} description - Transaction description * @property {string} payment_id - Related payment ID (if applicable) * @property {any} metadata - Additional transaction metadata * @property {boolean} is_credit * @property {boolean} is_debit * @property {string} created_at - When this record was created */

/**
 * @typedef {Object} Unsubscribe * @description Simple serializer for unsubscribe. * @property {number} subscription_id */

/**
 * @typedef {Object} UnsubscribeRequest * @description Simple serializer for unsubscribe. * @property {number} subscription_id */

/**
 * @typedef {Object} User * @description Serializer for user details. * @property {number} id * @property {string} email * @property {string} [first_name] * @property {string} [last_name] * @property {string} full_name - Get user's full name. * @property {string} initials - Get user's initials for avatar fallback. * @property {string} display_username - Get formatted username for display. * @property {string} [company] * @property {string} [phone] * @property {string} [position] * @property {string} [avatar] * @property {boolean} is_staff - Designates whether the user can log into this admin site. * @property {boolean} is_superuser - Designates that this user has all permissions without explicitly assigning them. * @property {string} date_joined * @property {string} last_login * @property {number} unanswered_messages_count - Get count of unanswered messages for the user. */

/**
 * @typedef {Object} UserBalance * @description User balance serializer with computed fields.

Provides balance information with display helpers. * @property {string} user * @property {number} balance_usd - Current balance in USD (float for performance) * @property {string} balance_display - Formatted balance display. * @property {boolean} is_empty - Check if balance is zero. * @property {boolean} has_transactions - Check if user has any transactions. * @property {string} created_at * @property {string} updated_at */

/**
 * @typedef {Object} UserProfileUpdateRequest * @description Serializer for updating user profile. * @property {string} [first_name] * @property {string} [last_name] * @property {string} [company] * @property {string} [phone] * @property {string} [position] */

/**
 * @typedef {Object} WebhookEvent * @description Serializer for individual webhook event. * @property {number} id * @property {string} provider * @property {string} event_type * @property {"success" | "failed" | "pending" | "retry"} status - * `success` - Success
* `failed` - Failed
* `pending` - Pending
* `retry` - Retry * @property {string} timestamp * @property {number} payload_size - Size in bytes * @property {number} response_time - Response time in ms * @property {number} [retry_count] * @property {string} [error_message] * @property {string} [payload_preview] * @property {number} [response_status_code] * @property {string} [webhook_url] */

/**
 * @typedef {Object} WebhookEventList * @description Serializer for paginated webhook events list. * @property {WebhookEvent[]} events * @property {number} total * @property {number} page * @property {number} per_page * @property {boolean} has_next * @property {boolean} has_previous */

/**
 * @typedef {Object} WebhookEventListRequest * @description Serializer for paginated webhook events list. * @property {WebhookEventRequest[]} events * @property {number} total * @property {number} page * @property {number} per_page * @property {boolean} has_next * @property {boolean} has_previous */

/**
 * @typedef {Object} WebhookEventRequest * @description Serializer for individual webhook event. * @property {string} provider * @property {string} event_type * @property {"success" | "failed" | "pending" | "retry"} status - * `success` - Success
* `failed` - Failed
* `pending` - Pending
* `retry` - Retry * @property {string} timestamp * @property {number} payload_size - Size in bytes * @property {number} response_time - Response time in ms * @property {number} [retry_count] * @property {string} [error_message] * @property {string} [payload_preview] * @property {number} [response_status_code] * @property {string} [webhook_url] */

/**
 * @typedef {Object} WebhookHealth * @description Serializer for webhook health check response. * @property {string} status - Health status * @property {string} timestamp - Check timestamp * @property {any} providers - Provider health status */

/**
 * @typedef {Object} WebhookProviderStats * @description Serializer for provider-specific webhook statistics. * @property {number} total * @property {number} successful * @property {number} failed * @property {number} [pending] * @property {number} success_rate */

/**
 * @typedef {Object} WebhookProviderStatsRequest * @description Serializer for provider-specific webhook statistics. * @property {number} total * @property {number} successful * @property {number} failed * @property {number} [pending] * @property {number} success_rate */

/**
 * @typedef {Object} WebhookResponse * @description Serializer for webhook processing response.

Standard response format for all webhook endpoints. * @property {boolean} success - Whether webhook was processed successfully * @property {string} message - Processing result message * @property {string} [payment_id] - Internal payment ID * @property {string} [provider_payment_id] - Provider payment ID * @property {string} [processed_at] - Processing timestamp */

/**
 * @typedef {Object} WebhookResponseRequest * @description Serializer for webhook processing response.

Standard response format for all webhook endpoints. * @property {boolean} success - Whether webhook was processed successfully * @property {string} message - Processing result message * @property {string} [payment_id] - Internal payment ID * @property {string} [provider_payment_id] - Provider payment ID * @property {string} [processed_at] - Processing timestamp */

/**
 * @typedef {Object} WebhookStats * @description Serializer for comprehensive webhook statistics. * @property {number} total * @property {number} successful * @property {number} failed * @property {number} pending * @property {number} success_rate * @property {Record<string, WebhookProviderStats>} providers - Statistics by provider * @property {Record<string, number>} last_24h - Events in last 24 hours * @property {number} avg_response_time * @property {number} max_response_time */

/**
 * @typedef {Object} WebhookStatsRequest * @description Serializer for comprehensive webhook statistics. * @property {number} total * @property {number} successful * @property {number} failed * @property {number} pending * @property {number} success_rate * @property {Record<string, WebhookProviderStatsRequest>} providers - Statistics by provider * @property {Record<string, number>} last_24h - Events in last 24 hours * @property {number} avg_response_time * @property {number} max_response_time */

/**
 * @typedef {Object} WorkerAction * @description Serializer for worker management actions. * @property {"start" | "stop" | "restart"} action - Action to perform on workers

* `start` - start
* `stop` - stop
* `restart` - restart * @property {number} [processes] - Number of worker processes * @property {number} [threads] - Number of threads per process */

/**
 * @typedef {Object} WorkerActionRequest * @description Serializer for worker management actions. * @property {"start" | "stop" | "restart"} action - Action to perform on workers

* `start` - start
* `stop` - stop
* `restart` - restart * @property {number} [processes] - Number of worker processes * @property {number} [threads] - Number of threads per process */


// Export empty object to make this a module
export {};