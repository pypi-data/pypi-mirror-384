import r from '@hat-open/renderer';
import * as u from '@hat-open/util';
function isMsgResponse(msg) {
    return msg.type == 'response';
}
function isMsgState(msg) {
    return msg.type == 'state';
}
function isMsgNotify(msg) {
    return msg.type == 'notify';
}
export class OpenEvent extends CustomEvent {
    constructor() {
        super('open');
    }
}
export class CloseEvent extends CustomEvent {
    constructor() {
        super('close');
    }
}
export class NotifyEvent extends CustomEvent {
    constructor(notification) {
        super('notify', { detail: notification });
    }
}
export class ChangeEvent extends CustomEvent {
    constructor(state) {
        super('change', { detail: state });
    }
}
export class ConnectedEvent extends CustomEvent {
    constructor() {
        super('connected');
    }
}
export class DisconnectedEvent extends CustomEvent {
    constructor() {
        super('disconnected');
    }
}
/**
 * Get default juggler server address
 */
export function getDefaultAddress() {
    const protocol = window.location.protocol == 'https:' ? 'wss' : 'ws';
    const hostname = window.location.hostname || 'localhost';
    const port = window.location.port;
    return `${protocol}://${hostname}` + (port ? `:${port}` : '') + '/ws';
}
/**
 * Juggler client connection
 *
 * Available events:
 *  - `OpenEvent` - connection is opened
 *  - `CloseEvent` - connection is closed
 *  - `NotifyEvent` - received new notification
 *  - `ChangeEvent` - remote state changed
 */
export class Connection extends EventTarget {
    _state = null;
    _nextId = 1;
    _futures = new Map();
    _pingDelayHandle = null;
    _pingTimeoutHandle = null;
    _receiveQueue = [];
    _ws;
    _pingDelay;
    _pingTimeout;
    _maxSegmentSize;
    /**
     * Create connection
     *
     * Juggler server address is formatted as
     * ``ws[s]://<host>[:<port>][/<path>]``. If not provided, hostname
     * and port obtained from ``widow.location`` are used instead, with
     * ``ws`` as a path.
     */
    constructor(address = getDefaultAddress(), pingDelay = 5000, pingTimeout = 5000, maxSegmentSize = 64 * 1024) {
        super();
        this._pingDelay = pingDelay;
        this._pingTimeout = pingTimeout;
        this._maxSegmentSize = maxSegmentSize;
        this._ws = new WebSocket(address);
        this._ws.addEventListener('open', () => this._onOpen());
        this._ws.addEventListener('close', () => this._onClose());
        this._ws.addEventListener('message', evt => this._onMessage(evt.data));
    }
    /**
     * Remote server state
     */
    get state() {
        return this._state;
    }
    /**
     * WebSocket ready state
     */
    get readyState() {
        return this._ws.readyState;
    }
    /**
     * Close connection
     */
    close() {
        this._close(1000);
    }
    /**
     * Send request and wait for response
     */
    async send(name, data) {
        if (this.readyState != WebSocket.OPEN) {
            throw new Error("connection not open");
        }
        const id = this._nextId++;
        const msg = {
            type: 'request',
            id: id,
            name: name,
            data: data
        };
        const msgStr = JSON.stringify(msg);
        let pos = 0;
        let moreFollows = true;
        while (moreFollows) {
            const payload = msgStr.substring(pos, pos + this._maxSegmentSize);
            pos += payload.length;
            moreFollows = pos < msgStr.length;
            const dataType = (moreFollows ? '1' : '0');
            this._ws.send(dataType + payload);
        }
        const f = u.createFuture();
        try {
            this._futures.set(id, f);
            return await f;
        }
        finally {
            this._futures.delete(id);
        }
    }
    _onOpen() {
        this._resetPing();
        this.dispatchEvent(new OpenEvent());
    }
    _onClose() {
        this.dispatchEvent(new CloseEvent());
        for (const f of this._futures.values())
            if (!f.done())
                f.setError(new Error("connection not open"));
    }
    _onMessage(data) {
        try {
            this._resetPing();
            const dataType = data[0];
            const payload = data.substring(1);
            if (dataType == '0') {
                this._receiveQueue.push(payload);
                const msgStr = this._receiveQueue.join('');
                this._receiveQueue = [];
                const msg = JSON.parse(msgStr);
                this._processMessage(msg);
            }
            else if (dataType == '1') {
                this._receiveQueue.push(payload);
            }
            else if (dataType == '2') {
                this._ws.send("3" + payload);
            }
            else if (dataType == '3') { // eslint-disable-line
            }
            else {
                throw new Error('unsupported data type');
            }
        }
        catch (e) {
            this._close();
            throw e;
        }
    }
    _onPingTimeout() {
        if (this._pingTimeoutHandle == null)
            return;
        this._close();
    }
    _resetPing() {
        this._stopPing();
        if (this._pingDelay != null) {
            this._pingDelayHandle = setTimeout(() => {
                this._sendPing();
            }, this._pingDelay);
        }
    }
    _sendPing() {
        if (this._pingDelayHandle == null)
            return;
        this._pingDelayHandle = null;
        this._ws.send("2");
        if (this._pingTimeoutHandle == null) {
            this._pingTimeoutHandle = setTimeout(() => {
                this._onPingTimeout();
            }, this._pingTimeout);
        }
    }
    _stopPing() {
        if (this._pingDelayHandle != null) {
            clearTimeout(this._pingDelayHandle);
            this._pingDelayHandle = null;
        }
        if (this._pingTimeoutHandle != null) {
            clearTimeout(this._pingTimeoutHandle);
            this._pingTimeoutHandle = null;
        }
    }
    _close(code) {
        this._stopPing();
        this._ws.close(code);
    }
    _processMessage(msg) {
        if (isMsgState(msg)) {
            this._state = u.patch(msg.diff, this._state);
            this.dispatchEvent(new ChangeEvent(this._state));
        }
        else if (isMsgNotify(msg)) {
            this.dispatchEvent(new NotifyEvent({
                name: msg.name,
                data: msg.data
            }));
        }
        else if (isMsgResponse(msg)) {
            const f = this._futures.get(msg.id);
            if (f && !f.done()) {
                if (msg.success) {
                    f.setResult(msg.data);
                }
                else {
                    f.setError(msg.data);
                }
            }
        }
        else {
            throw new Error('unsupported message type');
        }
    }
}
/**
 * Juggler based application
 *
 * Available events:
 *  - ConnectedEvent - connected to server
 *  - DisconnectedEvent - disconnected from server
 *  - NotifyEvent - received new notification
 */
