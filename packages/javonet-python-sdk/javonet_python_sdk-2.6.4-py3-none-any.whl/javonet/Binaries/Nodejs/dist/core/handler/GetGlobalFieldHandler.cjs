"use strict";
var __defProp = Object.defineProperty;
var __getOwnPropDesc = Object.getOwnPropertyDescriptor;
var __getOwnPropNames = Object.getOwnPropertyNames;
var __hasOwnProp = Object.prototype.hasOwnProperty;
var __export = (target, all) => {
  for (var name in all)
    __defProp(target, name, { get: all[name], enumerable: true });
};
var __copyProps = (to, from, except, desc) => {
  if (from && typeof from === "object" || typeof from === "function") {
    for (let key of __getOwnPropNames(from))
      if (!__hasOwnProp.call(to, key) && key !== except)
        __defProp(to, key, { get: () => from[key], enumerable: !(desc = __getOwnPropDesc(from, key)) || desc.enumerable });
  }
  return to;
};
var __toCommonJS = (mod) => __copyProps(__defProp({}, "__esModule", { value: true }), mod);
var GetGlobalFieldHandler_exports = {};
__export(GetGlobalFieldHandler_exports, {
  GetGlobalFieldHandler: () => GetGlobalFieldHandler
});
module.exports = __toCommonJS(GetGlobalFieldHandler_exports);
var import_AbstractHandler = require("./AbstractHandler.cjs");
class GetGlobalFieldHandler extends import_AbstractHandler.AbstractHandler {
  requiredParametersCount = 1;
  constructor() {
    super();
  }
  /**
   * @param {Command} command
   * @returns {any}
   */
  process(command) {
    try {
      if (command.payload.length < this.requiredParametersCount) {
        throw new Error("Invoke Global Field parameters mismatch");
      }
      const { payload } = command;
      const fieldName = payload[0];
      if (fieldName in global && typeof global[fieldName] !== "function") {
        return global[fieldName];
      } else {
        const fields = Object.getOwnPropertyNames(global).filter(
          (property) => typeof global[property] !== "function"
        );
        let message = `Field ${fieldName} not found in global. Available fields:
`;
        fields.forEach((field) => {
          message += `${field}
`;
        });
        throw new Error(message);
      }
    } catch (error) {
      throw this.process_stack_trace(error, this.constructor.name);
    }
  }
}
// Annotate the CommonJS export names for ESM import in node:
0 && (module.exports = {
  GetGlobalFieldHandler
});
