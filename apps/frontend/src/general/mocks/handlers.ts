import { delay, http, HttpResponse } from "msw";

export const createConversationMockResponse = {
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
        text: [
          "Halo! Selamat datang di layanan reservasi tukang.",
          "Saya dapat membantu Anda mencari informasi layanan atau memulai reservasi.",
          "Silakan pilih kebutuhan Anda.",
        ].join(" "),
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
} as const;

export const restoreConversationMockResponse = {
  ...createConversationMockResponse,
  status: {
    code: 120000000,
    message: "Success.",
    errorDetails: [],
  },
} as const;

export function createSendMessageMockResponse(text: string) {
  const isReservation = text === "reservation";

  return {
    status: {
      code: 120000000,
      message: "Success.",
      errorDetails: [],
    },
    data: {
      conversation_id: createConversationMockResponse.data.conversation_id,
      state: isReservation ? "SELECT_SERVICE" : "INFO_MODE",
      messages: [
        {
          id: "01K1A2B3C4D5E6F7G8H9J0K1M4",
          sender: "user",
          text,
          created_at: "2026-07-29T09:01:00+07:00",
        },
        {
          id: "01K1A2B3C4D5E6F7G8H9J0K1M5",
          sender: "bot",
          text: isReservation
            ? "Baik, mari mulai reservasi. Silakan pilih layanan Jasa Borongan atau Tukang Harian agar saya dapat memandu langkah berikutnya."
            : "Baik, saya siap membantu. Silakan ceritakan kebutuhan layanan tukang Anda.",
          created_at: "2026-07-29T09:01:01+07:00",
        },
      ],
      quick_replies: isReservation
        ? [
            { label: "Jasa Borongan", value: "borongan" },
            { label: "Tukang Harian", value: "harian" },
          ]
        : [
            { label: "Jasa Borongan", value: "borongan" },
            { label: "Tukang Harian", value: "harian" },
            { label: "Mulai reservasi", value: "reservation" },
          ],
      collected_slots: {},
      reservation_summary: null,
      price_breakdown: null,
      ticket: null,
    },
  } as const;
}

export const handlers = [
  http.post("*/conversations", async () => {
    await delay(250);

    return HttpResponse.json(createConversationMockResponse, { status: 201 });
  }),
  http.get("*/conversations/:conversationId", async () => {
    await delay(150);

    return HttpResponse.json(restoreConversationMockResponse);
  }),
  http.post("*/conversations/:conversationId/messages", async ({ request }) => {
    const body = (await request.json()) as {
      client_message_id: string;
      text: string;
    };
    await delay(250);

    return HttpResponse.json(createSendMessageMockResponse(body.text));
  }),
];
