import { delay, http, HttpResponse } from "msw";

export const handlers = [
  http.post("*/conversations", async () => {
    await delay(250);

    return HttpResponse.json(
      {
        status: {
          code: 120100000,
          message: "Created.",
          errorDetails: [],
        },
        data: {
          conversation_id: "01K1A2B3C4D5E6F7G8H9J0K1M2",
          state: "WELCOME",
          messages: [
            {
              id: "01K1A2B3C4D5E6F7G8H9J0K1M3",
              sender: "bot",
              text: "Halo, ada yang ingin saya bantu?",
              created_at: "2026-07-29T09:00:00+07:00",
            },
          ],
          quick_replies: [
            {
              label: "Tanya-tanya dulu layanan tukang",
              value: "info",
            },
            {
              label: "Langsung reservasi",
              value: "reservation",
            },
          ],
          collected_slots: {},
          reservation_summary: null,
          price_breakdown: null,
          ticket: null,
        },
      },
      { status: 201 },
    );
  }),
];
