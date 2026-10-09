# CampusFlow CLI

CampusFlow is a command-line helpdesk ticket tracker with validated ticket creation, priority calculation, sequential IDs, listing, and ticket detail views.

## Requirements

- Python 3.10 or newer
- No third-party runtime dependencies

## Run the CLI

From the repository root:

```bash
python -m campusflow.cli
```

Use the menu to create, list, and view tickets; assign a ticket; change its status; or explicitly reopen a resolved ticket. New tickets start as `open`. Assign a ticket before moving it to `in_progress`; move it from `in_progress` to `resolved` when work is complete. Resolved tickets reject normal changes until explicitly reopened. The CLI keeps tickets in memory for the current process; durable persistence is intentionally left to a separate feature.

## Run tests

```bash
python -m unittest discover -s tests -v
```

## Ticket fields

Each ticket contains exactly these eight fields: `id`, `title`, `category`, `urgency`, `affected_users`, `priority`, `status`, and `assigned_to`.

The list view shows ID, title, priority, status, and assignee. The detail view shows all eight fields and renders an empty assignee as **Unassigned**.

## Priority rules

Rules are evaluated in this order:

1. High urgency and at least 10 affected users → `critical`
2. Otherwise, high urgency or at least 10 affected users → `high`
3. Otherwise, medium urgency or at least 3 affected users → `medium`
4. Otherwise → `low`

The allowed categories, urgency levels, validation, priority calculation, ID generation, lookup, and formatting are centralized in `campusflow/tickets.py`.
