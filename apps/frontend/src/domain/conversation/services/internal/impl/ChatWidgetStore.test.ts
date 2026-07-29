import { describe, expect, it } from "vitest";

import ChatWidgetStore from "./ChatWidgetStore";

describe("ChatWidgetStore", () => {
  it("manages the launcher and panel visibility", () => {
    const store = new ChatWidgetStore();

    expect(store.isOpen).toBe(false);

    store.open();
    expect(store.isOpen).toBe(true);

    store.close();
    expect(store.isOpen).toBe(false);

    store.toggle();
    expect(store.isOpen).toBe(true);
  });
});
