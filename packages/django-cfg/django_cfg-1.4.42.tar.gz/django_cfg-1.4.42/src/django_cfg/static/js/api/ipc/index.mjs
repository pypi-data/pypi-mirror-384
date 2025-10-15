/**
 * Ipc API Module
 * Re-exports the API client for convenient importing
 * @module ipc
 */

import { IpcAPI, ipcAPI } from './client.mjs';

// Re-export the class and instance
export { IpcAPI, ipcAPI };

// Default export is the instance for convenience
export default ipcAPI;