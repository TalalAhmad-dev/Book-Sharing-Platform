# 🎨 Book Sharing Platform — Frontend Development Guide

> **CS619 Final Project** | Group: F25PROJECT92F39 | Supervisor: Muhammad Ilyas

---

## Table of Contents

1. [Frontend Overview](#1-frontend-overview)
2. [Template Folder Structure](#2-template-folder-structure)
3. [Base Template — base.html](#3-base-template--basehtml)
4. [Authentication Pages](#4-authentication-pages)
5. [Book Pages](#5-book-pages)
6. [Dashboard Pages](#6-dashboard-pages)
7. [Profile Pages](#7-profile-pages)
8. [Borrow Request UI Flow](#8-borrow-request-ui-flow)
9. [Admin Panel Pages](#9-admin-panel-pages)
10. [Favorites / Wishlist Page](#10-favorites--wishlist-page)
11. [Complete Template Reference](#11-complete-template-reference)
12. [JavaScript Interactions](#12-javascript-interactions)
13. [CSS Styling Guidelines](#13-css-styling-guidelines)

---

## 1. Frontend Overview

This document is the complete frontend development guide for the Book Sharing Platform. It covers the template structure, page-by-page UI requirements, form fields, JavaScript interactions, and styling guidelines — all derived from the project SRS and Design Document.

**Frontend Stack:**

| Layer | Technology |
|---|---|
| Markup | HTML5 with Jinja2 templating (server-rendered by Flask) |
| Styles | CSS3 — `static/css/style.css` |
| Scripts | Vanilla JavaScript — `static/js/main.js` |
| Framework | None — plain HTML/CSS/JS only |

---

## 2. Template Folder Structure

```
templates/
├── base.html                   # Master layout (navbar, flash messages, footer)
├── auth/
│   ├── register.html           # Registration form
│   └── login.html              # Login form
├── books/
│   ├── catalog.html            # Browse & search all books
│   ├── detail.html             # Single book details + actions
│   ├── add.html                # Add new book form
│   └── edit.html               # Edit book form
├── dashboard/
│   ├── index.html              # Main user dashboard
│   ├── my_books.html           # My shared books + incoming requests
│   └── borrowed.html           # Books I am borrowing
├── borrow/
│   ├── request_form.html       # Borrow request modal/form
│   └── request_detail.html     # View full borrow request details
├── profile/
│   ├── view.html               # Public profile page
│   └── edit.html               # Edit my profile
├── favorites/
│   └── wishlist.html           # My favorites/wishlist
├── admin/
│   ├── dashboard.html          # Admin overview stats
│   ├── users.html              # Manage users
│   ├── books.html              # Manage all books
│   └── reports.html            # Review submitted reports
└── errors/
    ├── 403.html                # Forbidden
    └── 404.html                # Not found
```

---

## 3. Base Template — `base.html`

All pages extend `base.html` using Jinja2 `{% block %}` tags. It provides the consistent navbar, flash messages, and footer shell.

### 3.1 Navbar Items

| Navbar Item | Condition / Behavior |
|---|---|
| Logo / Site Name | Always visible; links to `/books` |
| Browse Books | Always visible; links to `/books` |
| Add Book | Visible when logged in; links to `/books/add` |
| Dashboard | Visible when logged in; links to `/dashboard` |
| Favorites | Visible when logged in; links to `/favorites` |
| Admin Panel | Only when `current_user.role == 'admin'` |
| Profile / Logout | Visible when logged in; dropdown with profile link + logout |
| Login / Register | Visible when **not** logged in |

### 3.2 Flash Messages

```jinja
{% with messages = get_flashed_messages(with_categories=true) %}
  {% for category, message in messages %}
    <div class="alert alert-{{ category }}">{{ message }}</div>
  {% endfor %}
{% endwith %}
```

- ✅ Success messages → green banner
- ❌ Error messages → red banner
- Auto-dismiss via JavaScript after 4 seconds, or show an `×` close button

### 3.3 Jinja2 Blocks

```jinja
{% block title %}Page Title{% endblock %}
{% block content %}<!-- main body -->{% endblock %}
{% block scripts %}<!-- page-specific JS -->{% endblock %}
```

---

## 4. Authentication Pages

### 4.1 `auth/register.html`

| Field | Input Type | Required | Validation |
|---|---|---|---|
| Full Name | `text` | Yes | Non-empty |
| Email Address | `email` | Yes | Valid format; unique in DB |
| Password | `password` | Yes | Min 8 chars; 1 uppercase + 1 number |
| Confirm Password | `password` | Yes | Must match Password field |
| Contact | `text` | No | Phone or other contact info |

- On success → redirect to `/auth/login` with success flash
- On error → re-render form with error messages below each field
- Footer link: *"Already have an account? Login here"*

### 4.2 `auth/login.html`

- Fields: **Email** (`email`), **Password** (`password`)
- Submit button label: *"Sign In"*
- On failed login → flash: *"Invalid email or password"* or *"Account is blocked"*
- Footer link: *"Don't have an account? Register here"*

---

## 5. Book Pages

### 5.1 `books/catalog.html` — Browse & Search

This is the main discovery page where users search and filter books.

**Search Bar:**
- Text input for keyword search (searches title, author, category)
- Dropdown filter: **Category** (All, Programming, Fiction, Science, etc.)
- Dropdown filter: **Type** (All, Physical, Digital)
- Submits as `GET` with `?q=`, `?category=`, `?type=` query params

**Book Cards Grid:**
- Responsive grid: 3 columns on desktop, 1 on mobile
- Each card shows: cover placeholder, Title, Author, Category, Type badge, Status badge, Owner name
- Click card → navigate to `/books/<id>`
- No results → show *"No books found matching your search"*

---

### 5.2 `books/detail.html` — Book Details

Full detail view of a single book with context-aware action buttons.

| Section | Content |
|---|---|
| Book Info | Title, Author, Category, Type, Status, Description, Owner name (linked to profile) |
| Action Buttons | Context-aware — see table below |
| Exchange Details | If borrowed: proposed date, time, location (visible to both parties) |

**Action Button Logic:**

| Condition | Button Shown |
|---|---|
| Book is `available` + user is NOT owner | `Request to Borrow` |
| Book is digital + user has active borrow | `Download Book` |
| User is the owner | `Edit` and `Delete` |
| Book is `available` + not owner | `Add to Favorites` |
| Any logged-in user (not owner) | `Report this Book` link |

**Request to Borrow — Inline Form (Physical Books):**
- Collapsible form toggled by JavaScript when `Request to Borrow` is clicked
- Fields: Proposed Date (`date`), Proposed Time (`time`), Location (`text`), Message (`textarea`, optional)

---

### 5.3 `books/add.html` — Add Book Form

| Field | Input Type | Required | Notes |
|---|---|---|---|
| Title | `text` | Yes | Book title |
| Author | `text` | Yes | Author name |
| Category | `select` | Yes | Programming, Fiction, Science, Other… |
| Book Type | `radio` (Physical / Digital) | Yes | Triggers conditional fields |
| Description | `textarea` | No | Optional short description |
| Location Notes | `text` | If Physical | Show only when Type = Physical |
| Upload File | `file` | If Digital | Accept `.pdf`, `.epub`, `.txt`; show only when Type = Digital |
| Download Link | `url` | No | Alternative to file upload for digital books |

**JavaScript — Conditional Fields:**
```javascript
// Listen for change on Book Type radio
bookTypeRadios.forEach(radio => {
  radio.addEventListener('change', () => {
    if (radio.value === 'physical') {
      document.getElementById('location-section').style.display = 'block';
      document.getElementById('digital-section').style.display = 'none';
    } else {
      document.getElementById('digital-section').style.display = 'block';
      document.getElementById('location-section').style.display = 'none';
    }
  });
});
```

---

### 5.4 `books/edit.html` — Edit Book Form

- Same form as `add.html` but pre-filled with existing book data via Jinja2 `value="{{ book.field }}"`
- Show current uploaded filename if digital book already has a file
- Optional: *"Replace file"* checkbox to allow re-uploading

---

## 6. Dashboard Pages

### 6.1 `dashboard/index.html` — Main Dashboard

- Welcome message: *"Hello, {{ current_user.name }}"*
- Summary stat cards: Total Books Shared, Books Currently Borrowed, Pending Requests, Favorites count
- Quick links to: My Books, Borrowed Books, Favorites

---

### 6.2 `dashboard/my_books.html` — My Shared Books

**Section A — My Books List:**
- Table/card list of all books owned by current user
- Columns: Title, Type, Status badge, Actions (Edit / Delete)
- Status badge colors: `available` = green, `borrowed` = orange, `returned` = blue

**Section B — Incoming Borrow Requests:**
- Table of all pending requests on the user's books
- Columns: Book Title, Requester Name, Proposed Date/Time/Location, Status, Actions
- Action buttons depend on request status:

| Request Status | Buttons Available |
|---|---|
| `pending` | Accept \| Reject \| Suggest Alternative |
| `accepted` | Mark as Borrowed |
| `borrowed` | Mark as Returned |

---

### 6.3 `dashboard/borrowed.html` — Books I Am Borrowing

- List all `BorrowRequests` where `borrower_id = current_user.id`
- Columns: Book Title, Owner, Status, Exchange Date/Time/Location (if physical)
- For `status=borrowed` on digital books → show `Download` button
- For `status=borrowed` → show `Mark as Returned` button

---

## 7. Profile Pages

### 7.1 `profile/view.html` — Public Profile

- Profile image (or default avatar placeholder), Name, Bio, Contact, Member since date
- Grid of books shared by this user
- *"Report this User"* link (visible to other members, not to the profile owner)

### 7.2 `profile/edit.html` — Edit My Profile

| Field | Input Type | Notes |
|---|---|---|
| Full Name | `text` | Pre-filled from `current_user.name` |
| Bio | `textarea` | Short personal description |
| Contact | `text` | Phone or other contact info |
| Profile Image | `file` | Optional; accept `.jpg`, `.jpeg`, `.png`, `.gif` |

---

## 8. Borrow Request UI Flow

### 8.1 Physical Book Request

**Step 1 — Borrower submits request** (`/books/<id>`)
- Click *"Request to Borrow"* → inline form appears
- Fill Date, Time, Location, Message → Submit
- Flash: *"Borrow request sent! Waiting for owner approval."*

**Step 2 — Owner responds** (`/dashboard/incoming-requests`)
- Incoming request visible in dashboard table
- Owner clicks **Accept** → `status = 'accepted'`
- Owner clicks **Reject** → `status = 'rejected'`
- Owner clicks **Suggest Alternative** → edits date/time/location → `status = 'suggested'`

**Step 3 — After physical handover** (Owner)
- Owner clicks *"Mark as Borrowed"* → `book.status = 'borrowed'`, `borrowed_at` recorded

**Step 4 — After book is returned** (Owner or Borrower)
- Click *"Mark as Returned"* → `book.status = 'available'`, `returned_at` recorded

### 8.2 Digital Book Request

- Borrower clicks *"Borrow"* → request auto-created and auto-accepted
- *"Download Book"* button appears immediately
- *"Mark as Returned"* visible to borrower; system also auto-returns after 7 days

---

## 9. Admin Panel Pages

### 9.1 `admin/dashboard.html`

- Stat boxes: Total Users, Total Books, Open Reports, Active Borrows
- Quick nav links to: Manage Users, Manage Books, Review Reports

### 9.2 `admin/users.html` — Manage Users

- Table: ID, Name, Email, Role, Status, Registered Date, Actions
- Actions: **Block** (if active) / **Unblock** (if blocked) — shown as a toggle button
- Admin cannot block themselves — hide action button for own row
- Status badges: `active` = green, `blocked` = red

### 9.3 `admin/books.html` — Manage Books

- Table: Title, Author, Type, Owner, Status, Listed Date, Actions
- Actions: View Details, Delete
- Filter bar: by status, by type

### 9.4 `admin/reports.html` — Review Reports

- Table: Reporter, Target (Book or User), Reason, Date, Status, Actions
- Actions: Mark as Reviewed, Dismiss
- Filter: show open only vs. all

---

## 10. Favorites / Wishlist Page

- Responsive grid of book cards saved by the user
- Each card has a *"Remove from Favorites"* button
- If a favorited book is now `available` → show *"Request to Borrow"* shortcut button
- Empty state: *"No favorites yet. Browse books to add some!"*

---

## 11. Complete Template Reference

| Template File | Flask Route | Access | Key UI Elements |
|---|---|---|---|
| `auth/register.html` | `/auth/register` | Public | Registration form (5 fields) |
| `auth/login.html` | `/auth/login` | Public | Login form, flash errors |
| `books/catalog.html` | `/books` | Login req. | Search bar, filters, book card grid |
| `books/detail.html` | `/books/<id>` | Login req. | Book info, context-aware action buttons |
| `books/add.html` | `/books/add` | Login req. | Add book form with conditional JS fields |
| `books/edit.html` | `/books/<id>/edit` | Owner / Admin | Pre-filled edit form |
| `dashboard/index.html` | `/dashboard` | Login req. | Stats, welcome, quick links |
| `dashboard/my_books.html` | `/dashboard/incoming-requests` | Login req. | Incoming borrow requests with owner actions |
| `dashboard/borrowed.html` | `/dashboard/borrowed` | Login req. | Books I am borrowing |
| `profile/view.html` | `/profile/<id>` | Login req. | Public profile, user's books, report link |
| `profile/edit.html` | `/profile/edit` | Login req. | Edit name, bio, contact, profile image |
| `borrow/request_form.html` | Inline / modal | Login req. | Borrow request form (date, time, location) |
| `borrow/request_detail.html` | `/borrow/<id>` | Owner / Borrower | Full request details and status |
| `favorites/wishlist.html` | `/favorites` | Login req. | Saved books grid with remove buttons |
| `admin/dashboard.html` | `/admin/dashboard` | Admin only | Counts, overview stats |
| `admin/users.html` | `/admin/users` | Admin only | User table with block/unblock |
| `admin/books.html` | `/admin/books` | Admin only | All books with delete action |
| `admin/reports.html` | `/admin/reports` | Admin only | Reports queue, mark reviewed/dismiss |

---

## 12. JavaScript Interactions

All interactions live in `static/js/main.js`.

| Interaction | Implementation |
|---|---|
| Toggle borrow request form | `document.querySelector('#borrow-form').classList.toggle('hidden')` |
| Physical vs Digital fields | Listen on Book Type `radio` change; show/hide conditional sections |
| Flash message auto-dismiss | `setTimeout(() => { flash.remove() }, 4000)` for each flash alert |
| Delete confirmation | `confirm('Are you sure you want to delete this?')` before submitting delete form |
| Block/Unblock user confirm | `confirm()` dialog before submitting block/unblock form in admin |
| Search on Enter key | Listen for `keydown === 'Enter'` on search input; submit the form |
| Add to Favorites feedback | Toggle button text between *"Add to Favorites"* and *"Remove from Favorites"* |

---

## 13. CSS Styling Guidelines

### 13.1 Color Palette

| Element | Hex Color | Usage |
|---|---|---|
| Primary / Navbar | `#2E4A7A` | Navbar background, primary buttons |
| Available badge | `#28A745` | Book status: Available |
| Borrowed badge | `#FD7E14` | Book status: Borrowed |
| Returned badge | `#17A2B8` | Book status: Returned |
| Blocked badge (admin) | `#DC3545` | User status: Blocked |
| Success flash bg/text | `#D4EDDA` / `#155724` | Success alert |
| Error flash bg/text | `#F8D7DA` / `#721C24` | Error alert |

### 13.2 Responsive Design

- Use **CSS Flexbox or Grid** for the book catalog card layout
- Mobile breakpoint: `max-width: 768px` → stack cards to single column
- Navbar: collapse to hamburger menu on mobile
- Forms: `width: 100%` on mobile

### 13.3 Status Badge CSS Example

```css
.badge { padding: 4px 10px; border-radius: 12px; font-size: 0.8rem; font-weight: 600; }
.badge-available { background: #D4EDDA; color: #155724; }
.badge-borrowed  { background: #FFE5CC; color: #7A3A00; }
.badge-returned  { background: #D1ECF1; color: #0C5460; }
.badge-blocked   { background: #F8D7DA; color: #721C24; }
```

---

*Book Sharing Platform · CS619 Final Project · Group F25PROJECT92F39*
