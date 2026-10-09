"""Ticket creation, validation, lookup, and presentation for CampusFlow.

Business rules live here so the CLI and automated tests use the same logic.
The caller supplies the current ticket collection, which is the source of
truth for sequential ID generation and ticket views.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, replace
import re
from typing import Iterable, Mapping, MutableMapping, MutableSequence, TypeAlias

CATEGORIES = ("Network", "Hardware", "Software", "Other")
URGENCY_LEVELS = ("low", "medium", "high")
PRIORITIES = ("low", "medium", "high", "critical")
TICKET_STATUSES = ("open", "in_progress", "resolved")
TICKET_ID_PATTERN = re.compile(r"^T(\\d+)$")
DETAIL_FIELDS = (
    ("id", "ID"),
    ("title", "Title"),
    ("category", "Category"),
    ("urgency", "Urgency"),
    ("affected_users", "Affected users"),
    ("priority", "Priority"),
    ("status", "Status"),
    ("assigned_to", "Assigned to"),
)
LIST_FIELDS = (
    ("id", "ID"),
    ("title", "Title"),
    ("priority", "Priority"),
    ("status", "Status"),
    ("assigned_to", "Assignee"),
)


class TicketValidationError(ValueError):
    """Raised when user-supplied ticket data is invalid."""


@dataclass(frozen=True)
class Ticket:
    """The eight-field ticket record used by CampusFlow."""

    id: str
    title: str
    category: str
    urgency: str
    affected_users: int
    priority: str
    status: str
    assigned_to: str | None

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-serializable representation of this ticket."""
        return asdict(self)


TicketLike: TypeAlias = Ticket | Mapping[str, object]


def normalize_category(value: object) -> str:
    """Normalize a supported category, rejecting unsupported values."""
    if not isinstance(value, str):
        raise TicketValidationError(
            f"Category must be one of: {', '.join(CATEGORIES)}."
        )
    normalized = value.strip().casefold()
    for category in CATEGORIES:
        if normalized == category.casefold():
            return category
    raise TicketValidationError(
        f"Unsupported category {value!r}. Choose one of: {', '.join(CATEGORIES)}."
    )


def normalize_urgency(value: object) -> str:
    """Normalize a supported urgency value to lowercase."""
    if not isinstance(value, str):
        raise TicketValidationError(
            f"Urgency must be one of: {', '.join(URGENCY_LEVELS)}."
        )
    normalized = value.strip().casefold()
    if normalized not in URGENCY_LEVELS:
        raise TicketValidationError(
            f"Unsupported urgency {value!r}. Choose one of: {', '.join(URGENCY_LEVELS)}."
        )
    return normalized


def validate_title(value: object) -> str:
    """Return a trimmed title or raise a clear validation error."""
    if not isinstance(value, str) or not value.strip():
        raise TicketValidationError("Title cannot be blank.")
    return value.strip()


def validate_affected_users(value: object) -> int:
    """Require a positive integer; do not coerce strings, floats, or booleans."""
    if type(value) is not int or value <= 0:
        raise TicketValidationError("Affected users must be a positive whole number.")
    return value


def parse_affected_users_input(value: str) -> int:
    """Parse CLI text as a positive base-10 integer without truncation."""
    raw = value.strip()
    if not re.fullmatch(r"[0-9]+", raw):
        raise TicketValidationError("Affected users must be a positive whole number.")
    number = int(raw)
    return validate_affected_users(number)


def calculate_priority(urgency: str, affected_users: int) -> str:
    """Calculate priority using the required precedence, in one place."""
    normalized_urgency = normalize_urgency(urgency)
    users = validate_affected_users(affected_users)

    if normalized_urgency == "high" and users >= 10:
        return "critical"
    if normalized_urgency == "high" or users >= 10:
        return "high"
    if normalized_urgency == "medium" or users >= 3:
        return "medium"
    return "low"


def _field(ticket: TicketLike, name: str) -> object:
    """Read a field from either the canonical dataclass or a mapping."""
    if isinstance(ticket, Ticket):
        return getattr(ticket, name)
    return ticket.get(name)


def _display_value(value: object) -> str:
    """Convert a stored value into readable CLI text."""
    return "Unassigned" if value is None or value == "" else str(value)


def next_ticket_id(tickets: Iterable[TicketLike]) -> str:
    """Generate the next ID from the highest valid existing numeric suffix."""
    highest = 0
    for ticket in tickets:
        raw_id = _field(ticket, "id")
        if not isinstance(raw_id, str):
            continue
        match = TICKET_ID_PATTERN.fullmatch(raw_id)
        if match:
            highest = max(highest, int(match.group(1)))
    return f"T{highest + 1:03d}"


def create_ticket(
    tickets: MutableSequence[TicketLike],
    *,
    title: object,
    category: object,
    urgency: object,
    affected_users: object,
) -> Ticket:
    """Validate all fields, then append one ticket to the supplied collection."""
    clean_title = validate_title(title)
    clean_category = normalize_category(category)
    clean_urgency = normalize_urgency(urgency)
    users = validate_affected_users(affected_users)
    priority = calculate_priority(clean_urgency, users)
    ticket_id = next_ticket_id(tickets)

    ticket = Ticket(
        id=ticket_id,
        title=clean_title,
        category=clean_category,
        urgency=clean_urgency,
        affected_users=users,
        priority=priority,
        status="open",
        assigned_to=None,
    )
    tickets.append(ticket)
    return ticket


