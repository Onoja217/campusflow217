"""Automated tests for F2 ticket listing and detail views."""
import unittest

from campusflow.tickets import (
    Ticket,
    create_ticket,
    format_ticket_details,
    format_ticket_list,
    get_ticket_by_id,
    list_tickets,
)


def sample_ticket(ticket_id, title, assignee=None):
    return Ticket(
        id=ticket_id,
        title=title,
        category="Network",
        urgency="medium",
        affected_users=3,
        priority="medium",
        status="open",
        assigned_to=assignee,
    )


class TicketViewTests(unittest.TestCase):
    def setUp(self):
        self.tickets = []

    def test_empty_list_has_friendly_message(self):
        self.assertEqual(format_ticket_list(self.tickets), "No tickets found.")
        self.assertEqual(list_tickets(self.tickets), [])

    def test_listing_one_ticket_includes_required_summary_fields(self):
        self.tickets.append(sample_ticket("T001", "Wi-Fi unavailable"))
        output = format_ticket_list(self.tickets)
        for expected in ("ID", "Title", "Priority", "Status", "Assignee",
                         "T001", "Wi-Fi unavailable", "medium", "open", "Unassigned"):
            with self.subTest(expected=expected):
                self.assertIn(expected, output)

    def test_listing_multiple_tickets_includes_each_ticket(self):
        self.tickets.extend([
            sample_ticket("T001", "Wi-Fi unavailable"),
            sample_ticket("T002", "Projector broken", "Ada"),
        ])
        output = format_ticket_list(self.tickets)
        self.assertIn("T001", output)
        self.assertIn("Wi-Fi unavailable", output)
        self.assertIn("T002", output)
        self.assertIn("Projector broken", output)
        self.assertIn("Ada", output)
        self.assertEqual(len(list_tickets(self.tickets)), 2)

    def test_lookup_existing_id_returns_same_ticket(self):
        ticket = sample_ticket("T004", "Network outage")
        self.tickets.append(ticket)
        self.assertIs(get_ticket_by_id(self.tickets, "T004"), ticket)
        self.assertIs(get_ticket_by_id(self.tickets, "  T004  "), ticket)

    def test_unknown_blank_and_non_string_ids_return_none(self):
        self.tickets.append(sample_ticket("T001", "Network outage"))
        for requested in ("T999", "", "   ", None, 12):
            with self.subTest(requested=requested):
                self.assertIsNone(get_ticket_by_id(self.tickets, requested))

    def test_empty_collection_lookup_returns_none(self):
        self.assertIsNone(get_ticket_by_id([], "T001"))

    def test_detail_view_includes_all_eight_fields(self):
        ticket = sample_ticket("T003", "Wi-Fi unavailable")
        output = format_ticket_details(ticket)
        for expected in (
            "ID: T003",
            "Title: Wi-Fi unavailable",
            "Category: Network",
            "Urgency: medium",
            "Affected users: 3",
            "Priority: medium",
            "Status: open",
            "Assigned to: Unassigned",
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, output)
        self.assertEqual(len(output.splitlines()), 8)

    def test_detail_view_displays_assignee(self):
        output = format_ticket_details(sample_ticket("T005", "Broken projector", "Jordan"))
        self.assertIn("Assigned to: Jordan", output)

    def test_mapping_records_are_supported(self):
        mapping = {
            "id": "T010",
            "title": "Database unavailable",
            "category": "Software",
            "urgency": "high",
            "affected_users": 20,
            "priority": "critical",
            "status": "open",
            "assigned_to": "Alex",
        }
        self.assertIs(get_ticket_by_id([mapping], "T010"), mapping)
        self.assertIn("T010", format_ticket_list([mapping]))
        self.assertIn("Assigned to: Alex", format_ticket_details(mapping))

    def test_views_do_not_mutate_collection(self):
        self.tickets.append(sample_ticket("T001", "Network outage"))
        before = list(self.tickets)
        format_ticket_list(self.tickets)
        format_ticket_details(self.tickets[0])
        get_ticket_by_id(self.tickets, "missing")
        self.assertEqual(self.tickets, before)

    def test_f1_creation_still_integrates_with_views(self):
        ticket = create_ticket(
            self.tickets,
            title="Wi-Fi unavailable",
            category="Network",
            urgency="high",
            affected_users=10,
        )
        self.assertIs(get_ticket_by_id(self.tickets, ticket.id), ticket)
        self.assertIn("critical", format_ticket_list(self.tickets))
        self.assertIn("Affected users: 10", format_ticket_details(ticket))


if __name__ == "__main__":
    unittest.main()
