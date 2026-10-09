"""Minimal interactive CLI entry point for creating CampusFlow tickets."""
from __future__ import annotations

from .tickets import Ticket, TicketValidationError, create_ticket, parse_affected_users_input


def prompt_for_ticket(tickets: list[Ticket]) -> Ticket | None:
    """Prompt once for a ticket; return None when validation fails or input ends."""
    try:
        title = input("Ticket title: ")
        category = input("Category (Network/Hardware/Software/Other): ")
        urgency = input("Urgency (low/medium/high): ")
        affected_users = parse_affected_users_input(input("Affected users (positive whole number): "))
        ticket = create_ticket(
            tickets,
            title=title,
            category=category,
            urgency=urgency,
            affected_users=affected_users,
        )
    except (TicketValidationError, EOFError, KeyboardInterrupt) as error:
        if isinstance(error, TicketValidationError):
            print(f"Error: {error}")
        else:
            print("\nTicket creation cancelled.")
        return None

    print(
        f"Created {ticket.id}: {ticket.title} "
        f"(priority: {ticket.priority}, status: {ticket.status})"
    )
    return ticket


def main() -> None:
    """Run a small in-memory creation loop; persistence is handled by its own feature."""
    tickets: list[Ticket] = []
    print("CampusFlow ticket creation")
    print("Create tickets; press Ctrl+C or Ctrl+D to exit.")
    while True:
        ticket = prompt_for_ticket(tickets)
        if ticket is None:
            # A failed validation should not terminate the CLI; cancellation does.
            # EOF/interrupt is already handled by prompt_for_ticket, so keep this
            # simple starter CLI focused on the F1 in-memory workflow.
            continue


if __name__ == "__main__":
    main()
