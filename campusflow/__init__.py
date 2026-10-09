"""CampusFlow CLI domain package."""

from .tickets import Ticket, create_ticket, calculate_priority

__all__ = ["Ticket", "create_ticket", "calculate_priority"]
