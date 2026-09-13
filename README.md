# RCSS Connect

**Integrated Career, Research & Student Collaboration Portal**
Built for Rajagiri College of Social Sciences with Django, HTML5, CSS3, Bootstrap 5, vanilla JavaScript, Chart.js, and MySQL.

RCSS Connect brings Students, Faculty, the Placement Cell, Alumni, RLabs and Administrators onto a single platform so that placement drives, internships, research opportunities and RLabs projects are never missed — every publish action automatically finds and notifies the right students.

---

## 1. Features Implemented

- **Authentication & Roles** — custom `User` model with 6 roles (Student, Faculty, Placement Officer, RLabs Coordinator, Alumni, Administrator), role-based dashboards and access control via a `role_required` decorator.
- **Student module** — profile with photo, skills, CGPA, career interests, LinkedIn/GitHub; resume upload; projects, certifications, achievements; a public portfolio page; applications to placements/internships/research/RLabs.
- **Placement module** — Company & PlacementDrive CRUD, eligibility by department + minimum CGPA, drive publishing that **automatically identifies eligible students and creates notifications**, applicant tracking with status updates (Applied → Shortlisted → Interview → Selected/Rejected), and a Chart.js analytics dashboard (bar / line / pie / doughnut).
- **Internship module** — CRUD (Placement Officer, Faculty, Alumni can post), browse/search/apply, resume upload per application, applicant tracking.
- **Alumni module** — searchable directory (batch, department, company), mentor flag, success stories, profile with social links.
- **RLabs module** — project CRUD, publishing that **matches students by skill overlap and notifies them automatically**, applications and status tracking.
- **Research module** — Faculty post research opportunities that **notify matching students**, students apply with a statement of interest, Faculty accept/reject and a `ResearchTeam` is created automatically on acceptance. A separate **Research Paper Repository** lets faculty upload papers, searchable by title/author/area.
- **Events module** — workshops/seminars/hackathons/etc. with registration, seat limits and duplicate-registration prevention.
- **Notifications** — a single centralized model driving the navbar bell, dropdown, unread badge and full notification list, with AJAX "mark as read" / "mark all read" (vanilla JS, no page reload).
- **Digital Notice Board** and **Career Preparation Hub** for shared announcements and resources.
- **Admin Dashboard** — system-wide stats plus quick links into Django Admin (already registered for every model) for full CRUD management.
- **Global search** across companies, drives, internships, RLabs projects, research, alumni and events.
- Responsive Bootstrap 5 UI, royal-blue academic theme, Chart.js graphs, custom 404/403/500 pages, CSRF protection, password hashing, file-type/size validated uploads.

## 2. Technology Stack

| Layer      | Technology |
|------------|------------|
| Backend    | Python 3, Django |
| Frontend   | HTML5, CSS3, Bootstrap 5, vanilla JavaScript |
| Charts     | Chart.js |
| Icons      | Bootstrap Icons |
| Database   | MySQL (via PyMySQL) |
| Image lib  | Pillow |

## 3. Project Structure

```
rcss_connect/
├── manage.py
├── requirements.txt
├── rcss_connect/          # settings, urls, wsgi/asgi
├── accounts/              # custom User model, auth
├── students/               # StudentProfile, Resume, Projects, Certifications
├── faculty/                # FacultyProfile
├── placement/              # Company, PlacementDrive, PlacementApplication
├── internship/             # Internship, InternshipApplication
├── alumni/                 # AlumniProfile
├── rlabs/                  # RLabsProject, RLabsApplication
├── research/                # ResearchOpportunity, ResearchApplication, ResearchPaper, ResearchTeam
├── events/                 # Event, EventRegistration
├── notifications/          # Notification, context processor, AJAX views
├── dashboard/               # per-role dashboard views
├── core/                    # Department, Announcement, Achievement, CareerResource, home page, search, seed_data command
├── templates/               # base.html + one folder per app
├── static/{css,js,images,icons}
└── media/                   # user uploads (created at runtime)
```

## 4. Installation

### 4.1 Prerequisites
- Python 3.10+
- MySQL Server 8.x running locally (or update `.env` / environment variables to point elsewhere)

### 4.2 Clone / unzip and create a virtual environment

```bash
cd rcss_connect
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS / Linux

pip install -r requirements.txt
```

### 4.3 MySQL setup

Create the database:

```sql
CREATE DATABASE rcss_connect_db CHARACTER SET utf8mb4;
```

Set your credentials as environment variables (or create a `.env` and load it, or just edit these defaults directly — `settings.py` reads them via `os.environ.get`, so nothing else needs to change):

