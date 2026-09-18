"""
Unit tests for Module 4: Automated Retail Billing Engine.
"""

import pytest
from src.billing_engine import BillingSystem


@pytest.fixture
def billing_system():
    return BillingSystem(discount_rate=0.10)  # 10% discount for testing


@pytest.fixture
def clean_product():
    return {
        "sku": "SKU-BEV-001",
        "name": "Sparkling Citrus Soda (330ml)",
        "price": 2.50,
        "tax_rate": 0.08,
        "category": "Beverages"
    }


@pytest.fixture
def defective_product():
    return {
        "sku": "SKU-SNK-002",
        "name": "Damaged Oat Flakes",
        "price": 4.00,
        "tax_rate": 0.05,
        "category": "Snacks"
    }


def test_add_passed_item_to_cart(billing_system, clean_product):
    qc_pass = {"status": "PASS", "defect_score": 1.5}
    res = billing_system.process_inspected_item(clean_product, qc_pass)

    assert res["action"] == "ADDED_TO_CART"
    summary = billing_system.get_cart_summary()
    assert summary["total_items_count"] == 1
    assert summary["subtotal"] == 2.50


def test_reject_item_routes_to_quarantine(billing_system, defective_product):
    qc_reject = {"status": "REJECT", "defect_score": 42.0}
    res = billing_system.process_inspected_item(defective_product, qc_reject)

    assert res["action"] == "QUARANTINED"
    summary = billing_system.get_cart_summary()
    assert summary["total_items_count"] == 0  # Not in cart
    assert summary["quarantined_count"] == 1


def test_multiple_items_and_receipt_generation(billing_system, clean_product):
    qc_pass = {"status": "PASS", "defect_score": 2.0}
    billing_system.process_inspected_item(clean_product, qc_pass)
    billing_system.process_inspected_item(clean_product, qc_pass)  # 2 units

    summary = billing_system.get_cart_summary()
    assert summary["total_items_count"] == 2
    assert summary["subtotal"] == 5.00
    assert summary["discount_amount"] == 0.50  # 10% of 5.00
    assert summary["tax_total"] == 0.40       # 8% of 5.00
    assert summary["grand_total"] == 4.90     # 5.00 - 0.50 + 0.40

    receipt = billing_system.generate_receipt()
    assert receipt["receipt_id"].startswith("REC-")
    assert receipt["payment_status"] == "PAID"
    assert receipt["grand_total"] == 4.90


def test_empty_cart_receipt_error(billing_system):
    with pytest.raises(ValueError):
        billing_system.generate_receipt()
