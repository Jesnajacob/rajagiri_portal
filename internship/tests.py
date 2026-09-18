from django.test import TestCase
from django.urls import reverse

from accounts.models import User


class InternshipManagementAccessTests(TestCase):
    def test_placement_officer_can_view_manage_list(self):
        user = User.objects.create_user(
            username="placementuser",
            email="placement@example.com",
            password="securepass123",
            role="placement_officer",
        )

        self.client.force_login(user)
        response = self.client.get(reverse("internship:manage_list"))

        self.assertEqual(response.status_code, 200)