```bash
set DB_ENGINE=mysql
set DB_NAME=rcss_connect_db
set DB_USER=root
set DB_PASSWORD=yourpassword
set DB_HOST=127.0.0.1
set DB_PORT=3306
```

> **Quick local testing without MySQL:** set `DB_ENGINE=sqlite` and the project will use a local `db.sqlite3` file instead — useful for a fast first run. Switch back to `mysql` (or simply unset `DB_ENGINE`, since `mysql` is the default) before deploying.

### 4.4 Migrate, seed demo data, create a superuser

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py seed_data        # optional: populates demo students, faculty, drives, etc.
python manage.py createsuperuser  # optional if you don't use the seeded admin account
```

### 4.5 Run

```bash
python manage.py runserver
```

Visit **http://127.0.0.1:8000/**

## 5. Sample / Demo Accounts

Running `python manage.py seed_data` creates:

| Role | Username | Password |
|------|----------|----------|
| Administrator | `admin` | `admin12345` |
| Placement Officer | `placement1` | `password123` |
| RLabs Coordinator | `rlabs1` | `password123` |
| Faculty | `faculty1` … `faculty5` | `password123` |
| Student | `student1` … `student10` | `password123` |
| Alumni | `alumni1` … `alumni5` | `password123` |

It also creates 5 departments, 5 companies, 5 published placement drives, 5 internships, 5 RLabs projects, 5 research opportunities, 5 events, and sample achievements/announcements — enough to exercise every workflow immediately.

## 6. Key Workflows to Try

1. **Placement notification workflow** — log in as `placement1`, go to *Manage Drives*, click **Publish** on a draft (or re-publish is a no-op once published — create a new drive to see it fresh). Eligible students (matching department + CGPA) instantly get a notification. Log in as an eligible `studentN` to see it in the bell dropdown.
2. **RLabs notification workflow** — log in as `rlabs1`, *Manage Projects* → **Publish**. Students whose comma-separated `skills` overlap the project's `required_skills` are notified automatically.
3. **Research collaboration workflow** — log in as a `facultyN`, *Post Research Opportunity*. Students with matching skills (or all students, if no skill match) are notified; apply as a student, then have the faculty member Accept/Reject from *My Opportunities → Applicants* — accepting creates a `ResearchTeam`.
4. **Placement analytics** — log in as `placement1` → *Statistics* to see live Chart.js bar/line/pie/doughnut charts (mark some applications "Selected" first to see non-zero numbers).

## 7. Main URLs

```
/                              Home page
/accounts/login/               Login
/accounts/register/            Registration
/dashboard/                    Redirects to the correct role dashboard
/student/profile/edit/         Student profile
/placement/                    Placement drives (list/apply)
/placement/manage/drives/      Placement Officer management
/placement/statistics/         Placement analytics (Chart.js)
/internships/                  Internship listing
/alumni/                       Alumni directory
/rlabs/                        RLabs projects
/research/                     Research opportunities
/research/papers/              Research paper repository
/events/                       Events
/notifications/                Notification center
/dashboard/admin-dashboard/    Admin dashboard
/admin/                        Django admin (full CRUD for every model)
```

## 8. Notes & Known Limitations

- Ships configured for **MySQL** by default (via PyMySQL, no native build tools required); a `DB_ENGINE=sqlite` fallback is provided purely for a fast first run without installing MySQL.
- File uploads (resumes, photos, papers, certificates) are validated for extension and size (see `core/validators.py`, `MAX_UPLOAD_SIZE_MB` in `settings.py`) and stored under `media/`.
- All destructive actions (delete company/drive/project/event) show a confirmation page or a JS `confirm()` dialog before executing.
- The seed command is idempotent (`get_or_create`) — safe to re-run.
- `DEBUG=True` and a placeholder `SECRET_KEY` are the defaults for local development; set `DJANGO_DEBUG=False`, a real `DJANGO_SECRET_KEY`, and `DJANGO_ALLOWED_HOSTS` via environment variables before deploying.

## 9. Testing Performed

Before delivery this project was actually run (not just written): `makemigrations`/`migrate` completed with no errors, `manage.py check` reported zero issues, demo data was seeded, and the dev server was exercised end-to-end — registration, login/logout for every role, all six dashboards, placement drive publish → student notification, RLabs project publish → skill-matched notification, placement application → officer status update → student notification, research opportunity → apply → accept → team creation, the search page, the paper repository, and the Chart.js statistics endpoint all returned correct, error-free responses.
