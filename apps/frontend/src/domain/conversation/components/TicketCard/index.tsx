"use client";

import { Check, Copy, Mail, TicketCheck } from "lucide-react";
import { useState } from "react";

import type { Ticket } from "@/domain/conversation/interfaces/entities/conversation";

interface TicketCardProps {
  ticket: Ticket;
}

function formatCurrency(value: number): string {
  return new Intl.NumberFormat("id-ID", {
    style: "currency",
    currency: "IDR",
    maximumFractionDigits: 0,
  }).format(value);
}

function formatDateTime(value: string): string {
  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat("id-ID", {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone: "Asia/Jakarta",
  }).format(date);
}

export default function TicketCard({ ticket }: Readonly<TicketCardProps>) {
  const [copyState, setCopyState] = useState<"idle" | "copied" | "failed">(
    "idle",
  );

  const copyTicketNumber = async () => {
    try {
      await navigator.clipboard.writeText(ticket.ticket_number);
      setCopyState("copied");
    } catch {
      setCopyState("failed");
    }
  };

  return (
    <article
      aria-labelledby="ticket-card-title"
      className="ml-10 overflow-hidden rounded-2xl border border-[#b9d4c8] bg-white shadow-sm"
    >
      <div className="relative overflow-hidden bg-[#1d5949] px-4 py-4 text-white">
        <div
          aria-hidden="true"
          className="absolute -top-8 -right-8 size-24 rounded-full border-[18px] border-white/5"
        />
        <div className="relative flex items-center gap-2">
          <span className="grid size-9 place-items-center rounded-xl bg-white/12">
            <TicketCheck className="size-5" aria-hidden="true" />
          </span>
          <div>
            <h3 id="ticket-card-title" className="text-sm font-bold">
              Tiket reservasi berhasil dibuat
            </h3>
            <p className="mt-0.5 text-[11px] text-white/65">
              Simpan nomor ini untuk memeriksa status.
            </p>
          </div>
        </div>
      </div>

      <div className="p-4">
        <div className="rounded-xl border border-dashed border-[#a9c8ba] bg-[#f1f7f4] p-3">
          <p className="text-[10px] font-bold tracking-[0.14em] text-[#687b73] uppercase">
            Nomor tiket
          </p>
          <div className="mt-1.5 flex items-center gap-2">
            <code className="min-w-0 flex-1 text-sm font-extrabold break-all text-[#173f35]">
              {ticket.ticket_number}
            </code>
            <button
              type="button"
              onClick={() => void copyTicketNumber()}
              aria-label="Salin nomor tiket"
              className="flex shrink-0 items-center gap-1.5 rounded-lg bg-white px-2.5 py-2 text-xs font-bold text-[#27604f] shadow-sm transition hover:bg-[#e5f0eb] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#1d5949]"
            >
              {copyState === "copied" ? (
                <Check className="size-3.5" aria-hidden="true" />
              ) : (
                <Copy className="size-3.5" aria-hidden="true" />
              )}
              {copyState === "copied" ? "Tersalin" : "Salin"}
            </button>
          </div>
          <p className="sr-only" aria-live="polite">
            {copyState === "copied"
              ? "Nomor tiket berhasil disalin."
              : copyState === "failed"
                ? "Nomor tiket belum berhasil disalin."
                : ""}
          </p>
          {copyState === "failed" && (
            <p className="mt-2 text-[10px] text-[#ad402e]">
              Belum dapat menyalin otomatis. Silakan salin nomor di atas secara
              manual.
            </p>
          )}
        </div>

        <dl className="mt-3 space-y-2 text-xs">
          <div className="flex justify-between gap-3">
            <dt className="text-[#718078]">Layanan</dt>
            <dd className="font-bold text-[#314b43]">
              {ticket.service_type === "harian"
                ? "Tukang Harian"
                : "Jasa Borongan"}
            </dd>
          </div>
          <div className="flex justify-between gap-3">
            <dt className="text-[#718078]">Status</dt>
            <dd className="rounded-full bg-[#fff1c9] px-2 py-0.5 text-[10px] font-extrabold text-[#795d1e]">
              Menunggu pembayaran
            </dd>
          </div>
          <div className="flex justify-between gap-3">
            <dt className="text-[#718078]">Estimasi fixed</dt>
            <dd className="font-extrabold text-[#245c4b]">
              {formatCurrency(ticket.estimated_price)}
            </dd>
          </div>
          {ticket.budget !== null && (
            <div className="flex justify-between gap-3">
              <dt className="text-[#718078]">Budget Anda</dt>
              <dd className="font-bold text-[#314b43]">
                {formatCurrency(ticket.budget)}
              </dd>
            </div>
          )}
          <div className="flex justify-between gap-3">
            <dt className="text-[#718078]">Dibuat</dt>
            <dd className="text-right font-semibold text-[#314b43]">
              {formatDateTime(ticket.created_at)} WIB
            </dd>
          </div>
        </dl>

        <p className="mt-4 flex gap-1.5 rounded-lg bg-[#f4f5f2] p-2.5 text-[10px] leading-4 text-[#718078]">
          <Mail className="mt-0.5 size-3 shrink-0" aria-hidden="true" />
          Pengiriman tiket melalui email masih berupa simulasi dan belum
          dilakukan.
        </p>
      </div>
    </article>
  );
}
