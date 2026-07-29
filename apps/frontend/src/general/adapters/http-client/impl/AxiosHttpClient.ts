import axios, { type AxiosInstance } from "axios";
import { inject, injectable } from "inversify";

import {
  type HttpClient,
  HttpClientError,
  type HttpRequest,
  type HttpResponse,
} from "@/general/adapters/http-client";
import { TYPES } from "@/general/services/types";

@injectable()
export default class AxiosHttpClient implements HttpClient {
  private readonly client: AxiosInstance;

  constructor(@inject(TYPES.ApiBaseUrl) apiBaseUrl: string) {
    this.client = axios.create({
      baseURL: apiBaseUrl,
      headers: {
        "Accept-Language": "id-ID",
        "Content-Type": "application/json",
      },
      timeout: 10_000,
    });
  }

  async request<TData, TBody = unknown>({
    path,
    method,
    body,
    headers,
  }: HttpRequest<TBody>): Promise<HttpResponse<TData>> {
    try {
      const response = await this.client.request<TData>({
        url: path,
        method,
        data: body,
        headers,
      });

      return {
        data: response.data,
        status: response.status,
      };
    } catch (error) {
      if (axios.isAxiosError(error)) {
        throw new HttpClientError(
          error.response?.data?.status?.message ??
            "Permintaan ke layanan tidak berhasil.",
          error.response?.status ?? null,
          { cause: error },
        );
      }

      throw error;
    }
  }
}
