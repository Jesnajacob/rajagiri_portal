from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from .models import CareerResource


class CareerResourceTests(TestCase):
	def setUp(self):
		self.placement_officer = User.objects.create_user(
			username="career_placement",
			password="test-password",
			role="placement_officer",
		)
		self.student = User.objects.create_user(
			username="career_student",
			password="test-password",
			role="student",
		)

	def test_placement_officer_can_create_upload_edit_and_delete_resource(self):
		self.client.force_login(self.placement_officer)
		upload = SimpleUploadedFile("interview-guide.pdf", b"pdf content", content_type="application/pdf")
		response = self.client.post(reverse("core:career_resource_create"), {
			"title": "Interview Guide",
			"description": "Preparation notes",
			"resource_type": "interview",
			"file": upload,
			"link": "",
		})

		resource = CareerResource.objects.get(title="Interview Guide")
		self.assertRedirects(response, reverse("core:career_hub"))
		self.assertTrue(resource.file.name.startswith("career_resources/interview-guide"))
		self.assertTrue(resource.file.name.endswith(".pdf"))

		response = self.client.post(reverse("core:career_resource_edit", args=[resource.pk]), {
			"title": "Updated Interview Guide",
			"description": "Updated preparation notes",
			"resource_type": "interview",
			"file": "",
			"link": "https://example.com/interview-guide",
		})
		resource.refresh_from_db()
		self.assertRedirects(response, reverse("core:career_hub"))
		self.assertEqual(resource.title, "Updated Interview Guide")
		self.assertEqual(resource.link, "https://example.com/interview-guide")

		response = self.client.post(reverse("core:career_resource_delete", args=[resource.pk]))
		self.assertRedirects(response, reverse("core:career_hub"))
		self.assertFalse(CareerResource.objects.filter(pk=resource.pk).exists())

	def test_students_can_search_and_view_resources_but_cannot_manage_them(self):
		resource = CareerResource.objects.create(
			title="Aptitude Practice",
			description="Practice material",
			resource_type="aptitude",
			link="https://example.com/aptitude",
			uploaded_by=self.placement_officer,
		)
		self.client.force_login(self.student)

		response = self.client.get(reverse("core:career_hub"), {"q": "Aptitude"})
		self.assertContains(response, resource.title)
		self.assertContains(response, resource.link)
		self.assertEqual(
			self.client.get(reverse("core:career_resource_create")).status_code,
			403,
		)
