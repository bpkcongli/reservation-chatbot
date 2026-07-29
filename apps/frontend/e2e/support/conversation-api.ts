import { expect, type Page } from "@playwright/test";

const CONVERSATION_ID = "01K1A2B3C4D5E6F7G8H9J0K1M2";
const CREATED_AT = "2026-07-29T09:00:00+07:00";
const ID_PREFIX = "01K1A2B3C4D5E6F7G8H9J0K";

interface QuickReplyFixture {
  label: string;
  value: string;
}

interface ConversationStep {
  botText: string;
  expectedText: string;
  priceBreakdown?: Record<string, unknown>;
  quickReplies?: QuickReplyFixture[];
  reservationSummary?: Record<string, unknown>;
  state: string;
  ticket?: Record<string, unknown>;
}

interface ScenarioController {
  assertComplete(): void;
}

function messageId(sequence: number): string {
  return `${ID_PREFIX}${String(sequence).padStart(3, "0")}`;
}

function responseData(
  step: ConversationStep,
  sequence: number,
): Record<string, unknown> {
  return {
    conversation_id: CONVERSATION_ID,
    state: step.state,
    messages: [
      {
        id: messageId(sequence * 2),
        sender: "user",
        text: step.expectedText,
        created_at: CREATED_AT,
      },
      {
        id: messageId(sequence * 2 + 1),
        sender: "bot",
        text: step.botText,
        created_at: CREATED_AT,
      },
    ],
    quick_replies: step.quickReplies ?? [],
    collected_slots: {},
    reservation_summary: step.reservationSummary ?? null,
    price_breakdown: step.priceBreakdown ?? null,
    ticket: step.ticket ?? null,
  };
}

const reservationChoiceStep: ConversationStep = {
  expectedText: "reservation",
  state: "SELECT_SERVICE",
  botText:
    "Baik, mari mulai reservasi. Silakan pilih layanan Jasa Borongan atau Tukang Harian.",
  quickReplies: [
    { label: "Jasa Borongan", value: "borongan" },
    { label: "Tukang Harian", value: "harian" },
  ],
};

const confirmationReplies: QuickReplyFixture[] = [
  { label: "Ya, konfirmasi", value: "ya" },
  { label: "Ubah data", value: "ubah" },
  { label: "Batalkan", value: "batal" },
];

export const boronganSteps: ConversationStep[] = [
  reservationChoiceStep,
  {
    expectedText: "borongan",
    state: "BORONGAN_ASK_CUSTOMER_ID",
    botText: "Mohon masukkan ID pelanggan tepat 10 digit.",
  },
  {
    expectedText: "0123456789",
    state: "BORONGAN_ASK_PHONE",
    botText: "ID pelanggan sudah dicatat. Mohon masukkan nomor telepon.",
  },
  {
    expectedText: "081234567890",
    state: "BORONGAN_ASK_BUILDING",
    botText: "Silakan pilih jenis bangunan.",
    quickReplies: [
      { label: "Rumah", value: "rumah" },
      { label: "Apartemen", value: "apartemen" },
      { label: "Ruko", value: "ruko" },
    ],
  },
  {
    expectedText: "rumah",
    state: "BORONGAN_ASK_ADDRESS",
    botText: "Mohon tuliskan alamat survei secara lengkap.",
  },
  {
    expectedText: "Jalan Melati No. 10 Jakarta",
    state: "BORONGAN_ASK_SURVEY_DATE",
    botText: "Silakan masukkan tanggal survei.",
  },
  {
    expectedText: "2 Agustus 2026",
    state: "BORONGAN_ASK_SURVEY_TIME",
    botText: "Silakan masukkan waktu survei, misalnya 09:00.",
  },
  {
    expectedText: "09:00",
    state: "BORONGAN_ASK_BUDGET",
    botText: "Silakan masukkan budget pekerjaan.",
  },
  {
    expectedText: "20 juta",
    state: "CONFIRM_RESERVATION",
    botText: "Silakan periksa ringkasan Jasa Borongan sebelum konfirmasi.",
    quickReplies: confirmationReplies,
    reservationSummary: {
      service_type: "borongan",
      customer_id: "0123456789",
      phone_number_masked: "+62812****7890",
      building_type: "rumah",
      survey_address: "Jalan Melati No. 10 Jakarta",
      survey_date: "2026-08-02",
      survey_time: "09:00",
      budget: 20_000_000,
    },
    priceBreakdown: {
      service_type: "borongan",
      pricing_version: "pricing-v1",
      currency: "IDR",
      building_type: "rumah",
      base_price: 5_000_000,
      survey_fee: 100_000,
      subtotal: 5_000_000,
      budget: 20_000_000,
      admin_fee: 25_000,
      estimated_price: 5_125_000,
      disclaimer: "Harga fixed pricing-v1 hanya untuk demonstrasi chatbot.",
    },
  },
  {
    expectedText: "ya",
    state: "TICKET_CREATED",
    botText:
      "Reservasi berhasil dikonfirmasi. Nomor tiket Anda TKT-20260729-B0R0NG.",
    reservationSummary: {
      service_type: "borongan",
      customer_id: "0123456789",
      phone_number_masked: "+62812****7890",
      building_type: "rumah",
      survey_address: "Jalan Melati No. 10 Jakarta",
      survey_date: "2026-08-02",
      survey_time: "09:00",
      budget: 20_000_000,
    },
    priceBreakdown: {
      service_type: "borongan",
      pricing_version: "pricing-v1",
      currency: "IDR",
      building_type: "rumah",
      base_price: 5_000_000,
      survey_fee: 100_000,
      subtotal: 5_000_000,
      budget: 20_000_000,
      admin_fee: 25_000,
      estimated_price: 5_125_000,
      disclaimer: "Harga fixed pricing-v1 hanya untuk demonstrasi chatbot.",
    },
    ticket: {
      ticket_number: "TKT-20260729-B0R0NG",
      service_type: "borongan",
      status: "MENUNGGU_PEMBAYARAN",
      pricing_version: "pricing-v1",
      estimated_price: 5_125_000,
      budget: 20_000_000,
      created_at: CREATED_AT,
      email_delivery: "NOT_IMPLEMENTED",
    },
  },
];

