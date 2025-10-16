"""Google Cloud Storage utilities for file uploads."""

import asyncio
import base64
import json
from io import BytesIO
from typing import Optional, Union
from urllib.parse import urlparse

try:
  from google.cloud import storage
  from google.oauth2 import service_account

  GCP_AVAILABLE = True
except ImportError:
  storage = None  # type: ignore
  service_account = None  # type: ignore
  GCP_AVAILABLE = False

from ..config import settings


class GCPStorageError(Exception):
  """Base exception for GCP storage operations"""

  pass


class GCPConfigurationError(GCPStorageError):
  """Raised when GCP is not properly configured"""

  pass


class GCPUploadError(GCPStorageError):
  """Raised when file upload fails"""

  pass


class GCPClient:
  """GCP client for cloud storage operations."""

  def __init__(self):
    """Initialize GCP client.

    Raises:
        GCPConfigurationError: If GCP libraries are not installed or credentials are not configured
    """
    if not GCP_AVAILABLE:
      raise GCPConfigurationError("Google Cloud Storage library not installed. Install with: pip install google-cloud-storage")

    if not settings.gcp_creds:
      raise GCPConfigurationError("GCP credentials not configured. Set GCP_CREDS environment variable.")

    if not settings.gcp_bucket:
      raise GCPConfigurationError("GCP bucket not configured. Set GCP_BUCKET environment variable.")

    try:
      decoded_creds = base64.b64decode(settings.gcp_creds.get_secret_value()).decode("utf-8")
      creds_dict = json.loads(decoded_creds)
      self.project_id = creds_dict.get("project_id")
      if not self.project_id:
        raise GCPConfigurationError("GCP credentials missing 'project_id' field")

      credentials = service_account.Credentials.from_service_account_info(creds_dict)
      self.client = storage.Client(credentials=credentials, project=self.project_id)
      self.bucket_name = settings.gcp_bucket

    except json.JSONDecodeError as e:
      raise GCPConfigurationError(f"Invalid GCP credentials JSON: {e}")
    except Exception as e:
      raise GCPConfigurationError(f"Failed to initialize GCP client: {e}")

  def _get_bucket(self):
    """Get GCP bucket object.

    Returns:
        Bucket object

    Raises:
        GCPStorageError: If bucket cannot be accessed
    """
    try:
      return self.client.bucket(self.bucket_name)
    except Exception as e:
      raise GCPStorageError(f"Failed to access bucket '{self.bucket_name}': {e}")

  async def upload_file(
    self,
    file: Union[BytesIO, bytes],
    key: str,
    content_type: Optional[str] = None,
    generate_signed_url: bool = True,
    expires_in: int = 3600 * 24 * 7,
  ) -> str:
    """Upload a file to GCP Cloud Storage.

    Args:
        file: File to upload (BytesIO or bytes)
        key: GCP object key (path/filename)
        content_type: Optional MIME content type
        generate_signed_url: If True, returns a signed URL for private buckets (default: True)
        expires_in: Signed URL expiration in seconds (default: 7 days)

    Returns:
        str: Signed URL (if generate_signed_url=True) or public URL

    Raises:
        GCPUploadError: If upload fails
        ValueError: If file type is not supported
    """
    # Validate file type and prepare contents
    if isinstance(file, BytesIO):
      file.seek(0)
      contents = file.getvalue()
    elif isinstance(file, bytes):
      contents = file
    else:
      raise ValueError(f"Unsupported file type: {type(file)}. Expected BytesIO or bytes.")

    if not contents:
      raise ValueError("Cannot upload empty file")

    # Execute blocking GCP operations in a thread
    def sync_upload():
      bucket = self._get_bucket()
      blob = bucket.blob(key)

      if content_type:
        blob.content_type = content_type

      blob.upload_from_string(contents, content_type=content_type)

    try:
      await asyncio.to_thread(sync_upload)

      # Generate signed URL for private bucket access (default 7 days)
      if generate_signed_url:
        return await self.get_presigned_url(key, expires_in=expires_in)
      else:
        return f"https://storage.googleapis.com/{self.bucket_name}/{key}"

    except Exception as e:
      raise GCPUploadError(f"Failed to upload file to GCP: {e}")

  async def get_presigned_url(self, key: str, expires_in: int = 3600) -> str:
    """Generate a signed URL for private bucket access.

    Args:
        key: GCP object key (path/filename)
        expires_in: URL expiration time in seconds (default: 1 hour)

    Returns:
        str: Signed URL

    Raises:
        GCPStorageError: If URL generation fails
    """

    def sync_generate_url():
      try:
        from datetime import timedelta

        bucket = self._get_bucket()
        blob = bucket.blob(key)
        return blob.generate_signed_url(version="v4", expiration=timedelta(seconds=expires_in), method="GET")
      except Exception as e:
        raise GCPStorageError(f"Failed to generate signed URL for key '{key}': {e}")

    try:
      return await asyncio.to_thread(sync_generate_url)
    except GCPStorageError:
      raise
    except Exception as e:
      raise GCPStorageError(f"Failed to generate signed URL: {e}")

  @staticmethod
  def get_key_from_url(url: str) -> str:
    """Extract the GCP object key from a URL.

    Args:
        url: GCP URL

    Returns:
        str: GCP object key

    Raises:
        ValueError: If URL is invalid
    """
    if not url:
      raise ValueError("URL cannot be empty")

    try:
      parsed = urlparse(url)
      path = parsed.path.lstrip("/")
      # Remove bucket name from path if present
      parts = path.split("/", 1)
      return parts[1] if len(parts) > 1 else parts[0]
    except Exception as e:
      raise ValueError(f"Invalid GCP URL '{url}': {e}")


def get_gcp_client() -> Optional[GCPClient]:
  """Get GCP client instance if configured, otherwise return None.

  Returns:
      GCPClient instance if GCP is properly configured, None otherwise
  """
  try:
    # Only create client if settings are configured
    if not settings.gcp_bucket or not settings.gcp_creds:
      return None
    return GCPClient()
  except GCPConfigurationError:
    return None


# Module-level instance cache for reuse
_gcp_client_cache: Optional[GCPClient] = None


def get_gcp_client_cached() -> GCPClient:
  """Get or create cached GCP client instance.

  This function provides a singleton-like behavior for the GCP client,
  reusing the same instance across calls to avoid repeated initialization.

  Returns:
      GCPClient instance

  Raises:
      GCPConfigurationError: If GCP is not properly configured
  """
  global _gcp_client_cache
  if _gcp_client_cache is None:
    _gcp_client_cache = GCPClient()
  return _gcp_client_cache
