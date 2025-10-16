export type RuntimeName = import("../../types.d.ts").RuntimeName;
/**
 * @typedef {import('../../types.d.ts').RuntimeName} RuntimeName
 */
export class ComplexTypeResolver {
    /**
     * Resolve type from string name and optional module
     * @param {string} typeName - Name of the type to resolve
     * @param {string} [moduleName] - Optional module name to import from
     * @returns {Function} The resolved type/constructor function
     */
    static resolveType(typeName: string, moduleName?: string): Function;
    /**
     * Register a custom type mapping
     * @param {string} resultType - The type name from the target runtime
     * @param {Function} type - The JavaScript constructor function
     * @param {any[]} [args] - Default arguments for the constructor
     */
    register(resultType: string, type: Function, args?: any[]): void;
    /**
     * Convert InvocationContext result to appropriate JavaScript type
     * @param {InvocationContext} ic - The invocation context
     * @returns {any} The converted result
     */
    convertResult(ic: InvocationContext): any;
    #private;
}
import { InvocationContext } from '../InvocationContext.js';
