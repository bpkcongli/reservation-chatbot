import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import ChatMessageBubble from ".";

describe("ChatMessageBubble", () => {
  it.each([
    ["bot", "Pesan asisten"],
    ["user", "Pesan Anda"],
  ] as const)("renders a %s bubble with its timestamp", (sender, label) => {
    render(
      <ChatMessageBubble
        message={{
          id: `message-${sender}`,
          sender,
          text: `Pesan dari ${sender}`,
          createdAt: "2026-07-29T09:00:00+07:00",
        }}
      />,
    );

    expect(
      screen.getByRole("article", {
        name: `${label} pukul 09.00`,
      }),
    ).toHaveTextContent(`Pesan dari ${sender}`);
    expect(screen.getByText("09.00")).toBeInTheDocument();
  });
});
