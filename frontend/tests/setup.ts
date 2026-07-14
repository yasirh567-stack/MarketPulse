import "@testing-library/jest-dom/vitest";
import { afterEach } from "vitest";
import { cleanup } from "@testing-library/react";

afterEach(() => {
  cleanup();
});

// jsdom doesn't implement matchMedia — used by useTheme's initial system-theme check.
if (!window.matchMedia) {
  window.matchMedia = (query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: () => {},
    removeListener: () => {},
    addEventListener: () => {},
    removeEventListener: () => {},
    dispatchEvent: () => false,
  });
}

// jsdom's getContext exists but throws "not implemented" when called; plotly.js
// probes it for feature detection even for chart types that don't need it.
// Overriding with a no-op stub avoids noisy (but harmless) console errors.
// @ts-expect-error -- minimal stub, not a full CanvasRenderingContext2D
HTMLCanvasElement.prototype.getContext = () => null;

// jsdom has no URL.createObjectURL — plotly.js touches it while building its
// offline export menu, even for charts that never actually export anything.
if (!window.URL.createObjectURL) {
  window.URL.createObjectURL = () => "blob:mock";
}
if (!window.URL.revokeObjectURL) {
  window.URL.revokeObjectURL = () => {};
}

// jsdom has no WebSocket implementation; components that mount useMarketSocket
// need a harmless stand-in so tests don't crash trying to open a real socket.
class MockWebSocket {
  static CONNECTING = 0;
  static OPEN = 1;
  static CLOSING = 2;
  static CLOSED = 3;
  readyState = MockWebSocket.CONNECTING;
  onopen: (() => void) | null = null;
  onmessage: ((event: MessageEvent) => void) | null = null;
  onclose: (() => void) | null = null;
  onerror: (() => void) | null = null;
  send() {}
  close() {
    this.readyState = MockWebSocket.CLOSED;
    this.onclose?.();
  }
}

// @ts-expect-error -- intentionally replacing the global for tests
window.WebSocket = MockWebSocket;
