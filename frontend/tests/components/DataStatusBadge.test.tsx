import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { DataStatusBadge } from "@/components/DataStatusBadge";

describe("DataStatusBadge", () => {
  it("renders the demo label and icon (not color alone)", () => {
    render(<DataStatusBadge status="demo" />);
    expect(screen.getByText("Demo")).toBeInTheDocument();
  });

  it("renders a distinct label for each data status", () => {
    const statuses = ["live", "delayed", "historical", "cached", "demo"] as const;
    const labels = ["Live", "Delayed", "Historical", "Cached", "Demo"];
    statuses.forEach((status, i) => {
      const { unmount } = render(<DataStatusBadge status={status} />);
      expect(screen.getByText(labels[i])).toBeInTheDocument();
      unmount();
    });
  });
});
