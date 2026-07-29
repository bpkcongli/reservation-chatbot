import type { SendMessageRequest } from "@/domain/conversation/interfaces/requests/send-message-request";
import type { ConversationResponse } from "@/domain/conversation/interfaces/responses/conversation-response";

export interface IConversationService {
  createConversation(): Promise<ConversationResponse>;
  getConversation(conversationId: string): Promise<ConversationResponse>;
  sendMessage(
    conversationId: string,
    request: SendMessageRequest,
  ): Promise<ConversationResponse>;
}
