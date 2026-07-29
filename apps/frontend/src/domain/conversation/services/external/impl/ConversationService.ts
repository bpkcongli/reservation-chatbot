import { inject, injectable } from "inversify";

import type { CreateConversationRequest } from "@/domain/conversation/interfaces/requests/create-conversation-request";
import {
  conversationResponseSchema,
  type ConversationResponse,
} from "@/domain/conversation/interfaces/responses/conversation-response";
import type { IConversationService } from "@/domain/conversation/services/external";
import type { HttpClient } from "@/general/adapters/http-client";
import { TYPES as GENERAL_TYPES } from "@/general/services/types";

@injectable()
export default class ConversationService implements IConversationService {
  constructor(
    @inject(GENERAL_TYPES.HttpClient)
    private readonly httpClient: HttpClient,
  ) {}

  async createConversation(): Promise<ConversationResponse> {
    const response = await this.httpClient.request<
      ConversationResponse,
      CreateConversationRequest
    >({
      path: "/conversations",
      method: "POST",
      body: { locale: "id-ID" },
    });

    return conversationResponseSchema.parse(response.data);
  }
}
