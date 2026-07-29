import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import ApplicationProvider from "@/general/providers/ApplicationProvider";

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

  it("opens and closes the accessible chat panel", () => {
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

    const closeButton = screen.getByRole("button", {
      name: "Tutup asisten reservasi",
    });
    expect(closeButton).toHaveFocus();

    fireEvent.keyDown(document, { key: "Escape" });

    expect(
      screen.queryByRole("dialog", { name: "Asisten Reservasi" }),
    ).not.toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Buka asisten reservasi" }),
    ).toHaveFocus();
  });
});
