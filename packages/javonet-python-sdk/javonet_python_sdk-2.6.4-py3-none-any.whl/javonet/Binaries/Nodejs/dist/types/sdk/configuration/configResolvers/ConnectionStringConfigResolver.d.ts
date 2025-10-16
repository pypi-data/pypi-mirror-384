export class ConnectionStringConfigResolver extends ConfigResolver {
    /**
     * Parse and add multiple configuration lines from a connection string source.
     * @param {any} priority
     * @param {string} connectionStringSource
     */
    static addConfigs(priority: any, connectionStringSource: string): void;
    /**
     * Extract and set temporary license key from a line like "licensekey=VALUE;..."
     * @param {string} line
     * @private
     */
    private static _setLicenseKey;
    /**
     * Parse semicolon-separated key=value tokens into an object.
     * Ignores malformed tokens and logs them.
     * @param {string} line
     * @returns {Record<string, string>}
     * @private
     */
    private static _parseKeyValues;
}
import { ConfigResolver } from './ConfigResolver.js';
