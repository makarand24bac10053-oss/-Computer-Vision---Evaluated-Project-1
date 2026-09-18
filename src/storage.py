"""
Module 5: Storage & Database Management.
Manages relational SQLite persistence for inspection event telemetry,
defect incident logs, and checkout transactions.
"""

import sqlite3
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from src.config import DATABASE_PATH


class DatabaseManager:
    """
    Handles SQLite transactions and audit queries for quality control logs.
    """

    def __init__(self, db_path: str = str(DATABASE_PATH)):
        self.db_path = db_path
        self.init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self) -> None:
        """Initialize database schema tables."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Table for vision inspection logs
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS inspections (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    sku TEXT NOT NULL,
                    product_name TEXT NOT NULL,
                    status TEXT NOT NULL,
                    defect_score REAL NOT NULL,
                    defect_count INTEGER NOT NULL,
                    defects_json TEXT,
                    scan_method TEXT,
                    image_filename TEXT
                )
            """)

            # Table for point-of-sale transactions
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    receipt_id TEXT UNIQUE NOT NULL,
                    timestamp TEXT NOT NULL,
                    item_count INTEGER NOT NULL,
                    subtotal REAL NOT NULL,
                    tax REAL NOT NULL,
                    discount REAL NOT NULL,
                    grand_total REAL NOT NULL,
                    payment_method TEXT NOT NULL,
                    items_json TEXT NOT NULL
                )
            """)
            conn.commit()

    def log_inspection(
        self,
        product: Dict[str, Any],
        qc_result: Dict[str, Any],
        image_filename: str = ""
    ) -> int:
        """Record an inspection result to the database."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO inspections (
                    timestamp, sku, product_name, status, defect_score,
                    defect_count, defects_json, scan_method, image_filename
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                product.get("sku", "UNKNOWN"),
                product.get("name", "Unknown Item"),
                qc_result.get("status", "PASS"),
                float(qc_result.get("defect_score", 0.0)),
                int(qc_result.get("defect_count", 0)),
                json.dumps(qc_result.get("defects", [])),
                product.get("detection_method", "VISION"),
                image_filename
            ))
            conn.commit()
            return cursor.lastrowid

    def save_transaction(self, receipt: Dict[str, Any]) -> int:
        """Persist a completed sales receipt."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO transactions (
                    receipt_id, timestamp, item_count, subtotal,
                    tax, discount, grand_total, payment_method, items_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                receipt["receipt_id"],
                receipt["timestamp"],
                sum(item["quantity"] for item in receipt["items"]),
                receipt["subtotal"],
                receipt["tax"],
                receipt.get("discount", 0.0),
                receipt["grand_total"],
                receipt["payment_method"],
                json.dumps(receipt["items"])
            ))
            conn.commit()
            return cursor.lastrowid

    def get_recent_inspections(self, limit: int = 25) -> List[Dict[str, Any]]:
        """Retrieve recent inspection logs."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM inspections ORDER BY id DESC LIMIT ?
            """, (limit,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def get_qc_analytics(self) -> Dict[str, Any]:
        """Aggregate statistical metrics for quality compliance reporting."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    COUNT(*) AS total_scans,
                    SUM(CASE WHEN status = 'PASS' THEN 1 ELSE 0 END) AS pass_count,
                    SUM(CASE WHEN status = 'WARNING' THEN 1 ELSE 0 END) AS warn_count,
                    SUM(CASE WHEN status = 'REJECT' THEN 1 ELSE 0 END) AS reject_count,
                    AVG(defect_score) AS avg_defect_score
                FROM inspections
            """)
            row = cursor.fetchone()
            total = row["total_scans"] if row and row["total_scans"] else 0
            pass_c = row["pass_count"] if row and row["pass_count"] else 0
            warn_c = row["warn_count"] if row and row["warn_count"] else 0
            rej_c = row["reject_count"] if row and row["reject_count"] else 0
            avg_score = round(row["avg_defect_score"], 2) if row and row["avg_defect_score"] else 0.0
            pass_rate = round((pass_c / total * 100), 1) if total > 0 else 100.0

            return {
                "total_scans": total,
                "pass_count": pass_c,
                "warning_count": warn_c,
                "reject_count": rej_c,
                "pass_rate_pct": pass_rate,
                "avg_defect_score": avg_score
            }
