import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import Home from "./page";

describe("Home", () => {
  it("renders the project foundation status", () => {
    render(<Home />);

    expect(
      screen.getByRole("heading", { name: "Reservation Chatbot" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Chat hadir pada milestone M4" }),
    ).toBeDisabled();
  });
});