export const harianSteps: ConversationStep[] = [
  reservationChoiceStep,
  {
    expectedText: "harian",
    state: "HARIAN_ASK_CUSTOMER_ID",
    botText: "Mohon masukkan ID pelanggan tepat 10 digit.",
  },
  {
    expectedText: "0123456789",
    state: "HARIAN_ASK_PHONE",
    botText: "ID pelanggan sudah dicatat. Mohon masukkan nomor telepon.",
  },
  {
    expectedText: "081234567890",
    state: "HARIAN_ASK_SPECIALIZATION",
    botText: "Silakan pilih spesialisasi tukang.",
    quickReplies: [
      { label: "Spesialis Cat", value: "cat" },
      { label: "Spesialis Genteng", value: "genteng" },
      { label: "Spesialis AC", value: "ac" },
      { label: "Spesialis Listrik", value: "listrik" },
      { label: "Spesialis Keramik", value: "keramik" },
      { label: "Spesialis Pipa", value: "pipa" },
    ],
  },
  {
    expectedText: "listrik",
    state: "HARIAN_ASK_DESCRIPTION",
    botText: "Mohon jelaskan kebutuhan atau kendalanya.",
  },
  {
    expectedText: "Instalasi listrik sering turun mendadak",
    state: "HARIAN_ASK_WORKER_COUNT",
    botText: "Berapa tukang yang dibutuhkan?",
  },
  {
    expectedText: "2 orang",
    state: "HARIAN_ASK_START_DATE",
    botText: "Silakan masukkan tanggal mulai.",
  },
  {
    expectedText: "2 Agustus 2026",
    state: "HARIAN_ASK_END_DATE",
    botText: "Silakan masukkan tanggal selesai.",
  },
  {
    expectedText: "3 Agustus 2026",
    state: "HARIAN_ASK_SESSION",
    botText: "Silakan pilih sesi kerja.",
    quickReplies: [
      { label: "Sehari penuh", value: "sehari penuh" },
      { label: "Pagi", value: "pagi" },
      { label: "Sore", value: "sore" },
    ],
  },
  {
    expectedText: "pagi",
    state: "HARIAN_ASK_PHOTO",
    botText: "Foto kendala bersifat opsional.",
    quickReplies: [{ label: "Lewati foto", value: "lewati" }],
  },
  {
    expectedText: "lewati",
    state: "HARIAN_ASK_ADDRESS",
    botText: "Mohon tuliskan alamat pekerjaan secara lengkap.",
  },
  {
    expectedText: "Jalan Mawar No. 20 Jakarta Selatan",
    state: "CONFIRM_RESERVATION",
    botText: "Silakan periksa ringkasan Tukang Harian sebelum konfirmasi.",
    quickReplies: confirmationReplies,
    reservationSummary: {
      service_type: "harian",
      customer_id: "0123456789",
      phone_number_masked: "+62812****7890",
      specialization: "listrik",
      problem_description: "Instalasi listrik sering turun mendadak",
      worker_count: 2,
      start_date: "2026-08-02",
      end_date: "2026-08-03",
      work_session: "morning",
      work_address: "Jalan Mawar No. 20 Jakarta Selatan",
      attachment: null,
    },
    priceBreakdown: {
      service_type: "harian",
      pricing_version: "pricing-v1",
      currency: "IDR",
      specialization: "listrik",
      work_session: "morning",
      unit_rate: 195_000,
      worker_count: 2,
      day_count: 2,
      subtotal: 780_000,
      admin_fee: 25_000,
      estimated_price: 805_000,
      disclaimer: "Harga fixed pricing-v1 hanya untuk demonstrasi chatbot.",
    },
  },
  {
    expectedText: "ya",
    state: "TICKET_CREATED",
    botText:
      "Reservasi berhasil dikonfirmasi. Nomor tiket Anda TKT-20260729-HAR1AN.",
    reservationSummary: {
      service_type: "harian",
      customer_id: "0123456789",
      phone_number_masked: "+62812****7890",
      specialization: "listrik",
      problem_description: "Instalasi listrik sering turun mendadak",
      worker_count: 2,
      start_date: "2026-08-02",
      end_date: "2026-08-03",
      work_session: "morning",
      work_address: "Jalan Mawar No. 20 Jakarta Selatan",
      attachment: null,
    },
    priceBreakdown: {
      service_type: "harian",
      pricing_version: "pricing-v1",
      currency: "IDR",
      specialization: "listrik",
      work_session: "morning",
      unit_rate: 195_000,
      worker_count: 2,
      day_count: 2,
      subtotal: 780_000,
      admin_fee: 25_000,
      estimated_price: 805_000,
      disclaimer: "Harga fixed pricing-v1 hanya untuk demonstrasi chatbot.",
    },
    ticket: {
      ticket_number: "TKT-20260729-HAR1AN",
      service_type: "harian",
      status: "MENUNGGU_PEMBAYARAN",
      pricing_version: "pricing-v1",
      estimated_price: 805_000,
      budget: null,
      created_at: CREATED_AT,
      email_delivery: "NOT_IMPLEMENTED",
    },
  },
];

