import { describe, expect, it, vi } from "vitest";

import {
  attachmentUploadResponseSchema,
  conversationResponseSchema,
} from "@/domain/conversation/interfaces/responses/conversation-response";
import type { IConversationService } from "@/domain/conversation/services/external";
import { HttpClientError } from "@/general/adapters/http-client";
import type { Storage } from "@/general/adapters/storage";
import {
  createConversationMockResponse,
  createSendMessageMockResponse,
  restoreConversationMockResponse,
} from "@/general/mocks/handlers";

import ChatWidgetStore, { CONVERSATION_STORAGE_KEY } from "./ChatWidgetStore";

describe("ChatWidgetStore", () => {
  function createStore() {
    const createConversation =
      vi.fn<IConversationService["createConversation"]>();
    const getConversation = vi.fn<IConversationService["getConversation"]>();
    const sendMessage = vi.fn<IConversationService["sendMessage"]>();
    const uploadAttachment = vi.fn<IConversationService["uploadAttachment"]>();
    const service: IConversationService = {
      createConversation,
      getConversation,
      sendMessage,
      uploadAttachment,
    };
    const items = new Map<string, string>();
    const storage: Storage = {
      getItem: vi.fn((key: string) => items.get(key) ?? null),
      removeItem: vi.fn((key: string) => items.delete(key)),
      setItem: vi.fn((key: string, value: string) => items.set(key, value)),
    };
    const store = new ChatWidgetStore(service, storage);

    return {
      createConversation,
      getConversation,
      items,
      sendMessage,
      storage,
      store,
      uploadAttachment,
    };
  }

  it("creates and persists a conversation when no session exists", async () => {
    const { createConversation, items, store } = createStore();
    createConversation.mockResolvedValue(
      conversationResponseSchema.parse(createConversationMockResponse),
    );

    await store.initializeConversation();

    expect(store.messages).toHaveLength(1);
    expect(store.quickReplies).toHaveLength(2);
    expect(store.conversationId).toBe("01K1A2B3C4D5E6F7G8H9J0K1M2");
    expect(items.get(CONVERSATION_STORAGE_KEY)).toBe(store.conversationId);
  });

  it("restores a persisted conversation instead of creating another", async () => {
    const { createConversation, getConversation, items, store } = createStore();
    items.set(
      CONVERSATION_STORAGE_KEY,
      createConversationMockResponse.data.conversation_id,
    );
    getConversation.mockResolvedValue(
      conversationResponseSchema.parse(restoreConversationMockResponse),
    );

    await store.initializeConversation();

    expect(getConversation).toHaveBeenCalledWith(
      createConversationMockResponse.data.conversation_id,
    );
    expect(createConversation).not.toHaveBeenCalled();
    expect(store.messages).toHaveLength(1);
  });

  it("creates a fresh conversation when the persisted session expired", async () => {
    const { createConversation, getConversation, items, storage, store } =
      createStore();
    items.set(
      CONVERSATION_STORAGE_KEY,
      createConversationMockResponse.data.conversation_id,
    );
    getConversation.mockRejectedValue(
      new HttpClientError("Percakapan kedaluwarsa.", 410),
    );
    createConversation.mockResolvedValue(
      conversationResponseSchema.parse(createConversationMockResponse),
    );

    await store.initializeConversation();

    expect(storage.removeItem).toHaveBeenCalledWith(CONVERSATION_STORAGE_KEY);
    expect(createConversation).toHaveBeenCalledOnce();
    expect(store.conversationId).toBe(
      createConversationMockResponse.data.conversation_id,
    );
  });

  it("sends a quick reply value while displaying its label", async () => {
    const { createConversation, sendMessage, store } = createStore();
    createConversation.mockResolvedValue(
      conversationResponseSchema.parse(createConversationMockResponse),
    );
    sendMessage.mockResolvedValue(
      conversationResponseSchema.parse(
        createSendMessageMockResponse("reservation"),
      ),
    );
    await store.initializeConversation();

    await store.sendQuickReply({
      label: "Langsung reservasi",
      value: "reservation",
    });

    expect(sendMessage).toHaveBeenCalledWith(
      createConversationMockResponse.data.conversation_id,
      expect.objectContaining({ text: "reservation" }),
    );
    expect(store.messages.at(-2)?.text).toBe("Langsung reservasi");
    expect(store.messages.at(-1)?.sender).toBe("bot");
  });

  it("retries a failed send with the same idempotency key", async () => {
    const { createConversation, sendMessage, store } = createStore();
    createConversation.mockResolvedValue(
      conversationResponseSchema.parse(createConversationMockResponse),
    );
    sendMessage
      .mockRejectedValueOnce(new Error("Network error"))
      .mockResolvedValueOnce(
        conversationResponseSchema.parse(
          createSendMessageMockResponse("Butuh tukang listrik"),
        ),
      );
    await store.initializeConversation();
    store.setDraftText("Butuh tukang listrik");

    await store.submitDraft();

    expect(store.errorMessage).toBe(
      "Maaf, pesan belum terkirim. Silakan coba kembali.",
    );
    const firstRequest = sendMessage.mock.calls[0][1];

    await store.retry();

    const retryRequest = sendMessage.mock.calls[1][1];
    expect(retryRequest.client_message_id).toBe(firstRequest.client_message_id);
    expect(store.errorMessage).toBeNull();
    expect(store.messages.at(-1)?.sender).toBe("bot");
  });

  it("uploads a photo and restores the prompt after the attachment turn", async () => {
    const { createConversation, getConversation, store, uploadAttachment } =
      createStore();
    const photoStateResponse = conversationResponseSchema.parse({
      ...createConversationMockResponse,
      data: {
        ...createConversationMockResponse.data,
        state: "HARIAN_ASK_PHOTO",
        quick_replies: [{ label: "Lewati foto", value: "lewati" }],
      },
    });
    const restoredResponse = conversationResponseSchema.parse({
      ...restoreConversationMockResponse,
      data: {
        ...restoreConversationMockResponse.data,
        state: "HARIAN_ASK_ADDRESS",
        messages: [
          ...restoreConversationMockResponse.data.messages,
          {
            id: "01K1A2B3C4D5E6F7G8H9J0K1M4",
            sender: "bot",
            text: "Mohon masukkan alamat pekerjaan.",
            created_at: "2026-07-29T09:01:00+07:00",
          },
        ],
        quick_replies: [],
      },
    });
    createConversation.mockResolvedValue(photoStateResponse);
    uploadAttachment.mockResolvedValue(
      attachmentUploadResponseSchema.parse({
        status: {
          code: 120100000,
          message: "Created.",
          errorDetails: [],
        },
        data: {
          conversation_id: createConversationMockResponse.data.conversation_id,
          attachment: {
            attachment_id: "01K1A2B3C4D5E6F7G8H9J0K1M5",
            content_type: "image/png",
            size_bytes: 128,
            status: "ready",
          },
        },
      }),
    );
    getConversation.mockResolvedValue(restoredResponse);
    await store.initializeConversation();
    const file = new File(["png"], "kendala.png", { type: "image/png" });

    await store.uploadAttachment(file);

    expect(uploadAttachment).toHaveBeenCalledWith(
      createConversationMockResponse.data.conversation_id,
      file,
    );
    expect(getConversation).toHaveBeenCalledWith(
      createConversationMockResponse.data.conversation_id,
    );
    expect(store.state).toBe("HARIAN_ASK_ADDRESS");
    expect(store.messages.at(-1)?.text).toBe(
      "Mohon masukkan alamat pekerjaan.",
    );
    expect(store.attachmentError).toBeNull();
  });

  it("retries only the snapshot refresh when upload already succeeded", async () => {
    const { createConversation, getConversation, store, uploadAttachment } =
      createStore();
    const photoStateResponse = conversationResponseSchema.parse({
      ...createConversationMockResponse,
      data: {
        ...createConversationMockResponse.data,
        state: "HARIAN_ASK_PHOTO",
      },
    });
    const addressStateResponse = conversationResponseSchema.parse({
      ...restoreConversationMockResponse,
      data: {
        ...restoreConversationMockResponse.data,
        state: "HARIAN_ASK_ADDRESS",
      },
    });
    createConversation.mockResolvedValue(photoStateResponse);
    uploadAttachment.mockResolvedValue(
      attachmentUploadResponseSchema.parse({
        status: {
          code: 120100000,
          message: "Created.",
          errorDetails: [],
        },
        data: {
          conversation_id: createConversationMockResponse.data.conversation_id,
          attachment: {
            attachment_id: "01K1A2B3C4D5E6F7G8H9J0K1M5",
            content_type: "image/png",
            size_bytes: 128,
            status: "ready",
          },
        },
      }),
    );
    getConversation
      .mockRejectedValueOnce(new Error("Network error"))
      .mockResolvedValueOnce(addressStateResponse);
    await store.initializeConversation();
    const file = new File(["png"], "kendala.png", { type: "image/png" });

    await store.uploadAttachment(file);
    expect(store.attachmentError).toMatch(/Foto sudah tersimpan/);

    await store.uploadAttachment(file);

    expect(uploadAttachment).toHaveBeenCalledOnce();
    expect(getConversation).toHaveBeenCalledTimes(2);
    expect(store.state).toBe("HARIAN_ASK_ADDRESS");
    expect(store.attachmentError).toBeNull();
  });
});
