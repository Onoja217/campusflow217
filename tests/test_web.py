"""Regression tests for browser ticket creation."""
import json
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.request import Request, urlopen

from campusflow.web import CampusFlowHandler, PAGE


class BrowserTicketCreationTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        tickets_path = Path(self.temp_dir.name) / "tickets.json"

        class TestHandler(CampusFlowHandler):
            pass

        TestHandler.tickets_path = tickets_path
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), TestHandler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base_url = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        self.temp_dir.cleanup()

    def post_ticket(self, category):
        payload = {
            "title": f"{category} test ticket",
            "category": category,
            "urgency": "medium",
            "affected_users": 1,
        }
        request = Request(
            f"{self.base_url}/api/tickets",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(request) as response:
            return response.status, json.loads(response.read().decode("utf-8"))

    def test_hardware_ticket_is_created_and_persisted(self):
        status, result = self.post_ticket("Hardware")
        self.assertEqual(status, 201)
        self.assertEqual(result["ticket"]["category"], "Hardware")
        self.assertEqual(result["ticket"]["title"], "Hardware test ticket")
        self.assertEqual(len(result["tickets"]), 1)

    def test_software_ticket_is_created_and_persisted(self):
        status, result = self.post_ticket("Software")
        self.assertEqual(status, 201)
        self.assertEqual(result["ticket"]["category"], "Software")
        self.assertEqual(result["ticket"]["title"], "Software test ticket")
        self.assertEqual(len(result["tickets"]), 1)

    def test_ticket_form_does_not_call_reset_method(self):
        # Avoid the browser's form-reset call entirely; clear fields explicitly
        # only after the API confirms the ticket was created successfully.
        self.assertNotIn(".reset()", PAGE)
        self.assertIn("document.querySelector('#ticket-title').value=''", PAGE)
        self.assertIn("notify('Created '+data.ticket.id", PAGE)


if __name__ == "__main__":
    unittest.main()
