# CampusFlow

CampusFlow is a Python helpdesk ticket tracker with an interactive command-line interface (CLI) and a local browser dashboard. It supports validated ticket creation, automatic priority calculation, assignment, status changes, an unresolved-ticket priority queue, workload reports by status and priority, and JSON persistence.

## Features

- **Create tickets:** validate the title, category, urgency, and positive affected-user count.
- **Calculate priority:** assign `critical`, `high`, `medium`, or `low` automatically.
- **Generate ticket IDs:** use sequential IDs such as `T001`, `T002`, and so on.
- **Find tickets:** list all tickets or view one ticket by ID.
- **Assign tickets:** record the person responsible for an unresolved ticket.
- **Manage status:** follow the `open → in_progress → resolved` workflow, with an explicit action to reopen resolved tickets.
- **Review the priority queue:** order unresolved tickets by priority; resolved tickets are excluded.
- **View workload reports:** show totals by status and priority, including categories with zero tickets.
- **Save work:** persist tickets in JSON so they remain available after restart.
- **Use either interface:** the CLI and browser dashboard share the same ticket rules and default JSON file.

## Requirements

- Python 3.10 or newer
- No third-party runtime dependencies

## Setup

Clone the repository and open a terminal in the repository root:

```bash
git clone https://github.com/Onoja217/campusflow217.git
cd campusflow217
```

Confirm that Python 3.10 or newer is available:

```bash
python3 --version
```

On Windows, use `python` instead of `python3` if that is the command configured on your system. CampusFlow uses only the Python standard library, so no package installation step is required.

## Run the CLI

From the repository root:

```bash
python3 -m campusflow.cli
```

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
| 9 | Show ticket report |

## Run the browser dashboard

The dashboard uses Python's built-in HTTP server and does not require a separate frontend framework or JavaScript package dependencies.

1. From the repository root, run:

   ```bash
   python3 -m campusflow.web
   ```

