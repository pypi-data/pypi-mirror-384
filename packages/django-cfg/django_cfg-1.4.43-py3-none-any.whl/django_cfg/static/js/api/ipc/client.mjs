import { BaseAPIClient } from '../base.mjs';

/**
 * Ipc API Client
 * Auto-generated from OpenAPI schema
 * @module ipc
 * @extends BaseAPIClient
 */
export class IpcAPI extends BaseAPIClient {
    /**
     * Initialize ipc API client
     * @param {string} [baseURL] - Optional base URL
     */
    constructor(baseURL) {
        super(baseURL);
    }

    /**
     * Get RPC health status     * Returns the current health status of the RPC monitoring system.     * @returns {Promise<HealthCheck>} Response data
     */
    async ipcAdminApiMonitorHealthRetrieve() {
        const path = `/cfg/ipc/admin/api/monitor/health/`;        return this.get(path);    }
    /**
     * Get method statistics     * Returns statistics grouped by RPC method.     * @returns {Promise<MethodStats>} Response data
     */
    async ipcAdminApiMonitorMethodsRetrieve() {
        const path = `/cfg/ipc/admin/api/monitor/methods/`;        return this.get(path);    }
    /**
     * Get notification statistics     * Returns statistics about RPC notifications.     * @returns {Promise<NotificationStats>} Response data
     */
    async ipcAdminApiMonitorNotificationsRetrieve() {
        const path = `/cfg/ipc/admin/api/monitor/notifications/`;        return this.get(path);    }
    /**
     * Get overview statistics     * Returns overview statistics for RPC monitoring.     * @returns {Promise<OverviewStats>} Response data
     */
    async ipcAdminApiMonitorOverviewRetrieve() {
        const path = `/cfg/ipc/admin/api/monitor/overview/`;        return this.get(path);    }
    /**
     * Get recent RPC requests     * Returns a list of recent RPC requests with their details.     * @param {Object} [params={}] - Query parameters     * @param {number} [params.count] - Number of requests to return (default: 50, max: 200)     * @returns {Promise<RecentRequests>} Response data
     */
    async ipcAdminApiMonitorRequestsRetrieve(params = {}) {
        const path = `/cfg/ipc/admin/api/monitor/requests/`;        return this.get(path, params);    }
    /**
     * Get RPC health status     * Returns the current health status of the RPC monitoring system.     * @returns {Promise<HealthCheck>} Response data
     */
    async ipcMonitorHealthRetrieve() {
        const path = `/cfg/ipc/monitor/health/`;        return this.get(path);    }
    /**
     * Get method statistics     * Returns statistics grouped by RPC method.     * @returns {Promise<MethodStats>} Response data
     */
    async ipcMonitorMethodsRetrieve() {
        const path = `/cfg/ipc/monitor/methods/`;        return this.get(path);    }
    /**
     * Get notification statistics     * Returns statistics about RPC notifications.     * @returns {Promise<NotificationStats>} Response data
     */
    async ipcMonitorNotificationsRetrieve() {
        const path = `/cfg/ipc/monitor/notifications/`;        return this.get(path);    }
    /**
     * Get overview statistics     * Returns overview statistics for RPC monitoring.     * @returns {Promise<OverviewStats>} Response data
     */
    async ipcMonitorOverviewRetrieve() {
        const path = `/cfg/ipc/monitor/overview/`;        return this.get(path);    }
    /**
     * Get recent RPC requests     * Returns a list of recent RPC requests with their details.     * @param {Object} [params={}] - Query parameters     * @param {number} [params.count] - Number of requests to return (default: 50, max: 200)     * @returns {Promise<RecentRequests>} Response data
     */
    async ipcMonitorRequestsRetrieve(params = {}) {
        const path = `/cfg/ipc/monitor/requests/`;        return this.get(path, params);    }
}

// Default instance for convenience
export const ipcAPI = new IpcAPI();

// Default export
export default IpcAPI;