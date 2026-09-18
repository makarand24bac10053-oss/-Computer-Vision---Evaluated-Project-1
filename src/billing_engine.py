"""
Module 4: Automated Retail Billing & Inventory Engine.
Maintains session shopping cart, calculates subtotal, GST/sales taxes, discount rules,
quarantines defective items, and produces structured itemized sales receipts.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid


class BillingSystem:
    """
    Retail transaction controller integrating real-time computer vision inspection
    with automated point-of-sale operations.
    """

    def __init__(self, discount_rate: float = 0.0):
        self.cart: Dict[str, Dict[str, Any]] = {}
        self.discount_rate = discount_rate
        self.quarantined_items: List[Dict[str, Any]] = []

    def process_inspected_item(
        self,
        product: Dict[str, Any],
        qc_result: Dict[str, Any],
        allow_defective_override: bool = False
    ) -> Dict[str, Any]:
        """
        Evaluate inspected item and conditionally add to cart or route to defect quarantine.
        """
        sku = product.get("sku", "UNKNOWN")
        name = product.get("name", "Unknown Item")
        price = float(product.get("price", 0.0))
        tax_rate = float(product.get("tax_rate", 0.08))
        qc_status = qc_result.get("status", "PASS")
        defect_score = qc_result.get("defect_score", 0.0)

        # Rejection policy: Defective products cannot be billed normally
        if qc_status == "REJECT" and not allow_defective_override:
            incident = {
                "sku": sku,
                "name": name,
                "price": price,
                "defect_score": defect_score,
                "reason": f"Quality Failure: Defect score {defect_score}% exceeds tolerance threshold.",
                "timestamp": datetime.now().isoformat()
            }
            self.quarantined_items.append(incident)
            return {
                "action": "QUARANTINED",
                "message": f"Item '{name}' rejected by vision QC ({defect_score}% defect score). Cannot be added to cart.",
                "incident": incident
            }

        # Item accepted (PASS or approved WARNING)
        if sku in self.cart:
            self.cart[sku]["quantity"] += 1
            self.cart[sku]["total_price"] = round(self.cart[sku]["quantity"] * price, 2)
        else:
            self.cart[sku] = {
                "sku": sku,
                "name": name,
                "category": product.get("category", "General"),
                "unit_price": price,
                "quantity": 1,
                "tax_rate": tax_rate,
                "total_price": price,
                "qc_status": qc_status,
                "defect_score": defect_score
            }

        return {
            "action": "ADDED_TO_CART",
            "message": f"Item '{name}' verified ({qc_status}) and added to shopping cart.",
            "cart_summary": self.get_cart_summary()
        }

    def remove_item(self, sku: str) -> bool:
        """Remove a product from the shopping cart by SKU."""
        if sku in self.cart:
            del self.cart[sku]
            return True
        return False

    def clear_cart(self) -> None:
        """Reset cart and quarantine logs."""
        self.cart.clear()
        self.quarantined_items.clear()

    def get_cart_summary(self) -> Dict[str, Any]:
        """
        Calculate financial metrics for the current cart.
        """
        items_list = list(self.cart.values())
        subtotal = sum(item["unit_price"] * item["quantity"] for item in items_list)
        tax_total = sum(item["unit_price"] * item["quantity"] * item["tax_rate"] for item in items_list)
        discount_amount = subtotal * self.discount_rate
        grand_total = max(0.0, subtotal - discount_amount + tax_total)
        total_items_count = sum(item["quantity"] for item in items_list)

        return {
            "items": items_list,
            "total_items_count": total_items_count,
            "subtotal": round(subtotal, 2),
            "tax_total": round(tax_total, 2),
            "discount_rate_pct": round(self.discount_rate * 100, 1),
            "discount_amount": round(discount_amount, 2),
            "grand_total": round(grand_total, 2),
            "quarantined_count": len(self.quarantined_items),
            "quarantined_items": self.quarantined_items
        }

    def generate_receipt(self, payment_method: str = "Digital Wallet / UPI") -> Dict[str, Any]:
        """
        Produce a finalized itemized receipt document.
        """
        summary = self.get_cart_summary()
        if summary["total_items_count"] == 0:
            raise ValueError("Cannot generate receipt for an empty cart.")

        receipt_id = f"REC-{uuid.uuid4().hex[:8].upper()}"
        receipt = {
            "receipt_id": receipt_id,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "payment_method": payment_method,
            "payment_status": "PAID",
            "store_name": "VisionCart Autonomous Smart Mart",
            "store_address": "VIT Campus Innovation Hub, Technology Tower",
            "items": summary["items"],
            "subtotal": summary["subtotal"],
            "tax": summary["tax_total"],
            "discount": summary["discount_amount"],
            "grand_total": summary["grand_total"]
        }
        return receipt
