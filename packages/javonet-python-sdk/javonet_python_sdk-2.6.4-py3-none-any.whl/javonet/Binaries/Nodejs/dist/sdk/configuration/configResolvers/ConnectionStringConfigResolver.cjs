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
var ConnectionStringConfigResolver_exports = {};
__export(ConnectionStringConfigResolver_exports, {
  ConnectionStringConfigResolver: () => ConnectionStringConfigResolver
});
module.exports = __toCommonJS(ConnectionStringConfigResolver_exports);
var import_Config = require("../Config.cjs");
var import_ConfigsDictionary = require("../ConfigsDictionary.cjs");
var import_ActivationHelper = require("../../tools/ActivationHelper.cjs");
var import_ConfigResolver = require("./ConfigResolver.cjs");
class ConnectionStringConfigResolver extends import_ConfigResolver.ConfigResolver {
  /**
   * Parse and add multiple configuration lines from a connection string source.
   * @param {any} priority
   * @param {string} connectionStringSource
   */
  static addConfigs(priority, connectionStringSource) {
    if (!connectionStringSource || String(connectionStringSource).trim() === "") {
      throw new Error("Connection string source cannot be null or empty.");
    }
    const normalized = String(connectionStringSource).replace(/\r\n/g, "\n").replace(/\r/g, "\n");
    const lines = normalized.split("\n").map((l) => l.trim()).filter((l) => l.length > 0);
    for (const line of lines) {
      if (line.startsWith("#") || line.startsWith("//")) {
        continue;
      }
      if (line.toLowerCase().startsWith("licensekey")) {
        ConnectionStringConfigResolver._setLicenseKey(line);
        continue;
      }
      try {
        const keyValues = ConnectionStringConfigResolver._parseKeyValues(line);
        const configName = keyValues.name;
        const runtimeValue = keyValues.runtime;
        if (!configName || String(configName).trim() === "") {
          throw new Error("Missing or empty config name.");
        }
        if (!runtimeValue || String(runtimeValue).trim() === "") {
          throw new Error("Missing or empty runtime.");
        }
        const runtimeName = import_ConfigResolver.ConfigResolver.tryParseRuntime(runtimeValue);
        const hostValue = keyValues.host;
        const connectionData = import_ConfigResolver.ConfigResolver.buildConnectionData(hostValue);
        const plugins = keyValues.plugins || "";
        const modules = keyValues.modules || "";
        const config = new import_Config.Config(runtimeName, connectionData, plugins, modules);
        import_ConfigsDictionary.ConfigsDictionary.addConfig(configName, priority, config);
      } catch (ex) {
        console.log(`Failed to parse config line: '${line}'. Reason: ${ex}`);
        throw ex;
      }
    }
  }
  /**
   * Extract and set temporary license key from a line like "licensekey=VALUE;..."
   * @param {string} line
   * @private
   */
  static _setLicenseKey(line) {
    const eq = line.indexOf("=");
    if (eq > 0 && eq < line.length - 1) {
      let valuePortion = line.substring(eq + 1).trim();
      const semicolon = valuePortion.indexOf(";");
      if (semicolon >= 0) {
        valuePortion = valuePortion.substring(0, semicolon).trim();
      }
      const hashIdx = valuePortion.indexOf("#");
      if (hashIdx >= 0) {
        valuePortion = valuePortion.substring(0, hashIdx).trim();
      }
      const slashes = valuePortion.indexOf("//");
      if (slashes >= 0) {
        valuePortion = valuePortion.substring(0, slashes).trim();
      }
      import_ActivationHelper.ActivationHelper.setTemporaryLicenseKey(valuePortion);
    }
  }
  /**
   * Parse semicolon-separated key=value tokens into an object.
   * Ignores malformed tokens and logs them.
   * @param {string} line
   * @returns {Record<string, string>}
   * @private
   */
  static _parseKeyValues(line) {
    const result = {};
    const segments = line.split(";").map((s) => s.trim()).filter((s) => s.length > 0);
    for (const segment of segments) {
      const eq = segment.indexOf("=");
      if (eq <= 0 || eq === segment.length - 1) {
        console.log(`Ignoring malformed token '${segment}' in line: ${line}`);
        continue;
      }
      const key = segment.substring(0, eq).trim().toLowerCase();
      const value = segment.substring(eq + 1).trim();
      if (key) {
        result[key] = value;
      }
    }
    return result;
  }
}
// Annotate the CommonJS export names for ESM import in node:
0 && (module.exports = {
  ConnectionStringConfigResolver
});
