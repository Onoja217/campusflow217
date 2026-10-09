"""Interactive CLI entry point for CampusFlow ticket creation and views."""
from __future__ import annotations

from os import PathLike

from .persistence import (
    DEFAULT_TICKETS_PATH,
    TicketPersistenceError,
    load_tickets,
    save_tickets,
)
from .tickets import (
    Ticket,
    TicketValidationError,
    assign_ticket,
    change_ticket_status,
    create_ticket,
    format_ticket_details,
    format_ticket_list,
    get_ticket_by_id,
    parse_affected_users_input,
    reopen_ticket,
)


def _save_or_rollback(
    tickets: list[Ticket], previous: list[Ticket], path: str | PathLike[str]
) -> bool:
    """Persist a mutation or restore the in-memory collection on failure."""
    try:
        save_tickets(tickets, path)
    except TicketPersistenceError as error:
        tickets[:] = previous
        print(f"Persistence error: {error}")
        return False
    return True


def prompt_for_ticket(
    tickets: list[Ticket], tickets_path: str | PathLike[str] = DEFAULT_TICKETS_PATH
) -> Ticket | None:
    """Prompt for a ticket and report success only after it has been saved."""
    previous = list(tickets)
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

    if not _save_or_rollback(tickets, previous, tickets_path):
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


def main(tickets_path: str | PathLike[str] = DEFAULT_TICKETS_PATH) -> None:
    """Load persisted tickets and run the interactive menu."""
    try:
        tickets = load_tickets(tickets_path)
    except TicketPersistenceError as error:
        print(f"Persistence error: {error}")
        print("CampusFlow stopped to protect the existing ticket data.")
        return

    print("CampusFlow ticket tracker")
    try:
        while True:
            print(
                "\n1. Create ticket\n2. List all tickets\n3. View ticket by ID"
                "\n4. Assign ticket\n5. Change ticket status\n6. Reopen resolved ticket"
                "\n7. Exit"
            )
            choice = input("Choose an option: ").strip()
            if choice == "1":
                prompt_for_ticket(tickets, tickets_path)
            elif choice == "2":
                show_tickets(tickets)
            elif choice == "3":
                show_ticket_by_id(tickets, input("Ticket ID: "))
            elif choice == "4":
                previous = list(tickets)
                try:
                    ticket_id = input("Ticket ID to assign: ")
                    assignee = input("Assignee name: ")
                    ticket = assign_ticket(tickets, ticket_id, assignee)
                    if _save_or_rollback(tickets, previous, tickets_path):
                        print(f"Assigned {ticket.id} to {ticket.assigned_to}.")
                except TicketValidationError as error:
                    print(f"Error: {error}")
            elif choice == "5":
                previous = list(tickets)
                try:
                    ticket_id = input("Ticket ID: ")
                    new_status = input("New status (in_progress/resolved): ")
                    ticket = change_ticket_status(tickets, ticket_id, new_status)
                    if _save_or_rollback(tickets, previous, tickets_path):
                        print(f"{ticket.id} status changed to {ticket.status}.")
                except TicketValidationError as error:
                    print(f"Error: {error}")
            elif choice == "6":
                previous = list(tickets)
                try:
                    ticket = reopen_ticket(tickets, input("Ticket ID to reopen: "))
                    if _save_or_rollback(tickets, previous, tickets_path):
                        print(f"{ticket.id} reopened and set to open.")
                except TicketValidationError as error:
                    print(f"Error: {error}")
            elif choice == "7":
                print("CampusFlow closed.")
                return
            else:
                print("Invalid option. Choose 1, 2, 3, 4, 5, 6, or 7.")
    except (EOFError, KeyboardInterrupt):
        print("\nCampusFlow closed.")


if __name__ == "__main__":
    main()
