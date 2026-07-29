"use client";

import type { IChatWidgetStore } from "@/domain/conversation/services/internal";
import { TYPES } from "@/domain/conversation/services/types";
import { ServiceLocator } from "@/general/services/service-locator";

export function useChatWidgetStore(): IChatWidgetStore {
  return ServiceLocator.getConversationService<IChatWidgetStore>(
    TYPES.ChatWidgetStore,
  );
}
