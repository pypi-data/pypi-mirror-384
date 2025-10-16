export class ConfigsDictionary {
    /** @type {Map<string, Map<number, any>>} */
    static _configurations_collection: Map<string, Map<number, any>>;
    /**
     * Normalize priority to a numeric value.
     * Accepts either a number or an object with a numeric `value` property.
     * @param {any} priority
     * @returns {number|undefined}
     */
    static _normalizePriority(priority: any): number | undefined;
    /**
     * Add a configuration for a given name and priority.
     * If the same name+priority already exists, it will not be overwritten.
     * @param {string} name
     * @param {number|{value:number}} priority
     * @param {*} config
     */
    static addConfig(name: string, priority: number | {
        value: number;
    }, config: any): void;
    /**
     * Retrieve the configuration with the numerically smallest priority for the given name.
     * Throws if name is invalid or no configuration is found.
     * @param {string} name
     * @returns {*}
     */
    static getConfig(name: string): any;
    /** Clear all stored configurations. */
    static clearConfigs(): void;
}
