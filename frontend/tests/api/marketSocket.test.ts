import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

// Each test gets a fresh module instance so the manager's internal state
// (subscriptions, reconnect attempts) never leaks between tests.
async function freshManager() {
  vi.resetModules();
  const mod = await import("@/api/marketSocket");
  return mod.marketSocketManager;
}

class FakeWebSocket {
  static instances: FakeWebSocket[] = [];
  static CONNECTING = 0;
  static OPEN = 1;
  static CLOSING = 2;
  static CLOSED = 3;
  readyState = FakeWebSocket.CONNECTING;
  onopen: (() => void) | null = null;
  onmessage: ((event: { data: string }) => void) | null = null;
  onclose: (() => void) | null = null;
  onerror: (() => void) | null = null;
  sent: string[] = [];

  constructor(public url: string) {
    FakeWebSocket.instances.push(this);
  }

  send(data: string) {
    this.sent.push(data);
  }

  close() {
    this.readyState = FakeWebSocket.CLOSED;
    this.onclose?.();
  }

  simulateOpen() {
    this.readyState = FakeWebSocket.OPEN;
    this.onopen?.();
  }

  simulateMessage(payload: unknown) {
    this.onmessage?.({ data: JSON.stringify(payload) });
  }

  simulateDrop() {
    this.readyState = FakeWebSocket.CLOSED;
    this.onclose?.();
  }
}

describe("marketSocketManager", () => {
  beforeEach(() => {
    FakeWebSocket.instances = [];
    // @ts-expect-error -- test double for the global WebSocket
    global.WebSocket = FakeWebSocket;
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("sends a subscribe message on first subscriber and delivers quote messages", async () => {
    const manager = await freshManager();
    const received: unknown[] = [];
    manager.subscribe("AAPL", (msg) => received.push(msg));

    const socket = FakeWebSocket.instances[0];
    socket.simulateOpen();
    expect(
      socket.sent.some(
        (s) => JSON.parse(s).action === "subscribe" && JSON.parse(s).ticker === "AAPL"
      )
    ).toBe(true);

    socket.simulateMessage({ type: "quote", ticker: "AAPL", data: { price: 100 } });
    expect(received).toHaveLength(1);
  });

  it("does not send a duplicate subscribe for a second subscriber on the same ticker", async () => {
    const manager = await freshManager();
    manager.subscribe("AAPL", () => {});
    const socket = FakeWebSocket.instances[0];
    socket.simulateOpen();
    const sentBefore = socket.sent.length;

    manager.subscribe("AAPL", () => {}); // second listener, same ticker
    expect(socket.sent.length).toBe(sentBefore); // no new subscribe message sent
  });

  it("only sends unsubscribe once the last listener for a ticker is removed", async () => {
    const manager = await freshManager();
    const unsubA = manager.subscribe("AAPL", () => {});
    const unsubB = manager.subscribe("AAPL", () => {});
    const socket = FakeWebSocket.instances[0];
    socket.simulateOpen();

    unsubA();
    expect(socket.sent.some((s) => JSON.parse(s).action === "unsubscribe")).toBe(false);

    unsubB();
    expect(socket.sent.some((s) => JSON.parse(s).action === "unsubscribe")).toBe(true);
  });

  it("reconnects and re-subscribes to previously watched tickers after a drop", async () => {
    const manager = await freshManager();
    manager.subscribe("AAPL", () => {});
    const firstSocket = FakeWebSocket.instances[0];
    firstSocket.simulateOpen();

    firstSocket.simulateDrop();
    expect(manager.getStatus()).toBe("closed");

    await vi.advanceTimersByTimeAsync(1500); // base reconnect delay
    expect(FakeWebSocket.instances.length).toBe(2);

    const secondSocket = FakeWebSocket.instances[1];
    secondSocket.simulateOpen();
    expect(
      secondSocket.sent.some(
        (s) => JSON.parse(s).action === "subscribe" && JSON.parse(s).ticker === "AAPL"
      )
    ).toBe(true);
  });
});
