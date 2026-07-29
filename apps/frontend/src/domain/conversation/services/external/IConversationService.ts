import type { ConversationResponse } from "@/domain/conversation/interfaces/responses/conversation-response";

export interface IConversationService {
  createConversation(): Promise<ConversationResponse>;
}
