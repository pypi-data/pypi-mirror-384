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
var ConfigSourceResolver_exports = {};
__export(ConfigSourceResolver_exports, {
  ConfigSourceResolver: () => ConfigSourceResolver
});
module.exports = __toCommonJS(ConfigSourceResolver_exports);
var import_fs = __toESM(require("fs"), 1);
var import_process = __toESM(require("process"), 1);
var import_ConfigsDictionary = require("./ConfigsDictionary.cjs");
var import_JsonConfigResolver = require("./configResolvers/JsonConfigResolver.cjs");
var import_YamlConfigResolver = require("./configResolvers/YamlConfigResolver.cjs");
var import_ConnectionStringConfigResolver = require("./configResolvers/ConnectionStringConfigResolver.cjs");
class ConfigSourceResolver {
  static addConfigs(priority, configSource) {
    console.log(`Adding config from source: ${configSource} with priority '${priority}'`);
    const configString = ConfigSourceResolver._getConfigSourceAsString(configSource);
    ConfigSourceResolver._parseConfigsAndAddToCollection(priority, configString);
  }
  static getConfig(configName) {
    console.log(`Retrieving config ${configName}`);
    return import_ConfigsDictionary.ConfigsDictionary.getConfig(configName);
  }
  static clearConfigs() {
    import_ConfigsDictionary.ConfigsDictionary.clearConfigs();
  }
  static _getConfigSourceAsString(configSource) {
    if (!configSource || configSource.trim() === "") {
      throw new Error("Config source cannot be null or whitespace.");
    }
    const envValue = import_process.default.env[configSource];
    if (envValue && envValue.trim() !== "") {
      configSource = envValue;
    }
    if (import_fs.default.existsSync(configSource) && import_fs.default.statSync(configSource).isFile()) {
      configSource = import_fs.default.readFileSync(configSource, { encoding: "utf-8" });
    }
    return configSource.trim();
  }
  static _parseConfigsAndAddToCollection(priority, configString) {
    try {
      const jsonObject = JSON.parse(configString);
      import_JsonConfigResolver.JsonConfigResolver.addConfigs(priority, jsonObject);
      return;
    } catch (ex) {
      if (ex instanceof SyntaxError) {
      } else {
        console.log("Failed to parse config source as JSON: " + ex);
      }
    }
    try {
      import_YamlConfigResolver.YamlConfigResolver.addConfigs(priority, configString);
      return;
    } catch (ex) {
      if (ex.name === "SyntaxError") {
      } else {
        console.log("Failed to parse config source as YAML: " + ex);
      }
    }
    try {
      import_ConnectionStringConfigResolver.ConnectionStringConfigResolver.addConfigs(priority, configString);
      return;
    } catch (ex) {
      console.log("Failed to parse config source as connection string: " + ex);
    }
    throw new Error(
      "Config source is not valid JSON, YAML, or connection string format:\n" + configString
    );
  }
}
// Annotate the CommonJS export names for ESM import in node:
0 && (module.exports = {
  ConfigSourceResolver
});
