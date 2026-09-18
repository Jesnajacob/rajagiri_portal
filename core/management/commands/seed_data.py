import random
from datetime import timedelta, date

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model

from core.models import Department, Achievement, Announcement
from students.models import StudentProfile
from faculty.models import FacultyProfile
from alumni.models import AlumniProfile
from placement.models import Company, PlacementDrive
from internship.models import Internship
from rlabs.models import RLabsProject
from research.models import ResearchOpportunity
from events.models import Event

User = get_user_model()

DEPARTMENTS = [
    ("Computer Science", "CS"),
    ("Social Work", "SW"),
    ("Commerce", "COM"),
    ("Mass Communication", "MC"),
    ("Economics", "ECO"),
]

SKILLS_POOL = ["Python", "Django", "Java", "React", "SQL", "OpenCV", "Machine Learning",
               "Data Analysis", "Public Speaking", "Excel", "C++", "JavaScript", "AWS"]

FIRST_NAMES = ["Aarav", "Diya", "Kabir", "Meera", "Rohan", "Sneha", "Arjun", "Isha",
               "Vikram", "Ananya", "Nikhil", "Priya", "Rahul", "Kavya", "Aditya"]
LAST_NAMES = ["Nair", "Menon", "Pillai", "Varma", "Kurian", "Jose", "Thomas", "Iyer",
              "Krishnan", "Das"]


