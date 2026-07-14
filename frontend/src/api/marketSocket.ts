import { WS_BASE_URL } from "@/api/client";
import type { DataStatus } from "@/types/api";

export interface QuoteMessage {
  type: "quote";
  ticker: string;
  data: {
    price: number;
    previous_close: number | null;
    change_abs: number | null;
    change_pct: number | null;
    currency: string;
    data_status: DataStatus;
    source: string;
    as_of: string;
    poll_interval_seconds: number;
  };
}

type ServerMessage =
  | QuoteMessage
  | { type: "subscribed" | "unsubscribed"; ticker: string }
  | { type: "pong" }
  | { type: "error"; ticker?: string; message: string };

type Listener = (message: QuoteMessage) => void;
type StatusListener = (status: ConnectionStatus) => void;
export type ConnectionStatus = "connecting" | "open" | "closed" | "reconnecting";

const HEARTBEAT_INTERVAL_MS = 20_000;
const BASE_RECONNECT_DELAY_MS = 1_000;
const MAX_RECONNECT_DELAY_MS = 30_000;

/**
 * A single shared WebSocket connection for the whole app, ref-counted per
 * ticker so multiple components watching the same ticker (e.g. a chart and
 * the watchlist sidebar) never cause duplicate `subscribe` messages, and a
 * ticker is only unsubscribed server-side once its last listener unmounts.
 */
class MarketSocketManager {
  private ws: WebSocket | null = null;
  private status: ConnectionStatus = "closed";
  private reconnectAttempts = 0;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private heartbeatTimer: ReturnType<typeof setInterval> | null = null;
  private listeners = new Map<string, Set<Listener>>();
  private statusListeners = new Set<StatusListener>();
  private refCounts = new Map<string, number>();

  private setStatus(status: ConnectionStatus) {
    this.status = status;
    this.statusListeners.forEach((cb) => cb(status));
  }

  getStatus(): ConnectionStatus {
    return this.status;
  }

  onStatusChange(cb: StatusListener): () => void {
    this.statusListeners.add(cb);
    return () => this.statusListeners.delete(cb);
  }

  private ensureConnected() {
    if (
      this.ws &&
      (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING)
    ) {
      return;
    }
    this.setStatus(this.reconnectAttempts > 0 ? "reconnecting" : "connecting");
    const socket = new WebSocket(`${WS_BASE_URL}/api/v1/ws/market`);
    this.ws = socket;

    socket.onopen = () => {
      this.reconnectAttempts = 0;
      this.setStatus("open");
      // Re-subscribe to everything we were watching before a reconnect.
      for (const ticker of this.refCounts.keys()) {
        this.send({ action: "subscribe", ticker });
      }
      this.startHeartbeat();
    };

    socket.onmessage = (event) => {
      let message: ServerMessage;
      try {
        message = JSON.parse(event.data as string) as ServerMessage;
      } catch {
        return;
      }
      if (message.type === "quote") {
        this.listeners.get(message.ticker)?.forEach((cb) => cb(message));
      }
    };

    socket.onclose = () => {
      this.setStatus("closed");
      this.stopHeartbeat();
      this.scheduleReconnect();
    };

    socket.onerror = () => {
      socket.close();
    };
  }

  private send(payload: unknown) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(payload));
    }
  }

  private startHeartbeat() {
    this.stopHeartbeat();
    this.heartbeatTimer = setInterval(() => {
      this.send({ action: "ping" });
    }, HEARTBEAT_INTERVAL_MS);
  }

  private stopHeartbeat() {
    if (this.heartbeatTimer) clearInterval(this.heartbeatTimer);
    this.heartbeatTimer = null;
  }

  private scheduleReconnect() {
    if (this.reconnectTimer) return;
    const delay = Math.min(
      BASE_RECONNECT_DELAY_MS * 2 ** this.reconnectAttempts,
      MAX_RECONNECT_DELAY_MS
    );
    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = null;
      this.reconnectAttempts += 1;
      this.ensureConnected();
    }, delay);
  }

  subscribe(ticker: string, listener: Listener): () => void {
    this.ensureConnected();
    if (!this.listeners.has(ticker)) this.listeners.set(ticker, new Set());
    this.listeners.get(ticker)!.add(listener);

    const count = (this.refCounts.get(ticker) ?? 0) + 1;
    this.refCounts.set(ticker, count);
    if (count === 1) {
      this.send({ action: "subscribe", ticker });
    }

    return () => {
      this.listeners.get(ticker)?.delete(listener);
      const next = (this.refCounts.get(ticker) ?? 1) - 1;
      if (next <= 0) {
        this.refCounts.delete(ticker);
        this.listeners.delete(ticker);
        this.send({ action: "unsubscribe", ticker });
      } else {
        this.refCounts.set(ticker, next);
      }
    };
  }
}

export const marketSocketManager = new MarketSocketManager();
