"""Supabase Storage backend over its REST API.

Render's free web service disk is wiped on every deploy and every restart,
which was silently losing every uploaded photo (forum posts, profile
photos, observaciones de seguimiento). Storing files in a Supabase Storage
bucket instead keeps them across deploys.
"""

import mimetypes
from urllib.parse import quote

import requests
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import Storage
from django.utils.deconstruct import deconstructible


@deconstructible
class SupabaseStorage(Storage):
    def __init__(self, bucket=None, public=True):
        self.bucket = bucket or settings.SUPABASE_STORAGE_BUCKET
        self.public = public

    def _base_url(self):
        return settings.SUPABASE_URL.rstrip("/") + "/storage/v1"

    def _headers(self, **extra):
        key = settings.SUPABASE_SERVICE_ROLE_KEY
        return {"Authorization": f"Bearer {key}", "apikey": key, **extra}

    def _object_url(self, name):
        return f"{self._base_url()}/object/{self.bucket}/{quote(name)}"

    def _open(self, name, mode="rb"):  # noqa: ARG002 - Storage API shape
        response = requests.get(self._object_url(name), headers=self._headers(), timeout=20)
        response.raise_for_status()
        return ContentFile(response.content, name=name)

    def _save(self, name, content):
        content.seek(0)
        content_type = mimetypes.guess_type(name)[0] or "application/octet-stream"
        headers = self._headers(**{"Content-Type": content_type, "x-upsert": "true"})
        response = requests.post(self._object_url(name), headers=headers, data=content.read(), timeout=30)
        response.raise_for_status()
        return name

    def exists(self, name):
        response = requests.get(f"{self._base_url()}/object/info/{self.bucket}/{quote(name)}", headers=self._headers(), timeout=10)
        return response.status_code == 200

    def delete(self, name):
        requests.delete(self._object_url(name), headers=self._headers(), timeout=10)

    def size(self, name):
        response = requests.get(f"{self._base_url()}/object/info/{self.bucket}/{quote(name)}", headers=self._headers(), timeout=10)
        response.raise_for_status()
        return response.json().get("size", 0)

    def url(self, name):
        if not self.public:
            raise ValueError("Use the permission-checked attachment endpoint.")
        return f"{settings.SUPABASE_URL.rstrip('/')}/storage/v1/object/public/{self.bucket}/{quote(name)}"