2. Open [http://localhost:3000](http://localhost:3000) in your browser.
3. Keep the terminal open while using the dashboard. Stop the server with `Ctrl+C`.

The dashboard supports creating and searching tickets, filtering the list, assigning owners, changing status, reopening resolved tickets, and viewing the unresolved priority queue. If port 3000 is already in use, stop the other process before starting CampusFlow.

## Troubleshooting

- **The CLI does not start:** confirm Python 3.10 or newer with `python3 --version`, run the command from the repository root, and check that the package folder is named `campusflow`.
- **The browser page does not load:** start the server with `python3 -m campusflow.web`, keep that terminal running, and open `http://localhost:3000`. If port 3000 is already occupied, stop the other local process and retry.
- **Tickets seem to disappear after restarting:** run the app from the repository root so the relative `data/tickets.json` path resolves consistently. Check that the file exists and contains valid JSON; back it up before making manual changes.
- **A persistence error appears:** do not delete or overwrite the data file as a first response. Make a backup, inspect the error, and validate the JSON. A malformed file should be repaired deliberately rather than silently replaced.
- **The test suite cannot find tests:** run `python3 -m unittest discover -s tests -v` from the repository root and confirm the `tests/` directory is present.
- **A browser action fails:** inspect the browser's displayed error and the server terminal output. Retain the reproduction steps and input values (excluding sensitive data) when reporting the issue.

## Validation and priority rules

Supported categories are `Network`, `Hardware`, `Software`, and `Other`. Category matching is case-insensitive. Supported urgency values are `low`, `medium`, and `high`; urgency is normalized to lowercase. Titles cannot be blank, and affected-user counts must be positive whole numbers.

Priority rules are evaluated in this order:

1. High urgency **and** at least 10 affected users → `critical`
2. Otherwise, high urgency **or** at least 10 affected users → `high`
3. Otherwise, medium urgency **or** at least 3 affected users → `medium`
4. Otherwise → `low`

## Status-transition rules

- New tickets start with status `open`.
- An `open` ticket can move to `in_progress` only after it has an assignee.
- An `in_progress` ticket can move to `resolved`.
- A resolved ticket cannot be modified through normal assignment/status actions.
- Only a resolved ticket can be reopened; reopening sets its status to `open`.
- Unsupported transitions are rejected with a validation message.

## Data storage and safe reset

The default data file is `data/tickets.json`. Run CampusFlow from the repository root so this relative path resolves consistently. The data directory and file are created when ticket data is first saved. Both interfaces use this same file.

- A missing data file is treated as an empty ticket collection.
- Valid records, including assignment and status, are loaded on startup.
- Malformed JSON or invalid records produce a persistence error rather than silently replacing the existing data.
- Saves use a temporary file and atomic replacement to reduce the risk of partial writes.
- Avoid running multiple CampusFlow writers against the same JSON file simultaneously.

**To reset local ticket data safely:** stop the CLI/dashboard first, make a backup of `data/tickets.json` if you may need the records, and then delete or move that file. The next run starts with an empty collection and creates the file again when a ticket is saved. Do not delete this file if it contains records you need to keep. Automated persistence tests should use temporary directories and must not reset the real data file.

Each ticket record contains `id`, `title`, `category`, `urgency`, `affected_users`, `priority`, `status`, and `assigned_to`. Tickets without an assignee are shown as **Unassigned**.

## Run the full test suite

From the repository root:

```bash
python3 -m unittest discover -s tests -v
```

The tests use Python's standard-library `unittest` framework. They cover ticket validation and priority boundaries, ticket status transitions, CLI behavior, priority ordering, JSON persistence and recovery, and reports. Check the GitHub Actions result for the specific pull request/commit before merging.

## Team and contributions

The summaries below are based on the merged pull-request history. **Both fellows must review and confirm the display names, roles, and summaries before this section is treated as team-confirmed for assessment.** No confirmation is implied by this draft.

| Fellow | GitHub handle | Proposed role | Contribution summary and evidence |
| --- | --- | --- | --- |
| Jireh Ochygole Samuel | [@Jireh7521](https://github.com/Jireh7521) | Feature contributor | Implemented safe status transitions, the unresolved-ticket priority queue, and workload reports; related merged PRs: [#11](https://github.com/Onoja217/campusflow217/pull/11), [#15](https://github.com/Onoja217/campusflow217/pull/15), [#21](https://github.com/Onoja217/campusflow217/pull/21). |
| Display name to be confirmed by the fellow | [@Onoja217](https://github.com/Onoja217) | Feature contributor / repository owner (confirm with fellow) | Contributed validated ticket creation and priority calculation, ticket listing/details, persistence, and the browser dashboard; related merged PRs: [#8](https://github.com/Onoja217/campusflow217/pull/8), [#9](https://github.com/Onoja217/campusflow217/pull/9), [#14](https://github.com/Onoja217/campusflow217/pull/14), [#19](https://github.com/Onoja217/campusflow217/pull/19). |

### Review evidence

- [Issue #25 — peer review and merge evidence audit](https://github.com/Onoja217/campusflow217/issues/25) records the review evidence and historical gaps found in the merged PRs.
- [PR #15](https://github.com/Onoja217/campusflow217/pull/15) contains substantive partner feedback on queue ordering, tie-breaking, resolved-ticket exclusion, input mutation, persistence, and tests.
- Some merged PRs have approvals with empty review text. Those are listed as approval records, not represented as substantive written feedback. The review history is not backdated or reconstructed.

## Known limitations and future improvements

- The browser dashboard is a local development interface bound to `127.0.0.1:3000`; it is not a production multi-user service.
- There is no authentication or role-based access control.
- JSON persistence is suitable for this small local project, but concurrent writers can conflict. Avoid simultaneous CLI/dashboard writes; consider a transactional database such as SQLite if the project grows.
- Automated browser/API integration coverage should be expanded, including malformed requests, unknown routes, persistence failures, and concurrent updates.
- The dashboard does not yet present the CLI's full workload report by status and priority.
- Future work could add database-backed storage, authentication, stronger API integration tests, and report views in the dashboard.

## Project structure

```text
campusflow/
  cli.py                # Interactive CLI and menu actions
  web.py                # Local browser dashboard and HTTP server
  tickets.py            # Ticket model, validation, IDs, workflow, formatting
  persistence.py        # JSON load/save and record validation
  priority_queue.py     # Unresolved-ticket filtering and priority ordering
  reports.py            # Workload report aggregation
tests/
  test_cli.py
  test_persistence.py
  test_priority_queue.py
  test_reports.py
  test_ticket_status.py
  test_tickets.py
```

GitHub Actions runs the automated test suite for supported pull-request and push events. Verify the status of the exact commit under review before merging.
