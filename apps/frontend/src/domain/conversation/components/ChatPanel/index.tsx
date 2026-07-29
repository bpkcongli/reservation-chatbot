import { ArrowUp, Bot, LockKeyhole, MessageCircleMore, X } from "lucide-react";
import type { Ref } from "react";

interface ChatPanelProps {
  closeButtonRef: Ref<HTMLButtonElement>;
  onClose(): void;
}

export default function ChatPanel({
  closeButtonRef,
  onClose,
}: Readonly<ChatPanelProps>) {
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

        <div className="flex flex-1 flex-col overflow-y-auto px-5 py-6">
          <div className="mx-auto my-auto max-w-[300px] text-center">
            <span className="mx-auto grid size-16 place-items-center rounded-[22px] bg-[#e6eee9] text-[#173f35]">
              <MessageCircleMore className="size-7" aria-hidden="true" />
            </span>
            <h3 className="mt-5 text-lg font-bold text-[#173f35]">
              Mulai dari kebutuhan Anda
            </h3>
            <p
              id="chat-panel-description"
              className="mt-2 text-sm leading-6 text-[#61736d]"
            >
              Tanyakan layanan tukang atau mulai reservasi. Percakapan lengkap
              akan tersedia pada tahap integrasi berikutnya.
            </p>
            <div className="mt-5 flex items-center justify-center gap-1.5 text-xs font-medium text-[#6d7d77]">
              <LockKeyhole className="size-3.5" aria-hidden="true" />
              Data Anda diproses secara aman
            </div>
          </div>
        </div>

        <footer className="border-t border-[#e1e5e1] bg-white p-4">
          <div className="flex items-center gap-2 rounded-2xl border border-[#d7dfda] bg-[#f5f5f1] p-2 pl-4">
            <span className="flex-1 text-sm text-[#89948f]">
              Ketik kebutuhan Anda...
            </span>
            <button
              type="button"
              disabled
              aria-label="Kirim pesan"
              className="grid size-10 place-items-center rounded-xl bg-[#dfe4e1] text-[#9aa49f]"
            >
              <ArrowUp className="size-4" aria-hidden="true" />
            </button>
          </div>
          <p className="mt-2 text-center text-[11px] text-[#8b9691]">
            Asisten memberikan estimasi demo, bukan harga pasar.
          </p>
        </footer>
      </section>
    </>
  );
}
