"""Unit tests for assigning CampusFlow tickets to staff members."""
import json
import unittest

from campusflow.tickets import (
    Ticket,
    TicketValidationError,
    assign_ticket,
    create_ticket,
    format_ticket_details,
    format_ticket_list,
)


class TicketAssignmentTests(unittest.TestCase):
    def setUp(self):
        self.tickets = []
        self.ticket = create_ticket(
            self.tickets,
            title="Wi-Fi unavailable",
            category="Network",
            urgency="high",
            affected_users=10,
        )

    def test_assigns_trimmed_staff_name_to_existing_ticket_record(self):
        assigned = assign_ticket(self.tickets, " T001 ", "  Ada Okafor  ")

        self.assertEqual(assigned.assigned_to, "Ada Okafor")
        self.assertIs(self.tickets[0], assigned)
        self.assertEqual(self.tickets[0].id, "T001")

    def test_assignment_appears_in_list_and_detail_views(self):
        assign_ticket(self.tickets, "T001", "Ada Okafor")

        self.assertIn("Ada Okafor", format_ticket_list(self.tickets))
        self.assertIn("Assigned to: Ada Okafor", format_ticket_details(self.tickets[0]))

    def test_assignee_is_in_json_serializable_ticket_record(self):
        assign_ticket(self.tickets, "T001", "Ada Okafor")

        record = self.tickets[0].to_dict()
        self.assertEqual(record["assigned_to"], "Ada Okafor")
        self.assertEqual(json.loads(json.dumps(record))["assigned_to"], "Ada Okafor")

    def test_blank_and_whitespace_assignee_are_rejected_without_mutation(self):
        before = self.tickets[0].to_dict()
        for assignee in ("", "   ", "\t\n", None, 42):
            with self.subTest(assignee=assignee):
                with self.assertRaisesRegex(TicketValidationError, "Assignee cannot be blank"):
                    assign_ticket(self.tickets, "T001", assignee)
                self.assertEqual(self.tickets[0].to_dict(), before)

    def test_blank_and_unknown_ids_are_rejected_without_mutation(self):
        before = self.tickets[0].to_dict()
        for ticket_id in ("", "   ", "T999", None, 12):
            with self.subTest(ticket_id=ticket_id):
                with self.assertRaisesRegex(TicketValidationError, "No ticket found"):
                    assign_ticket(self.tickets, ticket_id, "Ada Okafor")
                self.assertEqual(self.tickets[0].to_dict(), before)

    def test_failed_assignment_does_not_change_other_tickets(self):
        other = create_ticket(
            self.tickets,
            title="Projector broken",
            category="Hardware",
            urgency="low",
            affected_users=1,
        )
        before = [ticket.to_dict() for ticket in self.tickets]

        with self.assertRaises(TicketValidationError):
            assign_ticket(self.tickets, "T999", "Ada Okafor")

        self.assertEqual([ticket.to_dict() for ticket in self.tickets], before)
        self.assertIs(self.tickets[1], other)

    def test_resolved_ticket_rejection_does_not_mutate_record(self):
        from dataclasses import replace
        self.tickets[0] = replace(self.tickets[0], status="resolved")
        before = self.tickets[0].to_dict()

        with self.assertRaisesRegex(TicketValidationError, "Resolved tickets"):
            assign_ticket(self.tickets, "T001", "Ada Okafor")

        self.assertEqual(self.tickets[0].to_dict(), before)

    def test_mutable_mapping_record_is_supported(self):
        mapping = {
            "id": "T025",
            "title": "Database unavailable",
            "category": "Software",
            "urgency": "medium",
            "affected_users": 3,
            "priority": "medium",
            "status": "open",
            "assigned_to": None,
        }
        self.tickets = [mapping]

        assigned = assign_ticket(self.tickets, "T025", "Jordan")

        self.assertIs(assigned, mapping)
        self.assertEqual(mapping["assigned_to"], "Jordan")


if __name__ == "__main__":
    unittest.main()
