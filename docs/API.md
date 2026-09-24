# Todo API

Run `python run.py dev`, then use `http://localhost:8000` or the interactive schema at `/docs`.

| Method | Path | Behavior |
| --- | --- | --- |
| GET | `/health` | Health status and application version |
| GET | `/todos` | All tasks ordered by ID; optional `done=true` or `done=false` filter |
| POST | `/todos` | Create a task; returns `201` |
| GET | `/todos/{todo_id}` | Retrieve one task |
| PATCH | `/todos/{todo_id}` | Update supplied task fields |
| DELETE | `/todos/{todo_id}` | Delete a task; returns `204` with no body |
| GET | `/stats` | Counts and completion percentage; intentionally fails for an empty database as a teaching exercise |

## Task fields

```json
{
  "id": 1,
  "title": "Prepare the report",
  "done": false,
  "created_at": "2026-09-24T06:00:00",
  "finish_date": "2026-10-01"
}
```

`finish_date` is an optional, user-selected **target calendar date**, not a completion timestamp.
Use `YYYY-MM-DD` or `null`; dates have no timezone and may be in the past.
Completing or reopening a task does not change its target date.
`created_at` records UTC; SQLite responses may omit the timezone suffix.

On creation, `title` is required and the finish date defaults to `null`.
On update, omitting `finish_date` preserves its value; explicitly sending `null` clears it.
Titles are trimmed and must contain 1–200 characters. Invalid titles or dates return `422`;
a missing task returns `404`. Invalid updates do not partially modify a task.

## Examples

These examples use a POSIX shell; equivalent request bodies can be entered in `/docs` on any platform.

```bash
curl -X POST http://localhost:8000/todos \
  -H 'Content-Type: application/json' \
  -d '{"title":"Prepare the report","finish_date":"2026-10-01"}'

curl -X PATCH http://localhost:8000/todos/1 \
  -H 'Content-Type: application/json' \
  -d '{"finish_date":"2026-10-08"}'

curl -X PATCH http://localhost:8000/todos/1 \
  -H 'Content-Type: application/json' \
  -d '{"finish_date":null}'
```

## Existing databases

Application startup adds nullable `finish_date DATE` to an existing SQLite `todos` table.
Existing tasks retain every previous field and receive `null` for the new date.
The upgrade is additive and repeatable; no data reset or new dependency is required.
Back up the database before upgrading. For an existing non-SQLite database, apply the nullable DATE
column using that database's migration procedure before starting this version.
