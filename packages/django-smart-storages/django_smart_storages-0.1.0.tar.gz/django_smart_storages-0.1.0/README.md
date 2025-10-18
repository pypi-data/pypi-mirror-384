# django-smart-storages

Reusable, specialized storage backends built on top of django-storages

This package provides a simple, consistent way to define multiple custom S3 or file storage backends in Django projects — each with its own configuration, bucket, or logic — without repeating boilerplate code.

# Features

Clean abstraction for per-use-case S3 buckets
Seamless integration with django-storages
Built-in backend resolver for dynamic imports
Optional fallback to local storage in development
Easy to extend for any specialized storage use case

# Installation

`pip install django-special-storages`

# Configuration

In your Django settings, add the relevant apps:

```python
# settings.py

INSTALLED_APPS = [
    'storages',    # this is for django-storages
]
```
## Example: Custom Storage Classes

Define specialized storage classes in your code (e.g., `views.py` or a separate `storages.py`):

```python
# views.py (or storages.py)

from smart_storages import BaseSpecialS3Storage

class ImportExportS3Storage(BaseSpecialS3Storage):
    storage_key = "import_export"

class AnalyticsS3Storage(BaseSpecialS3Storage):
    storage_key = "analytics"
```


## Example: Configuring Multiple Storages

Add your bucket names and the STORAGES setting:

```python
# settings.py

AWS_STORAGE_BUCKET_NAME = "main-bucket"

STORAGES = {
    # Default file storage
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },

    # Static files
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },

    # Import-export-specific S3 storage (using your custom base class)
    "import_export": {
        "BACKEND": "special_storages.s3.ImportExportS3Storage",
        "OPTIONS": {
            "custom_domain": None,
            "querystring_auth": True,
        },
    },

    # Analytics-specific S3 storage
    "analytics": {
        "BACKEND": "special_storages.s3.AnalyticsS3Storage",
        "OPTIONS": {
            "custom_domain": None,
        },
    },
}
```

# Example 1: Saving directly to S3 via FileField
## This will automatically use the given bucket configured in ImportExportS3.

```
class PublicImage(models.Model):
    file = models.FileField(storage=ImportExportS3())
```

# Example 2: Saving a file via model's save() method
## Useful if you need to process or manipulate the file before uploading.
```
class PublicImage(models.Model):
    file = models.FileField()

    def save(self, *args, **kwargs):
        # Only upload if a file is provided
        if self.file and hasattr(self.file, 'file'):
            storage = ImportExportS3()
            # Save file content to S3
            saved_name = storage.save(self.file.name, self.file)
            # Update the file name to the S3 path
            self.file.name = saved_name

        super().save(*args, **kwargs)
```

# Example 3: Uploading a file from a remote URL (binary download or streaming)
## Useful for fetching external content and storing it directly in S3.

```
import requests
from django.core.files.base import ContentFile

class PublicImage(models.Model):
    image = models.URLField(blank=True, null=True)

    def save(self, *args, **kwargs):
        # Fetch an image from a remote URL
        image_url = "https://www.edx.org/contentful/ii9ehdcj88bc/2SkUwC7Kf9G5I5b49hjVgu/1fa2453e92e46d980f9f99cf08a51e73/image_processing.jpg?w=435&h=245&fm=webp"
        response = requests.get(image_url)

        if response.status_code == 200:
            # Wrap content in Django ContentFile
            content = ContentFile(response.content)

            # Use custom S3 storage to save
            storage = ImportExportS3()
            file_name = storage.save("deb.png", content)

            # Update the model field with the S3 URL
            self.image = storage.url(file_name)

        # Save model instance
        super().save(*args, **kwargs)
```

> **Note:**  
> You can place these custom storage classes in any appropriate module (such as `storages.py`), and reference them in your `STORAGES` Django setting.
