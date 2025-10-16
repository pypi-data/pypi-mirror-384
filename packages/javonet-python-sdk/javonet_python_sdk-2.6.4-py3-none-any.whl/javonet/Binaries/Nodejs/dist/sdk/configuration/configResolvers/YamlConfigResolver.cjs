"use strict";
var __create = Object.create;
var __defProp = Object.defineProperty;
var __getOwnPropDesc = Object.getOwnPropertyDescriptor;
var __getOwnPropNames = Object.getOwnPropertyNames;
var __getProtoOf = Object.getPrototypeOf;
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
var __toESM = (mod, isNodeMode, target) => (target = mod != null ? __create(__getProtoOf(mod)) : {}, __copyProps(
  // If the importer is in node compatibility mode or this is not an ESM
  // file that has been converted to a CommonJS file using a Babel-
  // compatible transform (i.e. "__esModule" has not been set), then set
  // "default" to the CommonJS "module.exports" for node compatibility.
  isNodeMode || !mod || !mod.__esModule ? __defProp(target, "default", { value: mod, enumerable: true }) : target,
  mod
));
var __toCommonJS = (mod) => __copyProps(__defProp({}, "__esModule", { value: true }), mod);
var YamlConfigResolver_exports = {};
__export(YamlConfigResolver_exports, {
  YamlConfigResolver: () => YamlConfigResolver
});
module.exports = __toCommonJS(YamlConfigResolver_exports);
var import_js_yaml = __toESM(require("js-yaml"), 1);
var import_Config = require("../Config.cjs");
var import_ConfigsDictionary = require("../ConfigsDictionary.cjs");
var import_ConfigResolver = require("./ConfigResolver.cjs");
var import_ActivationHelper = require("../../tools/ActivationHelper.cjs");
class YamlConfigResolver extends import_ConfigResolver.ConfigResolver {
  /**
   * Parse YAML string and add configurations.
   * @param {any} priority
   * @param {string} yamlString
   */
  static addConfigs(priority, yamlString) {
    if (!yamlString || String(yamlString).trim() === "") {
      throw new Error("YAML string cannot be null or empty.");
    }
    let data;
    try {
      data = import_js_yaml.default.load(String(yamlString));
    } catch (ex) {
      throw new SyntaxError(`Failed to parse YAML: ${ex}`);
    }
    if (typeof data !== "object" || data == null || Array.isArray(data)) {
      throw new SyntaxError("Root YAML node must be a mapping.");
    }
    const root = (
      /** @type {RootYaml} */
      data
    );
    const licenseKey = root.licenseKey;
    if (typeof licenseKey === "string") {
      import_ActivationHelper.ActivationHelper.temporaryLicenseKey = licenseKey.trim();
    }
    const configs = root.configurations;
    if (typeof configs !== "object" || configs == null || Array.isArray(configs)) {
      throw new Error("YAML must contain 'configurations' mapping.");
    }
    for (const [configName, cfg] of Object.entries(configs)) {
      if (typeof configName !== "string" || configName.trim() === "") {
        console.log("Skipping entry with empty config name.");
        continue;
      }
      if (typeof cfg !== "object" || cfg == null || Array.isArray(cfg)) {
        console.log(`Skipping '${configName}': value is not a mapping.`);
        continue;
      }
      try {
        const runtimeValue = YamlConfigResolver._getRequiredString(cfg, "runtime");
        const runtimeName = import_ConfigResolver.ConfigResolver.tryParseRuntime(runtimeValue);
        const host = YamlConfigResolver._getOptionalString(cfg, "host");
        const connectionData = import_ConfigResolver.ConfigResolver.buildConnectionData(host);
        const plugins = YamlConfigResolver._getOptionalString(cfg, "plugins");
        const modules = YamlConfigResolver._getOptionalString(cfg, "modules");
        const config = new import_Config.Config(runtimeName, connectionData, plugins, modules);
        import_ConfigsDictionary.ConfigsDictionary.addConfig(configName, priority, config);
      } catch (ex) {
        console.log(`Failed to add config '${configName}': ${ex}`);
      }
    }
  }
  /**
   * Get required string from mapping, trimmed. Throws if missing/invalid.
   * @param {Record<string, unknown>} mapping
   * @param {string} key
   * @returns {string}
   * @private
   */
  static _getRequiredString(mapping, key) {
    const value = mapping[key];
    if (typeof value !== "string" || value.trim() === "") {
      throw new Error(`Missing or invalid '${key}' property.`);
    }
    return value.trim();
  }
  /**
   * Get optional string from mapping, or empty string if missing/not a string.
   * @param {Record<string, unknown>} mapping
   * @param {string} key
   * @returns {string}
   * @private
   */
  static _getOptionalString(mapping, key) {
    const value = mapping[key];
    if (typeof value === "string") {
      return value;
    }
    return "";
  }
}
// Annotate the CommonJS export names for ESM import in node:
0 && (module.exports = {
  YamlConfigResolver
});
