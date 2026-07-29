import { inject, injectable } from "inversify";
import {
  action,
  computed,
  makeObservable,
  observable,
  runInAction,
} from "mobx";

import type {
  ChatMessage,
  ConversationState,
  PriceBreakdown,
  QuickReply,
  ReservationSummary,
  Ticket,
} from "@/domain/conversation/interfaces/entities/conversation";
import { sendMessageRequestSchema } from "@/domain/conversation/interfaces/requests/send-message-request";
import {
  conversationIdSchema,
  type ConversationResponse,
} from "@/domain/conversation/interfaces/responses/conversation-response";
import type { IConversationService } from "@/domain/conversation/services/external";
import type { IChatWidgetStore } from "@/domain/conversation/services/internal/IChatWidgetStore";
import { TYPES } from "@/domain/conversation/services/types";
import { HttpClientError } from "@/general/adapters/http-client";
import type { Storage } from "@/general/adapters/storage";
import { TYPES as GENERAL_TYPES } from "@/general/services/types";

export const CONVERSATION_STORAGE_KEY = "reservation-chatbot.conversation-id";

interface PendingTurn {
  clientMessageId: string;
  displayText: string;
  optimisticMessageId: string;
  text: string;
}

function createClientMessageId(): string {
  const uuid = globalThis.crypto?.randomUUID?.();

  if (uuid) {
    return `web-${uuid}`;
  }

  return `web-${Date.now()}-${Math.random().toString(36).slice(2, 12)}`;
}

function normalizeMessages(
  response: ConversationResponse,
  displayText?: string,
): ChatMessage[] {
  let userMessageMapped = false;

  return response.data.messages.map((message) => {
    const shouldUseDisplayText =
      message.sender === "user" && displayText && !userMessageMapped;

    if (shouldUseDisplayText) {
      userMessageMapped = true;
    }

    return {
      id: message.id,
      sender: message.sender,
      text: shouldUseDisplayText ? displayText : message.text,
      createdAt: message.created_at,
    };
  });
}

function attachmentErrorMessage(error: unknown): string {
  if (error instanceof HttpClientError) {
    if (error.status === 413) {
      return "Ukuran foto melebihi batas 5 MB. Silakan pilih foto yang lebih kecil.";
    }
    if (error.status === 415) {
      return "Format atau isi foto belum didukung. Gunakan JPG, PNG, atau WebP.";
    }
    if (error.status === 409) {
      return "Foto tidak dapat ditambahkan pada langkah ini. Silakan lanjutkan percakapan.";
    }
  }

  return "Maaf, foto belum berhasil diunggah. Silakan coba kembali.";
}

@injectable()
export default class ChatWidgetStore implements IChatWidgetStore {
  @observable attachmentError: string | null = null;
  @observable conversationId: string | null = null;
  @observable draftText = "";
  @observable errorMessage: string | null = null;
  @observable isOpen = false;
  @observable isLoading = false;
  @observable isUploadingAttachment = false;
  @observable messages: ChatMessage[] = [];
  @observable priceBreakdown: PriceBreakdown | null = null;
  @observable quickReplies: QuickReply[] = [];
  @observable reservationSummary: ReservationSummary | null = null;
  @observable state: ConversationState | null = null;
  @observable ticket: Ticket | null = null;

  private attachmentNeedsSync = false;
  private pendingTurn: PendingTurn | null = null;

  constructor(
    @inject(TYPES.ConversationService)
    private readonly conversationService: IConversationService,
    @inject(GENERAL_TYPES.Storage)
    private readonly storage: Storage,
  ) {
    makeObservable(this);

    this.clearAttachmentError = this.clearAttachmentError.bind(this);
    this.close = this.close.bind(this);
    this.initializeConversation = this.initializeConversation.bind(this);
    this.open = this.open.bind(this);
    this.retry = this.retry.bind(this);
    this.sendMessage = this.sendMessage.bind(this);
    this.sendQuickReply = this.sendQuickReply.bind(this);
    this.setDraftText = this.setDraftText.bind(this);
    this.submitDraft = this.submitDraft.bind(this);
    this.toggle = this.toggle.bind(this);
    this.uploadAttachment = this.uploadAttachment.bind(this);
  }

