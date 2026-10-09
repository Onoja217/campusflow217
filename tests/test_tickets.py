"""Automated tests for F1 ticket creation and validation."""
import unittest

from campusflow.tickets import (
    Ticket,
    TicketValidationError,
    calculate_priority,
    create_ticket,
    next_ticket_id,
    parse_affected_users_input,
)


class TicketCreationTests(unittest.TestCase):
    def setUp(self):
        self.tickets = []

    def test_creates_all_eight_fields_and_normalizes_input(self):
        ticket = create_ticket(
            self.tickets,
            title="  Wi-Fi unavailable  ",
            category="nEtWoRk",
            urgency="HIGH",
            affected_users=10,
        )
        self.assertEqual(
            ticket.to_dict(),
            {
                "id": "T001",
                "title": "Wi-Fi unavailable",
                "category": "Network",
                "urgency": "high",
                "affected_users": 10,
                "priority": "critical",
                "status": "open",
                "assigned_to": None,
            },
        )
        self.assertEqual(len(self.tickets), 1)
        self.assertIs(self.tickets[0], ticket)

    def test_priority_precedence_and_boundaries(self):
        cases = [
            ("high", 10, "critical"),
            ("high", 2, "high"),
            ("low", 10, "high"),
            ("low", 3, "medium"),
            ("medium", 1, "medium"),
            ("low", 1, "low"),
        ]
        for urgency, users, expected in cases:
            with self.subTest(urgency=urgency, users=users):
                self.assertEqual(calculate_priority(urgency, users), expected)

    def test_invalid_title_does_not_mutate_collection(self):
        for title in ("", "   ", None):
            with self.subTest(title=title):
                with self.assertRaises(TicketValidationError):
                    create_ticket(
                        self.tickets,
                        title=title,
                        category="Network",
                        urgency="low",
                        affected_users=1,
                    )
                self.assertEqual(self.tickets, [])

    def test_invalid_category_and_urgency_are_rejected(self):
        for field, value in (("category", "Printer"), ("urgency", "urgent")):
            kwargs = {
                "title": "Example",
                "category": "Network",
                "urgency": "low",
                "affected_users": 1,
            }
            kwargs[field] = value
            with self.subTest(field=field, value=value):
                with self.assertRaises(TicketValidationError):
                    create_ticket(self.tickets, **kwargs)
                self.assertEqual(self.tickets, [])

    def test_affected_users_requires_positive_integer(self):
        for value in (0, -1, 1.5, "3", True, None):
            with self.subTest(value=value):
                with self.assertRaises(TicketValidationError):
                    create_ticket(
                        self.tickets,
                        title="Example",
                        category="Network",
                        urgency="low",
                        affected_users=value,
                    )
                self.assertEqual(self.tickets, [])

    def test_cli_integer_parser_rejects_decimal_and_non_positive_values(self):
        for value in ("3.5", "-2", "0", "abc", "", "2e1"):
            with self.subTest(value=value):
                with self.assertRaises(TicketValidationError):
                    parse_affected_users_input(value)
        self.assertEqual(parse_affected_users_input(" 12 "), 12)

    def test_ids_are_sequential_and_expand_past_three_digits(self):
        self.assertEqual(next_ticket_id([]), "T001")
        existing = [
            Ticket("T001", "A", "Network", "low", 1, "low", "open", None),
            Ticket("T009", "B", "Hardware", "low", 1, "low", "open", None),
        ]
        self.assertEqual(next_ticket_id(existing), "T010")
        existing.append(Ticket("T999", "C", "Other", "low", 1, "low", "open", None))
        self.assertEqual(next_ticket_id(existing), "T1000")

    def test_creation_uses_existing_collection_and_does_not_restart_ids(self):
        create_ticket(
            self.tickets,
            title="First",
            category="Other",
            urgency="low",
            affected_users=1,
        )
        second = create_ticket(
            self.tickets,
            title="Second",
            category="Software",
            urgency="low",
            affected_users=1,
        )
        self.assertEqual(second.id, "T002")
        self.assertEqual(len(self.tickets), 2)


if __name__ == "__main__":
    unittest.main()
