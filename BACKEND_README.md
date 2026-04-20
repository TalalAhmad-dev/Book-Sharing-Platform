# 📚 Book Sharing Platform — Backend Development Guide

> **CS619 Final Project** | Group: F25PROJECT92F39 | Supervisor: Muhammad Ilyas

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Project Structure](#2-project-structure)
3. [Database Models](#3-database-models)
4. [API Endpoints Reference](#4-api-endpoints-reference)
5. [Key Business Logic](#5-key-business-logic)
6. [Setup & Running the Project](#6-setup--running-the-project)
7. [Test Cases Quick Reference](#7-test-cases-quick-reference)

---

## 1. Project Overview

This document is the complete backend development guide for the Book Sharing Platform. It covers the project structure, all API endpoints, database models, business logic, and implementation notes for the Flask + SQLite backend.

**Tech Stack:**

| Layer | Technology |
|---|---|
| Backend Framework | Flask (Python) |
| Database | SQLite (raw `sqlite3`) |
| Authentication | Flask-Login + Werkzeug password hashing |
| Template Engine | Jinja2 |
| File Uploads | Werkzeug / Flask file handling |

---

## 2. Project Structure

```
book_sharing_platform/
├── app.py                  # App factory & entry point
├── config.py               # Configuration (DB URI, secret key, upload folder)
├── models.py               # SQLite DB models (User, Book, BorrowRequest, etc.)
├── extensions.py           # Flask-Login init
├── routes/
│   ├── auth.py             # Register, Login, Logout
│   ├── books.py            # Book CRUD + search
│   ├── borrow.py           # Borrow request workflow
│   ├── dashboard.py        # User dashboard
│   ├── admin.py            # Admin panel
│   └── profile.py          # Profile management
├── templates/              # Jinja2 HTML templates
├── static/                 # CSS, JS, uploaded files
│   └── uploads/            # Uploaded book files
├── requirements.txt
└── README.md
```

---

## 3. Database Models

Six core tables derived from the ERD in the Design Document.

### 3.1 `user`

| Field | Type | Notes |
|---|---|---|
| `id` | `INTEGER PK` | Auto-increment primary key |
| `name` | `TEXT NOT NULL` | Full display name |
| `email` | `TEXT UNIQUE NOT NULL` | Used for login; must be unique |
| `password_hash` | `TEXT NOT NULL` | `werkzeug.security.generate_password_hash()` |
| `role` | `TEXT DEFAULT 'member'` | Values: `member` \| `admin` |
| `status` | `TEXT DEFAULT 'active'` | Values: `active` \| `blocked` |
| `bio` | `TEXT` | Optional profile bio |
| `contact` | `TEXT` | Phone or contact info |
| `profile_image` | `TEXT` | Path to uploaded profile image |
| `created_at` | `DATETIME` | Auto-set on insert |

### 3.2 `book`

| Field | Type | Notes |
|---|---|---|
| `id` | `INTEGER PK` | Auto-increment |
| `title` | `TEXT NOT NULL` | Book title |
| `author` | `TEXT NOT NULL` | Author name |
| `category` | `TEXT` | e.g. Programming, Fiction, Science |
| `book_type` | `TEXT NOT NULL` | Values: `physical` \| `digital` |
| `status` | `TEXT DEFAULT 'available'` | Values: `available` \| `borrowed` \| `returned` |
| `description` | `TEXT` | Optional book description |
| `location_notes` | `TEXT` | Physical books: pickup location info |
| `file_path` | `TEXT` | Digital books: server file path |
| `download_link` | `TEXT` | Digital books: external URL alternative |
| `owner_id` | `INTEGER FK` | References `user.id` |
| `created_at` | `DATETIME` | Timestamp of listing creation |

### 3.3 `borrow_request`

| Field | Type | Notes |
|---|---|---|
| `id` | `INTEGER PK` | Auto-increment |
| `book_id` | `INTEGER FK` | References `book.id` |
| `borrower_id` | `INTEGER FK` | References `user.id` (the borrower) |
| `status` | `TEXT DEFAULT 'pending'` | Values: `pending` \| `accepted` \| `rejected` \| `suggested` \| `borrowed` \| `returned` |
| `proposed_date` | `DATE` | Proposed exchange date (physical books) |
| `proposed_time` | `TIME` | Proposed exchange time (physical books) |
| `location` | `TEXT` | Proposed exchange location (physical books) |
| `message` | `TEXT` | Optional note from borrower |
| `borrowed_at` | `DATETIME` | Set when owner marks as borrowed |
| `returned_at` | `DATETIME` | Set when returned; triggers book back to available |
| `created_at` | `DATETIME` | Request creation timestamp |

### 3.4 `favorite`

| Field | Type | Notes |
|---|---|---|
| `user_id` | `INTEGER FK` | References `user.id` |
| `book_id` | `INTEGER FK` | References `book.id` |
| `PRIMARY KEY (user_id, book_id)` | Constraint | Prevents duplicate favorites |

### 3.5 `report`

| Field | Type | Notes |
|---|---|---|
| `id` | `INTEGER PK` | Auto-increment |
| `reporter_id` | `INTEGER FK` | User submitting the report |
| `reported_book_id` | `INTEGER FK NULL` | Book being reported (nullable) |
| `reported_user_id` | `INTEGER FK NULL` | User being reported (nullable) |
| `reason` | `TEXT NOT NULL` | Reason text from reporter |
| `status` | `TEXT DEFAULT 'open'` | Values: `open` \| `reviewed` \| `dismissed` |
| `created_at` | `DATETIME` | Report timestamp |

### 3.6 `notification`

| Field | Type | Notes |
|---|---|---|
| `id` | `INTEGER PK` | Auto-increment |
| `recipient_id` | `INTEGER FK` | User receiving the notification |
| `actor_id` | `INTEGER FK NULL` | User who triggered the event (nullable) |
| `category` | `TEXT` | Notification type: `borrow` \| `admin` \| `general` |
| `title` | `TEXT` | Short notification title |
| `message` | `TEXT` | User-facing message |
| `entity_type` | `TEXT NULL` | Related entity type (`borrow_request`, `book`, `report`, etc.) |
| `entity_id` | `INTEGER NULL` | Related entity ID |
| `is_read` | `BOOLEAN` | Read state flag |
| `read_at` | `DATETIME NULL` | Timestamp when read |
| `created_at` | `DATETIME` | Notification creation time |

---

## 4. API Endpoints Reference

All routes are server-rendered (Flask + Jinja2). `GET` routes render templates; `POST` routes handle form submissions and redirect. Use `@login_required` from Flask-Login to protect authenticated routes.

### 4.1 Authentication — `/auth`

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/auth/register` | Public | Render registration page |
| `POST` | `/auth/register` | Public | Validate email uniqueness, hash password, create User record, redirect to login |
| `GET` | `/auth/login` | Public | Render login page |
| `POST` | `/auth/login` | Public | Validate credentials, check blocked status, `login_user()`, redirect to dashboard |
| `GET` | `/auth/logout` | Login required | `logout_user()`, clear session, redirect to login |

**Logic Notes:**
- Password hashing: `generate_password_hash()` on register; `check_password_hash()` on login
- Blocked users: if `user.status == 'blocked'` → flash error, deny login
- Role: all new registrations default to `role='member'`; admin created manually or via seed script

---

### 4.2 Books — `/books`

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/books` | Login required | Browse all books; supports `?q=`, `?category=`, `?type=` |
| `GET` | `/books/<id>` | Login required | View single book details, owner info, status, action buttons |
| `GET` | `/books/add` | Login required | Render Add Book form |
| `POST` | `/books/add` | Login required | Create Book record; handle file upload; set `status=available` |
| `GET` | `/books/<id>/edit` | Owner or Admin | Render Edit Book form pre-filled with book data |
| `POST` | `/books/<id>/edit` | Owner or Admin | Update Book fields; handle file replacement for digital books |
| `POST` | `/books/<id>/delete` | Owner or Admin | Delete Book record and associated file |
| `GET` | `/books/search` | Login required | Search by title, author, category, type using `LIKE` queries |

**Logic Notes:**
- Ownership check: `if book.owner_id != current_user.id and current_user.role != 'admin': abort(403)`
- File upload: use `werkzeug.utils.secure_filename()`; save to `static/uploads/`; store path in `file_path`
- Status flow: `available → borrowed → returned → available` (cyclic)
- Search: `LIKE '%keyword%'` on title, author, and category columns

---

### 4.3 Borrow Requests — `/borrow`

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/borrow/<book_id>/request` | Login required | Create BorrowRequest `status=pending`; book must be available; borrower ≠ owner |
| `POST` | `/borrow/<req_id>/accept` | Owner only | Set `request.status=accepted`; update book status |
| `POST` | `/borrow/<req_id>/reject` | Owner only | Set `request.status=rejected` |
| `POST` | `/borrow/<req_id>/suggest` | Owner only | Edit proposed date/time/location; set `status=suggested` |
| `POST` | `/borrow/<req_id>/update` | Borrower only | Edit exchange details on a pending/suggested request |
| `POST` | `/borrow/<req_id>/mark-borrowed` | Owner only | Set `status=borrowed`; set `borrowed_at=now`; set `book.status=borrowed` |
| `POST` | `/borrow/<req_id>/mark-returned` | Owner or Borrower | Set `returned_at=now`; set `book.status=available`; set `status=returned` |
| `GET` | `/borrow/<book_id>/digital` | Login required | Borrow digital book: auto-create + auto-accept request, enable download |

**Logic Notes:**
- State machine: `pending → accepted → borrowed → returned` (also `pending/suggested → rejected`)
- Physical borrow: requires `proposed_date`, `proposed_time`, `location`
- Digital borrow: no scheduling; request auto-accepted; download enabled immediately
- Auto-return for digital: on dashboard load check if `borrowed_at + 7 days <= now` → auto-return
- **Transactional**: when accepting, update BOTH `request.status` AND `book.status` in the same DB commit

---

### 4.4 Dashboard — `/dashboard`

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/dashboard` | Login required | Main dashboard: My Books + incoming requests + Borrowed Books |
| `GET` | `/dashboard/my-books` | Login required | All books where `owner_id = current_user.id` with their borrow requests |
| `GET` | `/dashboard/borrowed` | Login required | All BorrowRequests where `borrower_id = current_user.id` and status in `[accepted, borrowed]` |

---

### 4.5 Profile — `/profile`

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/profile/<user_id>` | Login required | View public profile of any user |
| `GET` | `/profile/edit` | Login required | Render profile edit form for current user |
| `POST` | `/profile/edit` | Login required | Update name, bio, contact, profile_image in User record |

---

### 4.6 Favorites — `/favorites`

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/favorites/<book_id>/add` | Login required | Insert Favorite record; `UNIQUE` constraint handles duplicates |
| `POST` | `/favorites/<book_id>/remove` | Login required | Delete Favorite record for current user + book |
| `GET` | `/favorites` | Login required | List all favorite books for `current_user` |

---

### 4.7 Reports — `/reports`

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/reports/book/<book_id>` | Login required | Submit report against a book; create Report with `reported_book_id` |
| `POST` | `/reports/user/<user_id>` | Login required | Submit report against a user; create Report with `reported_user_id` |

---

### 4.8 Digital Book Download — `/books`

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/books/<book_id>/download` | Login required | Verify active borrow request and serve file |

**Logic Notes:**
- Permission check: `BorrowRequest` must exist with `borrower_id=current_user.id`, `book_id=book_id`, `status='borrowed'`
- Serve with `flask.send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)`

---

### 4.9 Inbox — `/inbox`

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/inbox/` | Login required | List notifications for the current user |
| `POST` | `/inbox/<notification_id>/read` | Login required | Mark one notification as read |
| `POST` | `/inbox/read-all` | Login required | Mark all notifications as read |
| `POST` | `/inbox/<notification_id>/delete` | Login required | Delete one notification |

---

### 4.10 Admin — `/admin`

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/admin/dashboard` | Admin only | Overview: counts of users, books, open reports, active borrows |
| `GET` | `/admin/users` | Admin only | List all users with status, role, registration date |
| `POST` | `/admin/users/<id>/block` | Admin only | Set `user.status='blocked'`; admin cannot block self |
| `POST` | `/admin/users/<id>/unblock` | Admin only | Set `user.status='active'` |
| `GET` | `/admin/books` | Admin only | List all books with owner info and status |
| `POST` | `/admin/books/<id>/delete` | Admin only | Delete book and handle dependent borrow requests |
| `GET` | `/admin/reports` | Admin only | List all open reports with reporter and target info |
| `POST` | `/admin/reports/<id>/dismiss` | Admin only | Set `report.status='dismissed'` |
| `POST` | `/admin/reports/<id>/reviewed` | Admin only | Set `report.status='reviewed'` |

**Logic Notes:**
- Protect all admin routes with a custom `@admin_required` decorator: `if current_user.role != 'admin': abort(403)`
- Admin can delete any book regardless of owner
- Blocking a user does NOT end active sessions — their next login attempt will be denied

---

## 5. Key Business Logic

### 5.1 Authentication & Session

- Use Flask-Login's `LoginManager`; set `login_view = 'auth.login'`
- User loader: `@login_manager.user_loader` loads user by `id` from DB
- Check `user.status` before calling `login_user()` — deny if `blocked`

### 5.2 Book Status State Machine

```
available  ──(request accepted)──►  borrowed  ──(returned)──►  available
                                                                    ▲
                                                                    │
                                                           (cyclic, resets)
```

- A book can only receive new borrow requests when `status = 'available'`
- Physical books: `status` becomes `borrowed` only when owner clicks "Mark as Borrowed" (after physical handover)
- On mark-returned: set `book.status = 'available'`

### 5.3 Digital Book Auto-Return

**Option A (simpler):** On dashboard load, query:
```sql
SELECT * FROM borrow_request
WHERE status = 'borrowed'
AND datetime(borrowed_at, '+7 days') <= datetime('now')
```
Then update `status='returned'` and `book.status='available'`.

**Option B:** Use `APScheduler` for a nightly background task.

### 5.4 File Upload Handling

- Allowed extensions: `.pdf`, `.epub`, `.txt`, `.doc`, `.docx`
- Always use `secure_filename()` before saving
- Store at: `static/uploads/books/<user_id>/<filename>`
- On book deletion: delete the physical file with `os.remove()`

### 5.5 Access Control Summary

| Action | Allowed For | Denied For |
|---|---|---|
| Edit / Delete own book | Owner, Admin | Other members |
| Accept / Reject borrow request | Book owner only | Borrower, Admin |
| Mark as Returned | Owner or Borrower | Other members |
| Download digital book | Active borrower only | Non-borrowers |
| Block / Unblock users | Admin only | All members |
| Delete any book | Admin or Owner | Other members |

---

## 6. Setup & Running the Project

### 6.1 Install Dependencies

```bash
pip install flask flask-login werkzeug
```

### 6.2 `requirements.txt`

```
Flask==3.0.0
Flask-Login==0.6.3
Werkzeug==3.0.1
```

### 6.3 `config.py`

```python
SECRET_KEY = 'your-secret-key-change-this'
DATABASE = 'book_sharing.db'
UPLOAD_FOLDER = 'static/uploads'
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max upload
```

### 6.4 Initialize Database

```python
# In app.py or a separate init_db.py
with app.app_context():
    init_db()  # runs CREATE TABLE IF NOT EXISTS statements
```

### 6.5 Run the App

```bash
python app.py
# OR
flask --app app run --debug
```

### 6.6 Verify Tables Created

```bash
sqlite3 book_sharing.db ".tables"
```

Expected output: `books  borrow_requests  notifications  favorites  reports  users`

---

## 7. Test Cases Quick Reference

All 17 test cases from the Design Document map directly to backend endpoints:

| TC# | Scenario | Primary Endpoint |
|---|---|---|
| TC001 | Register | `POST /auth/register` |
| TC002 | Login / Logout | `POST /auth/login`, `GET /auth/logout` |
| TC003 | Manage Profile | `POST /profile/edit` |
| TC004 | Add Book | `POST /books/add` |
| TC005 | Edit / Delete Book | `POST /books/<id>/edit`, `POST /books/<id>/delete` |
| TC006 | Search & Browse | `GET /books?q=&category=&type=` |
| TC007 | View Book Details | `GET /books/<id>` |
| TC008 | Request to Borrow | `POST /borrow/<book_id>/request` |
| TC009 | Edit Exchange Details | `POST /borrow/<req_id>/update` |
| TC010 | Respond to Request | `POST /borrow/<req_id>/accept` or `/reject` |
| TC011 | Mark as Borrowed | `POST /borrow/<req_id>/mark-borrowed` |
| TC012 | Mark as Returned | `POST /borrow/<req_id>/mark-returned` |
| TC013 | Download Digital Book | `GET /books/<book_id>/download` |
| TC014 | Report Book / User | `POST /reports/book/<id>`, `POST /reports/user/<id>` |
| TC015 | Manage Users (Admin) | `POST /admin/users/<id>/block` |
| TC016 | Manage Books (Admin) | `POST /admin/books/<id>/delete` |
| TC017 | Favorites / Wishlist | `POST /favorites/<book_id>/add`, `GET /favorites` |

---

*Book Sharing Platform · CS619 Final Project · Group F25PROJECT92F39*
