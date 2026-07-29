import { z } from "zod";

export const conversationIdSchema = z
  .string()
  .length(26)
  .regex(/^[0-9A-HJKMNP-TV-Z]{26}$/);

export const conversationResponseSchema = z.object({
  status: z.object({
    code: z.union([z.literal(120000000), z.literal(120100000)]),
    message: z.string().min(1),
    errorDetails: z.array(z.unknown()),
  }),
  data: z.object({
    conversation_id: conversationIdSchema,
    state: z.string().min(1),
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
    reservation_summary: z.record(z.string(), z.unknown()).nullable(),
    price_breakdown: z.record(z.string(), z.unknown()).nullable(),
    ticket: z.record(z.string(), z.unknown()).nullable(),
  }),
});

export type ConversationResponse = z.infer<typeof conversationResponseSchema>;
