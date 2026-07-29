import { z } from "zod";

const conversationStates = [
  "WELCOME",
  "INFO_MODE",
  "FALLBACK",
  "SELECT_SERVICE",
  "BORONGAN_ASK_CUSTOMER_ID",
  "BORONGAN_ASK_PHONE",
  "BORONGAN_ASK_BUILDING",
  "BORONGAN_ASK_ADDRESS",
  "BORONGAN_ASK_SURVEY_DATE",
  "BORONGAN_ASK_SURVEY_TIME",
  "BORONGAN_ASK_BUDGET",
  "HARIAN_ASK_CUSTOMER_ID",
  "HARIAN_ASK_PHONE",
  "HARIAN_ASK_SPECIALIZATION",
  "HARIAN_ASK_DESCRIPTION",
  "HARIAN_ASK_WORKER_COUNT",
  "HARIAN_ASK_START_DATE",
  "HARIAN_ASK_END_DATE",
  "HARIAN_ASK_SESSION",
  "HARIAN_ASK_PHOTO",
  "HARIAN_ASK_ADDRESS",
  "CALCULATE_PRICE",
  "CONFIRM_RESERVATION",
  "EDIT_SLOT",
  "TICKET_LOOKUP",
  "TICKET_CREATED",
  "CANCELLED",
] as const;

export const conversationIdSchema = z
  .string()
  .length(26)
  .regex(/^[0-9A-HJKMNP-TV-Z]{26}$/);

export const attachmentSchema = z.object({
  attachment_id: conversationIdSchema,
  content_type: z.enum(["image/jpeg", "image/png", "image/webp"]),
  size_bytes: z.number().int().positive(),
  status: z.literal("ready"),
});

const boronganReservationSummarySchema = z.object({
  service_type: z.literal("borongan"),
  customer_id: z.string().regex(/^\d{10}$/),
  phone_number_masked: z.string().min(1),
  building_type: z.enum(["rumah", "apartemen", "ruko"]),
  survey_address: z.string().min(1),
  survey_date: z.string().date(),
  survey_time: z.string().regex(/^([01]\d|2[0-3]):[0-5]\d$/),
  budget: z.number().int().positive(),
});

const harianReservationSummarySchema = z.object({
  service_type: z.literal("harian"),
  customer_id: z.string().regex(/^\d{10}$/),
  phone_number_masked: z.string().min(1),
  specialization: z.enum([
    "cat",
    "genteng",
    "ac",
    "listrik",
    "keramik",
    "pipa",
  ]),
  problem_description: z.string().min(1),
  worker_count: z.number().int().positive(),
  start_date: z.string().date(),
  end_date: z.string().date(),
  work_session: z.enum(["full_day", "morning", "afternoon"]),
  work_address: z.string().min(1),
  attachment: attachmentSchema.nullable(),
});

const priceBreakdownBase = {
  pricing_version: z.literal("pricing-v1"),
  currency: z.literal("IDR"),
  admin_fee: z.number().int().nonnegative(),
  estimated_price: z.number().int().nonnegative(),
  disclaimer: z.string().min(1),
};

const harianPriceBreakdownSchema = z.object({
  ...priceBreakdownBase,
  service_type: z.literal("harian"),
  specialization: harianReservationSummarySchema.shape.specialization,
  work_session: harianReservationSummarySchema.shape.work_session,
  unit_rate: z.number().int().positive(),
  worker_count: z.number().int().positive(),
  day_count: z.number().int().positive(),
  subtotal: z.number().int().nonnegative(),
});

const boronganPriceBreakdownSchema = z.object({
  ...priceBreakdownBase,
  service_type: z.literal("borongan"),
  building_type: boronganReservationSummarySchema.shape.building_type,
  base_price: z.number().int().positive(),
  survey_fee: z.number().int().positive(),
  subtotal: z.number().int().positive(),
  budget: z.number().int().positive(),
});

const ticketSchema = z.object({
  ticket_number: z.string().regex(/^TKT-[0-9]{8}-[A-Z0-9]{6}$/),
  service_type: z.enum(["borongan", "harian"]),
  status: z.literal("MENUNGGU_PEMBAYARAN"),
  pricing_version: z.literal("pricing-v1"),
  estimated_price: z.number().int().positive(),
  budget: z.number().int().positive().nullable(),
  created_at: z.string().datetime({ offset: true }),
  email_delivery: z.literal("NOT_IMPLEMENTED"),
});

export const conversationResponseSchema = z.object({
  status: z.object({
    code: z.union([z.literal(120000000), z.literal(120100000)]),
    message: z.string().min(1),
    errorDetails: z.array(z.unknown()),
  }),
  data: z.object({
    conversation_id: conversationIdSchema,
    state: z.enum(conversationStates),
    messages: z.array(
      z.object({
        id: z.string().length(26),
        sender: z.enum(["bot", "user"]),
        text: z.string().min(1),
        created_at: z.string().datetime({ offset: true }),
      }),
    ),
    quick_replies: z.array(
      z.object({
        label: z.string().min(1),
        value: z.string().min(1),
      }),
    ),
    collected_slots: z.record(z.string(), z.unknown()),
    reservation_summary: z
      .discriminatedUnion("service_type", [
        boronganReservationSummarySchema,
        harianReservationSummarySchema,
      ])
      .nullable(),
    price_breakdown: z
      .discriminatedUnion("service_type", [
        harianPriceBreakdownSchema,
        boronganPriceBreakdownSchema,
      ])
      .nullable(),
    ticket: ticketSchema.nullable(),
  }),
});

export type ConversationResponse = z.infer<typeof conversationResponseSchema>;

export const attachmentUploadResponseSchema = z.object({
  status: z.object({
    code: z.literal(120100000),
    message: z.string().min(1),
    errorDetails: z.array(z.unknown()),
  }),
  data: z.object({
    conversation_id: conversationIdSchema,
    attachment: attachmentSchema,
  }),
});

export type AttachmentUploadResponse = z.infer<
  typeof attachmentUploadResponseSchema
>;
