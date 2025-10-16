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
var ConfigResolver_exports = {};
__export(ConfigResolver_exports, {
  ConfigResolver: () => ConfigResolver
});
module.exports = __toCommonJS(ConfigResolver_exports);
var import_RuntimeNameHandler = require("../../../utils/RuntimeNameHandler.cjs");
var import_InMemoryConnectionData = require("../../../utils/connectionData/InMemoryConnectionData.cjs");
var import_WsConnectionData = require("../../../utils/connectionData/WsConnectionData.cjs");
var import_TcpConnectionData = require("../../../utils/nodejs/connectionData/TcpConnectionData.cjs");
class ConfigResolver {
  /**
   * Parse a runtime string into the runtime enum/name using RuntimeNameHandler.
   * @param {string} runtime
   * @returns {*}
   */
  static tryParseRuntime(runtime) {
    if (!runtime || String(runtime).trim() === "") {
      throw new Error("Runtime string cannot be null or whitespace.");
    }
    const normalized = String(runtime).trim().toLowerCase();
    return import_RuntimeNameHandler.RuntimeNameHandler.getRuntime(normalized);
  }
  /**
   * Build appropriate connection data object from a host string.
   * - empty / null => InMemoryConnectionData
   * - "inmemory" or "in-memory" => InMemoryConnectionData
   * - ws:// or wss:// => WsConnectionData(fullAddress)
   * - tcp://... => parsed by parseTcp
   * - host:port or host:port/... => TcpConnectionData(host, port) if valid, otherwise InMemoryConnectionData
   * @param {string} hostValue
   * @returns {InMemoryConnectionData|WsConnectionData|TcpConnectionData}
   */
  static buildConnectionData(hostValue) {
    if (!hostValue || String(hostValue).trim() === "") {
      return new import_InMemoryConnectionData.InMemoryConnectionData();
    }
    const hv = String(hostValue).trim();
    const lower = hv.toLowerCase();
    if (lower === "inmemory" || lower === "in-memory") {
      return new import_InMemoryConnectionData.InMemoryConnectionData();
    }
    if (lower.startsWith("ws://") || lower.startsWith("wss://")) {
      return new import_WsConnectionData.WsConnectionData(hv);
    }
    if (lower.startsWith("tcp://")) {
      try {
        return ConfigResolver.parseTcp(hv.slice(6));
      } catch (e) {
        return new import_InMemoryConnectionData.InMemoryConnectionData();
      }
    }
    const colon = hv.indexOf(":");
    if (colon > 0 && colon < hv.length - 1) {
      let portPart = hv.substring(colon + 1);
      const slash = portPart.indexOf("/");
      if (slash >= 0) {
        portPart = portPart.substring(0, slash);
      }
      try {
        const port = parseInt(portPart, 10);
        if (!Number.isFinite(port) || Number.isNaN(port)) {
          throw new Error("invalid port");
        }
        const hostOnly = hv.substring(0, colon);
        if (String(hostOnly).trim()) {
          try {
            return new import_TcpConnectionData.TcpConnectionData(hostOnly, port);
          } catch (e) {
            return new import_InMemoryConnectionData.InMemoryConnectionData();
          }
        }
      } catch (e) {
      }
    }
    return new import_InMemoryConnectionData.InMemoryConnectionData();
  }
  /**
   * Parse tcp address portion (after tcp://) into TcpConnectionData.
   * Expected formats: host:port or host:port/...
   * Throws Error on invalid format or port.
   * @param {string} address
   * @returns {TcpConnectionData}
   */
  static parseTcp(address) {
    const slash = address.indexOf("/");
    const hostPort = slash >= 0 ? address.substring(0, slash) : address;
    const colon = hostPort.lastIndexOf(":");
    if (colon <= 0 || colon >= hostPort.length - 1) {
      throw new Error("Invalid tcp:// format.");
    }
    const host = hostPort.substring(0, colon);
    const portStr = hostPort.substring(colon + 1);
    const port = parseInt(portStr, 10);
    if (!Number.isFinite(port) || Number.isNaN(port)) {
      throw new Error("Invalid port in tcp:// address.");
    }
    return new import_TcpConnectionData.TcpConnectionData(host, port);
  }
}
// Annotate the CommonJS export names for ESM import in node:
0 && (module.exports = {
  ConfigResolver
});
