"""Ordering helpers for the unresolved-ticket work queue."""
from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import TypeAlias

from .tickets import PRIORITIES, TICKET_ID_PATTERN, TICKET_STATUSES, Ticket

TicketLike: TypeAlias = Ticket | Mapping[str, object]
UNRESOLVED_STATUSES = tuple(
    status for status in TICKET_STATUSES if status != "resolved"
)
_PRIORITY_RANK = {
    priority: rank for rank, priority in enumerate(reversed(PRIORITIES))
}


def _value(ticket: TicketLike, field: str) -> object:
    """Read a field from either a Ticket or a mapping-shaped record."""
    if isinstance(ticket, Ticket):
        return getattr(ticket, field)
    return ticket.get(field)


def _ticket_sort_key(ticket: TicketLike) -> tuple[int, int, int]:
    """Sort by priority, then valid numeric ticket ID (invalid IDs last)."""
    priority = _value(ticket, "priority")
    priority_rank = _PRIORITY_RANK.get(priority, len(_PRIORITY_RANK))
    raw_id = _value(ticket, "id")
    match = TICKET_ID_PATTERN.fullmatch(raw_id) if isinstance(raw_id, str) else None
    if match is None:
        return priority_rank, 1, 0
    return priority_rank, 0, int(match.group(1))


def prioritized_tickets(tickets: Iterable[TicketLike]) -> list[TicketLike]:
    """Return open and in-progress tickets in handling order without mutation."""
    unresolved = [
        ticket
        for ticket in tickets
        if _value(ticket, "status") in UNRESOLVED_STATUSES
    ]
    return sorted(unresolved, key=_ticket_sort_key)