export async function installConversationScenario(
  page: Page,
  steps: ConversationStep[],
): Promise<ScenarioController> {
  let stepIndex = 0;

  await page.route("**/api/v1/conversations**", async (route) => {
    const request = route.request();
    const pathname = new URL(request.url()).pathname;

    if (request.method() === "POST" && pathname.endsWith("/conversations")) {
      await route.fulfill({
        contentType: "application/json",
        status: 201,
        body: JSON.stringify({
          status: {
            code: 120100000,
            message: "Created.",
            errorDetails: [],
          },
          data: {
            conversation_id: CONVERSATION_ID,
            state: "WELCOME",
            messages: [
              {
                id: messageId(1),
                sender: "bot",
                text: "Halo! Selamat datang di layanan reservasi tukang.",
                created_at: CREATED_AT,
              },
            ],
            quick_replies: [
              {
                label: "Tanya-tanya dulu layanan tukang",
                value: "info",
              },
              { label: "Langsung reservasi", value: "reservation" },
            ],
            collected_slots: {},
            reservation_summary: null,
            price_breakdown: null,
            ticket: null,
          },
        }),
      });
      return;
    }

    if (request.method() === "POST" && pathname.endsWith("/messages")) {
      const body = request.postDataJSON() as { text: string };
      const step = steps[stepIndex];
      expect(
        step,
        `Tidak ada fixture untuk message ke-${stepIndex + 1}: ${body.text}`,
      ).toBeDefined();
      expect(body.text).toBe(step.expectedText);
      stepIndex += 1;

      await route.fulfill({
        contentType: "application/json",
        status: 200,
        body: JSON.stringify({
          status: {
            code: 120000000,
            message: "Success.",
            errorDetails: [],
          },
          data: responseData(step, stepIndex),
        }),
      });
      return;
    }

    await route.abort("failed");
  });

  return {
    assertComplete() {
      expect(stepIndex).toBe(steps.length);
    },
  };
}
