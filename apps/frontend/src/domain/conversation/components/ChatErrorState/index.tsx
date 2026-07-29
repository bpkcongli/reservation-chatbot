import { AlertTriangle, RotateCw } from "lucide-react";

interface ChatErrorStateProps {
  message: string;
  onRetry(): void;
}

export default function ChatErrorState({
  message,
  onRetry,
}: Readonly<ChatErrorStateProps>) {
  return (
    <div
      role="alert"
      className="rounded-2xl border border-[#efcfbf] bg-[#fff6f0] p-4 text-[#744331]"
    >
      <div className="flex items-start gap-3">
        <span className="grid size-9 shrink-0 place-items-center rounded-xl bg-[#f9dfd1] text-[#b95332]">
          <AlertTriangle className="size-4" aria-hidden="true" />
        </span>
        <div>
          <p className="text-sm leading-5">{message}</p>
          <button
            type="button"
            onClick={onRetry}
            className="mt-3 inline-flex items-center gap-1.5 rounded-md text-xs font-bold text-[#a74429] focus-visible:outline-2 focus-visible:outline-offset-3 focus-visible:outline-[#b95332]"
          >
            <RotateCw className="size-3.5" aria-hidden="true" />
            Coba lagi
          </button>
        </div>
      </div>
    </div>
  );
}
