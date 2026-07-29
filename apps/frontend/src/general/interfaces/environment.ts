import { z } from "zod";

const clientEnvironmentSchema = z.object({
  NEXT_PUBLIC_API_BASE_URL: z
    .string()
    .url()
    .default("http://localhost:8000/api/v1"),
  NEXT_PUBLIC_USE_MOCKS: z.enum(["true", "false"]).default("false"),
});

export type ClientEnvironment = z.infer<typeof clientEnvironmentSchema>;

export function getClientEnvironment(): ClientEnvironment {
  return clientEnvironmentSchema.parse({
    NEXT_PUBLIC_API_BASE_URL: process.env.NEXT_PUBLIC_API_BASE_URL,
    NEXT_PUBLIC_USE_MOCKS: process.env.NEXT_PUBLIC_USE_MOCKS,
  });
}
