import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { BacktestForm } from "@/features/backtesting/BacktestForm";

describe("BacktestForm", () => {
  it("submits with the default valid configuration", async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn();
    render(<BacktestForm ticker="AAPL" onSubmit={onSubmit} isSubmitting={false} />);

    await user.click(screen.getByRole("button", { name: /run backtest/i }));

    expect(onSubmit).toHaveBeenCalledWith(
      expect.objectContaining({ ticker: "AAPL", prob_threshold: 0.55 })
    );
  });

  it("rejects an exit threshold that is not lower than the entry threshold", async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn();
    render(<BacktestForm ticker="AAPL" onSubmit={onSubmit} isSubmitting={false} />);

    const exitInput = screen.getByLabelText(/exit probability/i);
    await user.clear(exitInput);
    await user.type(exitInput, "0.6"); // >= default entry threshold of 0.55

    await user.click(screen.getByRole("button", { name: /run backtest/i }));

    expect(onSubmit).not.toHaveBeenCalled();
    expect(screen.getByRole("alert")).toHaveTextContent(/lower than the entry threshold/i);
  });

  it("rejects a holding period outside the valid range", async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn();
    render(<BacktestForm ticker="AAPL" onSubmit={onSubmit} isSubmitting={false} />);

    const holdingInput = screen.getByLabelText(/holding period/i);
    await user.clear(holdingInput);
    await user.type(holdingInput, "999");

    await user.click(screen.getByRole("button", { name: /run backtest/i }));

    expect(onSubmit).not.toHaveBeenCalled();
    expect(screen.getByRole("alert")).toHaveTextContent(/between 1 and 60/i);
  });

  it("disables the submit button while submitting", () => {
    render(<BacktestForm ticker="AAPL" onSubmit={vi.fn()} isSubmitting />);
    expect(screen.getByRole("button", { name: /running backtest/i })).toBeDisabled();
  });

  it("does not render the sweep button when onSweep is not provided", () => {
    render(<BacktestForm ticker="AAPL" onSubmit={vi.fn()} isSubmitting={false} />);
    expect(
      screen.queryByRole("button", { name: /compare confidence thresholds/i })
    ).not.toBeInTheDocument();
  });

  it("calls onSweep with the current config when the sweep button is clicked", async () => {
    const user = userEvent.setup();
    const onSweep = vi.fn();
    render(
      <BacktestForm
        ticker="AAPL"
        onSubmit={vi.fn()}
        isSubmitting={false}
        onSweep={onSweep}
        isSweeping={false}
      />
    );

    await user.click(screen.getByRole("button", { name: /compare confidence thresholds/i }));

    expect(onSweep).toHaveBeenCalledWith(expect.objectContaining({ ticker: "AAPL" }));
  });

  it("disables the sweep button while sweeping", () => {
    render(
      <BacktestForm
        ticker="AAPL"
        onSubmit={vi.fn()}
        isSubmitting={false}
        onSweep={vi.fn()}
        isSweeping
      />
    );
    expect(screen.getByRole("button", { name: /comparing thresholds/i })).toBeDisabled();
  });
});
