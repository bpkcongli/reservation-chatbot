import { setupServer } from "msw/node";

import { handlers } from "@/general/mocks/handlers";

export const server = setupServer(...handlers);
