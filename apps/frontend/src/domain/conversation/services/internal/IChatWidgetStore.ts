import type {
  ChatMessage,
  QuickReply,
} from "@/domain/conversation/interfaces/entities/conversation";

export interface IChatWidgetStore {
  canSend: boolean;
  conversationId: string | null;
  draftText: string;
  errorMessage: string | null;
  isOpen: boolean;
  isLoading: boolean;
  messages: ChatMessage[];
  quickReplies: QuickReply[];

  close(): void;
  initializeConversation(): Promise<void>;
  open(): void;
  retry(): Promise<void>;
  sendMessage(text: string, displayText?: string): Promise<void>;
  sendQuickReply(reply: QuickReply): Promise<void>;
  setDraftText(value: string): void;
  submitDraft(): Promise<void>;
  toggle(): void;
}
