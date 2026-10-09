"""End-to-end regression tests for the interactive CampusFlow CLI."""
from contextlib import redirect_stdout
from io import StringIO
import unittest
from unittest.mock import patch

from campusflow.cli import main


class InteractiveCliTests(unittest.TestCase):
    def run_cli(self, inputs):
        output = StringIO()
        with patch("builtins.input", side_effect=inputs):
            with redirect_stdout(output):
                main()
        return output.getvalue()

    def test_create_list_and_view_ticket_in_one_session(self):
        output = self.run_cli([
            "1",
            "Wi-Fi unavailable",
            "Network",
            "high",
            "10",
            "2",
            "3",
            " T001 ",
            "4",
        ])

        self.assertIn("Created T001: Wi-Fi unavailable", output)
        self.assertIn("Wi-Fi unavailable", output)
        self.assertIn("critical", output)
        self.assertIn("ID: T001", output)
        self.assertIn("Category: Network", output)
        self.assertIn("Affected users: 10", output)
        self.assertIn("Assigned to: Unassigned", output)
        self.assertIn("CampusFlow closed.", output)

    def test_empty_list_and_lookup_are_friendly(self):
        output = self.run_cli(["2", "3", "T001", "4"])

        self.assertGreaterEqual(output.count("No tickets found."), 2)
        self.assertIn("CampusFlow closed.", output)

    def test_unknown_and_blank_ticket_ids_are_friendly(self):
        output = self.run_cli(["1", "Projector broken", "Hardware", "low", "2",
                               "3", "T999", "3", "   ", "4"])

        self.assertIn("No ticket found with ID T999.", output)
        self.assertIn("Please enter a ticket ID.", output)
        self.assertIn("Created T001: Projector broken", output)

    def test_invalid_ticket_does_not_break_session_or_create_record(self):
        output = self.run_cli(["1", "   ", "Network", "low", "1",
                               "2", "4"])

        self.assertIn("Error:", output)
        self.assertIn("No tickets found.", output)
        self.assertIn("CampusFlow closed.", output)
        self.assertNotIn("Created T001", output)

    def test_invalid_menu_option_keeps_cli_running(self):
        output = self.run_cli(["x", "4"])

        self.assertIn("Invalid option. Choose 1, 2, 3, or 4.", output)
        self.assertIn("CampusFlow closed.", output)

    def test_eof_exits_cleanly(self):
        output = StringIO()
        with patch("builtins.input", side_effect=EOFError), redirect_stdout(output):
            main()

        self.assertIn("CampusFlow closed.", output.getvalue())

    def test_keyboard_interrupt_exits_cleanly(self):
        output = StringIO()
        with patch("builtins.input", side_effect=KeyboardInterrupt), redirect_stdout(output):
            main()

        self.assertIn("CampusFlow closed.", output.getvalue())


if __name__ == "__main__":
    unittest.main()
