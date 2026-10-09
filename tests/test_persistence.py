"""Unit tests for safe JSON ticket persistence."""
import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

from campusflow.persistence import (
    TicketPersistenceError,
    load_tickets,
    save_tickets,
)
from campusflow.tickets import Ticket, create_ticket


class TicketPersistenceTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.directory = Path(self.temp_dir.name)
        self.path = self.directory / "tickets.json"

    def make_ticket(self, tickets=None, title="Wi-Fi unavailable"):
        if tickets is None:
            tickets = []
        return create_ticket(
            tickets,
            title=title,
            category="Network",
            urgency="high",
            affected_users=10,
        )

    def test_missing_file_loads_as_empty_collection(self):
        self.assertEqual(load_tickets(self.path), [])

    def test_save_and_load_round_trip_all_fields_and_unicode(self):
        tickets = []
        ticket = self.make_ticket(tickets, title="Wi-Fi — ห้องเรียน")
        from dataclasses import replace
        tickets[0] = replace(ticket, assigned_to="Ada Okafor", status="in_progress")

        save_tickets(tickets, self.path)
        loaded = load_tickets(self.path)

        self.assertEqual([item.to_dict() for item in loaded],
                         [item.to_dict() for item in tickets])
        self.assertIn("ห้องเรียน", self.path.read_text(encoding="utf-8"))

    def test_empty_collection_is_saved_as_json_array(self):
        save_tickets([], self.path)
        self.assertEqual(self.path.read_text(encoding="utf-8"), "[]\n")
        self.assertEqual(load_tickets(self.path), [])

    def test_malformed_json_is_rejected_without_modification(self):
        original = "{not valid JSON"
        self.path.write_text(original, encoding="utf-8")
        with self.assertRaisesRegex(TicketPersistenceError, "invalid JSON"):
            load_tickets(self.path)
        self.assertEqual(self.path.read_text(encoding="utf-8"), original)

    def test_non_array_document_is_rejected(self):
        self.path.write_text('{"tickets": []}', encoding="utf-8")
        with self.assertRaisesRegex(TicketPersistenceError, "JSON array"):
            load_tickets(self.path)

    def test_invalid_shapes_types_and_statuses_are_rejected(self):
        ticket = self.make_ticket().to_dict()
        cases = []
        missing = dict(ticket)
        del missing["assigned_to"]
        cases.append(("missing field", [missing]))
        extra = dict(ticket, extra="unexpected")
        cases.append(("extra field", [extra]))
        wrong_users = dict(ticket, affected_users=True)
        cases.append(("invalid integer", [wrong_users]))
        wrong_assignee = dict(ticket, assigned_to=42)
        cases.append(("invalid assignee", [wrong_assignee]))
        wrong_status = dict(ticket, status="waiting")
        cases.append(("invalid status", [wrong_status]))
        wrong_priority = dict(ticket, priority="low")
        cases.append(("priority inconsistent with business rules", [wrong_priority]))
        unassigned_in_progress = dict(ticket, status="in_progress", assigned_to=None)
        cases.append(("in-progress ticket without assignee", [unassigned_in_progress]))
        for label, payload in cases:
            with self.subTest(label=label):
                self.path.write_text(json.dumps(payload), encoding="utf-8")
                with self.assertRaises(TicketPersistenceError):
                    load_tickets(self.path)

    def test_duplicate_ticket_ids_are_rejected(self):
        record = self.make_ticket().to_dict()
        self.path.write_text(json.dumps([record, record]), encoding="utf-8")
        with self.assertRaisesRegex(TicketPersistenceError, "duplicate ID"):
            load_tickets(self.path)

    def test_id_generation_continues_after_reload_from_highest_id_not_last_record(self):
        tickets = []
        first = self.make_ticket(tickets, title="First")
        second = self.make_ticket(tickets, title="Second")
        third = self.make_ticket(tickets, title="Third")
        tickets[:] = [
            replace(third, id="T010"),
            replace(second, id="T002"),
            first,
        ]
        save_tickets(tickets, self.path)

        restored = load_tickets(self.path)
        restored_ids = [ticket.id for ticket in restored]
        next_ticket = self.make_ticket(restored, title="Created after reload")

        self.assertEqual(restored_ids, ["T010", "T002", "T001"])
        self.assertEqual(next_ticket.id, "T011")
        self.assertEqual(len({ticket.id for ticket in restored}), 4)

    def test_invalid_records_cannot_be_saved(self):
        invalid = Ticket("T001", "", "Network", "low", 1, "low", "open", None)
        with self.assertRaises(TicketPersistenceError):
            save_tickets([invalid], self.path)
        self.assertFalse(self.path.exists())

    def test_atomic_replace_failure_preserves_previous_file(self):
        self.path.write_text('[{"previous":"valid"}]\n', encoding="utf-8")
        previous = self.path.read_text(encoding="utf-8")
        with patch("campusflow.persistence.os.replace", side_effect=OSError("simulated replace failure")):
            with self.assertRaisesRegex(TicketPersistenceError, "Cannot safely save"):
                save_tickets([self.make_ticket()], self.path)
        self.assertEqual(self.path.read_text(encoding="utf-8"), previous)
        self.assertEqual(list(self.directory.glob(".tickets.json.*.tmp")), [])

    def test_unreadable_file_is_not_treated_as_missing(self):
        self.path.mkdir()
        with self.assertRaises(TicketPersistenceError):
            load_tickets(self.path)


if __name__ == "__main__":
    unittest.main()
