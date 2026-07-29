import { injectable } from "inversify";

import type { Storage } from "@/general/adapters/storage";

@injectable()
export default class BrowserStorage implements Storage {
  getItem(key: string): string | null {
    if (typeof window === "undefined") {
      return null;
    }

    try {
      return window.localStorage.getItem(key);
    } catch {
      return null;
    }
  }

  removeItem(key: string): void {
    if (typeof window === "undefined") {
      return;
    }

    try {
      window.localStorage.removeItem(key);
    } catch {
      // Storage may be unavailable in privacy-restricted browser contexts.
    }
  }

  setItem(key: string, value: string): void {
    if (typeof window === "undefined") {
      return;
    }

    try {
      window.localStorage.setItem(key, value);
    } catch {
      // The active chat remains usable even when persistence is unavailable.
    }
  }
}
