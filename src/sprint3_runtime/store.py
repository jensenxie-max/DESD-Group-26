"""Durable follow-up lifecycle and explicit message-delivery observations."""

from datetime import datetime, timezone
import json

from sprint2_runtime.store import Store as Sprint2Store, encode


def now():
    return datetime.now(timezone.utc).isoformat()


class Store(Sprint2Store):
    def __init__(self, path):
        super().__init__(path)
        self.connection.executescript("""
            CREATE TABLE IF NOT EXISTS follow_up_events(
                event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                request_id TEXT NOT NULL, status TEXT NOT NULL,
                body TEXT NOT NULL, recorded_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS message_outbox(
                operation_id TEXT PRIMARY KEY, action TEXT NOT NULL,
                message_name TEXT NOT NULL, correlation_key TEXT NOT NULL,
                message_id TEXT NOT NULL, payload TEXT NOT NULL,
                status TEXT NOT NULL, response TEXT, error TEXT,
                recorded_at TEXT NOT NULL, updated_at TEXT NOT NULL);
        """)

    def find_product(self, product_id):
        row = self.connection.execute("SELECT body FROM products WHERE product_id=?", (product_id,)).fetchone()
        return json.loads(row["body"]) if row else None

    def get_follow_up(self, request_id):
        row = self.connection.execute("SELECT body FROM follow_ups WHERE request_id=?", (request_id,)).fetchone()
        return json.loads(row["body"]) if row else None

    def set_follow_up(self, request_id, product_id, result):
        previous = self.get_follow_up(request_id)
        if previous and previous.get("productId") != product_id:
            raise ValueError("A follow-up request cannot be reused for a different product")
        stamp = now()
        value = {**(previous or {}), **result, "requestId": request_id, "productId": product_id,
                 "assignedRole": "Catalogue and producer support", "updatedAt": stamp}
        value.setdefault("createdAt", stamp)
        self.follow_up(request_id, product_id, value)
        self.connection.execute("INSERT INTO follow_up_events(request_id,status,body,recorded_at) VALUES(?,?,?,?)",
                                (request_id, value["followUpStatus"], encode(value), stamp))
        return value

    def prepare_message(self, operation_id, action, name, correlation_key, message_id, payload):
        """Commit intent before transport; job replay does not silently resend uncertainty."""
        self.connection.execute("BEGIN IMMEDIATE")
        try:
            row = self.connection.execute("SELECT * FROM message_outbox WHERE operation_id=?", (operation_id,)).fetchone()
            if row is None:
                stamp = now()
                self.connection.execute("INSERT INTO message_outbox VALUES(?,?,?,?,?,?,?,NULL,NULL,?,?)",
                                        (operation_id, action, name, correlation_key, str(message_id), encode(payload),
                                         "prepared", stamp, stamp))
            else:
                expected = (action, name, correlation_key, str(message_id), encode(payload))
                actual = tuple(row[key] for key in ("action", "message_name", "correlation_key", "message_id", "payload"))
                if actual != expected:
                    raise ValueError("An outbox operation cannot be reused with a different message contract")
            self.connection.commit()
        except BaseException:
            self.connection.rollback()
            raise
        return self.get_message(operation_id)

    def get_message(self, operation_id):
        row = self.connection.execute("SELECT * FROM message_outbox WHERE operation_id=?", (operation_id,)).fetchone()
        if row is None:
            raise ValueError("Unknown outbox operation")
        result = dict(row)
        result["payload"] = json.loads(result["payload"])
        result["response"] = json.loads(result["response"]) if result["response"] else None
        return result

    def claim_message(self, operation_id):
        result = self.connection.execute("UPDATE message_outbox SET status='in_flight',updated_at=? WHERE operation_id=? AND status='prepared'",
                                         (now(), operation_id))
        return result.rowcount == 1

    def message_accepted(self, operation_id, response):
        self.connection.execute("UPDATE message_outbox SET status='accepted',response=?,error=NULL,updated_at=? WHERE operation_id=?",
                                (encode(response), now(), operation_id))

    def message_uncertain(self, operation_id, error):
        self.connection.execute("UPDATE message_outbox SET status='uncertain',error=?,updated_at=? WHERE operation_id=?",
                                (str(error)[:2000], now(), operation_id))

    def reconcile_message(self, operation_id, resolution, evidence):
        """Operator decision after inspecting receiver/transport evidence, never inferred from HTTP 400."""
        if resolution not in {"accepted", "not_sent"}:
            raise ValueError("resolution must be accepted or not_sent")
        if not isinstance(evidence, str) or not evidence.strip():
            raise ValueError("Record the actual receiver/transport evidence before reconciling")
        current = self.get_message(operation_id)
        if current["status"] not in {"uncertain", "in_flight"}:
            raise ValueError("Only uncertain/in-flight messages need reconciliation")
        status = "accepted" if resolution == "accepted" else "prepared"
        response = {"operatorReconciled": True, "evidence": evidence.strip()} if resolution == "accepted" else None
        self.connection.execute("UPDATE message_outbox SET status=?,response=?,error=?,updated_at=? WHERE operation_id=?",
                                (status, encode(response) if response else None, "Reconciled: " + evidence.strip(), now(), operation_id))
        return self.get_message(operation_id)

    def snapshot(self):
        return super().snapshot() | {
            "followUpEvents": [dict(row) | {"body": json.loads(row["body"])}
                               for row in self.connection.execute("SELECT * FROM follow_up_events ORDER BY event_id")],
            "messageOutbox": [self.get_message(row[0]) for row in self.connection.execute("SELECT operation_id FROM message_outbox ORDER BY recorded_at,operation_id")],
        }
