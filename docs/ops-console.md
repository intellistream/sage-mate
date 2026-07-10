# Operations Console

The operations console is the `v2` admin workspace for running the faculty twin as a daily service.
It turns booking requests, knowledge gaps, student context, handoffs, follow-ups, feedback, and
anonymous suggestions into one reviewable workbench instead of separate admin panels.

## Access

Start the application, open the web UI, and switch to admin mode. Admin login uses the configured
`DIGITAL_TWIN_ADMIN_USERNAME`, `DIGITAL_TWIN_ADMIN_PASSWORD`, and
`DIGITAL_TWIN_ADMIN_SESSION_SECRET` values.

The browser console reads the same admin-authenticated API contract used by tests:

- `GET /operations/overview?days=7`
- `GET /operations/workbench?days=7&limit=10`
- `PATCH /operations/tasks/{task_key}`

All three endpoints require the admin session cookie. Ordinary users should stay on the chat and
booking surfaces.

## Workbench Modules

The workbench currently includes these sections:

- **Unified task queue**: combines pending bookings, knowledge gaps, escalations, follow-ups, and
  suggestions into one operator queue. Each item can be marked `open`, `in_progress`, `done`, or
  `deferred`, with optional owner and note fields.
- **Booking review**: shows meeting requests that still need the owner or admin to approve,
  reject, or follow up. The deployment default is local availability plus human review, not direct
  calendar writes.
- **Student profiles**: summarizes NeuroMem profile records into operations-oriented student cards,
  including segment, recent questions, stored summaries, and suggested next action.
- **Satisfaction**: aggregates feedback into positive rate, unresolved rate, human-handoff rate,
  feedback coverage, reason summaries, and daily trend points.
- **Knowledge gaps**: turns recurring or unresolved question clusters into draftable knowledge
  tickets that can be published back into the knowledge store.
- **Escalations and follow-ups**: keeps human handoff and due follow-up records visible next to the
  queue that operators already process.
- **Anonymous suggestions**: surfaces low-friction feedback from users without mixing it into
  identity-bound student memory.

## Task State

The unified task queue does not mutate the source booking, escalation, follow-up, or knowledge-gap
records when an operator changes task status. Instead, it stores an overlay in
`data/operations_task_state/`. This keeps the console workflow traceable without duplicating source
store ownership.

Use `PATCH /operations/tasks/{task_key}` with any combination of:

```json
{
  "status": "in_progress",
  "assigned_to": "admin@example.edu",
  "note": "Waiting for student confirmation."
}
```

Valid statuses are `open`, `in_progress`, `done`, and `deferred`.

## Booking and Calendar Boundary

For the current school deployment, the booking workflow intentionally uses local availability files
and admin approval. A confirmed request is recorded by the app and can trigger email notification,
but it does not attempt to write into a real Google, Outlook, Exchange, or CalDAV calendar.

Real calendar-provider sync remains a future optional integration for environments that expose a
supported API. It is not a `v2` release blocker.

## Runtime Data

The console reads and writes runtime state in ignored data directories. The key operations-specific
directory is:

- `data/operations_task_state/`

Related stores include knowledge-gap drafts, escalations, follow-up actions, conversation memory,
user accounts, and generated knowledge. See [runtime-data.md](runtime-data.md) for the full source
control boundary.

## Validation

Use these checks after changing the console contract or UI:

```bash
PYTHONPATH=src pytest tests/test_operations_overview.py
PYTHONPATH=src pytest tests/test_admin_auth.py tests/test_operations_overview.py
node --check src/sage_faculty_twin/web/app.js
```

For a production-like local check, restart the managed app service and verify:

```bash
systemctl --user restart sage-mate-app.service
curl -fsS http://127.0.0.1:55601/health
```
