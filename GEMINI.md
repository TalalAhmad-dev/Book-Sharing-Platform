# Book Sharing Platform

A Flask-based web application for sharing physical and digital books among users. This project is a CS619 Final Project (Group F25PROJECT92F39).

## Project Overview

- **Purpose:** Peer-to-peer book sharing platform with search, borrowing workflows, and admin management.
- **Tech Stack:**
  - **Backend:** Flask (Python >= 3.14)
  - **Database:** SQLite (SQLAlchemy recommended)
  - **Authentication:** Flask-Login + Werkzeug (password hashing)
  - **Frontend:** Jinja2 Templates + Vanilla CSS/JS
  - **Package Management:** uv

## Core Features

- **User Management:** Registration, login (with block/unblock support), profile management.
- **Book Management:** CRUD for physical and digital books, search/filter by category/type.
- **Borrowing Workflow:** 
  - **Physical:** Request -> Accept/Suggest Alternative -> Mark Borrowed -> Mark Returned.
  - **Digital:** Instant borrow/download with auto-return after 7 days.
- **Admin Panel:** Manage users (block/unblock), manage books (delete), review reports.
- **Additional:** Favorites/Wishlist, Reporting system for books/users.

## Recommended Project Structure

```text
.
├── app.py                  # App factory & entry point
├── config.py               # Configuration (DB URI, secret key, upload folder)
├── models.py               # SQLite DB models (User, Book, BorrowRequest, etc.)
├── extensions.py           # Flask-Login init
├── routes/                 # Blueprint-based routes
│   ├── auth.py             # Register, Login, Logout
│   ├── books.py            # Book CRUD + search
│   ├── borrow.py           # Borrow request workflow
│   ├── dashboard.py        # User dashboard
│   ├── admin.py            # Admin panel
│   └── profile.py          # Profile management
├── templates/              # Jinja2 HTML templates
├── static/                 # CSS, JS, uploaded files
│   └── uploads/            # Uploaded book files
├── pyproject.toml          # Project metadata and dependencies
└── uv.lock                 # Dependency lockfile
```

## Database Models (Schema)

- **User:** `id`, `name`, `email`, `password_hash`, `role` (member/admin), `status` (active/blocked), `bio`, `contact`, `profile_image`.
- **Book:** `id`, `title`, `author`, `category`, `book_type` (physical/digital), `status` (available/borrowed), `location_notes`, `file_path`, `owner_id`.
- **BorrowRequest:** `id`, `book_id`, `borrower_id`, `status` (pending/accepted/rejected/suggested/borrowed/returned), `proposed_date`, `proposed_time`, `location`.
- **Favorite:** `user_id`, `book_id`.
- **Report:** `id`, `reporter_id`, `reported_book_id`, `reported_user_id`, `reason`, `status`.
- **DownloadLog:** `id`, `user_id`, `book_id`, `downloaded_at`.

## Building and Running

### Setup

1. **Sync Dependencies:**
   ```bash
   uv sync
   ```

2. **Initialize Database:** (Create a script or use Flask shell)
   ```bash
   uv run python -c "from app import app, db; with app.app_context(): db.create_all()"
   ```

3. **Run Application:**
   ```bash
   uv run flask run --debug
   ```

## Development Conventions

- **Security:** Use `@login_required` for protected routes and `@admin_required` (custom decorator) for admin features.
- **Files:** Use `werkzeug.utils.secure_filename` for all uploads. Store digital books in `static/uploads/`.
- **Logic:** Implement digital book auto-return (7-day limit) either on dashboard load or via a background task.
- **Styling:** Follow the color palette and responsive design guidelines in `Frontend_Guide.docx`.
