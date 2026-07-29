import { injectable } from "inversify";
import { action, makeObservable, observable } from "mobx";

import type { IChatWidgetStore } from "@/domain/conversation/services/internal/IChatWidgetStore";

@injectable()
export default class ChatWidgetStore implements IChatWidgetStore {
  @observable isOpen = false;

  constructor() {
    makeObservable(this);

    this.close = this.close.bind(this);
    this.open = this.open.bind(this);
    this.toggle = this.toggle.bind(this);
  }

  @action close(): void {
    this.isOpen = false;
  }

  @action open(): void {
    this.isOpen = true;
  }

  @action toggle(): void {
    this.isOpen = !this.isOpen;
  }
}
