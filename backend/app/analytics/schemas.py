from decimal import Decimal
from typing import List

from pydantic import BaseModel


class RecentOrderDTO(BaseModel):
    id: int
    order_number: str | None
    status: str
    total_amount: Decimal | None
    created_at: str


class RecentInquiryDTO(BaseModel):
    id: int
    inquiry_type: str
    summary: str
    status: str
    created_at: str


class OrderMetricsDTO(BaseModel):
    total_count: int
    status_counts: dict[str, int]
    known_total_revenue: Decimal
    orders_with_unknown_revenue_count: int
    recent_orders: List[RecentOrderDTO]


class ProductMetricItemDTO(BaseModel):
    product_name: str
    total_quantity: Decimal
    line_count: int


class ProductMetricsDTO(BaseModel):
    top_products: List[ProductMetricItemDTO]


class InquiryMetricsDTO(BaseModel):
    total_count: int
    status_counts: dict[str, int]
    recent_inquiries: List[RecentInquiryDTO]


class CustomerMetricsDTO(BaseModel):
    total_known_customers: int
    repeat_customer_count: int


class FeedbackMetricsDTO(BaseModel):
    total_count: int
    sentiment_counts: dict[str, int]


class BusinessAnalyticsReportDTO(BaseModel):
    business_id: int
    order_metrics: OrderMetricsDTO
    product_metrics: ProductMetricsDTO
    inquiry_metrics: InquiryMetricsDTO
    customer_metrics: CustomerMetricsDTO
    feedback_metrics: FeedbackMetricsDTO
