# CampusFlow

CampusFlow is a Python helpdesk ticket tracker with both an interactive command-line interface (CLI) and a local browser dashboard. It supports validated ticket creation, automatic priority calculation, assignment, status changes, an unresolved-ticket priority queue, and JSON persistence.

## Features

- **Create tickets:** validate the title, category, urgency, and positive affected-user count.
- **Calculate priority:** automatically assign `critical`, `high`, `medium`, or `low`.
- **Generate ticket IDs:** use IDs such as `T001`, `T002`, and so on.
- **Find and browse tickets:** list all tickets or view an individual ticket by ID.
- **Assign tickets:** record the person responsible for a ticket.
- **Manage status:** move tickets through `open → in_progress → resolved`; assigned tickets are required before starting work. Resolved tickets can be explicitly reopened.
- **Review the priority queue:** see unresolved tickets ordered by priority, with resolved tickets excluded.
- **Save work:** store ticket records in JSON so they persist after the app restarts.
- **Use either interface:** the CLI and browser dashboard use the same ticket rules and default JSON data file.

## Requirements

- Python 3.10 or newer
- No third-party runtime dependencies

## Run the CLI

From the repository root, run:

```bash
python3 -m campusflow.cli
```

Choose an action from the menu:

| Option | Action |
| --- | --- |
| 1 | Create ticket |
| 2 | List all tickets |
| 3 | View ticket by ID |
| 4 | Assign ticket |
| 5 | Change ticket status |
| 6 | Reopen resolved ticket |
| 7 | Exit |
| 8 | Show unresolved priority queue |

On systems where `python` points to Python 3, you can use `python -m campusflow.cli` instead.

## Run the browser dashboard

CampusFlow includes a browser-based dashboard served by Python's standard library. You do not need to install a separate frontend framework or JavaScript package dependencies.

1. Open a terminal in the repository root.
2. Start the web server:

   ```bash
   python3 -m campusflow.web
   ```

3. Open [http://localhost:3000](http://localhost:3000) in your browser.

The dashboard lets you create tickets, search and filter the ticket list, assign owners, update ticket status, reopen resolved tickets, and inspect the unresolved priority queue. Stop the server with `Ctrl+C`.

If port 3000 is already in use, stop the other process using it before starting CampusFlow. Keep the terminal running while you use the dashboard.

## Data storage

By default, CampusFlow stores tickets in `data/tickets.json`. Run the app from the repository root so the relative data path resolves consistently. The data directory and file are created when ticket data is first saved.

- A missing file starts with an empty ticket collection.
- Valid JSON records are loaded on startup, including ticket assignment and status.
- Malformed JSON or invalid ticket records result in a persistence error rather than silently overwriting the existing data.
- Writes use a temporary file and atomic replacement to reduce the risk of a partial write.
- The CLI and browser dashboard use the same default data file. Avoid running multiple writers against that file at the same time.

Each ticket record contains these fields: `id`, `title`, `category`, `urgency`, `affected_users`, `priority`, `status`, and `assigned_to`. Tickets without an assignee are shown as **Unassigned**.

## Validation and priority rules

Supported categories are `Network`, `Hardware`, `Software`, and `Other`. Category matching is case-insensitive. Supported urgency values are `low`, `medium`, and `high`; urgency is normalized to lowercase. Titles cannot be blank, and affected-user counts must be positive whole numbers.

Priority rules are evaluated in this order:

1. High urgency **and** at least 10 affected users → `critical`
2. Otherwise, high urgency **or** at least 10 affected users → `high`
3. Otherwise, medium urgency **or** at least 3 affected users → `medium`
4. Otherwise → `low`

## Run the tests

From the repository root, run:

```bash
python3 -m unittest discover -s tests -v
```

The standard-library `unittest` suite covers ticket validation and priority boundaries, assignment and status transitions, CLI behavior, priority queue ordering, and JSON persistence and recovery. Persistence tests should use temporary directories so they do not alter real ticket data.

## Project structure

```text
campusflow/
  cli.py             # Interactive CLI
  web.py             # Local browser dashboard and HTTP server
  tickets.py         # Ticket model, validation, IDs, workflow, formatting
  persistence.py     # JSON load/save and record validation
  priority_queue.py  # Unresolved-ticket filtering and priority ordering
tests/
  test_cli.py
  test_persistence.py
  test_priority_queue.py
  test_tickets.py
```

GitHub Actions is intended to run the unittest suite for pull requests and pushes to supported branches. Check the Actions results for the specific commit before merging.
