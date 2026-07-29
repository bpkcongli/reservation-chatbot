import type {
  ChatMessage,
  ConversationState,
  PriceBreakdown,
  QuickReply,
  ReservationSummary,
  Ticket,
} from "@/domain/conversation/interfaces/entities/conversation";

export interface IChatWidgetStore {
  attachmentError: string | null;
  canSend: boolean;
  conversationId: string | null;
  draftText: string;
  errorMessage: string | null;
  isOpen: boolean;
  isUploadingAttachment: boolean;
  isLoading: boolean;
  messages: ChatMessage[];
  priceBreakdown: PriceBreakdown | null;
  quickReplies: QuickReply[];
  reservationSummary: ReservationSummary | null;
  state: ConversationState | null;
  ticket: Ticket | null;

  clearAttachmentError(): void;
  close(): void;
  initializeConversation(): Promise<void>;
  open(): void;
  retry(): Promise<void>;
  sendMessage(text: string, displayText?: string): Promise<void>;
  sendQuickReply(reply: QuickReply): Promise<void>;
  setDraftText(value: string): void;
  submitDraft(): Promise<void>;
  toggle(): void;
  uploadAttachment(file: File): Promise<void>;
}
