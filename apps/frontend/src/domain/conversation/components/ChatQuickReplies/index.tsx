import type { QuickReply } from "@/domain/conversation/interfaces/entities/conversation";

interface ChatQuickRepliesProps {
  replies: QuickReply[];
  onSelect(reply: QuickReply): void;
}

export default function ChatQuickReplies({
  replies,
  onSelect,
}: Readonly<ChatQuickRepliesProps>) {
  if (replies.length === 0) {
    return null;
  }

  return (
    <div
      role="group"
      aria-label="Pilihan jawaban cepat"
      className="ml-10 flex flex-wrap gap-2"
    >
      {replies.map((reply) => (
        <button
          key={reply.value}
          type="button"
          onClick={() => onSelect(reply)}
          className="rounded-full border border-[#a8c6bb] bg-white px-3.5 py-2 text-left text-xs leading-4 font-bold text-[#245c4b] transition hover:border-[#1d5949] hover:bg-[#edf4f0] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#1d5949]"
        >
          {reply.label}
        </button>
      ))}
    </div>
  );
}
