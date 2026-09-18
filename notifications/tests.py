from django.core import mail
from django.test import TestCase, override_settings
from django.utils import timezone

from accounts.models import User
from core.models import Department
from notifications.models import Notification, NotificationPreference, EmailNotificationLog
from notifications.services import send_placement_email
from placement.models import Company, PlacementDrive
from students.models import StudentProfile


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class NotificationEmailFlowTests(TestCase):
    def setUp(self):
        self.dept = Department.objects.create(name="MSc Computer Science", code="MCS")
        self.user = User.objects.create_user(
            username="student1",
            email="student1@example.com",
            password="StrongPass123",
            first_name="Student",
            last_name="One",
            role="student",
        )
        self.profile = StudentProfile.objects.create(
            user=self.user,
            register_number="RCSS001",
            department=self.dept,
            semester=2,
            cgpa=8.9,
            skills="Python, Django, SQL",
        )
        self.company = Company.objects.create(name="ABC Technologies", industry="IT", location="Bangalore")
        self.drive = PlacementDrive.objects.create(
            company=self.company,
            job_role="Software Developer",
            job_description="Build products.",
            package="8 LPA",
            minimum_cgpa=7.0,
            required_skills="Python, Django",
            registration_deadline=timezone.now() + timezone.timedelta(days=10),
            posted_by=self.user,
            is_published=True,
        )
        self.drive.eligible_departments.add(self.dept)

    def test_send_placement_email_creates_notification_and_log(self):
        sent = send_placement_email(self.user, self.drive)
        self.assertTrue(sent)
        self.assertTrue(Notification.objects.filter(recipient=self.user, category="placement").exists())
        self.assertEqual(EmailNotificationLog.objects.filter(recipient=self.user, notification_type="placement").count(), 1)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("New Placement Opportunity", mail.outbox[0].subject)

    def test_duplicate_placement_email_is_not_sent_twice(self):
        first = send_placement_email(self.user, self.drive)
        second = send_placement_email(self.user, self.drive)
        self.assertTrue(first)
        self.assertFalse(second)
        self.assertEqual(len(mail.outbox), 1)

    def test_email_disabled_prevents_send_but_website_notification_still_created(self):
        pref = NotificationPreference.for_user(self.user)
        pref.enable_email_notifications = False
        pref.save(update_fields=["enable_email_notifications"])

        sent = send_placement_email(self.user, self.drive)
        self.assertFalse(sent)
        self.assertTrue(Notification.objects.filter(recipient=self.user, category="placement").exists())
        self.assertEqual(len(mail.outbox), 0)
