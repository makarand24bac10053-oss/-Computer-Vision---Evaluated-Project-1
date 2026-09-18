"""
Unit tests for Module 5: Storage & SQLite Database Management.
"""

import pytest
import os
from src.storage import DatabaseManager


@pytest.fixture
def temp_db(tmp_path):
    db_file = tmp_path / "test_inspection.db"
    return DatabaseManager(db_path=str(db_file))


def test_db_initialization(temp_db):
    analytics = temp_db.get_qc_analytics()
    assert analytics["total_scans"] == 0
    assert analytics["pass_rate_pct"] == 100.0


def test_log_inspection_and_query(temp_db):
    product = {"sku": "SKU-BEV-001", "name": "Citrus Soda", "detection_method": "OPTICAL_QR"}
    qc_result = {"status": "PASS", "defect_score": 2.5, "defect_count": 0, "defects": []}

    rec_id = temp_db.log_inspection(product, qc_result, image_filename="sample.png")
    assert rec_id > 0

    recent = temp_db.get_recent_inspections(limit=5)
    assert len(recent) == 1
    assert recent[0]["sku"] == "SKU-BEV-001"
    assert recent[0]["status"] == "PASS"


def test_save_transaction_and_analytics(temp_db):
    # Log 1 pass and 1 reject
    temp_db.log_inspection({"sku": "SKU-1", "name": "Item 1"}, {"status": "PASS", "defect_score": 1.0, "defect_count": 0, "defects": []})
    temp_db.log_inspection({"sku": "SKU-2", "name": "Item 2"}, {"status": "REJECT", "defect_score": 35.0, "defect_count": 2, "defects": []})

    analytics = temp_db.get_qc_analytics()
    assert analytics["total_scans"] == 2
    assert analytics["pass_count"] == 1
    assert analytics["reject_count"] == 1
    assert analytics["pass_rate_pct"] == 50.0

    # Save transaction
    receipt = {
        "receipt_id": "REC-TEST1234",
        "timestamp": "2026-09-18 00:00:00",
        "items": [{"sku": "SKU-1", "quantity": 1}],
        "subtotal": 10.00,
        "tax": 0.80,
        "discount": 0.0,
        "grand_total": 10.80,
        "payment_method": "UPI"
    }
    tx_id = temp_db.save_transaction(receipt)
    assert tx_id > 0
