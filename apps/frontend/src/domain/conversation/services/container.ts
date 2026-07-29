import type { Container } from "inversify";
import { Container as InversifyContainer } from "inversify";

import type { IConversationService } from "@/domain/conversation/services/external";
import { ConversationService } from "@/domain/conversation/services/external/impl";
import {
  ChatWidgetStore,
  type IChatWidgetStore,
} from "@/domain/conversation/services/internal";
import { TYPES } from "@/domain/conversation/services/types";

export function createConversationContainer(
  parentContainer: Container,
): Container {
  const container = new InversifyContainer({ defaultScope: "Singleton" });
  container.parent = parentContainer;

  container
    .bind<IConversationService>(TYPES.ConversationService)
    .to(ConversationService);
  container.bind<IChatWidgetStore>(TYPES.ChatWidgetStore).to(ChatWidgetStore);

  return container;
}