  @computed get canSend(): boolean {
    return (
      Boolean(this.conversationId) &&
      !this.isLoading &&
      !this.isUploadingAttachment &&
      !this.errorMessage &&
      this.draftText.trim().length > 0 &&
      this.draftText.trim().length <= 1_000
    );
  }

  @action clearAttachmentError(): void {
    this.attachmentError = null;
  }

  @action close(): void {
    this.isOpen = false;
  }

  @action open(): void {
    this.isOpen = true;

    if (!this.conversationId && !this.isLoading && !this.errorMessage) {
      void this.initializeConversation();
    }
  }

  async initializeConversation(): Promise<void> {
    if (this.isLoading || this.conversationId) {
      return;
    }

    runInAction(() => {
      this.errorMessage = null;
      this.isLoading = true;
    });

    try {
      const storedConversationId = this.storage.getItem(
        CONVERSATION_STORAGE_KEY,
      );
      const parsedConversationId =
        conversationIdSchema.safeParse(storedConversationId);
      let response: ConversationResponse;

      if (parsedConversationId.success) {
        try {
          response = await this.conversationService.getConversation(
            parsedConversationId.data,
          );
        } catch (error) {
          if (
            error instanceof HttpClientError &&
            (error.status === 404 || error.status === 410)
          ) {
            this.storage.removeItem(CONVERSATION_STORAGE_KEY);
            response = await this.conversationService.createConversation();
          } else {
            throw error;
          }
        }
      } else {
        if (storedConversationId) {
          this.storage.removeItem(CONVERSATION_STORAGE_KEY);
        }
        response = await this.conversationService.createConversation();
      }

      this.storage.setItem(
        CONVERSATION_STORAGE_KEY,
        response.data.conversation_id,
      );
      runInAction(() => {
        this.conversationId = response.data.conversation_id;
        this.messages = normalizeMessages(response);
        this.quickReplies = response.data.quick_replies;
        this.priceBreakdown = response.data.price_breakdown;
        this.reservationSummary = response.data.reservation_summary;
        this.state = response.data.state;
        this.ticket = response.data.ticket;
        this.attachmentError = null;
        this.errorMessage = null;
        this.isLoading = false;
      });
    } catch {
      runInAction(() => {
        this.errorMessage =
          "Maaf, percakapan belum dapat disiapkan. Silakan coba kembali.";
        this.isLoading = false;
      });
    }
  }

  async retry(): Promise<void> {
    if (this.pendingTurn) {
      await this.deliverPendingTurn();
      return;
    }

    if (this.conversationId) {
      runInAction(() => {
        this.errorMessage = null;
      });
      return;
    }

    await this.initializeConversation();
  }

  async sendMessage(text: string, displayText = text): Promise<void> {
    if (
      !this.conversationId ||
      this.isLoading ||
      this.isUploadingAttachment ||
      this.pendingTurn
    ) {
      return;
    }

    const clientMessageId = createClientMessageId();
    const request = sendMessageRequestSchema.safeParse({
      client_message_id: clientMessageId,
      text,
    });

    if (!request.success) {
      runInAction(() => {
        this.errorMessage =
          "Pesan perlu berisi 1–1000 karakter. Silakan periksa kembali.";
      });
      return;
    }

    const pendingTurn: PendingTurn = {
      clientMessageId,
      displayText: displayText.trim(),
      optimisticMessageId: `pending-${clientMessageId}`,
      text: request.data.text,
    };
    this.pendingTurn = pendingTurn;

    runInAction(() => {
      this.draftText = "";
      this.errorMessage = null;
      this.isLoading = true;
      this.attachmentError = null;
      this.quickReplies = [];
      this.messages.push({
        id: pendingTurn.optimisticMessageId,
        sender: "user",
        text: pendingTurn.displayText,
        createdAt: new Date().toISOString(),
      });
    });

    await this.deliverPendingTurn();
  }

