"""End-to-end regression tests for the interactive CampusFlow CLI."""
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from campusflow.cli import main


class InteractiveCliTests(unittest.TestCase):
    def run_cli(self, inputs, tickets_path=None):
        if tickets_path is None:
            temporary_directory = tempfile.TemporaryDirectory()
            self.addCleanup(temporary_directory.cleanup)
            tickets_path = Path(temporary_directory.name) / "tickets.json"
        output = StringIO()
        with patch("builtins.input", side_effect=inputs):
            with redirect_stdout(output):
                main(tickets_path)
        return output.getvalue()

    def test_create_list_and_view_ticket_in_one_session(self):
        output = self.run_cli(["1", "Wi-Fi unavailable", "Network", "high", "10",
                               "2", "3", " T001 ", "7"])
        self.assertIn("Created T001: Wi-Fi unavailable", output)
        self.assertIn("Wi-Fi unavailable", output)
        self.assertIn("critical", output)
        self.assertIn("ID: T001", output)
        self.assertIn("Category: Network", output)
        self.assertIn("Affected users: 10", output)
        self.assertIn("Assigned to: Unassigned", output)
        self.assertIn("CampusFlow closed.", output)

    def test_cli_can_assign_ticket_and_show_assignee(self):
        output = self.run_cli(["1", "Wi-Fi unavailable", "Network", "high", "10",
                               "4", " T001 ", "  Ada Okafor  ", "2", "3", "T001", "7"])
        self.assertIn("Assigned T001 to Ada Okafor.", output)
        self.assertIn("Ada Okafor", output)
        self.assertIn("Assigned to: Ada Okafor", output)

    def test_cli_assignment_errors_are_friendly_and_recoverable(self):
        output = self.run_cli(["1", "Wi-Fi unavailable", "Network", "high", "10",
                               "4", "T001", "   ", "4", "T999", "Ada", "2", "7"])
        self.assertIn("Error: Assignee cannot be blank.", output)
        self.assertIn("Error: No ticket found with ID 'T999'.", output)
        self.assertIn("Unassigned", output)
        self.assertIn("CampusFlow closed.", output)

    def test_tickets_persist_between_separate_cli_runs(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "tickets.json"
            first = self.run_cli(["1", "Wi-Fi unavailable", "Network", "high", "10",
                                  "4", "T001", "Ada Okafor", "5", "T001",
                                  "in_progress", "7"], path)
            second = self.run_cli(["2", "3", "T001", "7"], path)
        self.assertIn("Created T001: Wi-Fi unavailable", first)
        self.assertIn("Assigned T001 to Ada Okafor.", first)
        self.assertIn("T001 status changed to in_progress.", first)
        self.assertIn("Ada Okafor", second)
        self.assertIn("Status: in_progress", second)
        self.assertIn("ID: T001", second)

    def test_new_ticket_id_continues_after_separate_cli_restart(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "tickets.json"
            first = self.run_cli(["1", "First ticket", "Network", "low", "1", "7"], path)
            second = self.run_cli(["1", "Second ticket", "Hardware", "medium", "2", "7"], path)
            third = self.run_cli(["2", "7"], path)
        self.assertIn("Created T001: First ticket", first)
        self.assertIn("Created T002: Second ticket", second)
        self.assertIn("T001", third)
        self.assertIn("T002", third)

    def test_corrupt_persistence_file_stops_without_overwriting_it(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "tickets.json"
            original = "this is not JSON"
            path.write_text(original, encoding="utf-8")
            output = self.run_cli(["1", "Should not create", "Network", "low", "1", "7"], path)
            self.assertEqual(path.read_text(encoding="utf-8"), original)
        self.assertIn("Persistence error:", output)
        self.assertIn("stopped to protect", output)
        self.assertNotIn("Created T001", output)

    def test_empty_list_and_lookup_are_friendly(self):
        output = self.run_cli(["2", "3", "T001", "7"])
        self.assertGreaterEqual(output.count("No tickets found."), 2)
        self.assertIn("CampusFlow closed.", output)

    def test_unknown_and_blank_ticket_ids_are_friendly(self):
        output = self.run_cli(["1", "Projector broken", "Hardware", "low", "2",
                               "3", "T999", "3", "   ", "7"])
        self.assertIn("No ticket found with ID T999.", output)
        self.assertIn("Please enter a ticket ID.", output)
        self.assertIn("Created T001: Projector broken", output)

    def test_invalid_ticket_does_not_break_session_or_create_record(self):
        output = self.run_cli(["1", "   ", "Network", "low", "1", "2", "7"])
        self.assertIn("Error:", output)
        self.assertIn("No tickets found.", output)
        self.assertIn("CampusFlow closed.", output)
        self.assertNotIn("Created T001", output)

    def test_invalid_menu_option_keeps_cli_running(self):
        output = self.run_cli(["x", "7"])
        self.assertIn("Invalid option. Choose 1, 2, 3, 4, 5, 6, 7, or 8.", output)
        self.assertIn("CampusFlow closed.", output)

    def test_eof_exits_cleanly(self):
        output = StringIO()
        with tempfile.TemporaryDirectory() as directory:
            with patch("builtins.input", side_effect=EOFError), redirect_stdout(output):
                main(Path(directory) / "tickets.json")
        self.assertIn("CampusFlow closed.", output.getvalue())

    def test_keyboard_interrupt_exits_cleanly(self):
        output = StringIO()
        with tempfile.TemporaryDirectory() as directory:
            with patch("builtins.input", side_effect=KeyboardInterrupt), redirect_stdout(output):
                main(Path(directory) / "tickets.json")
        self.assertIn("CampusFlow closed.", output.getvalue())


if __name__ == "__main__":
    unittest.main()
