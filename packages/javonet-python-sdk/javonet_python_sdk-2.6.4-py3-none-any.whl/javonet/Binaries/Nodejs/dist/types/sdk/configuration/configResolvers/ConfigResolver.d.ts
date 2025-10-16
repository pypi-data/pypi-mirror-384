export class ConfigResolver {
    /**
     * Parse a runtime string into the runtime enum/name using RuntimeNameHandler.
     * @param {string} runtime
     * @returns {*}
     */
    static tryParseRuntime(runtime: string): any;
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
    static buildConnectionData(hostValue: string): InMemoryConnectionData | WsConnectionData | TcpConnectionData;
    /**
     * Parse tcp address portion (after tcp://) into TcpConnectionData.
     * Expected formats: host:port or host:port/...
     * Throws Error on invalid format or port.
     * @param {string} address
     * @returns {TcpConnectionData}
     */
    static parseTcp(address: string): TcpConnectionData;
}
import { InMemoryConnectionData } from '../../../utils/connectionData/InMemoryConnectionData.js';
import { WsConnectionData } from '../../../utils/connectionData/WsConnectionData.js';
import { TcpConnectionData } from '../../../utils/nodejs/connectionData/TcpConnectionData.js';
