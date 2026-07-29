import { createRef } from "react";
import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import ChatPanel from ".";

function renderPanel(overrides: Partial<Parameters<typeof ChatPanel>[0]> = {}) {
  const props: Parameters<typeof ChatPanel>[0] = {
    attachmentError: null,
    canSend: false,
    closeButtonRef: createRef<HTMLButtonElement>(),
    dialogRef: createRef<HTMLElement>(),
    draftText: "",
    errorMessage: null,
    isLoading: false,
    isUploadingAttachment: false,
    messages: [],
    priceBreakdown: null,
    quickReplies: [],
    reservationSummary: null,
    state: "WELCOME",
    ticket: null,
    onClearAttachmentError: vi.fn(),
    onClose: vi.fn(),
    onDraftChange: vi.fn(),
    onQuickReply: vi.fn(),
    onRetry: vi.fn(),
    onSend: vi.fn(),
    onUploadAttachment: vi.fn(async () => undefined),
    ...overrides,
  };

  render(<ChatPanel {...props} />);

  return props;
}

describe("ChatPanel", () => {
  it("renders an actionable empty state when no messages exist", () => {
    renderPanel();

    expect(screen.getByRole("status")).toHaveTextContent("Belum ada pesan");
    expect(screen.getByRole("textbox", { name: "Pesan" })).toBeEnabled();
  });

  it("renders a blocking error with retry and disables the composer", () => {
    const onRetry = vi.fn();
    renderPanel({
      errorMessage: "Percakapan belum dapat dimuat.",
      onRetry,
    });

    expect(screen.getByRole("alert")).toHaveTextContent(
      "Percakapan belum dapat dimuat.",
    );
    expect(screen.queryByText("Belum ada pesan")).not.toBeInTheDocument();
    expect(screen.getByRole("textbox", { name: "Pesan" })).toBeDisabled();

    fireEvent.click(screen.getByRole("button", { name: "Coba lagi" }));
    expect(onRetry).toHaveBeenCalledOnce();
  });

  it("shows the backend summary, price, and confirmation choices together", () => {
    const onQuickReply = vi.fn();
    renderPanel({
      messages: [
        {
          id: "message-bot",
          sender: "bot",
          text: "Silakan periksa ringkasan reservasi.",
          createdAt: "2026-07-29T09:00:00+07:00",
        },
      ],
      state: "CONFIRM_RESERVATION",
      reservationSummary: {
        service_type: "borongan",
        customer_id: "0123456789",
        phone_number_masked: "+62812****7890",
        building_type: "rumah",
        survey_address: "Jalan Melati No. 10 Jakarta",
        survey_date: "2026-08-02",
        survey_time: "09:00",
        budget: 20_000_000,
      },
      priceBreakdown: {
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
        disclaimer: "Harga fixed hanya untuk demonstrasi chatbot.",
      },
      quickReplies: [
        { label: "Ya, konfirmasi", value: "ya" },
        { label: "Ubah data", value: "ubah" },
      ],
      onQuickReply,
    });

    expect(
      screen.getByRole("heading", { name: "Ringkasan reservasi" }),
    ).toBeInTheDocument();
    expect(screen.getByText(/5\.125\.000/)).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Ya, konfirmasi" }));
    expect(onQuickReply).toHaveBeenCalledWith({
      label: "Ya, konfirmasi",
      value: "ya",
    });
  });

  it("submits Enter while preserving Shift+Enter for a new line", () => {
    const onSend = vi.fn();
    renderPanel({
      canSend: true,
      draftText: "Butuh tukang",
      onSend,
    });
    const composer = screen.getByRole("textbox", { name: "Pesan" });

    fireEvent.keyDown(composer, { key: "Enter", shiftKey: true });
    expect(onSend).not.toHaveBeenCalled();

    fireEvent.keyDown(composer, { key: "Enter" });
    expect(onSend).toHaveBeenCalledOnce();
  });
});
