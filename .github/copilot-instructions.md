# Copilot Instructions for Book Sharing Platform

## Build, test, and lint commands

- **Install dependencies:** `uv sync`
- **Run the app (app factory):** `uv run flask --app app:create_app run --debug`
- **Apply migrations:** `uv run flask --app app:create_app db upgrade`
- **Create a migration after model changes:** `uv run flask --app app:create_app db migrate -m "describe change"`
- **Seed demo data:** `uv run python seed.py`
- **Playwright MCP server (for UI automation tasks):** `npx -y @playwright/mcp@latest`
- **Tests:** No automated test suite is configured in this repository yet (no pytest/unittest test files or test runner config present).
- **Linting/formatting:** No linter/formatter command is configured in this repository yet.

## High-level architecture

- Flask app uses an **application factory** in `app.py` (`create_app`) and initializes `SQLAlchemy`, `Flask-Migrate`, and `Flask-Login` from `extensions.py`.
- Route logic is split by domain into blueprints under `routes/`: `auth`, `books`, `borrow`, `dashboard`, `admin`, `profile`, `favorites`, `reports`, and `inbox`.
- Data model is centralized in `models.py` with SQLAlchemy models: `User`, `Book`, `BorrowRequest`, `Favorite`, `Report`, and `Notification`.
- UI is server-rendered Jinja templates with shared bases in `templates/base/`:
  - `base/_skeleton.html` (shared assets + toast rendering)
  - `base/public.html` (auth pages)
  - `base/protected.html` (authenticated navigation/layout)
- `books.catalog` serves both full-page and HTMX partial responses (`books/_book_cards.html`) depending on `HX-Request` header.
- Borrowing workflow state is split across `Book.status` and `BorrowRequest.status`:
  - Physical flow: request/suggest/accept -> `mark-borrowed` -> `mark-returned` (book availability changes here)
  - Digital flow: owner/borrower acceptance can move request to borrowed; downloads are gated by request state.

## Key repository conventions

- **Auth + role protection**
  - Use `@login_required` for protected routes.
  - Admin-only routes use `@admin_required` defined in `routes/admin.py`.
- **Input/file safety pattern**
  - Text from forms is commonly sanitized with `markupsafe.escape` (see `routes/books.py`).
  - Uploaded filenames must use `werkzeug.utils.secure_filename`.
  - Uploaded paths are stored relative to `UPLOAD_FOLDER` (for example `books/<user_id>/...`, `covers/<user_id>/...`, `profiles/...`).
- **Borrow request messaging convention**
  - `BorrowRequest.message` is used as JSON text for two-sided conversation metadata: `{"borrower": "...", "owner": "..."}`.
  - Templates decode this with the custom `fromjson` Jinja filter from `app.py`.
- **Template + flash behavior**
  - Flash categories are rendered as Bootstrap toasts in `base/_skeleton.html`; category `error` is mapped to Bootstrap `danger`.
  - Shared date/time formatting in templates uses custom Jinja filters `format_date` and `format_time` from `app.py`.
- **Timestamp convention**
  - Model timestamps generally use UTC-aware defaults via `datetime.now(timezone.utc)` in `models.py`.
- **Route ownership/permission checks**
  - Mutating book actions (edit/delete) follow owner-or-admin checks.
  - Borrow request actions enforce participant role checks (owner vs borrower) before state changes.
