from pathlib import Path
from uuid import uuid4
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.utils.deconstruct import deconstructible

@deconstructible
class ForumStorage(FileSystemStorage):
    def __init__(self):
        super().__init__(location=Path(settings.BASE_DIR) / 'private_forum')
    def url(self, name):
        raise ValueError('Use the permission-checked attachment endpoint.')

def attachment_path(instance, filename):
    return f'{uuid4().hex}{Path(filename).suffix.lower()}'
