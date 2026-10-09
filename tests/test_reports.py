"""Tests for ticket reports, including empty and mixed workloads."""
import unittest

from campusflow.reports import build_ticket_report
from campusflow.tickets import PRIORITIES, TICKET_STATUSES, Ticket


def make_ticket(ticket_id, priority, status):
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


class TicketReportTests(unittest.TestCase):
    def test_empty_data_returns_total_and_zero_for_every_category(self):
        report = build_ticket_report([])

        self.assertEqual(report["total"], 0)
        self.assertEqual(report["by_status"], dict.fromkeys(TICKET_STATUSES, 0))
        self.assertEqual(report["by_priority"], dict.fromkeys(PRIORITIES, 0))

    def test_mixed_tickets_have_correct_totals_and_breakdowns(self):
        tickets = [
            make_ticket("T001", "critical", "open"),
            make_ticket("T002", "high", "in_progress"),
            make_ticket("T003", "high", "open"),
            make_ticket("T004", "low", "resolved"),
            make_ticket("T005", "medium", "resolved"),
        ]

        report = build_ticket_report(tickets)

        self.assertEqual(report["total"], len(tickets))
        self.assertEqual(
            report["by_status"],
            {"open": 2, "in_progress": 1, "resolved": 2},
        )
        self.assertEqual(
            report["by_priority"],
            {"low": 1, "medium": 1, "high": 2, "critical": 1},
        )

    def test_counts_include_zero_categories_in_mixed_data(self):
        report = build_ticket_report([make_ticket("T001", "low", "open")])

        self.assertEqual(report["by_status"]["in_progress"], 0)
        self.assertEqual(report["by_status"]["resolved"], 0)
        self.assertEqual(report["by_priority"]["critical"], 0)
        self.assertEqual(report["by_priority"]["high"], 0)
        self.assertEqual(report["by_priority"]["medium"], 0)


if __name__ == "__main__":
    unittest.main()
