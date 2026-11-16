from pathlib import Path
from uuid import uuid4

from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.utils.deconstruct import deconstructible

from huertos_medicinales.storage import SupabaseStorage


@deconstructible
class ForumStorage(FileSystemStorage):
    """Kept under this name: earlier migrations serialize a reference to it."""

    def __init__(self):
        super().__init__(location=Path(settings.BASE_DIR) / "private_forum")

    def url(self, name):
        msg = "Use the permission-checked attachment endpoint."
        raise ValueError(msg)


def forum_storage():
    """Supabase Storage when configured (production); local disk otherwise (dev)."""
    bucket = getattr(settings, "SUPABASE_STORAGE_BUCKET_FORUM", "")
    if bucket:
        return SupabaseStorage(bucket=bucket, public=False)
    return ForumStorage()


def attachment_path(instance, filename):
    return f"{uuid4().hex}{Path(filename).suffix.lower()}"
