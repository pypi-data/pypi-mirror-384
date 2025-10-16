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
var GetResultTypeHandler_exports = {};
__export(GetResultTypeHandler_exports, {
  GetResultTypeHandler: () => GetResultTypeHandler
});
module.exports = __toCommonJS(GetResultTypeHandler_exports);
var import_TypesHandler = require("../../utils/TypesHandler.cjs");
var import_AbstractHandler = require("./AbstractHandler.cjs");
class GetResultTypeHandler extends import_AbstractHandler.AbstractHandler {
  constructor() {
    super();
    this.requiredParametersCount = 1;
  }
  /**
   * Processes the given command to convert JType to Type.
   * @param {Command} command - The command to process.
   * @returns {any} The converted type.
   */
  process(command) {
    return command.payload[0].constructor.name;
  }
}
// Annotate the CommonJS export names for ESM import in node:
0 && (module.exports = {
  GetResultTypeHandler
});
