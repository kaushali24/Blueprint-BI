from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database.models import Order, OrderItem, Inquiry, Customer, Feedback, ExtractionTarget
from app.analytics.schemas import (
    BusinessAnalyticsReportDTO,
    CustomerMetricsDTO,
    FeedbackMetricsDTO,
    InquiryMetricsDTO,
    OrderMetricsDTO,
    ProductMetricItemDTO,
    ProductMetricsDTO,
    RecentInquiryDTO,
    RecentOrderDTO,
)


class AnalyticsService:
    @staticmethod
    def get_order_metrics(session: Session, business_id: int) -> OrderMetricsDTO:
        # Total count and status counts
        status_counts_query = select(Order.status, func.count(Order.id)).where(
            Order.business_id == business_id
        ).group_by(Order.status)
        
        status_counts = {row[0]: row[1] for row in session.execute(status_counts_query).all()}
        total_count = sum(status_counts.values())

        # Revenue logic (only confirmed orders)
        revenue_query = select(
            func.sum(Order.total_amount).label("known_total_revenue"),
            func.count(Order.id).filter(Order.total_amount.is_(None)).label("unknown_count")
        ).where(
            Order.business_id == business_id,
            Order.status == 'confirmed'
        )
        revenue_result = session.execute(revenue_query).first()
        
        known_total_revenue = revenue_result.known_total_revenue if revenue_result and revenue_result.known_total_revenue is not None else Decimal("0")
        orders_with_unknown_revenue_count = revenue_result.unknown_count if revenue_result and revenue_result.unknown_count is not None else 0

        # Recent orders
        from sqlalchemy.orm import joinedload
        recent_orders_query = select(Order).options(
            joinedload(Order.customer),
            joinedload(Order.order_items),
            joinedload(Order.extraction_target).joinedload(ExtractionTarget.end_message)
        ).where(
            Order.business_id == business_id
        ).order_by(
            Order.created_at.desc(),
            Order.id.desc()
        ).limit(5)
        
        recent_orders = []
        for order in session.scalars(recent_orders_query).unique():
            customer_name = order.customer.name if order.customer else None
            first_item = order.order_items[0] if order.order_items else None
            first_product_name = first_item.product_name if first_item else None
            
            order_date = order.created_at
            if order.extraction_target and order.extraction_target.end_message and order.extraction_target.end_message.sent_at:
                order_date = order.extraction_target.end_message.sent_at
                
            recent_orders.append(
                RecentOrderDTO(
                    id=order.id,
                    order_number=order.order_number,
                    status=order.status,
                    total_amount=order.total_amount,
                    created_at=order_date.isoformat(),
                    customer_name=customer_name,
                    first_product_name=first_product_name
                )
            )

        return OrderMetricsDTO(
            total_count=total_count,
            status_counts=status_counts,
            known_total_revenue=known_total_revenue,
            orders_with_unknown_revenue_count=orders_with_unknown_revenue_count,
            recent_orders=recent_orders
        )

    @staticmethod
    def get_product_metrics(session: Session, business_id: int) -> ProductMetricsDTO:
        query = select(
            OrderItem.product_name,
            func.sum(OrderItem.quantity).label("total_quantity"),
            func.count(OrderItem.id).label("line_count")
        ).join(Order, Order.id == OrderItem.order_id).where(
            Order.business_id == business_id,
            Order.status == 'confirmed'
        ).group_by(
            OrderItem.product_name
        ).order_by(
            func.sum(OrderItem.quantity).desc(),
            func.count(OrderItem.id).desc(),
            OrderItem.product_name.asc()
        ).limit(10)
        
        top_products = []
        for row in session.execute(query).all():
            top_products.append(
                ProductMetricItemDTO(
                    product_name=row.product_name,
                    total_quantity=row.total_quantity if row.total_quantity is not None else Decimal("0"),
                    line_count=row.line_count
                )
            )
            
        return ProductMetricsDTO(top_products=top_products)

    @staticmethod
    def get_inquiry_metrics(session: Session, business_id: int) -> InquiryMetricsDTO:
        status_counts_query = select(Inquiry.status, func.count(Inquiry.id)).where(
            Inquiry.business_id == business_id
        ).group_by(Inquiry.status)
        
        status_counts = {row[0]: row[1] for row in session.execute(status_counts_query).all()}
        total_count = sum(status_counts.values())
        
        recent_inquiries_query = select(Inquiry).where(
            Inquiry.business_id == business_id
        ).order_by(
            Inquiry.created_at.desc(),
            Inquiry.id.desc()
        ).limit(5)
        
        recent_inquiries = []
        for inquiry in session.scalars(recent_inquiries_query):
            recent_inquiries.append(
                RecentInquiryDTO(
                    id=inquiry.id,
                    inquiry_type=inquiry.inquiry_type,
                    summary=inquiry.summary,
                    status=inquiry.status,
                    created_at=inquiry.created_at.isoformat()
                )
            )
            
        return InquiryMetricsDTO(
            total_count=total_count,
            status_counts=status_counts,
            recent_inquiries=recent_inquiries
        )

    @staticmethod
    def get_customer_metrics(session: Session, business_id: int) -> CustomerMetricsDTO:
        total_known_customers = session.scalar(
            select(func.count(Customer.id)).where(Customer.business_id == business_id)
        ) or 0
        
        # Repeat customer logic: > 1 confirmed order for the same non-null customer_id
        subquery = select(
            Order.customer_id,
            func.count(Order.id).label("confirmed_order_count")
        ).where(
            Order.business_id == business_id,
            Order.status == 'confirmed',
            Order.customer_id.is_not(None)
        ).group_by(Order.customer_id).having(
            func.count(Order.id) > 1
        ).subquery()
        
        repeat_customer_count = session.scalar(
            select(func.count()).select_from(subquery)
        ) or 0
        
        return CustomerMetricsDTO(
            total_known_customers=total_known_customers,
            repeat_customer_count=repeat_customer_count
        )

    @staticmethod
    def get_feedback_metrics(session: Session, business_id: int) -> FeedbackMetricsDTO:
        sentiment_counts_query = select(Feedback.sentiment, func.count(Feedback.id)).where(
            Feedback.business_id == business_id
        ).group_by(Feedback.sentiment)
        
        sentiment_counts = {row[0]: row[1] for row in session.execute(sentiment_counts_query).all()}
        total_count = sum(sentiment_counts.values())
        
        return FeedbackMetricsDTO(
            total_count=total_count,
            sentiment_counts=sentiment_counts
        )

    @staticmethod
    def get_business_analytics_report(session: Session, business_id: int) -> BusinessAnalyticsReportDTO:
        return BusinessAnalyticsReportDTO(
            business_id=business_id,
            order_metrics=AnalyticsService.get_order_metrics(session, business_id),
            product_metrics=AnalyticsService.get_product_metrics(session, business_id),
            inquiry_metrics=AnalyticsService.get_inquiry_metrics(session, business_id),
            customer_metrics=AnalyticsService.get_customer_metrics(session, business_id),
            feedback_metrics=AnalyticsService.get_feedback_metrics(session, business_id),
        )
