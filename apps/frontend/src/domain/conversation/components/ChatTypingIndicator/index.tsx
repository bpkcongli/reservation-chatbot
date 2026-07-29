import { Bot } from "lucide-react";

export default function ChatTypingIndicator() {
  return (
    <div
      role="status"
      aria-live="polite"
      aria-label="Asisten sedang mengetik"
      className="flex items-end gap-2.5"
    >
      <span className="grid size-8 shrink-0 place-items-center rounded-xl bg-[#dfeae4] text-[#245c4b]">
        <Bot className="size-4" aria-hidden="true" />
      </span>
      <span className="flex h-11 items-center gap-1 rounded-[18px] rounded-bl-md border border-[#e1e6e2] bg-white px-4 shadow-sm">
        {[0, 1, 2].map((index) => (
          <span
            key={index}
            aria-hidden="true"
            className="typing-dot size-1.5 rounded-full bg-[#719086]"
            style={{ animationDelay: `${index * 140}ms` }}
          />
        ))}
      </span>
      <span className="sr-only">Asisten sedang menyiapkan balasan.</span>
    </div>
  );
}
