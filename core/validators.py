import os
from django.core.exceptions import ValidationError
from django.conf import settings


def validate_file_size(value):
    max_size = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if value.size > max_size:
        raise ValidationError(f"File too large. Max size is {settings.MAX_UPLOAD_SIZE_MB}MB.")


def validate_resume_extension(value):
    ext = os.path.splitext(value.name)[1].lower()
    if ext not in settings.ALLOWED_RESUME_EXTENSIONS:
        raise ValidationError("Only PDF, DOC, DOCX resumes are allowed.")


def validate_image_extension(value):
    ext = os.path.splitext(value.name)[1].lower()
    if ext not in settings.ALLOWED_IMAGE_EXTENSIONS:
        raise ValidationError("Only JPG and PNG images are allowed.")


def validate_document_extension(value):
    ext = os.path.splitext(value.name)[1].lower()
    if ext not in settings.ALLOWED_DOCUMENT_EXTENSIONS:
        raise ValidationError("Unsupported document type.")
