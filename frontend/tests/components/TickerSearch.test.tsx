import { describe, expect, it, vi, beforeEach } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { renderWithProviders } from "../testUtils";
import { TickerSearch } from "@/components/TickerSearch";
import { api } from "@/api/endpoints";

vi.mock("@/api/endpoints", () => ({
  api: {
    searchInstruments: vi.fn(),
  },
}));

describe("TickerSearch", () => {
  beforeEach(() => {
    vi.mocked(api.searchInstruments).mockReset();
  });

  it("debounces input and calls the search API with the typed query", async () => {
    vi.mocked(api.searchInstruments).mockResolvedValue([
      { ticker: "AAPL", name: "Apple Inc.", exchange: null, sector: "Technology", is_demo: true },
    ]);
    const user = userEvent.setup();
    const onSelect = vi.fn();
    renderWithProviders(<TickerSearch onSelect={onSelect} />);

    await user.type(screen.getByRole("combobox"), "AAPL");

    await waitFor(() =>
      expect(api.searchInstruments).toHaveBeenCalledWith("AAPL", expect.anything())
    );
    expect(await screen.findByText("AAPL")).toBeInTheDocument();
  });

  it("calls onSelect with the chosen ticker and clears the input", async () => {
    vi.mocked(api.searchInstruments).mockResolvedValue([
      {
        ticker: "MSFT",
        name: "Microsoft Corporation",
        exchange: null,
        sector: null,
        is_demo: true,
      },
    ]);
    const user = userEvent.setup();
    const onSelect = vi.fn();
    renderWithProviders(<TickerSearch onSelect={onSelect} />);

    const input = screen.getByRole("combobox");
    await user.type(input, "MSFT");
    const option = await screen.findByRole("option");
    await user.click(option);

    expect(onSelect).toHaveBeenCalledWith("MSFT");
    expect(input).toHaveValue("");
  });

  it("shows an empty state when no tickers match", async () => {
    vi.mocked(api.searchInstruments).mockResolvedValue([]);
    const user = userEvent.setup();
    renderWithProviders(<TickerSearch onSelect={vi.fn()} />);

    await user.type(screen.getByRole("combobox"), "ZZZ");

    expect(await screen.findByText(/no matching tickers/i)).toBeInTheDocument();
  });
});
