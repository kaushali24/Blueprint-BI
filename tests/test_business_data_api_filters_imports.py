import pytest
from tests.conftest import make_business, make_order, make_inquiry, make_import_batch

class TestOrderFiltering:
    def test_orders_filtered_by_status(self, client, db):
        biz = make_business(db)

        # Create a pending order and a confirmed order
        make_order(db, biz, status='pending', total_amount=100)
        make_order(db, biz, status='confirmed', total_amount=200)
        db.commit()

        response = client.get(f"/api/v1/businesses/{biz.id}/orders?status=pending")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["status"] == "pending"

class TestInquiryFiltering:
    def test_inquiries_filtered_by_open_status(self, client, db):
        biz = make_business(db)

        # Create an open inquiry and a resolved inquiry
        make_inquiry(db, biz, status='investigating', inquiry_type='general', summary='Test')
        make_inquiry(db, biz, status='resolved', inquiry_type='general', summary='Test')
        db.commit()

        response = client.get(f"/api/v1/businesses/{biz.id}/inquiries?status=open")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["status"] == "investigating"

class TestImportsList:
    def test_list_recent_imports(self, client, db):
        biz = make_business(db)

        # Create imports
        make_import_batch(db, biz)
        db.commit()

        response = client.get(f"/api/v1/businesses/{biz.id}/imports")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["import_name"] == "test.zip"
        assert data[0]["status"] == "completed"