class Command(BaseCommand):
    help = "Seed the database with demo data for RCSS Connect."

    def handle(self, *args, **options):
        self.stdout.write("Seeding RCSS Connect demo data...")

        departments = []
        for name, code in DEPARTMENTS:
            dept, _ = Department.objects.get_or_create(name=name, code=code)
            departments.append(dept)

        # ---------------- Admin ----------------
        if not User.objects.filter(username="admin").exists():
            User.objects.create_superuser(
                username="admin", email="admin@rcss.edu", password="admin12345",
                first_name="System", last_name="Administrator", role="admin",
            )
            self.stdout.write("Created superuser: admin / admin12345")

        # ---------------- Placement Officer ----------------
        officer, created = User.objects.get_or_create(
            username="placement1", defaults=dict(
                email="placement1@rcss.edu", first_name="Priya", last_name="Officer",
                role="placement_officer",
            ))
        if created:
            officer.set_password("password123")
            officer.save()

        # ---------------- RLabs Coordinator ----------------
        coordinator, created = User.objects.get_or_create(
            username="rlabs1", defaults=dict(
                email="rlabs1@rcss.edu", first_name="Rahul", last_name="Coordinator",
                role="rlabs_coordinator",
            ))
        if created:
            coordinator.set_password("password123")
            coordinator.save()

        # ---------------- Faculty ----------------
        faculty_profiles = []
        for i in range(5):
            username = f"faculty{i+1}"
            user, created = User.objects.get_or_create(
                username=username, defaults=dict(
                    email=f"{username}@rcss.edu",
                    first_name=random.choice(FIRST_NAMES), last_name=random.choice(LAST_NAMES),
                    role="faculty",
                ))
            if created:
                user.set_password("password123")
                user.save()
            profile, _ = FacultyProfile.objects.get_or_create(
                user=user, defaults=dict(
                    department=random.choice(departments),
                    designation=random.choice(["assistant_professor", "associate_professor", "professor"]),
                    specialization=random.choice(SKILLS_POOL),
                    bio="Faculty member passionate about mentoring students in research and innovation.",
                ))
            faculty_profiles.append(profile)

        # ---------------- Students ----------------
        student_profiles = []
        for i in range(10):
            username = f"student{i+1}"
            user, created = User.objects.get_or_create(
                username=username, defaults=dict(
                    email=f"{username}@rcss.edu",
                    first_name=random.choice(FIRST_NAMES), last_name=random.choice(LAST_NAMES),
                    role="student",
                ))
            if created:
                user.set_password("password123")
                user.save()
            profile, _ = StudentProfile.objects.get_or_create(
                user=user, defaults=dict(
                    register_number=f"RCSS{1000+i}",
                    department=random.choice(departments),
                    semester=random.randint(3, 8),
                    cgpa=round(random.uniform(6.0, 9.5), 2),
                    skills=", ".join(random.sample(SKILLS_POOL, 4)),
                    career_interests="Software Development, Research",
                ))
            student_profiles.append(profile)

        # ---------------- Alumni ----------------
        for i in range(5):
            username = f"alumni{i+1}"
            user, created = User.objects.get_or_create(
                username=username, defaults=dict(
                    email=f"{username}@rcss.edu",
                    first_name=random.choice(FIRST_NAMES), last_name=random.choice(LAST_NAMES),
                    role="alumni",
                ))
            if created:
                user.set_password("password123")
                user.save()
            AlumniProfile.objects.get_or_create(
                user=user, defaults=dict(
                    department=random.choice(departments),
                    batch="2018-2022", graduation_year=2022,
                    current_company=random.choice(["TCS", "Infosys", "Wipro", "Deloitte", "EY"]),
                    designation="Software Engineer",
                    location="Bangalore", is_mentor=True,
                    success_story="Graduated from RCSS and built a rewarding career in the tech industry.",
                ))

        # ---------------- Companies ----------------
        company_names = ["TCS", "Infosys", "Wipro", "Deloitte", "EY"]
        companies = []
        for name in company_names:
            c, _ = Company.objects.get_or_create(
                name=name, defaults=dict(
                    industry="IT Services", location="Bangalore",
                    description=f"{name} is a leading company hiring RCSS graduates.",
                ))
            companies.append(c)

        # ---------------- Placement Drives ----------------
        now = timezone.now()
        for i, c in enumerate(companies):
            drive, created = PlacementDrive.objects.get_or_create(
                company=c, job_role=f"{'Software Developer' if i % 2 == 0 else 'Business Analyst'}",
                defaults=dict(
                    job_description="Exciting opportunity to join our team and work on impactful projects.",
                    package=f"{random.randint(4, 12)} LPA",
                    minimum_cgpa=round(random.uniform(6.0, 7.5), 2),
                    required_skills=", ".join(random.sample(SKILLS_POOL, 3)),
                    registration_deadline=now + timedelta(days=random.randint(5, 20)),
                    interview_date=now + timedelta(days=random.randint(21, 30)),
                    posted_by=officer, is_published=True,
                ))
            if created:
                drive.eligible_departments.set(random.sample(departments, 2))

        # ---------------- Internships ----------------
        for i, c in enumerate(companies):
            Internship.objects.get_or_create(
                company=c, title=f"{'Data Analyst Intern' if i % 2 == 0 else 'Software Intern'}",
                defaults=dict(
                    description="Work with our engineering team on live projects.",
                    location="Remote", duration="3 months", stipend="15000/month",
                    skills_required=", ".join(random.sample(SKILLS_POOL, 3)),
                    start_date=date.today() + timedelta(days=15),
                    application_deadline=date.today() + timedelta(days=10),
                    posted_by=officer, is_active=True,
                ))

        # ---------------- RLabs Projects ----------------
        rlabs_titles = ["AI-based Computer Vision Project", "Smart Campus IoT System",
                         "Natural Language Chatbot", "Blockchain Voting System", "Predictive Analytics Dashboard"]
        for title in rlabs_titles:
            RLabsProject.objects.get_or_create(
                title=title, defaults=dict(
                    description="An RLabs research project open to CS students with relevant skills.",
                    required_skills=", ".join(random.sample(SKILLS_POOL, 3)),
                    faculty_mentor=random.choice(faculty_profiles),
                    students_required=random.randint(2, 4),
                    deadline=date.today() + timedelta(days=15),
                    duration="8 weeks", status="open",
                    coordinator=coordinator, is_published=True,
                ))

        # ---------------- Research Opportunities ----------------
        research_topics = ["Social Impact of Digital Learning", "Machine Learning for Healthcare",
                            "Sustainable Urban Development", "Behavioral Economics Study", "Climate Change Awareness"]
        for topic in research_topics:
            ResearchOpportunity.objects.get_or_create(
                topic=topic, defaults=dict(
                    faculty=random.choice(faculty_profiles),
                    research_area=random.choice(["Technology", "Social Sciences", "Environment", "Economics"]),
                    description="Join this research initiative and contribute to meaningful academic work.",
                    required_skills=", ".join(random.sample(SKILLS_POOL, 2)),
                    students_required=random.randint(1, 3),
                    duration="1 semester",
                    application_deadline=date.today() + timedelta(days=20),
                ))

        # ---------------- Events ----------------
        event_titles = ["AI & Data Science Workshop", "Career Guidance Seminar", "National Hackathon 2026",
                         "Placement Preparation Bootcamp", "Alumni Meet 2026"]
        for i, title in enumerate(event_titles):
            Event.objects.get_or_create(
                title=title, defaults=dict(
                    description="Join us for this exciting event organized by RCSS Connect.",
                    event_type=random.choice(["workshop", "seminar", "hackathon", "career_talk"]),
                    date=now + timedelta(days=10 + i * 3),
                    venue="RCSS Main Auditorium", organizer="RCSS Connect",
                    registration_deadline=now + timedelta(days=8 + i * 3),
                    max_participants=100, created_by=officer,
                ))

        # ---------------- Achievements ----------------
        for sp in random.sample(student_profiles, 4):
            Achievement.objects.get_or_create(
                user=sp.user, title=random.choice(
                    ["Won Smart India Hackathon", "Published Research Paper", "Best Intern Award", "1st Prize in Coding Contest"]),
                defaults=dict(
                    achievement_type=random.choice(["hackathon", "publication", "award", "competition"]),
                    is_featured=True,
                ))

        # ---------------- Announcements ----------------
        Announcement.objects.get_or_create(
            title="Welcome to RCSS Connect!",
            defaults=dict(
                message="RCSS Connect is now live. Explore placements, internships, career resources, and student experiences in one place.",
                category="general", posted_by=officer,
            ))

        self.stdout.write(self.style.SUCCESS("Demo data seeded successfully!"))
