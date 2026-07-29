import { MessageCircleMore } from "lucide-react";

interface ChatLauncherProps {
  expanded: boolean;
  onClick(): void;
  ref?: React.Ref<HTMLButtonElement>;
}

export default function ChatLauncher({
  expanded,
  onClick,
  ref,
}: Readonly<ChatLauncherProps>) {
  return (
    <button
      ref={ref}
      type="button"
      onClick={onClick}
      aria-controls="reservation-chat-panel"
      aria-expanded={expanded}
      aria-label="Buka asisten reservasi"
      className="chat-launcher group fixed right-4 bottom-4 z-50 flex h-14 items-center gap-3 rounded-full bg-[#173f35] px-4 text-sm font-bold text-white shadow-[0_18px_50px_rgba(16,56,46,0.35)] transition hover:-translate-y-1 hover:bg-[#0f332a] focus-visible:outline-3 focus-visible:outline-offset-4 focus-visible:outline-[#ef6842] sm:right-7 sm:bottom-7 sm:h-16 sm:px-5"
    >
      <span className="relative grid size-9 place-items-center rounded-full bg-white/12">
        <MessageCircleMore className="size-5" aria-hidden="true" />
        <span className="absolute -top-0.5 -right-0.5 size-2.5 rounded-full border-2 border-[#173f35] bg-[#f6a83b]" />
      </span>
      <span className="hidden pr-1 sm:inline">Tanya Asisten</span>
    </button>
  );
}
