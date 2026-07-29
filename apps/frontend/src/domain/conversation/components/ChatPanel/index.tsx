import { ArrowUp, Bot, LockKeyhole, X } from "lucide-react";
import { useEffect, useRef, type Ref } from "react";

import ChatErrorState from "@/domain/conversation/components/ChatErrorState";
import ChatMessageBubble from "@/domain/conversation/components/ChatMessageBubble";
import ChatQuickReplies from "@/domain/conversation/components/ChatQuickReplies";
import ChatTypingIndicator from "@/domain/conversation/components/ChatTypingIndicator";
import type {
  ChatMessage,
  QuickReply,
} from "@/domain/conversation/interfaces/entities/conversation";

interface ChatPanelProps {
  canSend: boolean;
  closeButtonRef: Ref<HTMLButtonElement>;
  draftText: string;
  errorMessage: string | null;
  isLoading: boolean;
  messages: ChatMessage[];
  quickReplies: QuickReply[];
  onClose(): void;
  onDraftChange(value: string): void;
  onQuickReply(reply: QuickReply): void;
  onRetry(): void;
  onSend(): void;
}

export default function ChatPanel({
  canSend,
  closeButtonRef,
  draftText,
  errorMessage,
  isLoading,
  messages,
  quickReplies,
  onClose,
  onDraftChange,
  onQuickReply,
  onRetry,
  onSend,
}: Readonly<ChatPanelProps>) {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView?.({
      behavior: "smooth",
      block: "nearest",
    });
  }, [isLoading, messages, quickReplies]);

  return (
    <>
      <button
        type="button"
        aria-label="Tutup panel chat"
        tabIndex={-1}
        onClick={onClose}
        className="fixed inset-0 z-40 bg-[#0b2821]/35 backdrop-blur-[2px] sm:hidden"
      />

      <section
        id="reservation-chat-panel"
        role="dialog"
        aria-labelledby="chat-panel-title"
        aria-describedby="chat-panel-description"
        className="chat-panel-enter fixed inset-0 z-50 flex flex-col overflow-hidden bg-[#fbfaf6] shadow-2xl sm:inset-auto sm:right-7 sm:bottom-24 sm:h-[min(670px,calc(100vh-8rem))] sm:w-[410px] sm:rounded-[28px] sm:border sm:border-[#dce4de]"
      >
        <header className="relative overflow-hidden bg-[#173f35] px-5 pt-5 pb-6 text-white">
          <div
            aria-hidden="true"
            className="absolute -top-12 -right-12 size-36 rounded-full border-[24px] border-white/5"
          />
          <div className="relative flex items-center gap-3">
            <span className="grid size-11 shrink-0 place-items-center rounded-2xl bg-white/12">
              <Bot className="size-6" aria-hidden="true" />
            </span>
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-2">
                <h2 id="chat-panel-title" className="font-bold tracking-tight">
                  Asisten Reservasi
                </h2>
                <span
                  className="size-2 rounded-full bg-[#7dd5a7]"
                  aria-hidden
                />
              </div>
              <p className="mt-0.5 text-xs text-white/70">
                Siap membantu memilih layanan
              </p>
            </div>
            <button
              ref={closeButtonRef}
              type="button"
              onClick={onClose}
              aria-label="Tutup asisten reservasi"
              className="grid size-10 place-items-center rounded-full text-white/80 transition hover:bg-white/10 hover:text-white focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white"
            >
              <X className="size-5" aria-hidden="true" />
            </button>
          </div>
        </header>

        <p id="chat-panel-description" className="sr-only">
          Percakapan dengan asisten untuk informasi layanan dan reservasi
          tukang.
        </p>

        <div className="flex flex-1 flex-col overflow-y-auto bg-[#f7f6f1] px-4 py-5">
          <div
            aria-live="polite"
            aria-relevant="additions"
            className="space-y-4"
          >
            {messages.map((message) => (
              <ChatMessageBubble key={message.id} message={message} />
            ))}

            {isLoading && <ChatTypingIndicator />}

            {errorMessage && (
              <ChatErrorState message={errorMessage} onRetry={onRetry} />
            )}

            {!isLoading && !errorMessage && (
              <ChatQuickReplies
                replies={quickReplies}
                onSelect={onQuickReply}
              />
            )}

            {!isLoading && !errorMessage && messages.length > 0 && (
              <div className="flex items-center justify-center gap-1.5 pt-2 text-[10px] font-medium text-[#89958f]">
                <LockKeyhole className="size-3" aria-hidden="true" />
                Data sensitif tidak ditampilkan secara penuh
              </div>
            )}

            <div ref={messagesEndRef} aria-hidden="true" />
          </div>
        </div>

        <footer className="border-t border-[#e1e5e1] bg-white p-4">
          <form
            onSubmit={(event) => {
              event.preventDefault();
              onSend();
            }}
            className="flex items-end gap-2 rounded-2xl border border-[#d7dfda] bg-[#f5f5f1] p-2 pl-4 focus-within:border-[#89aa9e] focus-within:ring-2 focus-within:ring-[#dce9e4]"
          >
            <textarea
              aria-label="Pesan"
              value={draftText}
              onChange={(event) => onDraftChange(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter" && !event.shiftKey) {
                  event.preventDefault();
                  onSend();
                }
              }}
              rows={1}
              maxLength={1_000}
              disabled={isLoading || Boolean(errorMessage)}
              placeholder="Ketik kebutuhan Anda..."
              className="max-h-20 min-h-10 flex-1 resize-none bg-transparent py-2 text-sm leading-6 text-[#52655e] outline-none placeholder:text-[#89948f] disabled:cursor-not-allowed"
            />
            <button
              type="submit"
              disabled={!canSend}
              aria-label="Kirim pesan"
              className="grid size-10 shrink-0 place-items-center rounded-xl bg-[#1d5949] text-white transition hover:bg-[#16483b] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#1d5949] disabled:cursor-not-allowed disabled:bg-[#dfe4e1] disabled:text-[#9aa49f]"
            >
              <ArrowUp className="size-4" aria-hidden="true" />
            </button>
          </form>
          <p className="mt-2 text-center text-[11px] text-[#8b9691]">
            Asisten memberikan estimasi demo, bukan harga pasar.
          </p>
        </footer>
      </section>
    </>
  );
}
