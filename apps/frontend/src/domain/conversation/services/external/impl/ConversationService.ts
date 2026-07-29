import { inject, injectable } from "inversify";

import type { CreateConversationRequest } from "@/domain/conversation/interfaces/requests/create-conversation-request";
import {
  sendMessageRequestSchema,
  type SendMessageRequest,
} from "@/domain/conversation/interfaces/requests/send-message-request";
import {
  attachmentUploadResponseSchema,
  conversationIdSchema,
  conversationResponseSchema,
  type AttachmentUploadResponse,
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

  async getConversation(conversationId: string): Promise<ConversationResponse> {
    const validConversationId = conversationIdSchema.parse(conversationId);
    const response = await this.httpClient.request<ConversationResponse>({
      path: `/conversations/${validConversationId}`,
      method: "GET",
    });

    return conversationResponseSchema.parse(response.data);
  }

  async sendMessage(
    conversationId: string,
    request: SendMessageRequest,
  ): Promise<ConversationResponse> {
    const validConversationId = conversationIdSchema.parse(conversationId);
    const validRequest = sendMessageRequestSchema.parse(request);
    const response = await this.httpClient.request<
      ConversationResponse,
      SendMessageRequest
    >({
      path: `/conversations/${validConversationId}/messages`,
      method: "POST",
      body: validRequest,
    });

    return conversationResponseSchema.parse(response.data);
  }

  async uploadAttachment(
    conversationId: string,
    file: File,
  ): Promise<AttachmentUploadResponse> {
    const validConversationId = conversationIdSchema.parse(conversationId);
    const body = new FormData();
    body.append("file", file);
    const response = await this.httpClient.request<
      AttachmentUploadResponse,
      FormData
    >({
      path: `/conversations/${validConversationId}/attachments`,
      method: "POST",
      body,
      headers: { "Content-Type": "multipart/form-data" },
    });

    return attachmentUploadResponseSchema.parse(response.data);
  }
}
