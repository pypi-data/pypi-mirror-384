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
var ConfigsDictionary_exports = {};
__export(ConfigsDictionary_exports, {
  ConfigsDictionary: () => ConfigsDictionary
});
module.exports = __toCommonJS(ConfigsDictionary_exports);
class ConfigsDictionary {
  /** @type {Map<string, Map<number, any>>} */
  static _configurations_collection = /* @__PURE__ */ new Map();
  /**
   * Normalize priority to a numeric value.
   * Accepts either a number or an object with a numeric `value` property.
   * @param {any} priority
   * @returns {number|undefined}
   */
  static _normalizePriority(priority) {
    if (typeof priority === "number" && Number.isFinite(priority)) {
      return priority;
    }
    if (priority && typeof priority === "object" && "value" in priority && typeof priority.value === "number") {
      return priority.value;
    }
    return void 0;
  }
  /**
   * Add a configuration for a given name and priority.
   * If the same name+priority already exists, it will not be overwritten.
   * @param {string} name
   * @param {number|{value:number}} priority
   * @param {*} config
   */
  static addConfig(name, priority, config) {
    if (!name || String(name).trim() === "") {
      console.log("Config name cannot be null or whitespace. Skipping add.");
      return;
    }
    if (config == null) {
      console.log("Config instance is null. Skipping add.");
      return;
    }
    const key = ConfigsDictionary._normalizePriority(priority);
    if (typeof key !== "number") {
      console.log(
        "Priority must be a numeric value or an object with a numeric `value` property. Skipping add."
      );
      return;
    }
    let perPriority = ConfigsDictionary._configurations_collection.get(name);
    if (!perPriority) {
      perPriority = /* @__PURE__ */ new Map();
      ConfigsDictionary._configurations_collection.set(name, perPriority);
    }
    if (perPriority.has(key)) {
      console.log(
        `Config with name \`${name}\` and priority \`${key}\` already exists. It will not be added or updated.`
      );
      return;
    }
    perPriority.set(key, config);
    let serialized;
    try {
      serialized = JSON.stringify(config);
    } catch {
      serialized = String(config);
    }
    console.log(`Added configuration \`${name}\` with priority \`${key}\` and parameters ${serialized}`);
  }
  /**
   * Retrieve the configuration with the numerically smallest priority for the given name.
   * Throws if name is invalid or no configuration is found.
   * @param {string} name
   * @returns {*}
   */
  static getConfig(name) {
    if (!name || String(name).trim() === "") {
      throw new Error("Config name cannot be null or whitespace");
    }
    const perPriority = ConfigsDictionary._configurations_collection.get(name);
    if (!perPriority || perPriority.size === 0) {
      throw new Error(`Configuration ${name} not found`);
    }
    const keysArray = [...perPriority.keys()];
    const smallest = keysArray.reduce((min, k) => k < min ? k : min, keysArray[0]);
    const config = perPriority.get(smallest);
    let serialized;
    try {
      serialized = JSON.stringify(config);
    } catch {
      serialized = String(config);
    }
    console.log(
      `Retrieved configuration \`${name}\` with priority \`${smallest}\` and parameters ${serialized}`
    );
    return config;
  }
  /** Clear all stored configurations. */
  static clearConfigs() {
    ConfigsDictionary._configurations_collection.clear();
  }
}
// Annotate the CommonJS export names for ESM import in node:
0 && (module.exports = {
  ConfigsDictionary
});
