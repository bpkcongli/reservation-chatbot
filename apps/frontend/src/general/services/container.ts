import "reflect-metadata";

import { Container } from "inversify";

import { createConversationContainer } from "@/domain/conversation/services/container";
import {
  AxiosHttpClient,
  type HttpClient,
} from "@/general/adapters/http-client";
import type { ClientEnvironment } from "@/general/interfaces/environment";
import { TYPES } from "@/general/services/types";

export function createRootContainer(environment: ClientEnvironment): Container {
  const container = new Container({ defaultScope: "Singleton" });

  container
    .bind<string>(TYPES.ApiBaseUrl)
    .toConstantValue(environment.NEXT_PUBLIC_API_BASE_URL);
  container.bind<HttpClient>(TYPES.HttpClient).to(AxiosHttpClient);

  const conversationContainer = createConversationContainer(container);
  container
    .bind<Container>(TYPES.ConversationContainer)
    .toConstantValue(conversationContainer);

  return container;
}
