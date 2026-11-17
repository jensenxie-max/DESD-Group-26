"""Transactional local demo storage; a worker retry does not repeat a DB write."""

import json
from pathlib import Path
import sqlite3


def encode(value):
    return json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True)


class Store:
    def __init__(self, path):
        self.path = str(path)
        if self.path != ":memory:":
            Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.path, timeout=10, isolation_level=None)
        self.connection.row_factory = sqlite3.Row
        self.connection.executescript("""
            PRAGMA journal_mode=WAL;
            CREATE TABLE IF NOT EXISTS products(
                product_id TEXT PRIMARY KEY, version INTEGER NOT NULL,
                created_request_id TEXT NOT NULL, body TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS operations(
                operation_id TEXT PRIMARY KEY, action TEXT NOT NULL, result TEXT NOT NULL,
                recorded_at TEXT NOT NULL DEFAULT(strftime('%Y-%m-%dT%H:%M:%fZ','now')));
            CREATE TABLE IF NOT EXISTS customer_availability(
                product_id TEXT PRIMARY KEY, version INTEGER NOT NULL, available INTEGER NOT NULL);
            CREATE TABLE IF NOT EXISTS follow_ups(
                request_id TEXT PRIMARY KEY, product_id TEXT NOT NULL, body TEXT NOT NULL);
        """)

    def close(self):
        self.connection.close()

    def get_product(self, product_id):
        row = self.connection.execute("SELECT body FROM products WHERE product_id=?", (product_id,)).fetchone()
        if row is None:
            raise ValueError(f"Product {product_id!r} does not exist; seed it or complete F1 first")
        return json.loads(row["body"])

    def insert_product(self, product, request_id):
        self.connection.execute("INSERT INTO products VALUES(?,?,?,?)",
                                (product["productId"], product["version"], request_id, encode(product)))

    def update_product(self, product, expected_version):
        result = self.connection.execute("UPDATE products SET version=?,body=? WHERE product_id=? AND version=?",
                                         (product["version"], encode(product), product["productId"], expected_version))
        if result.rowcount != 1:
            raise RuntimeError("Optimistic product version changed during transaction")

    def once(self, operation_id, action, callback):
        self.connection.execute("BEGIN IMMEDIATE")
        try:
            row = self.connection.execute("SELECT action,result FROM operations WHERE operation_id=?", (operation_id,)).fetchone()
            if row:
                if row["action"] != action:
                    raise ValueError("An operation ID cannot be reused for a different action")
                result = json.loads(row["result"])
            else:
                result = callback()
                self.connection.execute("INSERT INTO operations(operation_id,action,result) VALUES(?,?,?)",
                                        (operation_id, action, encode(result)))
            self.connection.commit()
            return result
        except BaseException:
            self.connection.rollback()
            raise

    def sync_availability(self, product_id):
        product = self.get_product(product_id)
        self.connection.execute("""INSERT INTO customer_availability VALUES(?,?,?)
            ON CONFLICT(product_id) DO UPDATE SET version=excluded.version,available=excluded.available
            WHERE excluded.version >= customer_availability.version""",
                                (product_id, product["version"], int(product["available"])))
        return {"productId": product_id, "version": product["version"], "available": product["available"]}

    def follow_up(self, request_id, product_id, result):
        self.connection.execute("INSERT INTO follow_ups VALUES(?,?,?) ON CONFLICT(request_id) DO UPDATE SET body=excluded.body",
                                (request_id, product_id, encode(result)))

    def snapshot(self):
        return {"storage": "SQLite", "products": [json.loads(r[0]) for r in self.connection.execute("SELECT body FROM products ORDER BY product_id")],
                "customerAvailability": [dict(r) for r in self.connection.execute("SELECT * FROM customer_availability ORDER BY product_id")],
                "followUps": [json.loads(r[0]) for r in self.connection.execute("SELECT body FROM follow_ups ORDER BY request_id")],
                "operations": [dict(r) for r in self.connection.execute("SELECT operation_id,action,recorded_at FROM operations ORDER BY recorded_at,operation_id")]}