  async sendQuickReply(reply: QuickReply): Promise<void> {
    await this.sendMessage(reply.value, reply.label);
  }

  @action setDraftText(value: string): void {
    this.draftText = value.slice(0, 1_000);
  }

  async submitDraft(): Promise<void> {
    if (!this.canSend) {
      return;
    }

    await this.sendMessage(this.draftText);
  }

  @action toggle(): void {
    if (this.isOpen) {
      this.close();
      return;
    }

    this.open();
  }

  private async deliverPendingTurn(): Promise<void> {
    const pendingTurn = this.pendingTurn;
    const conversationId = this.conversationId;

    if (!pendingTurn || !conversationId || this.isLoading === false) {
      if (!pendingTurn || !conversationId) {
        return;
      }

      runInAction(() => {
        this.errorMessage = null;
        this.isLoading = true;
      });
    }

    try {
      const response = await this.conversationService.sendMessage(
        conversationId,
        {
          client_message_id: pendingTurn.clientMessageId,
          text: pendingTurn.text,
        },
      );
      const newMessages = normalizeMessages(response, pendingTurn.displayText);

      runInAction(() => {
        const existingMessages = this.messages.filter(
          (message) => message.id !== pendingTurn.optimisticMessageId,
        );
        const newMessageIds = new Set(newMessages.map((message) => message.id));

        this.messages = [
          ...existingMessages.filter(
            (message) => !newMessageIds.has(message.id),
          ),
          ...newMessages,
        ];
        this.quickReplies = response.data.quick_replies;
        this.priceBreakdown = response.data.price_breakdown;
        this.reservationSummary = response.data.reservation_summary;
        this.state = response.data.state;
        this.ticket = response.data.ticket;
        this.errorMessage = null;
        this.isLoading = false;
        this.pendingTurn = null;
      });
    } catch {
      runInAction(() => {
        this.errorMessage = "Maaf, pesan belum terkirim. Silakan coba kembali.";
        this.isLoading = false;
      });
    }
  }

  async uploadAttachment(file: File): Promise<void> {
    const conversationId = this.conversationId;

    if (
      !conversationId ||
      this.state !== "HARIAN_ASK_PHOTO" ||
      this.isLoading ||
      this.isUploadingAttachment
    ) {
      return;
    }

    runInAction(() => {
      this.attachmentError = null;
      this.isUploadingAttachment = true;
    });

    try {
      if (!this.attachmentNeedsSync) {
        await this.conversationService.uploadAttachment(conversationId, file);
        this.attachmentNeedsSync = true;
      }
      const response =
        await this.conversationService.getConversation(conversationId);
      const existingMessages = new Map(
        this.messages.map((message) => [message.id, message]),
      );
      const restoredMessages = normalizeMessages(response).map((message) => {
        const existing = existingMessages.get(message.id);
        return existing?.sender === "user" ? existing : message;
      });

      runInAction(() => {
        this.messages = restoredMessages;
        this.quickReplies = response.data.quick_replies;
        this.priceBreakdown = response.data.price_breakdown;
        this.reservationSummary = response.data.reservation_summary;
        this.state = response.data.state;
        this.ticket = response.data.ticket;
        this.attachmentError = null;
        this.isUploadingAttachment = false;
        this.attachmentNeedsSync = false;
      });
    } catch (error) {
      runInAction(() => {
        this.attachmentError = this.attachmentNeedsSync
          ? "Foto sudah tersimpan, tetapi langkah berikutnya belum termuat. Tekan tombol sekali lagi untuk melanjutkan."
          : attachmentErrorMessage(error);
        this.isUploadingAttachment = false;
      });
    }
  }
}
