export class JsonConfigResolver extends ConfigResolver {
    /**
     * Parse and add configurations from a JSON object.
     * @param {any} priority
     * @param {Record<string, unknown>} jsonObject
     */
    static addConfigs(priority: any, jsonObject: Record<string, unknown>): void;
    /**
     * Get a required string property from an object, trimmed.
     * Throws if missing or empty.
     * @param {Record<string, unknown>} obj
     * @param {string} property
     * @returns {string}
     * @private
     */
    private static _getRequiredString;
    /**
     * Get an optional string property; return empty string when missing or not a string.
     * @param {Record<string, unknown>} obj
     * @param {string} property
     * @returns {string}
     * @private
     */
    private static _getOptionalString;
}
import { ConfigResolver } from './ConfigResolver.js';
