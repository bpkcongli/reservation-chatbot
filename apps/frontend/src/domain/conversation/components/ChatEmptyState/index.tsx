import { MessageCircleMore } from "lucide-react";

export default function ChatEmptyState() {
  return (
    <div
      role="status"
      className="mx-auto my-8 max-w-64 rounded-2xl border border-dashed border-[#cbd8d2] bg-white/70 px-5 py-6 text-center"
    >
      <span className="mx-auto grid size-10 place-items-center rounded-2xl bg-[#e5efea] text-[#28604f]">
        <MessageCircleMore className="size-5" aria-hidden="true" />
      </span>
      <p className="mt-3 text-sm font-bold text-[#314b43]">Belum ada pesan</p>
      <p className="mt-1 text-xs leading-5 text-[#718078]">
        Ketik kebutuhan Anda di bawah agar asisten dapat mulai membantu.
      </p>
    </div>
  );
}
