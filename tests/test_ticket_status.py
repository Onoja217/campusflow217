"""Tests for safe ticket status transitions."""
import unittest

from campusflow.tickets import (
    TicketValidationError,
    change_ticket_status,
    create_ticket,
    reopen_ticket,
)


def make_ticket(tickets, assignee=None):
    ticket = create_ticket(
        tickets,
        title="Wi-Fi unavailable",
        category="Network",
        urgency="medium",
        affected_users=3,
    )
    if assignee is not None:
        # Tickets are immutable; replace the stored record with an assigned copy.
        from dataclasses import replace
        assigned = replace(ticket, assigned_to=assignee)
        tickets[0] = assigned
        return assigned
    return ticket


class TicketStatusTransitionTests(unittest.TestCase):
    def setUp(self):
        self.tickets = []

    def test_assigned_ticket_can_move_open_to_in_progress_to_resolved(self):
        ticket = make_ticket(self.tickets, "Jireh")
        started = change_ticket_status(self.tickets, ticket.id, "in_progress")
        self.assertEqual(started.status, "in_progress")
        resolved = change_ticket_status(self.tickets, ticket.id, "resolved")
        self.assertEqual(resolved.status, "resolved")

    def test_unassigned_ticket_cannot_move_to_in_progress(self):
        ticket = make_ticket(self.tickets)
        with self.assertRaisesRegex(TicketValidationError, "unassigned ticket"):
            change_ticket_status(self.tickets, ticket.id, "in_progress")
        self.assertEqual(self.tickets[0].status, "open")

    def test_cannot_resolve_open_ticket_directly(self):
        ticket = make_ticket(self.tickets, "Jireh")
        with self.assertRaisesRegex(TicketValidationError, "open -> resolved"):
            change_ticket_status(self.tickets, ticket.id, "resolved")
        self.assertEqual(self.tickets[0].status, "open")

    def test_resolved_ticket_cannot_use_normal_status_change(self):
        ticket = make_ticket(self.tickets, "Jireh")
        change_ticket_status(self.tickets, ticket.id, "in_progress")
        change_ticket_status(self.tickets, ticket.id, "resolved")
        with self.assertRaisesRegex(TicketValidationError, "Reopen the ticket first"):
            change_ticket_status(self.tickets, ticket.id, "in_progress")
        self.assertEqual(self.tickets[0].status, "resolved")

    def test_explicit_reopen_returns_ticket_to_open(self):
        ticket = make_ticket(self.tickets, "Jireh")
        change_ticket_status(self.tickets, ticket.id, "in_progress")
        change_ticket_status(self.tickets, ticket.id, "resolved")
        reopened = reopen_ticket(self.tickets, ticket.id)
        self.assertEqual(reopened.status, "open")

    def test_only_resolved_ticket_can_be_reopened(self):
        ticket = make_ticket(self.tickets, "Jireh")
        with self.assertRaisesRegex(TicketValidationError, "Only resolved tickets"):
            reopen_ticket(self.tickets, ticket.id)
        self.assertEqual(self.tickets[0].status, "open")

    def test_unsupported_status_is_rejected_with_clear_message(self):
        ticket = make_ticket(self.tickets, "Jireh")
        with self.assertRaisesRegex(TicketValidationError, "Unsupported status"):
            change_ticket_status(self.tickets, ticket.id, "closed")

    def test_ticket_id_must_exist(self):
        with self.assertRaisesRegex(TicketValidationError, "No ticket found"):
            change_ticket_status(self.tickets, "T999", "in_progress")

    def test_mapping_ticket_records_are_updated(self):
        mapping = {
            "id": "T010",
            "title": "Wi-Fi unavailable",
            "category": "Network",
            "urgency": "medium",
            "affected_users": 3,
            "priority": "medium",
            "status": "open",
            "assigned_to": "Jireh",
        }
        self.tickets.append(mapping)
        change_ticket_status(self.tickets, "T010", "in_progress")
        self.assertEqual(mapping["status"], "in_progress")


if __name__ == "__main__":
    unittest.main()
