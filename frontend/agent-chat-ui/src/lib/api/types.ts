export interface RecentOrderDTO {
  id: number;
  order_number: string | null;
  status: string;
  total_amount: string | null;
  created_at: string;
  customer_name: string | null;
  first_product_name: string | null;
  item_count?: number;
}

export interface ProductMetricItemDTO {
  product_name: string;
  total_quantity: string;
  line_count: number;
}

export interface RecentInquiryDTO {
  id: number;
  inquiry_type: string;
  summary: string;
  status: string;
  created_at: string;
  customer_name: string | null;
}

export interface OrderMetricsDTO {
  total_count: number;
  status_counts: Record<string, number>;
  known_total_revenue: string;
  orders_with_unknown_revenue_count: number;
  recent_orders: RecentOrderDTO[];
}

export interface CustomerMetricsDTO {
  total_known_customers: number;
  repeat_customer_count: number;
}

export interface InquiryMetricsDTO {
  total_count: number;
  status_counts: Record<string, number>;
  recent_inquiries: RecentInquiryDTO[];
}

export interface BusinessAnalyticsReportDTO {
  business_id: number;
  order_metrics: OrderMetricsDTO;
  product_metrics: { top_products: ProductMetricItemDTO[] };
  inquiry_metrics: InquiryMetricsDTO;
  customer_metrics: CustomerMetricsDTO;
  feedback_metrics: { total_count: number; sentiment_counts: Record<string, number> };
}

export interface OrderSummaryDTO {
  id: number;
  order_number: string | null;
  status: string;
  total_amount: string | null;
  created_at: string;
  customer_name: string | null;
  first_product_name: string | null;
  item_count?: number;
}

export interface OrderItemDTO {
  product_name: string;
  quantity: string;
  unit_price: string | null;
  line_total: string | null;
}

export interface OrderDetailDTO {
  id: number;
  order_number: string | null;
  status: string;
  total_amount: string | null;
  created_at: string;
  customer_name: string | null;
  items: OrderItemDTO[];
}

export interface EvidenceMessageDTO {
  evidence_text: string;
  message_content: string | null;
  sender_name: string | null;
  sender_type: string | null;
  sent_at: string | null;
}

export interface InquirySummaryDTO {
  id: number;
  inquiry_type: string;
  summary: string;
  status: string;
  created_at: string;
  customer_name: string | null;
}

export interface ImportResultDTO {
  import_batch_id: number;
  status: string;
  is_successful: boolean;
  errors: string[];
  warnings: string[];
}

export interface ChatResponseDTO {
  response: string;
}

export interface ImportBatchDTO {
  id: number;
  import_name: string;
  source_file_name: string | null;
  status: string;
  created_at: string;
}