def list_tickets(tickets: Iterable[TicketLike]) -> list[TicketLike]:
    """Return the current tickets in collection order without mutating them."""
    return list(tickets)


def get_ticket_by_id(
    tickets: Iterable[TicketLike], ticket_id: object
) -> TicketLike | None:
    """Find a ticket by ID; trim surrounding whitespace from the requested ID."""
    if not isinstance(ticket_id, str) or not ticket_id.strip():
        return None
    requested_id = ticket_id.strip()
    for ticket in tickets:
        if _field(ticket, "id") == requested_id:
            return ticket
    return None


def _replace_ticket_status(
    tickets: MutableSequence[TicketLike], index: int, status: str
) -> TicketLike:
    """Update status while respecting the immutable Ticket dataclass."""
    ticket = tickets[index]
    if isinstance(ticket, Ticket):
        updated_ticket = replace(ticket, status=status)
        tickets[index] = updated_ticket
        return updated_ticket
    if isinstance(ticket, MutableMapping):
        ticket["status"] = status
        return ticket
    raise TicketValidationError(
        "This ticket record cannot be updated because it is read-only."
    )


def change_ticket_status(
    tickets: MutableSequence[TicketLike],
    ticket_id: object,
    new_status: object,
) -> TicketLike:
    """Apply one allowed workflow transition to a ticket in the collection."""
    ticket = get_ticket_by_id(tickets, ticket_id)
    if ticket is None:
        raise TicketValidationError(f"No ticket found with ID {ticket_id!r}.")

    if not isinstance(new_status, str):
        raise TicketValidationError(
            f"Unsupported status {new_status!r}. Choose one of: {', '.join(TICKET_STATUSES)}."
        )
    requested_status = new_status.strip().casefold()
    if requested_status not in TICKET_STATUSES:
        raise TicketValidationError(
            f"Unsupported status {new_status!r}. Choose one of: {', '.join(TICKET_STATUSES)}."
        )

    current_status = _field(ticket, "status")
    if current_status == "resolved":
        raise TicketValidationError(
            "Resolved tickets cannot be changed through normal workflow actions. Reopen the ticket first."
        )
    if current_status not in TICKET_STATUSES:
        raise TicketValidationError(
            f"Ticket has unsupported current status {current_status!r}."
        )

    allowed_transition = (
        (current_status == "open" and requested_status == "in_progress")
        or (current_status == "in_progress" and requested_status == "resolved")
    )
    if not allowed_transition:
        raise TicketValidationError(
            f"Unsupported status transition: {current_status} -> {requested_status}."
        )

    if current_status == "open" and requested_status == "in_progress":
        assignee = _field(ticket, "assigned_to")
        if not isinstance(assignee, str) or not assignee.strip():
            raise TicketValidationError(
                "An unassigned ticket cannot move to in_progress. Assign the ticket first."
            )

    for index, candidate in enumerate(tickets):
        if candidate is ticket:
            return _replace_ticket_status(tickets, index, requested_status)

    raise TicketValidationError(f"No ticket found with ID {ticket_id!r}.")


def reopen_ticket(
    tickets: MutableSequence[TicketLike], ticket_id: object
) -> TicketLike:
    """Explicitly reopen a resolved ticket by setting its status to open."""
    ticket = get_ticket_by_id(tickets, ticket_id)
    if ticket is None:
        raise TicketValidationError(f"No ticket found with ID {ticket_id!r}.")
    if _field(ticket, "status") != "resolved":
        raise TicketValidationError(
            "Only resolved tickets can be reopened."
        )

    for index, candidate in enumerate(tickets):
        if candidate is ticket:
            return _replace_ticket_status(tickets, index, "open")

    raise TicketValidationError(f"No ticket found with ID {ticket_id!r}.")


def format_ticket_list(tickets: Iterable[TicketLike]) -> str:
    """Format a concise ticket listing with identifiers and current status."""
    current = list_tickets(tickets)
    if not current:
        return "No tickets found."

    rows = [
        [_display_value(_field(ticket, key)) for key, _label in LIST_FIELDS]
        for ticket in current
    ]
    headers = [label for _key, label in LIST_FIELDS]
    widths = [
        max(len(headers[index]), *(len(row[index]) for row in rows))
        for index in range(len(headers))
    ]
    render = lambda values: " | ".join(
        value.ljust(widths[index]) for index, value in enumerate(values)
    )
    divider = "-+-".join("-" * width for width in widths)
    return "\n".join([render(headers), divider, *(render(row) for row in rows)])


def format_ticket_details(ticket: TicketLike) -> str:
    """Format all eight fields of a ticket with human-readable labels."""
    return "\n".join(
        f"{label}: {_display_value(_field(ticket, key))}"
        for key, label in DETAIL_FIELDS
    )
