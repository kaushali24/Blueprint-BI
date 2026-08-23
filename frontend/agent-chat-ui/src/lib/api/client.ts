import {
  BusinessAnalyticsReportDTO,
  OrderSummaryDTO,
  OrderDetailDTO,
  EvidenceMessageDTO,
  InquirySummaryDTO,
  ImportResultDTO,
  ChatResponseDTO,
} from "./types";

export class ApiError extends Error {
  constructor(
    public status: number,
    public body: any,
    message: string = "API Error"
  ) {
    super(message);
    this.name = "ApiError";
  }
}

const API_URL = "";

async function fetchWithHandling(input: RequestInfo | URL, init?: RequestInit) {
  const response = await fetch(input, init);
  
  if (!response.ok) {
    let body;
    try {
      body = await response.json();
    } catch {
      body = await response.text();
    }
    throw new ApiError(response.status, body, `HTTP ${response.status}`);
  }
  
  return response.json();
}

function normalizeAssistantResponse(raw: unknown): string {
  if (typeof raw === "string") return raw;
  if (Array.isArray(raw)) {
    return raw
      .map((block) => {
        if (typeof block === "string") return block;
        if (block && typeof block === "object" && "text" in block) {
          return String((block as { text: unknown }).text ?? "");
        }
        return "";
      })
      .filter(Boolean)
      .join("\n");
  }
  if (raw == null) return "";
  return String(raw);
}

export const apiClient = {
  getAnalytics: (businessId: number): Promise<BusinessAnalyticsReportDTO> =>
    fetchWithHandling(`${API_URL}/api/v1/businesses/${businessId}/analytics`),

  getOrders: (businessId: number): Promise<OrderSummaryDTO[]> =>
    fetchWithHandling(`${API_URL}/api/v1/businesses/${businessId}/orders`),

  getOrder: (businessId: number, orderId: number): Promise<OrderDetailDTO> =>
    fetchWithHandling(`${API_URL}/api/v1/businesses/${businessId}/orders/${orderId}`),

  getOrderEvidence: (businessId: number, orderId: number): Promise<EvidenceMessageDTO[]> =>
    fetchWithHandling(`${API_URL}/api/v1/businesses/${businessId}/orders/${orderId}/evidence`),

  getInquiries: (businessId: number): Promise<InquirySummaryDTO[]> =>
    fetchWithHandling(`${API_URL}/api/v1/businesses/${businessId}/inquiries`),

  uploadImport: (businessId: number, file: File): Promise<ImportResultDTO> => {
    const formData = new FormData();
    formData.append("business_id", businessId.toString());
    formData.append("file", file);
    return fetchWithHandling(`${API_URL}/api/v1/whatsapp/imports`, {
      method: "POST",
      body: formData,
      // Do NOT set Content-Type manually for FormData
    });
  },

  chat: async (businessId: number, message: string): Promise<ChatResponseDTO> => {
    const raw = await fetchWithHandling(`${API_URL}/api/v1/assistant/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ business_id: businessId, message }),
    });
    return { response: normalizeAssistantResponse(raw.response) };
  },
};
