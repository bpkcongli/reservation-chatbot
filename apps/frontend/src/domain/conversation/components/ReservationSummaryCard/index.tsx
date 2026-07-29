import {
  CalendarDays,
  CheckCircle2,
  MapPin,
  Paperclip,
  ReceiptText,
  Users,
} from "lucide-react";

import type {
  PriceBreakdown,
  ReservationSummary,
} from "@/domain/conversation/interfaces/entities/conversation";

interface ReservationSummaryCardProps {
  priceBreakdown: PriceBreakdown;
  summary: ReservationSummary;
}

const DISPLAY_LABELS: Record<string, string> = {
  ac: "Spesialis AC",
  afternoon: "Siang",
  apartemen: "Apartemen",
  cat: "Spesialis Cat",
  full_day: "Sehari penuh",
  genteng: "Spesialis Genteng",
  keramik: "Spesialis Keramik",
  listrik: "Spesialis Listrik",
  morning: "Pagi",
  pipa: "Spesialis Pipa",
  rumah: "Rumah",
  ruko: "Ruko",
};

function formatCurrency(value: number): string {
  return new Intl.NumberFormat("id-ID", {
    style: "currency",
    currency: "IDR",
    maximumFractionDigits: 0,
  }).format(value);
}

function formatDate(value: string): string {
  const date = new Date(`${value}T00:00:00+07:00`);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat("id-ID", {
    day: "numeric",
    month: "long",
    year: "numeric",
    timeZone: "Asia/Jakarta",
  }).format(date);
}

function SummaryRow({
  label,
  value,
}: Readonly<{ label: string; value: string }>) {
  return (
    <div className="grid grid-cols-[7.5rem_1fr] gap-2 border-b border-[#edf0ed] py-2 last:border-0">
      <dt className="text-xs text-[#718078]">{label}</dt>
      <dd className="text-right text-xs font-semibold break-words text-[#314b43]">
        {value}
      </dd>
    </div>
  );
}

function PriceRow({
  emphasis = false,
  label,
  value,
}: Readonly<{ emphasis?: boolean; label: string; value: number }>) {
  return (
    <div
      className={
        emphasis
          ? "mt-2 flex items-center justify-between border-t border-[#b8d2c7] pt-3 text-[#16483b]"
          : "flex items-center justify-between py-1 text-[#53675f]"
      }
    >
      <span className={emphasis ? "text-sm font-bold" : "text-xs"}>
        {label}
      </span>
      <span className={emphasis ? "text-base font-extrabold" : "text-xs"}>
        {formatCurrency(value)}
      </span>
    </div>
  );
}

export default function ReservationSummaryCard({
  priceBreakdown,
  summary,
}: Readonly<ReservationSummaryCardProps>) {
  const isHarian = summary.service_type === "harian";

  return (
    <article
      aria-labelledby="reservation-summary-title"
      className="ml-10 overflow-hidden rounded-2xl border border-[#cbdcd4] bg-white shadow-sm"
    >
      <div className="bg-[#173f35] px-4 py-3 text-white">
        <div className="flex items-center gap-2">
          <CheckCircle2 className="size-4 text-[#8de0b5]" aria-hidden="true" />
          <h3 id="reservation-summary-title" className="text-sm font-bold">
            Ringkasan reservasi
          </h3>
        </div>
        <p className="mt-1 text-[11px] text-white/65">
          Periksa kembali sebelum mengonfirmasi.
        </p>
      </div>

      <div className="p-4">
        <div className="mb-3 flex items-center gap-2 rounded-xl bg-[#f0f6f3] px-3 py-2.5 text-xs font-bold text-[#245c4b]">
          <ReceiptText className="size-4" aria-hidden="true" />
          {isHarian ? "Tukang Harian" : "Jasa Borongan"}
        </div>

        <dl>
          <SummaryRow label="ID pelanggan" value={summary.customer_id} />
          <SummaryRow label="No. telepon" value={summary.phone_number_masked} />
          {summary.service_type === "borongan" ? (
            <>
              <SummaryRow
                label="Bangunan"
                value={DISPLAY_LABELS[summary.building_type]}
              />
              <SummaryRow
                label="Alamat survei"
                value={summary.survey_address}
              />
              <SummaryRow
                label="Jadwal survei"
                value={`${formatDate(summary.survey_date)}, ${summary.survey_time} WIB`}
              />
              <SummaryRow
                label="Budget Anda"
                value={formatCurrency(summary.budget)}
              />
            </>
          ) : (
            <>
              <SummaryRow
                label="Spesialisasi"
                value={DISPLAY_LABELS[summary.specialization]}
              />
              <SummaryRow label="Kendala" value={summary.problem_description} />
              <SummaryRow
                label="Jumlah tukang"
                value={`${summary.worker_count} orang`}
              />
              <SummaryRow
                label="Tanggal kerja"
                value={`${formatDate(summary.start_date)} – ${formatDate(summary.end_date)}`}
              />
              <SummaryRow
                label="Sesi"
                value={DISPLAY_LABELS[summary.work_session]}
              />
              <SummaryRow label="Alamat kerja" value={summary.work_address} />
              <SummaryRow
                label="Foto"
                value={
                  summary.attachment
                    ? `Terlampir (${Math.ceil(summary.attachment.size_bytes / 1024)} KB)`
                    : "Tidak dilampirkan"
                }
              />
            </>
          )}
        </dl>

        <div className="mt-4 rounded-xl border border-[#c9ddd4] bg-[#edf6f2] p-3">
          <div className="mb-2 flex items-center justify-between">
            <div>
              <p className="text-xs font-extrabold text-[#245c4b]">
                Rincian estimasi
              </p>
              <p className="text-[10px] text-[#718078]">
                Versi {priceBreakdown.pricing_version}
              </p>
            </div>
            {priceBreakdown.service_type === "harian" ? (
              <Users className="size-4 text-[#4d806e]" aria-hidden="true" />
            ) : (
              <MapPin className="size-4 text-[#4d806e]" aria-hidden="true" />
            )}
          </div>

          {priceBreakdown.service_type === "harian" ? (
            <>
              <PriceRow label="Tarif satuan" value={priceBreakdown.unit_rate} />
              <p className="py-1 text-[10px] text-[#718078]">
                {priceBreakdown.worker_count} tukang ×{" "}
                {priceBreakdown.day_count} hari
              </p>
            </>
          ) : (
            <>
              <PriceRow label="Harga dasar" value={priceBreakdown.base_price} />
              <PriceRow
                label="Biaya survei"
                value={priceBreakdown.survey_fee}
              />
            </>
          )}
          <PriceRow label="Subtotal" value={priceBreakdown.subtotal} />
          <PriceRow label="Biaya admin" value={priceBreakdown.admin_fee} />
          <PriceRow
            label="Total estimasi"
            value={priceBreakdown.estimated_price}
            emphasis
          />
        </div>

        {priceBreakdown.service_type === "borongan" && (
          <p className="mt-3 flex gap-1.5 rounded-lg bg-[#fff6df] p-2.5 text-[10px] leading-4 text-[#795d1e]">
            <CalendarDays
              className="mt-0.5 size-3 shrink-0"
              aria-hidden="true"
            />
            Budget Anda ditampilkan sebagai preferensi dan tidak digunakan untuk
            menghitung estimasi fixed.
          </p>
        )}

        <p className="mt-3 flex gap-1.5 text-[10px] leading-4 text-[#7a8781]">
          <Paperclip className="mt-0.5 size-3 shrink-0" aria-hidden="true" />
          {priceBreakdown.disclaimer}
        </p>
      </div>
    </article>
  );
}
