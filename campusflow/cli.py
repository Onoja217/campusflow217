"""Interactive CLI entry point for CampusFlow ticket creation and views."""
from __future__ import annotations

from .tickets import (
    Ticket,
    TicketValidationError,
    create_ticket,
    format_ticket_details,
    format_ticket_list,
    get_ticket_by_id,
    parse_affected_users_input,
)


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


def show_tickets(tickets: list[Ticket]) -> None:
    """Print the concise view of all tickets."""
    print(format_ticket_list(tickets))


def show_ticket_by_id(tickets: list[Ticket], ticket_id: str) -> None:
    """Print one ticket's details or a friendly not-found message."""
    if not tickets:
        print("No tickets found.")
        return
    ticket = get_ticket_by_id(tickets, ticket_id)
    if ticket is None:
        requested = ticket_id.strip() if isinstance(ticket_id, str) else ""
        if requested:
            print(f"No ticket found with ID {requested}.")
        else:
            print("Please enter a ticket ID.")
        return
    print(format_ticket_details(ticket))


def main() -> None:
    """Run the in-memory menu; persistence belongs to a separate feature."""
    tickets: list[Ticket] = []
    print("CampusFlow ticket tracker")
    try:
        while True:
            print("\\n1. Create ticket\\n2. List all tickets\\n3. View ticket by ID\\n4. Exit")
            choice = input("Choose an option: ").strip()
            if choice == "1":
                prompt_for_ticket(tickets)
            elif choice == "2":
                show_tickets(tickets)
            elif choice == "3":
                show_ticket_by_id(tickets, input("Ticket ID: "))
            elif choice == "4":
                print("CampusFlow closed.")
                return
            else:
                print("Invalid option. Choose 1, 2, 3, or 4.")
    except (EOFError, KeyboardInterrupt):
        print("\\nCampusFlow closed.")


if __name__ == "__main__":
    main()
