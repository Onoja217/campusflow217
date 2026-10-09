"""End-to-end smoke test for persistence across separate CLI processes."""
from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


class CliPersistenceSmokeTests(unittest.TestCase):
    def test_ticket_assignee_and_status_survive_cli_restart(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            tickets_path = Path(directory) / "tickets.json"
            environment = os.environ.copy()
            existing_pythonpath = environment.get("PYTHONPATH", "")
            environment["PYTHONPATH"] = os.pathsep.join(
                part for part in (str(REPOSITORY_ROOT), existing_pythonpath) if part
            )
            command = [
                sys.executable,
                "-c",
                f"from campusflow.cli import main; main({str(tickets_path)!r})",
            ]

            first_launch = subprocess.run(
                command,
                cwd=REPOSITORY_ROOT,
                env=environment,
                input=(
                    "1\n"
                    "Persistence smoke test ticket\n"
                    "Network\n"
                    "high\n"
                    "12\n"
                    "4\n"
                    "T1\n"
                    "Jireh Samuel\n"
                    "5\n"
                    "T1\n"
                    "in_progress\n"
                    "7\n"
                ),
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(
                first_launch.returncode,
                0,
                msg=f"First CLI launch failed:\n{first_launch.stdout}\n{first_launch.stderr}",
            )
            self.assertIn("Created T1:", first_launch.stdout)
            self.assertIn("Assigned T1 to Jireh Samuel.", first_launch.stdout)
            self.assertIn("T1 status changed to in_progress.", first_launch.stdout)
            self.assertTrue(tickets_path.is_file(), "CLI did not create the ticket file.")

            second_launch = subprocess.run(
                command,
                cwd=REPOSITORY_ROOT,
                env=environment,
                input="2\n3\nT1\n7\n",
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(
                second_launch.returncode,
                0,
                msg=f"Second CLI launch failed:\n{second_launch.stdout}\n{second_launch.stderr}",
            )
            self.assertIn("Persistence smoke test ticket", second_launch.stdout)
            self.assertIn("Jireh Samuel", second_launch.stdout)
            self.assertIn("in_progress", second_launch.stdout)
            self.assertIn("CampusFlow closed.", second_launch.stdout)


if __name__ == "__main__":
    unittest.main()
