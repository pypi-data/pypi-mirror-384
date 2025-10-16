export type Command = import("../../utils/Command.js").Command;
/**
 * @typedef {import('../../utils/Command.js').Command} Command
 */
/**
 * GetResultTypeHandler class handles the conversion of JType to Type.
 */
export class GetResultTypeHandler extends AbstractHandler {
    /** @type {number} */
    requiredParametersCount: number;
    /**
     * Processes the given command to convert JType to Type.
     * @param {Command} command - The command to process.
     * @returns {any} The converted type.
     */
    process(command: Command): any;
}
import { AbstractHandler } from './AbstractHandler.js';
