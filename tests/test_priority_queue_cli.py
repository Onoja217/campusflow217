"""CLI presentation tests for the unresolved-ticket priority queue."""
from contextlib import redirect_stdout
from io import StringIO
import unittest

from campusflow.cli import show_priority_queue
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


class PriorityQueueCliTests(unittest.TestCase):
    def capture_output(self, tickets):
        output = StringIO()
        with redirect_stdout(output):
            show_priority_queue(tickets)
        return output.getvalue()

    def test_shows_friendly_message_for_empty_queue(self):
        self.assertEqual(self.capture_output([]), "No unresolved tickets.\n")

    def test_queue_output_uses_priority_and_numeric_id_order(self):
        output = self.capture_output([
            make_ticket("T010", "high"),
            make_ticket("T002", "high"),
            make_ticket("T001", "critical", "resolved"),
            make_ticket("T003", "critical", "in_progress"),
        ])
        rows = [line for line in output.splitlines() if line.startswith("T")]
        self.assertEqual([row.split(" | ")[0].strip() for row in rows],
                         ["T003", "T002", "T010"])
        self.assertNotIn("T001", output)


if __name__ == "__main__":
    unittest.main()
