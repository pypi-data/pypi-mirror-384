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
var Javonet_exports = {};
__export(Javonet_exports, {
  CommandDeserializer: () => import_CommandDeserializer.CommandDeserializer,
  CommandSerializer: () => import_CommandSerializer.CommandSerializer,
  ConfigPriority: () => import_ConfigPriority.ConfigPriority,
  Javonet: () => Javonet,
  TcpConnectionData: () => import_TcpConnectionData.TcpConnectionData,
  WsConnectionData: () => import_WsConnectionData.WsConnectionData
});
module.exports = __toCommonJS(Javonet_exports);
var import_ConfigRuntimeFactory = require("./ConfigRuntimeFactory.cjs");
var import_RuntimeFactory = require("./RuntimeFactory.cjs");
var import_RuntimeContext = require("./RuntimeContext.cjs");
var import_InMemoryConnectionData = require("../utils/connectionData/InMemoryConnectionData.cjs");
var import_Runtime = require("../utils/Runtime.cjs");
var import_CommandSerializer = require("../core/protocol/CommandSerializer.cjs");
var import_CommandDeserializer = require("../core/protocol/CommandDeserializer.cjs");
var import_RuntimeLogger = require("../utils/RuntimeLogger.cjs");
var import_TcpConnectionData = require("../utils/nodejs/connectionData/TcpConnectionData.cjs");
var import_WsConnectionData = require("../utils/connectionData/WsConnectionData.cjs");
var import_UtilsConst = require("../utils/UtilsConst.cjs");
var import_ConfigSourceResolver = require("./configuration/ConfigSourceResolver.cjs");
var import_ConfigPriority = require("./configuration/ConfigPriority.cjs");
const import_meta = {};
const requireDynamic = (0, import_Runtime.getRequire)(import_meta.url);
let _Transmitter = null;
if ((0, import_Runtime.isNodejsRuntime)()) {
  try {
    const { Transmitter } = require("../core/transmitter/Transmitter.cjs");
    _Transmitter = Transmitter;
  } catch (error) {
    throw error;
  }
}
class Javonet {
  /**
   * Initializes Javonet using an in-memory channel on the same machine.
   * @returns {RuntimeFactory} A RuntimeFactory instance configured for an in-memory connection.
   * @see [Javonet Guides](https://www.javonet.com/guides/v2/javascript/foundations/in-memory-channel)
   */
  static inMemory() {
    return new import_RuntimeFactory.RuntimeFactory(new import_InMemoryConnectionData.InMemoryConnectionData());
  }
  /**
   * Initializes Javonet with a TCP connection to a remote machine.
   * @param {TcpConnectionData} tcpConnectionData - The tcp connection data of the remote machine.
   * @returns {RuntimeFactory} A RuntimeFactory instance configured for a TCP connection.
   * @see [Javonet Guides](https://www.javonet.com/guides/v2/javascript/foundations/tcp-channel)
   */
  static tcp(tcpConnectionData) {
    return new import_RuntimeFactory.RuntimeFactory(tcpConnectionData);
  }
  /**
   * Initializes Javonet with a WebSocket connection to a remote machine.
   * @param {WsConnectionData} wsConnectionData - The WebSocket connection data of the remote machine.
   * @returns {RuntimeFactory} A RuntimeFactory instance configured for a WebSocket connection.
   * @see [Javonet Guides](https://www.javonet.com/guides/v2/javascript/foundations/websocket-channel)
   */
  static webSocket(wsConnectionData) {
    return new import_RuntimeFactory.RuntimeFactory(wsConnectionData);
  }
  /**
   * Initializes Javonet with a custom configuration file taken from external source.
   * Currentyl supported: Configuration file in JSON format
   * @param {string|ConfigSource} config - Path to a configuration file.
   * @returns {ConfigRuntimeFactory} A ConfigRuntimeFactory instance with configuration data.
   * @see [Javonet Guides](https://www.javonet.com/guides/v2/javascript/foundations/configure-channel)
   */
  static withConfig(config) {
    return new import_ConfigRuntimeFactory.ConfigRuntimeFactory(config);
  }
  /**
   * Activates Javonet with the provided license key.
   * @param {string} licenseKey - The license key to activate Javonet.
   * @returns {void} The activation status code.
   * @see [Javonet Guides](https://www.javonet.com/guides/v2/javascript/getting-started/activating-javonet)
   */
  static activate(licenseKey) {
    import_UtilsConst.UtilsConst.setLicenseKey(licenseKey);
  }
  /**
   * Gets the runtime information.
   * @returns {string} The runtime information.
   */
  static getRuntimeInfo() {
    if ((0, import_Runtime.isNodejsRuntime)()) {
      return import_RuntimeLogger.RuntimeLogger.getRuntimeInfo();
    } else {
      throw new Error("Javonet.getRuntimeInfo is allowed only to run in nodejs runtime");
    }
  }
  /**
   * Sets the configuration source for the Javonet SDK.
   * @param {string} configSource - The configuration source.
   * @returns {void}
   */
  static setConfigSource(configSource) {
    import_UtilsConst.UtilsConst.setConfigSource(configSource);
  }
  /**
   * Sets the working directory for the Javonet SDK.
   * @param {string} path - The working directory.
   * @returns {void}
   */
  static setJavonetWorkingDirectory(path) {
    import_UtilsConst.UtilsConst.setJavonetWorkingDirectory(path);
  }
  /**
   * Adds a configuration to the ConfigSourceResolver with the specified priority and source.
   * @param {number} priority - The priority of the configuration.
   * @param {string} configSource - The configuration source.
   */
  static addConfig(priority, configSource) {
    import_ConfigSourceResolver.ConfigSourceResolver.addConfigs(priority, configSource);
  }
  /**
   * Initializes a RuntimeContext instance based on the specified configuration name.
   * @param {string} configName - The name of the configuration to use.
   * @returns {RuntimeContext}  A RuntimeContext instance initialized with the specified configuration.
   */
  static initializeRc(configName) {
    const config = import_ConfigSourceResolver.ConfigSourceResolver.getConfig(configName);
    return import_RuntimeFactory.RuntimeFactory.initializeRuntimeContext(config);
  }
}
// Annotate the CommonJS export names for ESM import in node:
0 && (module.exports = {
  CommandDeserializer,
  CommandSerializer,
  ConfigPriority,
  Javonet,
  TcpConnectionData,
  WsConnectionData
});
