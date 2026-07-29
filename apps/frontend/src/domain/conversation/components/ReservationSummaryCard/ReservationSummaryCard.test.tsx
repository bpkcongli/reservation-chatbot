import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import ReservationSummaryCard from ".";

describe("ReservationSummaryCard", () => {
  it("keeps a borongan budget separate from the backend estimate", () => {
    render(
      <ReservationSummaryCard
        summary={{
          service_type: "borongan",
          customer_id: "0123456789",
          phone_number_masked: "+62812****7890",
          building_type: "rumah",
          survey_address: "Jalan Mawar No. 20",
          survey_date: "2026-08-02",
          survey_time: "09:00",
          budget: 20_000_000,
        }}
        priceBreakdown={{
          service_type: "borongan",
          pricing_version: "pricing-v1",
          currency: "IDR",
          building_type: "rumah",
          base_price: 5_000_000,
          survey_fee: 100_000,
          subtotal: 5_000_000,
          budget: 20_000_000,
          admin_fee: 25_000,
          estimated_price: 5_125_000,
          disclaimer: "Harga fixed pricing-v1 hanya untuk demonstrasi chatbot.",
        }}
      />,
    );

    expect(
      screen.getByRole("heading", { name: "Ringkasan reservasi" }),
    ).toBeInTheDocument();
    expect(screen.getByText(/20\.000\.000/)).toBeInTheDocument();
    expect(screen.getByText(/5\.125\.000/)).toBeInTheDocument();
    expect(
      screen.getByText(/tidak digunakan untuk menghitung/i),
    ).toBeInTheDocument();
  });
});
