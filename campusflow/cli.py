"""Minimal interactive CLI entry point for creating CampusFlow tickets."""
from __future__ import annotations

from .tickets import Ticket, TicketValidationError, create_ticket, parse_affected_users_input


def prompt_for_ticket(tickets: list[Ticket]) -> Ticket | None:
    """Prompt once for a ticket; invalid input returns None without mutation."""
    try:
        title = input("Ticket title: ")
        category = input("Category (Network/Hardware/Software/Other): ")
        urgency = input("Urgency (low/medium/high): ")
        affected_users = parse_affected_users_input(
            input("Affected users (positive whole number): ")
        )
        ticket = create_ticket(
            tickets,
            title=title,
            category=category,
            urgency=urgency,
            affected_users=affected_users,
        )
    except TicketValidationError as error:
        print(f"Error: {error}")
        return None

    print(
        f"Created {ticket.id}: {ticket.title} "
        f"(priority: {ticket.priority}, status: {ticket.status})"
    )
    return ticket


def main() -> None:
    """Run an in-memory creation loop; persistence is handled by its own feature."""
    tickets: list[Ticket] = []
    print("CampusFlow ticket creation")
    print("Create tickets; press Ctrl+C or Ctrl+D to exit.")
    try:
        while True:
            prompt_for_ticket(tickets)
    except (EOFError, KeyboardInterrupt):
        print("\nCampusFlow ticket creation closed.")


if __name__ == "__main__":
    main()
