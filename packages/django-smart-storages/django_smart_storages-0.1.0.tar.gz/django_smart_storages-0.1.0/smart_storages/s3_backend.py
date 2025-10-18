from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage


class BaseSpecialS3Storage(S3Boto3Storage):
    """
    Generic reusable S3 storage backend that provides a robust configuration
    hierarchy for bucket name, region, and options.
    """

    storage_key = None  # e.g. "import_export" or "analytics"

    def __init__(self, **kwargs):
        # 1. Validation: Ensure the subclass has set a storage_key
        if self.storage_key is None:
            raise NotImplementedError(
                "Subclasses of BaseSpecialS3Storage must set a 'storage_key' class attribute."
            )

        # 2. Initialize Options: Start with project-wide/legacy defaults
        options = {
            "querystring_auth": getattr(settings, "AWS_QUERYSTRING_AUTH", True),
            "default_acl": getattr(settings, "AWS_DEFAULT_ACL", None),
            "object_parameters": getattr(settings, "AWS_S3_OBJECT_PARAMETERS", {}),
            # General region default
            "region_name": getattr(settings, "AWS_S3_REGION_NAME", None),
        }

        bucket_name = None

        # 3. Hierarchy for Options and Bucket Name (Prioritizing STORAGES)
        if hasattr(settings, "STORAGES"):
            storage_conf = settings.STORAGES.get(self.storage_key, {})

            # Update base options with OPTIONS from STORAGES (includes region_name)
            options.update(storage_conf.get("OPTIONS", {}))

            # Check for bucket_name within the updated options
            bucket_name = options.get("bucket_name", None)

        # 4. Fallback for Bucket Name (Directly to AWS_STORAGE_BUCKET_NAME)
        # This is the single, final bucket name fallback.
        if bucket_name is None:
            bucket_name = getattr(settings, "AWS_STORAGE_BUCKET_NAME", None)

        # 5. Secondary Fallback for Region (Explicitly check <STORAGE_KEY>_REGION)
        # This remains useful for specific regional overrides not in STORAGES.
        if options["region_name"] is None:
            region_key = f"{self.storage_key.upper()}_REGION"
            options["region_name"] = getattr(settings, region_key, None)

        # 6. Final Assembly and Override
        options["bucket_name"] = bucket_name

        # Override any setting with explicit kwargs passed to the constructor
        options.update(kwargs)

        super().__init__(**options)
