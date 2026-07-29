import { setupWorker } from "msw/browser";

import { handlers } from "@/general/mocks/handlers";

export const worker = setupWorker(...handlers);
