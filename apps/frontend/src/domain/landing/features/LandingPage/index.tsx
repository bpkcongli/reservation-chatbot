"use client";

import {
  ArrowRight,
  BadgeCheck,
  CalendarCheck2,
  Check,
  ChevronRight,
  Clock3,
  HardHat,
  Home,
  MessageCircleMore,
  Paintbrush,
  ShieldCheck,
  Sparkles,
  Star,
  Wrench,
} from "lucide-react";
import { observer } from "mobx-react-lite";

import { Button } from "@/components/ui/button";
import { useChatWidgetStore } from "@/domain/conversation/hooks";
import BrandMark from "@/general/components/BrandMark";

const services = [
  {
    eyebrow: "Untuk proyek terencana",
    title: "Jasa Borongan",
    description:
      "Cocok untuk renovasi menyeluruh dengan survei lokasi, ruang lingkup jelas, dan estimasi terstruktur.",
    icon: Home,
    accent: "bg-[#f6e2d7] text-[#b84729]",
    points: ["Rumah, apartemen, dan ruko", "Jadwal survei fleksibel"],
  },
  {
    eyebrow: "Untuk kebutuhan spesifik",
    title: "Tukang Harian",
    description:
      "Pilih tenaga ahli sesuai masalah rumah, jumlah pekerja, sesi, dan rentang hari yang Anda perlukan.",
    icon: HardHat,
    accent: "bg-[#dce9e4] text-[#17604d]",
    points: ["6 pilihan spesialisasi", "Sesi pagi, siang, atau sehari"],
  },
];

const steps = [
  {
    number: "01",
    title: "Ceritakan kebutuhan",
    description:
      "Jawab pertanyaan singkat melalui chat agar kami memahami pekerjaan Anda.",
    icon: MessageCircleMore,
  },
  {
    number: "02",
    title: "Atur layanan & jadwal",
    description:
      "Pilih Borongan atau Harian, lalu tentukan jadwal yang paling sesuai.",
    icon: CalendarCheck2,
  },
  {
    number: "03",
    title: "Terima tiket reservasi",
    description:
      "Periksa ringkasan dan estimasi sebelum mengonfirmasi permintaan Anda.",
    icon: BadgeCheck,
  },
];

