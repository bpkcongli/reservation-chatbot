import { Hammer } from "lucide-react";

import { Button } from "@/components/ui/button";

export default function Home() {
  return (
    <main className="grid min-h-screen place-items-center px-6">
      <section className="mx-auto max-w-xl text-center">
        <div className="bg-primary text-primary-foreground mx-auto mb-6 grid size-14 place-items-center rounded-2xl">
          <Hammer aria-hidden="true" className="size-7" />
        </div>
        <p className="text-primary mb-3 text-sm font-semibold tracking-widest uppercase">
          Fondasi aplikasi siap
        </p>
        <h1 className="text-4xl font-bold tracking-tight sm:text-5xl">
          Reservation Chatbot
        </h1>
        <p className="text-muted-foreground mt-5 text-lg leading-8">
          Baseline Next.js untuk pengalaman reservasi Jasa Borongan dan Tukang
          Harian.
        </p>
        <Button className="mt-8" disabled>
          Chat hadir pada milestone M4
        </Button>
      </section>
    </main>
  );
}
