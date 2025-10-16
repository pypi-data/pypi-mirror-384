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
var Config_exports = {};
__export(Config_exports, {
  Config: () => Config
});
module.exports = __toCommonJS(Config_exports);
class Config {
  /**
   * @param {*} runtime
   * @param {*} connectionData
   * @param {string} [plugins=""]
   * @param {string} [modules=""]
   */
  constructor(runtime, connectionData, plugins = "", modules = "") {
    this.runtime = runtime;
    this.connectionData = connectionData;
    this.plugins = plugins ?? "";
    this.modules = modules ?? "";
  }
  toString() {
    const parts = [];
    parts.push(`Runtime: ${this.runtime}`);
    if (this.connectionData != null) {
      parts.push(`Host: ${this.connectionData}`);
    }
    if (String(this.plugins).trim()) {
      parts.push(`Plugins: ${this.plugins}`);
    }
    if (String(this.modules).trim()) {
      parts.push(`Modules: ${this.modules}`);
    }
    return parts.join(", ");
  }
}
// Annotate the CommonJS export names for ESM import in node:
0 && (module.exports = {
  Config
});
