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
var TypeParsingUtils_exports = {};
__export(TypeParsingUtils_exports, {
  handleResultWithAction: () => handleResultWithAction
});
module.exports = __toCommonJS(TypeParsingUtils_exports);
var import_IsThenable = require("../../../utils/IsThenable.cjs");
const handleResultWithAction = (result, action) => {
  if ((0, import_IsThenable.isThenable)(result)) {
    return result.then((result2) => action(result2.getValue()));
  }
  return action(result.getValue());
};
// Annotate the CommonJS export names for ESM import in node:
0 && (module.exports = {
  handleResultWithAction
});
