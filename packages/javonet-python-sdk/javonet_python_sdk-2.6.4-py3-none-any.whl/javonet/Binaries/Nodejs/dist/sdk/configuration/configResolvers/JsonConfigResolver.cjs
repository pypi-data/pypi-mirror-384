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
var JsonConfigResolver_exports = {};
__export(JsonConfigResolver_exports, {
  JsonConfigResolver: () => JsonConfigResolver
});
module.exports = __toCommonJS(JsonConfigResolver_exports);
var import_Config = require("../Config.cjs");
var import_ConfigsDictionary = require("../ConfigsDictionary.cjs");
var import_ConfigResolver = require("./ConfigResolver.cjs");
var import_ActivationHelper = require("../../tools/ActivationHelper.cjs");
class JsonConfigResolver extends import_ConfigResolver.ConfigResolver {
  /**
   * Parse and add configurations from a JSON object.
   * @param {any} priority
   * @param {Record<string, unknown>} jsonObject
   */
  static addConfigs(priority, jsonObject) {
    if (jsonObject == null) {
      throw new Error("json_object cannot be None");
    }
    if (typeof jsonObject !== "object" || Array.isArray(jsonObject)) {
      throw new Error("Root JSON element must be a dict/object.");
    }
    const licenseKey = (
      /** @type {Record<string, unknown>} */
      jsonObject.licenseKey
    );
    if (typeof licenseKey === "string") {
      import_ActivationHelper.ActivationHelper.setTemporaryLicenseKey(licenseKey.trim());
    }
    const configs = (
      /** @type {Record<string, unknown>} */
      jsonObject.configurations
    );
    if (typeof configs !== "object" || configs == null || Array.isArray(configs)) {
      throw new Error("JSON must contain 'configurations' object.");
    }
    for (const [configName, cfg] of Object.entries(
      /** @type {Record<string, unknown>} */
      configs
    )) {
      try {
        if (typeof cfg !== "object" || cfg == null || Array.isArray(cfg)) {
          throw new Error("Configuration value must be an object/dict.");
        }
        const runtimeValue = JsonConfigResolver._getRequiredString(
          /** @type {Record<string, unknown>} */
          cfg,
          "runtime"
        );
        const runtimeName = import_ConfigResolver.ConfigResolver.tryParseRuntime(runtimeValue);
        const host = JsonConfigResolver._getOptionalString(
          /** @type {Record<string, unknown>} */
          cfg,
          "host"
        );
        const connectionData = import_ConfigResolver.ConfigResolver.buildConnectionData(host);
        const plugins = JsonConfigResolver._getOptionalString(
          /** @type {Record<string, unknown>} */
          cfg,
          "plugins"
        );
        const modules = JsonConfigResolver._getOptionalString(
          /** @type {Record<string, unknown>} */
          cfg,
          "modules"
        );
        const config = new import_Config.Config(runtimeName, connectionData, plugins, modules);
        import_ConfigsDictionary.ConfigsDictionary.addConfig(configName, priority, config);
      } catch (ex) {
        console.log(`Failed to add config '${configName}': ${ex}`);
      }
    }
  }
  /**
   * Get a required string property from an object, trimmed.
   * Throws if missing or empty.
   * @param {Record<string, unknown>} obj
   * @param {string} property
   * @returns {string}
   * @private
   */
  static _getRequiredString(obj, property) {
    const value = obj[property];
    if (typeof value !== "string" || value.trim() === "") {
      throw new Error(`Missing or invalid '${property}' property.`);
    }
    return value.trim();
  }
  /**
   * Get an optional string property; return empty string when missing or not a string.
   * @param {Record<string, unknown>} obj
   * @param {string} property
   * @returns {string}
   * @private
   */
  static _getOptionalString(obj, property) {
    const value = obj[property];
    if (typeof value === "string") {
      return value;
    }
    return "";
  }
}
// Annotate the CommonJS export names for ESM import in node:
0 && (module.exports = {
  JsonConfigResolver
});
