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
var NodejsTypeParsingFunctions_exports = {};
__export(NodejsTypeParsingFunctions_exports, {
  NodejsTypeParsingFunctions: () => NodejsTypeParsingFunctions,
  parseDate: () => parseDate
});
module.exports = __toCommonJS(NodejsTypeParsingFunctions_exports);
var import_TypeParsingUtils = require("./TypeParsingUtils.cjs");
function parseDate(invocationContext) {
  const result = invocationContext.invokeInstanceMethod("getTime").execute();
  const action = (timestamp) => {
    if (!timestamp) {
      throw new Error("getTime.getValue() returned null");
    }
    return new Date(
      /** @type {number} */
      timestamp
    );
  };
  return (0, import_TypeParsingUtils.handleResultWithAction)(result, action);
}
const NodejsTypeParsingFunctions = /* @__PURE__ */ new Map([["Date", parseDate]]);
// Annotate the CommonJS export names for ESM import in node:
0 && (module.exports = {
  NodejsTypeParsingFunctions,
  parseDate
});
