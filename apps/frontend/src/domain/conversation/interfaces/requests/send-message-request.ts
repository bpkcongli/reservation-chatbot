import { z } from "zod";

export const sendMessageRequestSchema = z.object({
  client_message_id: z
    .string()
    .min(8)
    .max(100)
    .regex(/^[A-Za-z0-9_-]+$/),
  text: z.string().trim().min(1).max(1_000),
});

export type SendMessageRequest = z.infer<typeof sendMessageRequestSchema>;
