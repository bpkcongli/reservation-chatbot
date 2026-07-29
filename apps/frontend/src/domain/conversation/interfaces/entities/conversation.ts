export type ConversationState = "WELCOME";

export interface ChatMessage {
  id: string;
  sender: "bot" | "user";
  text: string;
  createdAt: string;
}

export interface QuickReply {
  label: string;
  value: string;
}
