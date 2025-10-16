export type RuntimeType = import("../types.d.ts").RuntimeType;
/**
 * @typedef {import('../types.d.ts').RuntimeType} RuntimeType
 */
export class RuntimeNameHandler {
    /**
     * @param {number} runtimeName
     * @returns {RuntimeType}
     */
    static getName(runtimeName: number): RuntimeType;
    /**
     * @param {string} name
     * @returns {number}
     */
    static getRuntime: (name: string) => number;
}
