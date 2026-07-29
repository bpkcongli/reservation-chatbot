import { Bot, CheckCheck } from "lucide-react";

import type { ChatMessage } from "@/domain/conversation/interfaces/entities/conversation";

interface ChatMessageBubbleProps {
  message: ChatMessage;
}

function formatMessageTime(value: string): string {
  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return "--.--";
  }

  return new Intl.DateTimeFormat("id-ID", {
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
    timeZone: "Asia/Jakarta",
  })
    .format(date)
    .replace(":", ".");
}

export default function ChatMessageBubble({
  message,
}: Readonly<ChatMessageBubbleProps>) {
  const isBot = message.sender === "bot";
  const time = formatMessageTime(message.createdAt);

  return (
    <article
      aria-label={`${isBot ? "Pesan asisten" : "Pesan Anda"} pukul ${time}`}
      className={`flex items-end gap-2.5 ${isBot ? "justify-start" : "justify-end"}`}
    >
      {isBot && (
        <span className="grid size-8 shrink-0 place-items-center rounded-xl bg-[#dfeae4] text-[#245c4b]">
          <Bot className="size-4" aria-hidden="true" />
        </span>
      )}

      <div
        className={`max-w-[82%] ${isBot ? "items-start" : "items-end"} flex flex-col`}
      >
        <div
          className={
            isBot
              ? "rounded-[18px] rounded-bl-md border border-[#e1e6e2] bg-white px-4 py-3 text-[#314b43] shadow-sm"
              : "rounded-[18px] rounded-br-md bg-[#1d5949] px-4 py-3 text-white shadow-sm"
          }
        >
          <p className="text-sm leading-6 whitespace-pre-wrap">
            {message.text}
          </p>
        </div>
        <div
          className={`mt-1.5 flex items-center gap-1 px-1 text-[10px] text-[#89958f] ${
            isBot ? "justify-start" : "justify-end"
          }`}
        >
          <time dateTime={message.createdAt}>{time}</time>
          {!isBot && <CheckCheck className="size-3" aria-hidden="true" />}
        </div>
      </div>
    </article>
  );
}
