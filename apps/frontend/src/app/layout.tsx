import type { Metadata } from "next";
import type { ReactNode } from "react";

import ApplicationProvider from "@/general/providers/ApplicationProvider";

import "./globals.css";

export const metadata: Metadata = {
  title: "ReservasiTukang — Cari layanan tukang tanpa ribet",
  description:
    "Reservasi Jasa Borongan dan Tukang Harian melalui percakapan sederhana.",
};

export default function RootLayout({
  children,
}: Readonly<{ children: ReactNode }>) {
  return (
    <html lang="id">
      <body>
        <ApplicationProvider>{children}</ApplicationProvider>
      </body>
    </html>
  );
}
