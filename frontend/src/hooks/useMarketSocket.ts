import { useEffect, useState } from "react";
import { marketSocketManager, type ConnectionStatus, type QuoteMessage } from "@/api/marketSocket";

interface MarketSocketState {
  quote: QuoteMessage["data"] | null;
  status: ConnectionStatus;
}

/** Subscribes to live (polling-interval) quote pushes for one ticker over
 * the shared WebSocket connection. Multiple components can call this with
 * the same ticker without causing duplicate server-side subscriptions. */
export function useMarketSocket(ticker: string): MarketSocketState {
  const [quote, setQuote] = useState<QuoteMessage["data"] | null>(null);
  const [status, setStatus] = useState<ConnectionStatus>(marketSocketManager.getStatus());

  useEffect(() => {
    const unsubscribeStatus = marketSocketManager.onStatusChange(setStatus);
    return unsubscribeStatus;
  }, []);

  useEffect(() => {
    setQuote(null);
    if (!ticker) return;
    const unsubscribe = marketSocketManager.subscribe(ticker, (message) => {
      setQuote(message.data);
    });
    return unsubscribe;
  }, [ticker]);

  return { quote, status };
}
