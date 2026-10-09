"""Workload reporting helpers for CampusFlow tickets."""
from __future__ import annotations

from collections.abc import Iterable

from .tickets import PRIORITIES, TICKET_STATUSES, Ticket


def build_ticket_report(tickets: Iterable[Ticket]) -> dict[str, object]:
    """Summarize ticket totals by supported status and priority.

    Every supported category is included, even when its count is zero.
    The supplied iterable is read once and is never modified.
    """
    status_counts = dict.fromkeys(TICKET_STATUSES, 0)
    priority_counts = dict.fromkeys(PRIORITIES, 0)
    total = 0

    for ticket in tickets:
        total += 1
        status_counts[ticket.status] += 1
        priority_counts[ticket.priority] += 1

    return {
        "total": total,
        "by_status": status_counts,
        "by_priority": priority_counts,
    }
