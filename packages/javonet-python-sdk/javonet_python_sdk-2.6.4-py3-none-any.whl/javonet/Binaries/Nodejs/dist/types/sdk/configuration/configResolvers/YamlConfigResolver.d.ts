export type RootYaml = {
    licenseKey?: string;
    configurations?: Record<string, Record<string, unknown>>;
};
/**
 * @typedef {{ licenseKey?: string, configurations?: Record<string, Record<string, unknown>> }} RootYaml
 */
export class YamlConfigResolver extends ConfigResolver {
    /**
     * Parse YAML string and add configurations.
     * @param {any} priority
     * @param {string} yamlString
     */
    static addConfigs(priority: any, yamlString: string): void;
    /**
     * Get required string from mapping, trimmed. Throws if missing/invalid.
     * @param {Record<string, unknown>} mapping
     * @param {string} key
     * @returns {string}
     * @private
     */
    private static _getRequiredString;
    /**
     * Get optional string from mapping, or empty string if missing/not a string.
     * @param {Record<string, unknown>} mapping
     * @param {string} key
     * @returns {string}
     * @private
     */
    private static _getOptionalString;
}
import { ConfigResolver } from './ConfigResolver.js';
