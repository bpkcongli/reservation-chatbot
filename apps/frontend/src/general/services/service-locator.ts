import type { Container } from "inversify";

import { TYPES } from "@/general/services/types";

export class ServiceLocator {
  private static mainContainer: Container | undefined;

  static setMainContainer(container: Container): void {
    this.mainContainer = container;
  }

  static getMainContainer(): Container {
    if (!this.mainContainer) {
      throw new Error("Dependency container belum diinisialisasi.");
    }

    return this.mainContainer;
  }

  static getConversationContainer(): Container {
    return this.getMainContainer().get<Container>(TYPES.ConversationContainer);
  }

  static getConversationService<T>(identifier: symbol): T {
    return this.getConversationContainer().get<T>(identifier);
  }
}
