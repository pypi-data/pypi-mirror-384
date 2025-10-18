# tests/test_storages.py
import os
from django.test import TestCase
from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage
from smart_storages.s3_backend import BaseSpecialS3Storage  # Assuming this is the module path

# Ensure Django settings are configured for standalone test runs
# Assuming 'smart_storages.tests.settings' exists and configures AWS_STORAGE_BUCKET_NAME, STORAGES, etc.
if not settings.configured:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "smart_storages.tests.settings")


# --- Helper Storage Subclasses ---

class MissingKeyS3Storage(BaseSpecialS3Storage):
    # Intentional: storage_key = None
    pass


class ImportExportS3Storage(BaseSpecialS3Storage):
    storage_key = "import_export"


class AnalyticsS3Storage(BaseSpecialS3Storage):
    storage_key = "analytics"


# --- Test Suite ---

class TestSpecialStorages(TestCase):

    # --- New Tests for Robustness ---

    def test_missing_storage_key_raises_error(self):
        """The base class must raise NotImplementedError if storage_key is not set."""
        with self.assertRaises(NotImplementedError):
            MissingKeyS3Storage()

    def test_region_is_picked_up_from_storages_dict(self):
        """The class should pick up the region name from the STORAGES dict."""
        storage = AnalyticsS3Storage()
        # Assuming settings.STORAGES['analytics']['OPTIONS']['region_name'] is set to 'eu-west-1'
        self.assertEqual(storage.region_name, settings.STORAGES["analytics"]["OPTIONS"]["region_name"])
        self.assertEqual(storage.bucket_name, settings.STORAGES["analytics"]["OPTIONS"]["bucket_name"])

    def test_region_falls_back_to_global_setting(self):
        """If not in STORAGES, region should fallback to AWS_S3_REGION_NAME."""
        # For this test, we temporarily set the key to something not in STORAGES
        # and assume AWS_S3_REGION_NAME is globally set (e.g., 'us-east-1').

        # We'll use ImportExportS3Storage, but temporarily clear its region option for the test
        temp_options = settings.STORAGES["import_export"]["OPTIONS"].copy()
        temp_options.pop("region_name", None)
        settings.STORAGES["import_export"]["OPTIONS"] = temp_options

        storage = ImportExportS3Storage()
        self.assertEqual(storage.region_name, settings.AWS_S3_REGION_NAME)

        # Restore settings to avoid side effects
        settings.STORAGES["import_export"]["OPTIONS"]["region_name"] = "us-east-1-specific"

    # --- Modified/Existing Tests ---

    def test_base_storage_uses_default_bucket(self):
        """Fallback to AWS_STORAGE_BUCKET_NAME if specific bucket is not in STORAGES."""

        # To test the fallback properly, we use a key that we assume exists in STORAGES,
        # but does *not* define a 'bucket_name' option.
        class TempNoBucketStorage(BaseSpecialS3Storage):
            storage_key = "default_fallback_test"

        # Temporarily configure a non-existent storage key without a bucket_name
        settings.STORAGES["default_fallback_test"] = {"BACKEND": "..."}

        storage = TempNoBucketStorage()

        self.assertIsInstance(storage, S3Boto3Storage)
        self.assertEqual(storage.bucket_name, settings.AWS_STORAGE_BUCKET_NAME)
        # Verify defaults from settings are applied
        self.assertFalse(storage.querystring_auth)
        self.assertEqual(storage.default_acl, "private")
        self.assertEqual(storage.object_parameters, {"CacheControl": "max-age=3600"})
        # Clean up
        del settings.STORAGES["default_fallback_test"]

    def test_custom_bucket_is_used(self):
        """The class should pick up its bucket name from the STORAGES dict."""
        storage = ImportExportS3Storage()
        self.assertEqual(storage.bucket_name, settings.STORAGES["import_export"]["OPTIONS"]["bucket_name"])

    def test_multiple_subclasses_can_have_different_buckets(self):
        """Each subclass can have its own bucket."""
        export_storage = ImportExportS3Storage()
        analytics_storage = AnalyticsS3Storage()

        self.assertNotEqual(export_storage.bucket_name, analytics_storage.bucket_name)
        self.assertEqual(export_storage.bucket_name, settings.STORAGES["import_export"]["OPTIONS"]["bucket_name"])
        self.assertEqual(analytics_storage.bucket_name, settings.STORAGES["analytics"]["OPTIONS"]["bucket_name"])

    def test_init_allows_overriding_default_kwargs(self):
        """User-provided kwargs override defaults."""
        # The default for import_export should be True (assuming settings)
        storage = ImportExportS3Storage(querystring_auth=False)
        self.assertFalse(storage.querystring_auth)
        self.assertEqual(storage.bucket_name, settings.STORAGES["import_export"]["OPTIONS"]["bucket_name"])

    def test_acl_can_be_customized(self):
        """Custom ACLs are respected."""
        storage = ImportExportS3Storage(default_acl="public-read")
        self.assertEqual(storage.default_acl, "public-read")

    def test_combined_overrides_with_acl(self):
        """ACL and querystring_auth can both be customized."""
        storage = ImportExportS3Storage(default_acl="private", querystring_auth=False)
        self.assertEqual(storage.default_acl, "private")
        self.assertFalse(storage.querystring_auth)
