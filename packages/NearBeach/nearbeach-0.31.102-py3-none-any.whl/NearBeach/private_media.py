from django.conf import settings
from django.core.files.storage import FileSystemStorage


class FileStorage(FileSystemStorage):
    def __init__(self, location=None, base_url=None):
        if location is None:
            location = settings.PRIVATE_MEDIA_ROOT
        if base_url is None:
            base_url = settings.PRIVATE_MEDIA_URL
        super(FileStorage, self).__init__(location, base_url)
