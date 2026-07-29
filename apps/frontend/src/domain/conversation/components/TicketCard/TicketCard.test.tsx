import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import TicketCard from ".";

const writeText = vi.fn(async () => undefined);

describe("TicketCard", () => {
  beforeEach(() => {
    writeText.mockClear();
    Object.defineProperty(navigator, "clipboard", {
      configurable: true,
      value: { writeText },
    });
  });

  it("copies the ticket number and labels simulated email delivery", async () => {
    render(
      <TicketCard
        ticket={{
          ticket_number: "TKT-20260729-AB12CD",
          service_type: "harian",
          status: "MENUNGGU_PEMBAYARAN",
          pricing_version: "pricing-v1",
          estimated_price: 805_000,
          budget: null,
          created_at: "2026-07-29T09:00:00+07:00",
          email_delivery: "NOT_IMPLEMENTED",
        }}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Salin nomor tiket" }));

    expect(writeText).toHaveBeenCalledWith("TKT-20260729-AB12CD");
    await waitFor(() =>
      expect(screen.getByText("Tersalin")).toBeInTheDocument(),
    );
    expect(
      screen.getByText(/email masih berupa simulasi/i),
    ).toBeInTheDocument();
  });
});
