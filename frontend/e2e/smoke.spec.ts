import { expect, test } from "@playwright/test";

// End-to-end smoke test against the real backend running in DEMO_MODE=true.
// Deliberately covers the exact recruiter demo path called out in the
// project's README/PLAN: launch -> pick a ticker -> see charts -> run a
// backtest -> ask the assistant a question.

test("full demo walkthrough: landing -> dashboard -> backtest -> assistant", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: /real-time stock sentiment/i })).toBeVisible();

  await page.getByRole("link", { name: /launch dashboard/i }).click();
  await expect(page).toHaveURL(/\/dashboard/);

  // Market overview cards should load with a demo-labeled quote.
  await expect(page.getByText("Demo").first()).toBeVisible({ timeout: 15_000 });
  await expect(page.getByText(/price & volume/i)).toBeVisible();

  // The prediction card trains a real model on first load — allow generous time.
  await expect(page.getByText(/next-day direction estimate/i)).toBeVisible({ timeout: 30_000 });

  // Switch ticker via the watchlist search box.
  const searchBox = page.getByRole("combobox", { name: /search stocks/i });
  await searchBox.fill("MSFT");
  await page.getByRole("option", { name: /MSFT/i }).click();
  await expect(page.getByRole("heading", { name: "MSFT", exact: true })).toBeVisible();

  // Backtesting page: run with defaults and see real results.
  await page.getByRole("link", { name: "Backtesting" }).click();
  await expect(page).toHaveURL(/\/backtesting/);
  await page.getByRole("button", { name: /run backtest/i }).click();
  await expect(page.getByText(/hypothetical results/i)).toBeVisible();
  await expect(page.getByText("Total return")).toBeVisible({ timeout: 30_000 });

  // Assistant page: ask a suggested question and see a cited answer.
  await page.getByRole("link", { name: "Assistant" }).click();
  await expect(page).toHaveURL(/\/assistant/);
  await page.getByRole("button", { name: /why is this stock moving/i }).click();
  await expect(page.getByText(/not proof of causality/i)).toBeVisible({ timeout: 15_000 });

  // Status page: data-source/methodology transparency.
  await page.getByRole("link", { name: "Status" }).click();
  await expect(page.getByRole("heading", { name: /system status/i })).toBeVisible();
  await expect(page.getByText(/demo/i).first()).toBeVisible();
});

test("backtest form rejects an invalid configuration before hitting the API", async ({ page }) => {
  await page.goto("/backtesting");
  const holdingInput = page.getByLabel(/holding period/i);
  await holdingInput.fill("999");
  await page.getByRole("button", { name: /run backtest/i }).click();
  await expect(page.getByRole("alert")).toContainText(/between 1 and 60/i);
});
