"""Tests for the unresolved-ticket priority queue."""
import unittest

from campusflow.priority_queue import prioritized_tickets
from campusflow.tickets import Ticket


def make_ticket(ticket_id, priority, status="open"):
    return Ticket(
        id=ticket_id,
        title=f"Ticket {ticket_id}",
        category="Network",
        urgency="low",
        affected_users=1,
        priority=priority,
        status=status,
        assigned_to=None,
    )


class PriorityQueueTests(unittest.TestCase):
    def test_sorts_priority_then_numeric_ticket_id_and_excludes_resolved(self):
        tickets = [
            make_ticket("T010", "high"),
            make_ticket("T002", "high"),
            make_ticket("T004", "low"),
            make_ticket("T007", "critical", "in_progress"),
            make_ticket("T001", "medium", "resolved"),
            make_ticket("T003", "medium", "in_progress"),
            make_ticket("T005", "medium"),
        ]

        result = prioritized_tickets(tickets)

        self.assertEqual(
            [ticket.id for ticket in result],
            ["T007", "T002", "T010", "T003", "T005", "T004"],
        )
        self.assertEqual(len(tickets), 7, "The input collection must not be mutated.")

    def test_returns_empty_list_when_no_unresolved_tickets_exist(self):
        self.assertEqual(prioritized_tickets([]), [])
        self.assertEqual(
            prioritized_tickets([make_ticket("T001", "critical", "resolved")]),
            [],
        )

    def test_includes_open_and_in_progress_tickets(self):
        tickets = [
            make_ticket("T001", "low", "open"),
            make_ticket("T002", "high", "in_progress"),
        ]

        self.assertEqual(
            [ticket.id for ticket in prioritized_tickets(tickets)],
            ["T002", "T001"],
        )


if __name__ == "__main__":
    unittest.main()
