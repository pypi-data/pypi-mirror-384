export class Config {
    /**
     * @param {*} runtime
     * @param {*} connectionData
     * @param {string} [plugins=""]
     * @param {string} [modules=""]
     */
    constructor(runtime: any, connectionData: any, plugins?: string, modules?: string);
    runtime: any;
    connectionData: any;
    plugins: string;
    modules: string;
    toString(): string;
}