const LandingPage = observer(() => {
  const chatWidgetStore = useChatWidgetStore();

  return (
    <div className="bg-background overflow-x-clip">
      <header className="absolute inset-x-0 top-0 z-30">
        <div className="mx-auto flex h-20 max-w-7xl items-center justify-between px-5 sm:px-8 lg:px-10">
          <a
            href="#beranda"
            className="focus-visible:outline-primary flex items-center gap-3 rounded-lg focus-visible:outline-3 focus-visible:outline-offset-4"
            aria-label="Reservasi Tukang, kembali ke beranda"
          >
            <BrandMark />
            <span className="hidden text-[17px] font-extrabold tracking-tight text-[#173f35] min-[360px]:inline">
              Reservasi<span className="text-primary">Tukang</span>
            </span>
          </a>

          <nav
            aria-label="Navigasi utama"
            className="hidden items-center gap-8 md:flex"
          >
            <a className="nav-link" href="#layanan">
              Layanan
            </a>
            <a className="nav-link" href="#keunggulan">
              Keunggulan
            </a>
            <a className="nav-link" href="#cara-kerja">
              Cara kerja
            </a>
          </nav>

          <Button
            type="button"
            onClick={chatWidgetStore.open}
            className="h-11 rounded-full bg-[#173f35] px-5 text-white shadow-sm hover:bg-[#0f332a]"
          >
            Mulai chat
            <ArrowRight className="size-4" aria-hidden="true" />
          </Button>
        </div>
      </header>

      <main>
        <section
          id="beranda"
          className="relative min-h-[760px] overflow-hidden pt-32 sm:pt-36 lg:min-h-[820px]"
        >
          <div
            aria-hidden="true"
            className="absolute top-0 right-0 -z-0 h-full w-[42%] bg-[#e7eee9] max-lg:hidden"
          />
          <div
            aria-hidden="true"
            className="absolute top-28 -left-36 size-80 rounded-full bg-[#f6c9ac]/35 blur-3xl"
          />

          <div className="relative z-10 mx-auto grid max-w-7xl items-center gap-14 px-5 sm:px-8 lg:grid-cols-[1.03fr_0.97fr] lg:px-10">
            <div className="hero-reveal max-w-2xl">
              <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-[#d8dfda] bg-white/75 px-3.5 py-2 text-xs font-bold tracking-wide text-[#34564d] shadow-sm backdrop-blur">
                <Sparkles
                  className="text-primary size-3.5"
                  aria-hidden="true"
                />
                RESERVASI TUKANG, TANPA RIBET
              </div>
              <h1
                aria-label="Rumah nyaman dimulai di sini."
                className="font-display text-[3.25rem] leading-[0.98] font-bold tracking-[-0.045em] text-[#173f35] sm:text-7xl lg:text-[5.4rem]"
              >
                Rumah nyaman
                <span className="text-primary relative mt-1 block">
                  dimulai di sini.
                  <svg
                    aria-hidden="true"
                    className="absolute -bottom-3 left-1 h-3 w-[70%] text-[#f5b454]"
                    viewBox="0 0 320 16"
                    fill="none"
                    preserveAspectRatio="none"
                  >
                    <path
                      d="M3 12C83 2 230 3 317 7"
                      stroke="currentColor"
                      strokeWidth="7"
                      strokeLinecap="round"
                    />
                  </svg>
                </span>
              </h1>
              <p className="mt-9 max-w-xl text-base leading-8 text-[#5b6d67] sm:text-lg">
                Temukan layanan Jasa Borongan atau Tukang Harian melalui
                percakapan sederhana. Jelaskan kebutuhan Anda, pilih jadwal,
                lalu dapatkan tiket reservasi.
              </p>
              <div className="mt-9 flex flex-col items-start gap-4 sm:flex-row sm:items-center">
                <Button
                  size="lg"
                  type="button"
                  onClick={chatWidgetStore.open}
                  className="h-14 rounded-full px-7 text-base shadow-[0_14px_35px_rgba(218,80,45,0.24)]"
                >
                  Konsultasi gratis
                  <ArrowRight className="size-5" aria-hidden="true" />
                </Button>
                <a
                  href="#layanan"
                  className="focus-visible:outline-primary inline-flex h-14 items-center gap-2 rounded-full px-5 text-sm font-bold text-[#173f35] transition hover:bg-[#e7eee9] focus-visible:outline-3 focus-visible:outline-offset-2"
                >
                  Lihat layanan
                  <ChevronRight className="size-4" aria-hidden="true" />
                </a>
              </div>

              <div className="mt-10 flex flex-wrap gap-x-7 gap-y-3 text-sm font-medium text-[#53675f]">
                {["Alur transparan", "Jadwal fleksibel", "Estimasi jelas"].map(
                  (item) => (
                    <span key={item} className="flex items-center gap-2">
                      <span className="grid size-5 place-items-center rounded-full bg-[#dce9e2] text-[#17604d]">
                        <Check className="size-3" aria-hidden="true" />
                      </span>
                      {item}
                    </span>
                  ),
                )}
              </div>
            </div>

            <div className="relative mx-auto w-full max-w-[560px] lg:ml-auto">
              <div
                aria-hidden="true"
                className="absolute -top-5 -left-6 z-0 hidden h-[82%] w-[86%] rounded-[42px] border-2 border-[#b8cbc2] lg:block"
              />
              <div className="relative overflow-hidden rounded-[32px] bg-[#1b493e] p-5 shadow-[0_35px_80px_rgba(22,63,53,0.25)] sm:p-7">
                <div className="relative h-[490px] overflow-hidden rounded-[24px] bg-[#e9d9c5] sm:h-[540px]">
                  <div
                    aria-hidden="true"
                    className="absolute inset-x-0 bottom-0 h-[68%] bg-gradient-to-t from-[#c88d68] to-[#eacdb5]"
                  />
                  <div
                    aria-hidden="true"
                    className="absolute top-14 left-1/2 h-56 w-64 -translate-x-1/2 rounded-t-[120px] bg-[#f5efe4] shadow-[0_24px_80px_rgba(105,65,43,0.18)] sm:h-64 sm:w-72"
                  >
                    <div className="absolute top-20 left-1/2 h-32 w-40 -translate-x-1/2 border-[12px] border-[#e16d44] bg-[#8cb7b3]">
                      <div className="absolute inset-x-1/2 top-0 h-full w-2 -translate-x-1/2 bg-[#e16d44]" />
                      <div className="absolute inset-y-1/2 left-0 h-2 w-full -translate-y-1/2 bg-[#e16d44]" />
                    </div>
                  </div>
                  <div
                    aria-hidden="true"
                    className="absolute right-6 bottom-6 left-6 h-24 rounded-[50%] bg-[#704c38]/25 blur-xl"
                  />
                  <div
                    aria-hidden="true"
                    className="absolute right-[14%] bottom-9 h-52 w-28 rounded-t-full bg-[#f4a33e]"
                  >
                    <div className="absolute -top-12 left-1/2 size-20 -translate-x-1/2 rounded-full bg-[#7f4d33]" />
                    <HardHat className="absolute -top-16 left-1/2 size-24 -translate-x-1/2 fill-[#f6b84e] text-[#d7802b]" />
                    <div className="absolute top-12 -left-20 h-12 w-28 rotate-[18deg] rounded-full bg-[#f4a33e]" />
                    <Paintbrush className="absolute top-7 -left-24 size-14 -rotate-12 text-[#24574c]" />
                  </div>
                  <div className="absolute top-5 left-5 flex items-center gap-2 rounded-full bg-white/90 px-3 py-2 text-xs font-bold text-[#244b40] shadow-lg backdrop-blur">
                    <span className="size-2 rounded-full bg-[#37a674]" />
                    Tenaga ahli terpilih
                  </div>
                </div>

                <div className="absolute right-2 bottom-8 left-2 mx-auto flex max-w-[86%] items-center gap-3 rounded-2xl bg-white p-3.5 shadow-[0_15px_40px_rgba(20,50,42,0.2)] sm:right-5 sm:bottom-10 sm:left-auto sm:max-w-[280px]">
                  <span className="grid size-11 shrink-0 place-items-center rounded-xl bg-[#e3eee8] text-[#17604d]">
                    <CalendarCheck2 className="size-5" aria-hidden="true" />
                  </span>
                  <span>
                    <span className="block text-xs text-[#6d7c76]">
                      Reservasi terjadwal
                    </span>
                    <span className="mt-0.5 block text-sm font-bold text-[#173f35]">
                      Sabtu, 09.00 WIB
                    </span>
                  </span>
                  <BadgeCheck
                    className="ml-auto size-5 text-[#2e9a6b]"
                    aria-hidden="true"
                  />
                </div>
              </div>

              <div className="absolute -bottom-7 -left-3 flex items-center gap-3 rounded-2xl border border-white/80 bg-white/95 p-4 shadow-[0_16px_42px_rgba(22,63,53,0.16)] backdrop-blur sm:-left-8">
                <div className="flex -space-x-2">
                  {[Wrench, Paintbrush, HardHat].map((Icon, index) => (
                    <span
                      key={index}
                      className="grid size-9 place-items-center rounded-full border-2 border-white bg-[#edf1ed] text-[#315b4f]"
                    >
                      <Icon className="size-4" aria-hidden="true" />
                    </span>
                  ))}
                </div>
                <div>
                  <div className="flex gap-0.5 text-[#f2a53a]">
                    {Array.from({ length: 5 }).map((_, index) => (
                      <Star
                        key={index}
                        className="size-3 fill-current"
                        aria-hidden="true"
                      />
                    ))}
                  </div>
                  <p className="mt-1 text-xs font-bold text-[#38564e]">
                    Beragam spesialisasi
                  </p>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section
          id="layanan"
          className="scroll-mt-16 bg-white px-5 py-24 sm:px-8 lg:py-28"
        >
          <div className="mx-auto max-w-7xl">
            <div className="grid gap-8 lg:grid-cols-[0.8fr_1.2fr] lg:items-end">
              <div>
                <p className="section-eyebrow">PILIH SESUAI KEBUTUHAN</p>
                <h2 className="section-title mt-4">
                  Satu tempat untuk dua jenis pekerjaan.
                </h2>
              </div>
              <p className="max-w-xl text-base leading-7 text-[#66756f] lg:ml-auto">
                Dari perbaikan kecil sampai renovasi menyeluruh, pilih cara
                kerja yang paling cocok tanpa harus memahami istilah teknis.
              </p>
            </div>

            <div className="mt-12 grid gap-5 lg:grid-cols-2">
              {services.map((service) => {
                const Icon = service.icon;
                return (
                  <article
                    key={service.title}
                    className="group relative overflow-hidden rounded-[28px] border border-[#e0e5e1] bg-[#fbfaf6] p-6 transition duration-300 hover:-translate-y-1 hover:border-[#c8d5cf] hover:shadow-[0_20px_50px_rgba(26,66,55,0.09)] sm:p-8"
                  >
                    <div className="flex items-start justify-between gap-5">
                      <span
                        className={`grid size-14 place-items-center rounded-2xl ${service.accent}`}
                      >
                        <Icon className="size-6" aria-hidden="true" />
                      </span>
                      <span className="rounded-full border border-[#dde3df] bg-white px-3 py-1.5 text-[11px] font-bold tracking-wide text-[#5e7069] uppercase">
                        {service.eyebrow}
                      </span>
                    </div>
                    <h3 className="mt-8 text-2xl font-bold tracking-tight text-[#173f35]">
                      {service.title}
                    </h3>
                    <p className="mt-3 max-w-lg leading-7 text-[#66756f]">
                      {service.description}
                    </p>
                    <div className="mt-7 grid gap-3 border-t border-[#e2e6e3] pt-6 sm:grid-cols-2">
                      {service.points.map((point) => (
                        <span
                          key={point}
                          className="flex items-center gap-2 text-sm font-semibold text-[#3f5c53]"
                        >
                          <Check
                            className="size-4 text-[#27815f]"
                            aria-hidden
                          />
                          {point}
                        </span>
                      ))}
                    </div>
                    <button
                      type="button"
                      onClick={chatWidgetStore.open}
                      className="text-primary focus-visible:outline-primary mt-7 inline-flex items-center gap-2 rounded-md text-sm font-bold transition group-hover:gap-3 focus-visible:outline-3 focus-visible:outline-offset-4"
                    >
                      Konsultasikan kebutuhan
                      <ArrowRight className="size-4" aria-hidden="true" />
                    </button>
                  </article>
                );
              })}
            </div>
          </div>
        </section>

        <section
          id="keunggulan"
          className="scroll-mt-16 bg-[#173f35] px-5 py-24 text-white sm:px-8 lg:py-28"
        >
          <div className="mx-auto grid max-w-7xl gap-14 lg:grid-cols-2 lg:items-center">
            <div className="relative">
              <div className="grid min-h-[430px] place-items-center overflow-hidden rounded-[32px] bg-[#e9b584] p-8">
                <div className="relative w-full max-w-sm rounded-[28px] bg-[#fbfaf6] p-6 text-[#173f35] shadow-[0_30px_70px_rgba(8,35,28,0.25)]">
                  <div className="flex items-center justify-between border-b border-[#e4e7e3] pb-4">
                    <div className="flex items-center gap-3">
                      <BrandMark className="size-9 rounded-xl" />
                      <div>
                        <p className="text-sm font-bold">Ringkasan kebutuhan</p>
                        <p className="text-xs text-[#718079]">
                          Siap Anda periksa
                        </p>
                      </div>
                    </div>
                    <BadgeCheck
                      className="size-5 text-[#2e9a6b]"
                      aria-hidden="true"
                    />
                  </div>
                  <dl className="mt-5 space-y-4 text-sm">
                    <div className="flex justify-between gap-4">
                      <dt className="text-[#78857f]">Layanan</dt>
                      <dd className="font-bold">Tukang Harian</dd>
                    </div>
                    <div className="flex justify-between gap-4">
                      <dt className="text-[#78857f]">Spesialisasi</dt>
                      <dd className="font-bold">Listrik</dd>
                    </div>
                    <div className="flex justify-between gap-4">
                      <dt className="text-[#78857f]">Jadwal</dt>
                      <dd className="font-bold">Sabtu, sesi pagi</dd>
                    </div>
                  </dl>
                  <div className="mt-6 rounded-2xl bg-[#e8efeb] px-4 py-3 text-xs font-semibold text-[#315a4e]">
                    Anda selalu bisa mengubah data sebelum konfirmasi.
                  </div>
                </div>
              </div>
              <div className="absolute -right-3 -bottom-5 flex items-center gap-3 rounded-2xl bg-white px-4 py-3 text-[#173f35] shadow-xl sm:-right-5">
                <ShieldCheck className="size-7 text-[#2d8f67]" aria-hidden />
                <div>
                  <p className="text-xs text-[#77847f]">Konfirmasi dahulu</p>
                  <p className="text-sm font-bold">
                    Tidak ada biaya tersembunyi
                  </p>
                </div>
              </div>
            </div>

            <div className="lg:pl-10">
              <p className="text-xs font-extrabold tracking-[0.18em] text-[#f3ae76]">
                LEBIH TENANG, LEBIH JELAS
              </p>
              <h2 className="font-display mt-4 text-4xl leading-tight font-bold tracking-tight sm:text-5xl">
                Anda pegang kendali di setiap langkah.
              </h2>
              <p className="mt-5 max-w-xl leading-8 text-white/68">
                Asisten kami memandu proses satu per satu, menampilkan kembali
                data penting, dan baru membuat tiket setelah Anda setuju.
              </p>
              <div className="mt-9 grid gap-6 sm:grid-cols-2">
                {[
                  {
                    icon: Clock3,
                    title: "Hemat waktu",
                    text: "Tidak perlu berpindah halaman atau mengisi form panjang.",
                  },
                  {
                    icon: ShieldCheck,
                    title: "Transparan",
                    text: "Ringkasan dan estimasi ditampilkan sebelum konfirmasi.",
                  },
                  {
                    icon: MessageCircleMore,
                    title: "Bahasa sederhana",
                    text: "Ceritakan kebutuhan seperti sedang mengobrol.",
                  },
                  {
                    icon: Wrench,
                    title: "Pilihan spesifik",
                    text: "Mulai dari cat, listrik, AC, genteng, keramik, hingga pipa.",
                  },
                ].map((item) => {
                  const Icon = item.icon;
                  return (
                    <div key={item.title}>
                      <Icon
                        className="size-5 text-[#f3ae76]"
                        aria-hidden="true"
                      />
                      <h3 className="mt-3 font-bold">{item.title}</h3>
                      <p className="mt-1.5 text-sm leading-6 text-white/62">
                        {item.text}
                      </p>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        </section>

        <section
          id="cara-kerja"
          className="scroll-mt-16 px-5 py-24 sm:px-8 lg:py-28"
        >
          <div className="mx-auto max-w-7xl">
            <div className="mx-auto max-w-2xl text-center">
              <p className="section-eyebrow">CARA KERJA</p>
              <h2 className="section-title mt-4">
                Dari cerita singkat menjadi reservasi.
              </h2>
              <p className="mt-5 leading-7 text-[#66756f]">
                Tiga langkah sederhana, dengan kesempatan memeriksa ulang
                sebelum permintaan diteruskan.
              </p>
            </div>

            <div className="relative mt-14 grid gap-5 lg:grid-cols-3">
              <div
                aria-hidden="true"
                className="absolute top-12 right-[16%] left-[16%] hidden border-t border-dashed border-[#b8c9c1] lg:block"
              />
              {steps.map((step) => {
                const Icon = step.icon;
                return (
                  <article
                    key={step.number}
                    className="relative rounded-[26px] border border-[#dfe5e1] bg-white p-7"
                  >
                    <div className="flex items-center justify-between">
                      <span className="grid size-12 place-items-center rounded-2xl bg-[#e4eee9] text-[#17604d]">
                        <Icon className="size-5" aria-hidden="true" />
                      </span>
                      <span className="font-display text-3xl font-bold text-[#d8e1dc]">
                        {step.number}
                      </span>
                    </div>
                    <h3 className="mt-7 text-lg font-bold text-[#173f35]">
                      {step.title}
                    </h3>
                    <p className="mt-2 text-sm leading-6 text-[#6a7973]">
                      {step.description}
                    </p>
                  </article>
                );
              })}
            </div>
          </div>
        </section>

        <section className="px-5 pb-20 sm:px-8">
          <div className="relative mx-auto max-w-7xl overflow-hidden rounded-[34px] bg-[#e9623b] px-6 py-14 text-white sm:px-12 lg:flex lg:items-center lg:justify-between lg:px-16 lg:py-16">
            <div
              aria-hidden="true"
              className="absolute -top-20 -right-12 size-64 rounded-full border-[45px] border-white/8"
            />
            <div
              aria-hidden="true"
              className="absolute -bottom-36 left-[45%] size-72 rounded-full border-[50px] border-[#f5bd62]/20"
            />
            <div className="relative max-w-2xl">
              <p className="text-xs font-extrabold tracking-[0.18em] text-white/75">
                SIAP MEMULAI?
              </p>
              <h2 className="font-display mt-3 text-4xl leading-tight font-bold tracking-tight sm:text-5xl">
                Ceritakan kebutuhan rumah Anda.
              </h2>
              <p className="mt-4 max-w-xl leading-7 text-white/78">
                Buka chat, jawab beberapa pertanyaan, dan temukan layanan yang
                paling sesuai.
              </p>
            </div>
            <Button
              type="button"
              size="lg"
              onClick={chatWidgetStore.open}
              className="relative mt-8 h-14 rounded-full bg-white px-7 text-[#b84225] shadow-xl hover:bg-[#fff7ef] lg:mt-0"
            >
              Mulai konsultasi
              <ArrowRight className="size-5" aria-hidden="true" />
            </Button>
          </div>
        </section>
      </main>

      <footer className="border-t border-[#dfe5e1] px-5 py-8 sm:px-8">
        <div className="mx-auto flex max-w-7xl flex-col gap-5 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-3">
            <BrandMark className="size-9 rounded-xl" />
            <span className="text-sm font-extrabold text-[#173f35]">
              ReservasiTukang
            </span>
          </div>
          <p className="text-xs leading-5 text-[#78857f]">
            Platform demo reservasi Jasa Borongan dan Tukang Harian.
          </p>
        </div>
      </footer>
    </div>
  );
});

export default LandingPage;
