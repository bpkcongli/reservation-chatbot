import { fireEvent, render, screen } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { describe, expect, it } from "vitest";

import ApplicationProvider from "@/general/providers/ApplicationProvider";
import { CONVERSATION_STORAGE_KEY } from "@/domain/conversation/services/internal/impl/ChatWidgetStore";
import { createConversationMockResponse } from "@/general/mocks/handlers";
import { server } from "@/general/mocks/server";

import Home from "./page";

describe("Home", () => {
  function renderHome() {
    return render(
      <ApplicationProvider>
        <Home />
      </ApplicationProvider>,
    );
  }

  it("renders the landing page sections and service choices", () => {
    renderHome();

    expect(
      screen.getByRole("heading", {
        name: /Rumah nyaman dimulai di sini/i,
      }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Jasa Borongan" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Tukang Harian" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", {
        name: "Dari cerita singkat menjadi reservasi.",
      }),
    ).toBeInTheDocument();
  });

  it("opens and closes the accessible chat panel", async () => {
    renderHome();

    const launcher = screen.getByRole("button", {
      name: "Buka asisten reservasi",
    });
    launcher.focus();
    fireEvent.click(launcher);

    const dialog = screen.getByRole("dialog", {
      name: "Asisten Reservasi",
    });
    expect(dialog).toBeInTheDocument();
    expect(dialog).toHaveAttribute("aria-modal", "true");
    expect(document.body).toHaveStyle({ overflow: "hidden" });

    const closeButton = screen.getByRole("button", {
      name: "Tutup asisten reservasi",
    });
    expect(closeButton).toHaveFocus();
    expect(
      await screen.findByText(/Selamat datang di layanan reservasi tukang/i),
    ).toBeInTheDocument();

    fireEvent.keyDown(document, { key: "Escape" });

    expect(
      screen.queryByRole("dialog", { name: "Asisten Reservasi" }),
    ).not.toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Buka asisten reservasi" }),
    ).toHaveFocus();
    expect(document.body).not.toHaveStyle({ overflow: "hidden" });
  });

  it("keeps keyboard focus inside the open dialog", async () => {
    renderHome();
    fireEvent.click(
      screen.getByRole("button", { name: "Buka asisten reservasi" }),
    );
    await screen.findByText(/Selamat datang di layanan reservasi tukang/i);

    const closeButton = screen.getByRole("button", {
      name: "Tutup asisten reservasi",
    });
    const composer = screen.getByRole("textbox", { name: "Pesan" });
    closeButton.focus();

    fireEvent.keyDown(document, { key: "Tab", shiftKey: true });
    expect(composer).toHaveFocus();

    fireEvent.keyDown(document, { key: "Tab" });
    expect(closeButton).toHaveFocus();
  });

  it("sends an initial quick reply and renders the next turn", async () => {
    renderHome();

    fireEvent.click(
      screen.getByRole("button", { name: "Buka asisten reservasi" }),
    );

    expect(
      screen.getByRole("status", { name: "Asisten sedang mengetik" }),
    ).toBeInTheDocument();

    const reservationReply = await screen.findByRole("button", {
      name: "Langsung reservasi",
    });
    expect(
      screen.getByRole("button", {
        name: "Tanya-tanya dulu layanan tukang",
      }),
    ).toBeInTheDocument();

    fireEvent.click(reservationReply);

    expect(
      await screen.findByText(/Baik, mari mulai reservasi/i),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("article", { name: /Pesan Anda pukul/i }),
    ).toHaveTextContent("Langsung reservasi");
    expect(screen.getByRole("textbox", { name: "Pesan" })).toHaveValue("");
    expect(
      screen.getByRole("button", { name: "Jasa Borongan" }),
    ).toBeInTheDocument();
  });

  it("sends a typed message through the composer", async () => {
    renderHome();
    fireEvent.click(
      screen.getByRole("button", { name: "Buka asisten reservasi" }),
    );
    await screen.findByText(/Selamat datang di layanan reservasi tukang/i);

    const composer = screen.getByRole("textbox", { name: "Pesan" });
    fireEvent.change(composer, {
      target: { value: "Butuh tukang listrik" },
    });
    const sendButton = screen.getByRole("button", { name: "Kirim pesan" });
    expect(sendButton).toBeEnabled();
    fireEvent.click(sendButton);

    expect(
      await screen.findByText(/Silakan ceritakan kebutuhan layanan tukang/i),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("article", { name: /Pesan Anda pukul/i }),
    ).toHaveTextContent("Butuh tukang listrik");
  });

  it("restores a persisted conversation instead of creating a new one", async () => {
    let createRequests = 0;
    let restoreRequests = 0;
    window.localStorage.setItem(
      CONVERSATION_STORAGE_KEY,
      createConversationMockResponse.data.conversation_id,
    );
    server.use(
      http.post("*/conversations", () => {
        createRequests += 1;
        return HttpResponse.json(createConversationMockResponse, {
          status: 201,
        });
      }),
      http.get("*/conversations/:conversationId", () => {
        restoreRequests += 1;
        return HttpResponse.json({
          ...createConversationMockResponse,
          status: {
            code: 120000000,
            message: "Success.",
            errorDetails: [],
          },
        });
      }),
    );
    renderHome();

    fireEvent.click(
      screen.getByRole("button", { name: "Buka asisten reservasi" }),
    );

    expect(
      await screen.findByText(/Selamat datang di layanan reservasi tukang/i),
    ).toBeInTheDocument();
    expect(restoreRequests).toBe(1);
    expect(createRequests).toBe(0);
  });

  it("renders a friendly error and retries the initial prompt", async () => {
    let shouldFail = true;
    server.use(
      http.post("*/conversations", () => {
        if (shouldFail) {
          return HttpResponse.json(
            {
              status: {
                code: 150300001,
                message: "Layanan belum siap.",
                errorDetails: [],
              },
            },
            { status: 503 },
          );
        }

        return HttpResponse.json(createConversationMockResponse, {
          status: 201,
        });
      }),
    );
    renderHome();

    fireEvent.click(
      screen.getByRole("button", { name: "Buka asisten reservasi" }),
    );

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Maaf, percakapan belum dapat disiapkan. Silakan coba kembali.",
    );

    shouldFail = false;
    fireEvent.click(screen.getByRole("button", { name: "Coba lagi" }));

    expect(
      await screen.findByText(/Selamat datang di layanan reservasi tukang/i),
    ).toBeInTheDocument();
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });
});
