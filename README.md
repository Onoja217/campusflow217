# CampusFlow CLI

CampusFlow is a Python command-line helpdesk ticket tracker. It supports validated ticket creation, automatic priority calculation, sequential IDs, ticket lookup and listing, assignment, controlled status transitions, an unresolved-ticket priority queue, and local JSON persistence.

## Current capabilities

- **Create tickets:** validate the title, category, urgency, and positive affected-user count.
- **Calculate priority:** assign `critical`, `high`, `medium`, or `low` using the rules below.
- **Generate ticket IDs:** use IDs such as `T001`, `T002`, and so on, based on the highest existing numeric suffix.
- **List and inspect tickets:** view a compact list or the full eight-field record for a ticket ID.
- **Assign tickets:** store a trimmed assignee name; resolved tickets must be reopened before they can be changed.
- **Manage status:** follow `open → in_progress → resolved`. A ticket must be assigned before it can move to `in_progress`. Reopening a resolved ticket is an explicit action that sets its status back to `open`.
- **Prioritize unresolved work:** view open and in-progress tickets ordered by `critical → high → medium → low`; tickets at the same priority are ordered by the numeric ID suffix. Resolved tickets are excluded.
- **Persist data safely:** load and save ticket records in JSON so they survive process restarts.

## Requirements

- Python 3.10 or newer
- No third-party runtime dependencies

## Run CampusFlow

From the repository root:

```bash
python -m campusflow.cli
```

### Browser-based UI (local development)\n\nCampusFlow also includes a browser dashboard served by Python's standard library; no frontend package installation is required. From the repository root, run:\n\n```bash\npython3 -m campusflow.web\n```\n\nThen open [http://localhost:3000](http://localhost:3000). The dashboard supports creating tickets, viewing and filtering tickets, assigning owners, moving tickets through the supported status workflow, reopening resolved tickets, and reviewing the unresolved priority queue. It uses the same ticket rules and the same `data/tickets.json` file as the CLI. Stop the server with `Ctrl+C`.\n\nChoose an action from the interactive menu:

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

## JSON storage and recovery

CampusFlow stores ticket data in `data/tickets.json` by default. Run the CLI from the repository root so the repository-relative path resolves as expected. The directory and file are created when the first ticket is saved.

- A missing file starts with an empty ticket collection.
- A valid JSON file is restored at startup, including ticket fields, assignment, and status.
- Malformed JSON or invalid ticket records produce a clear persistence error. CampusFlow stops rather than silently discarding or overwriting the existing data.
- Writes use a temporary file and atomic replacement to reduce the risk of leaving a partially written file.
- If a save fails after a ticket mutation, the CLI reports the error and restores the in-memory collection instead of claiming the change was saved.
- Persistence functions accept an explicit path, and the CLI entry point supports `main(tickets_path)`, allowing tests to use isolated temporary files.

Each ticket record contains exactly eight fields: `id`, `title`, `category`, `urgency`, `affected_users`, `priority`, `status`, and `assigned_to`. An empty assignee is displayed as **Unassigned**.

## Validation and priority rules

Supported categories are `Network`, `Hardware`, `Software`, and `Other`. Supported urgency values are `low`, `medium`, and `high`; category matching is case-insensitive and urgency is normalized to lowercase. Titles cannot be blank, and affected-user counts must be positive whole numbers.

Priority rules are evaluated in this order:

1. High urgency **and** at least 10 affected users → `critical`
2. Otherwise, high urgency **or** at least 10 affected users → `high`
3. Otherwise, medium urgency **or** at least 3 affected users → `medium`
4. Otherwise → `low`

The ticket validation, priority calculation, ID generation, status workflow, lookup, and formatting logic are centralized in `campusflow/tickets.py`. JSON validation and storage behavior are centralized in `campusflow/persistence.py`; unresolved queue ordering is handled by `campusflow/priority_queue.py`.

## Run the tests

From the repository root:

```bash
python -m unittest discover -s tests -v
```

The standard-library `unittest` suite covers ticket validation and priority boundaries, assignment and status transitions, CLI behavior, priority queue ordering, and JSON persistence and recovery. Persistence tests should use temporary directories so they never modify real ticket data.

## Project structure

```text
campusflow/
  cli.py             # Interactive CLI and persistence integration
  tickets.py         # Ticket model, validation, IDs, workflow, formatting
  persistence.py     # JSON load/save, record validation, atomic writes
  priority_queue.py  # Unresolved-ticket filtering and priority ordering
tests/
  test_cli.py
  test_persistence.py
  test_priority_queue.py
  test_tickets.py
```

GitHub Actions runs the full unittest suite for pull requests and pushes to `main` and `feat/**` branches. Review the Actions result before merging a change.
