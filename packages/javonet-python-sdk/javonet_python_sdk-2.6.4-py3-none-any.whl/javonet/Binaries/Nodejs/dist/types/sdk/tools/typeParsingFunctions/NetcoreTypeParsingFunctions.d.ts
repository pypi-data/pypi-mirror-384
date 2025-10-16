/**
 * @param {InvocationContext} invocationContext - InvocationContext pointing to the target object
 * @returns {Date} A JavaScript Date parsed from the Java timestamp
 */
export function parseDate(invocationContext: InvocationContext): Date;
/**
 * Mapping of parsing functions for different type signatures.
 * @type {Map<string, (invocationContext: InvocationContext) => unknown>}
 */
export const NetcoreTypeParsingFunctions: Map<string, (invocationContext: InvocationContext) => unknown>;
export type InvocationContext = import("../../InvocationContext.js").InvocationContext;
