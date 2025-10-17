import { Renderer } from '@hat-open/renderer';
import * as u from '@hat-open/util';
type MsgRequest = {
    type: 'request';
    id: number;
    name: string;
    data: u.JData;
};
type MsgResponse = {
    type: 'response';
    id: number;
    success: boolean;
    data: u.JData;
};
type MsgState = {
    type: 'state';
    diff: u.JPatch;
};
type MsgNotify = {
    type: 'notify';
    name: string;
    data: u.JData;
};
type Msg = MsgRequest | MsgResponse | MsgState | MsgNotify;
export type Notification = {
    name: string;
    data: u.JData;
};
export declare class OpenEvent extends CustomEvent<undefined> {
    readonly type: 'open';
    constructor();
}
export declare class CloseEvent extends CustomEvent<undefined> {
    readonly type: 'close';
    constructor();
}
export declare class NotifyEvent extends CustomEvent<Notification> {
    readonly type: 'notify';
    constructor(notification: Notification);
}
export declare class ChangeEvent extends CustomEvent<u.JData> {
    readonly type: 'change';
    constructor(state: u.JData);
}
export declare class ConnectedEvent extends CustomEvent<undefined> {
    readonly type: 'connected';
    constructor();
}
export declare class DisconnectedEvent extends CustomEvent<undefined> {
    readonly type: 'disconnected';
    constructor();
}
/**
 * Get default juggler server address
 */
export declare function getDefaultAddress(): string;
/**
 * Juggler client connection
 *
 * Available events:
 *  - `OpenEvent` - connection is opened
 *  - `CloseEvent` - connection is closed
 *  - `NotifyEvent` - received new notification
 *  - `ChangeEvent` - remote state changed
 */
export declare class Connection extends EventTarget {
    _state: u.JData;
    _nextId: number;
    _futures: Map<number, u.Future<u.JData>>;
    _pingDelayHandle: number | null;
    _pingTimeoutHandle: number | null;
    _receiveQueue: string[];
    _ws: WebSocket;
    _pingDelay: number | null;
    _pingTimeout: number;
    _maxSegmentSize: number;
    /**
     * Create connection
     *
     * Juggler server address is formatted as
     * ``ws[s]://<host>[:<port>][/<path>]``. If not provided, hostname
     * and port obtained from ``widow.location`` are used instead, with
     * ``ws`` as a path.
     */
    constructor(address?: string, pingDelay?: number | null, pingTimeout?: number, maxSegmentSize?: number);
    /**
     * Remote server state
     */
    get state(): u.JData;
    /**
     * WebSocket ready state
     */
    get readyState(): number;
    /**
     * Close connection
     */
    close(): void;
    /**
     * Send request and wait for response
     */
    send(name: string, data: u.JData): Promise<u.JData>;
    _onOpen(): void;
    _onClose(): void;
    _onMessage(data: string): void;
    _onPingTimeout(): void;
    _resetPing(): void;
    _sendPing(): void;
    _stopPing(): void;
    _close(code?: number): void;
    _processMessage(msg: Msg): void;
}
/**
 * Juggler based application
 *
 * Available events:
 *  - ConnectedEvent - connected to server
 *  - DisconnectedEvent - disconnected from server
 *  - NotifyEvent - received new notification
 */
export declare class Application extends EventTarget {
    _conn: Connection | null;
    _next_address_index: number;
    _statePath: u.JPath | null;
    _renderer: Renderer;
    _addresses: string[];
    _retryDelay: number | null;
    _pingDelay: number | null;
    _pingTimeout: number;
    _maxSegmentSize: number;
    /**
     * Create application
     *
     * If `statePath` is `null`, remote server state is not synced to renderer
     * state.
     *
     * Format of provided addresses is same as in `Connection` constructor.
     *
     * If `retryDelay` is `null`, once connection to server is closed,
     * new connection is not established.
     */
    constructor(statePath?: u.JPath | null, renderer?: Renderer, addresses?: string[], retryDelay?: number | null, pingDelay?: number | null, pingTimeout?: number, maxSegmentSize?: number);
    /**
     * Server addresses
     */
    get addresses(): string[];
    /**
     * Set server addresses
     */
    setAddresses(addresses: string[]): void;
    /**
     * Disconnect from current server
     *
     * After active connection is closed, application immediately tries to
     * establish connection using next server address or tries to connect
     * to  first server address after `retryDelay` elapses.
     */
    disconnect(): void;
    /**
     * Send request and wait for response
     */
    send(name: string, data: u.JData): Promise<u.JData>;
    _connectLoop(): Promise<void>;
}
export {};
