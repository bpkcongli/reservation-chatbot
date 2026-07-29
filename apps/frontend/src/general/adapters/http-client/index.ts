export type HttpMethod = "GET" | "POST" | "PUT" | "PATCH" | "DELETE";

export interface HttpRequest<TBody = unknown> {
  path: string;
  method: HttpMethod;
  body?: TBody;
  headers?: Record<string, string>;
}

export interface HttpResponse<TData> {
  data: TData;
  status: number;
}

export interface HttpClient {
  request<TData, TBody = unknown>(
    request: HttpRequest<TBody>,
  ): Promise<HttpResponse<TData>>;
}

export { default as AxiosHttpClient } from "./impl/AxiosHttpClient";
