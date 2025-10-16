/**
 * Details for activating a type with constructor arguments
 */
export class ActivatorDetails {
    /**
     * @param {Function} type - The constructor function/class
     * @param {any[]} [args] - Arguments to pass to constructor
     */
    constructor(type: Function, args?: any[]);
    type: Function;
    arguments: any[];
}
