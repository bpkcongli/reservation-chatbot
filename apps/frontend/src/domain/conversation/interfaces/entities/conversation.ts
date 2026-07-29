export type ConversationState =
  | "WELCOME"
  | "INFO_MODE"
  | "FALLBACK"
  | "SELECT_SERVICE"
  | "BORONGAN_ASK_CUSTOMER_ID"
  | "BORONGAN_ASK_PHONE"
  | "BORONGAN_ASK_BUILDING"
  | "BORONGAN_ASK_ADDRESS"
  | "BORONGAN_ASK_SURVEY_DATE"
  | "BORONGAN_ASK_SURVEY_TIME"
  | "BORONGAN_ASK_BUDGET"
  | "HARIAN_ASK_CUSTOMER_ID"
  | "HARIAN_ASK_PHONE"
  | "HARIAN_ASK_SPECIALIZATION"
  | "HARIAN_ASK_DESCRIPTION"
  | "HARIAN_ASK_WORKER_COUNT"
  | "HARIAN_ASK_START_DATE"
  | "HARIAN_ASK_END_DATE"
  | "HARIAN_ASK_SESSION"
  | "HARIAN_ASK_PHOTO"
  | "HARIAN_ASK_ADDRESS"
  | "CALCULATE_PRICE"
  | "CONFIRM_RESERVATION"
  | "EDIT_SLOT"
  | "TICKET_LOOKUP"
  | "TICKET_CREATED"
  | "CANCELLED";

export interface ChatMessage {
  id: string;
  sender: "bot" | "user";
  text: string;
  createdAt: string;
}

export interface QuickReply {
  label: string;
  value: string;
}

export interface Attachment {
  attachment_id: string;
  content_type: "image/jpeg" | "image/png" | "image/webp";
  size_bytes: number;
  status: "ready";
}

export interface BoronganReservationSummary {
  service_type: "borongan";
  customer_id: string;
  phone_number_masked: string;
  building_type: "rumah" | "apartemen" | "ruko";
  survey_address: string;
  survey_date: string;
  survey_time: string;
  budget: number;
}

export interface HarianReservationSummary {
  service_type: "harian";
  customer_id: string;
  phone_number_masked: string;
  specialization: "cat" | "genteng" | "ac" | "listrik" | "keramik" | "pipa";
  problem_description: string;
  worker_count: number;
  start_date: string;
  end_date: string;
  work_session: "full_day" | "morning" | "afternoon";
  work_address: string;
  attachment: Attachment | null;
}

export type ReservationSummary =
  BoronganReservationSummary | HarianReservationSummary;

interface PriceBreakdownBase {
  pricing_version: "pricing-v1";
  currency: "IDR";
  admin_fee: number;
  estimated_price: number;
  disclaimer: string;
}

export interface HarianPriceBreakdown extends PriceBreakdownBase {
  service_type: "harian";
  specialization: HarianReservationSummary["specialization"];
  work_session: HarianReservationSummary["work_session"];
  unit_rate: number;
  worker_count: number;
  day_count: number;
  subtotal: number;
}

export interface BoronganPriceBreakdown extends PriceBreakdownBase {
  service_type: "borongan";
  building_type: BoronganReservationSummary["building_type"];
  base_price: number;
  survey_fee: number;
  subtotal: number;
  budget: number;
}

export type PriceBreakdown = HarianPriceBreakdown | BoronganPriceBreakdown;

export interface Ticket {
  ticket_number: string;
  service_type: "borongan" | "harian";
  status: "MENUNGGU_PEMBAYARAN";
  pricing_version: "pricing-v1";
  estimated_price: number;
  budget: number | null;
  created_at: string;
  email_delivery: "NOT_IMPLEMENTED";
}
