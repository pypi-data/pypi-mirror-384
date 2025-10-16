export class ConfigSourceResolver {
    static addConfigs(priority: any, configSource: any): void;
    static getConfig(configName: any): any;
    static clearConfigs(): void;
    static _getConfigSourceAsString(configSource: any): any;
    static _parseConfigsAndAddToCollection(priority: any, configString: any): void;
}