export class Application extends EventTarget {
    _conn = null;
    _next_address_index = 0;
    _statePath;
    _renderer;
    _addresses;
    _retryDelay;
    _pingDelay;
    _pingTimeout;
    _maxSegmentSize;
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
    constructor(statePath = null, renderer = r, addresses = [getDefaultAddress()], retryDelay = 5000, pingDelay = 5000, pingTimeout = 5000, maxSegmentSize = 64 * 1024) {
        super();
        this._statePath = statePath;
        this._renderer = renderer;
        this._addresses = addresses;
        this._retryDelay = retryDelay;
        this._pingDelay = pingDelay;
        this._pingTimeout = pingTimeout;
        this._maxSegmentSize = maxSegmentSize;
        u.delay(() => this._connectLoop());
    }
    /**
     * Server addresses
     */
    get addresses() {
        return this._addresses;
    }
    /**
     * Set server addresses
     */
    setAddresses(addresses) {
        this._addresses = addresses;
        this._next_address_index = 0;
    }
    /**
     * Disconnect from current server
     *
     * After active connection is closed, application immediately tries to
     * establish connection using next server address or tries to connect
     * to  first server address after `retryDelay` elapses.
     */
    disconnect() {
        if (!this._conn)
            return;
        this._conn.close();
    }
    /**
     * Send request and wait for response
     */
    async send(name, data) {
        if (!this._conn)
            throw new Error("connection closed");
        return await this._conn.send(name, data);
    }
    async _connectLoop() {
        while (true) {
            while (this._next_address_index < this._addresses.length) {
                const address = this._addresses[this._next_address_index++];
                const closeFuture = u.createFuture();
                const conn = new Connection(address, this._pingDelay, this._pingTimeout, this._maxSegmentSize);
                conn.addEventListener('open', () => {
                    this.dispatchEvent(new ConnectedEvent());
                });
                conn.addEventListener('close', () => {
                    closeFuture.setResult();
                    if (this._statePath)
                        this._renderer.set(this._statePath, null);
                    this.dispatchEvent(new DisconnectedEvent());
                });
                conn.addEventListener('notify', evt => {
                    const notification = evt.detail;
                    this.dispatchEvent(new NotifyEvent(notification));
                });
                conn.addEventListener('change', evt => {
                    if (this._statePath == null)
                        return;
                    const data = evt.detail;
                    this._renderer.set(this._statePath, data);
                });
                this._conn = conn;
                await closeFuture;
                this._conn = null;
            }
            if (this._retryDelay == null)
                break;
            await u.sleep(this._retryDelay);
            this._next_address_index = 0;
        }
    }
}
