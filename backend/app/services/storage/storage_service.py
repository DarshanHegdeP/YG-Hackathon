import os
import hashlib
from typing import Tuple
from app.config import settings


class StorageService:
    """
    Unified storage service with three backends (tried in order):
      1. Supabase S3-compatible API  (boto3, uses SUPABASE_S3_* credentials)
      2. Supabase Python client      (uses SUPABASE_SERVICE_ROLE_KEY)
      3. Local filesystem fallback
    """

    def __init__(self):
        self.bucket = settings.SUPABASE_STORAGE_BUCKET
        self.local_dir = settings.LOCAL_STORAGE_DIR
        self._s3_client = None
        self._supabase_client = None

        os.makedirs(self.local_dir, exist_ok=True)

        # ── Backend 1: Supabase S3-compatible (boto3) ──────────────────────
        if settings.has_supabase_s3():
            try:
                import boto3
                from botocore.config import Config
                self._s3_client = boto3.client(
                    "s3",
                    endpoint_url=settings.SUPABASE_S3_ENDPOINT,
                    aws_access_key_id=settings.SUPABASE_S3_ACCESS_KEY_ID,
                    aws_secret_access_key=settings.SUPABASE_S3_SECRET_ACCESS_KEY,
                    region_name=settings.SUPABASE_S3_REGION,
                    config=Config(signature_version="s3v4"),
                )
                print(f"[StorageService] ✅ Using Supabase S3 storage (bucket: {self.bucket})")
            except Exception as e:
                print(f"[StorageService] ⚠ Failed to init S3 client: {e}. Will try Supabase client.")

        # ── Backend 2: Supabase Python client (fallback) ───────────────────
        if not self._s3_client and settings.SUPABASE_URL and settings.SUPABASE_SERVICE_ROLE_KEY:
            try:
                from supabase import create_client
                self._supabase_client = create_client(
                    settings.SUPABASE_URL,
                    settings.SUPABASE_SERVICE_ROLE_KEY,
                )
                print(f"[StorageService] ✅ Using Supabase Python client storage (bucket: {self.bucket})")
            except Exception as e:
                print(f"[StorageService] ⚠ Failed to init Supabase client: {e}. Falling back to local storage.")

        if not self._s3_client and not self._supabase_client:
            print(f"[StorageService] ℹ Using local filesystem storage ({self.local_dir})")

    # ── Helpers ────────────────────────────────────────────────────────────

    def calculate_sha256(self, file_bytes: bytes) -> str:
        return hashlib.sha256(file_bytes).hexdigest()

    # ── Upload ─────────────────────────────────────────────────────────────

    async def upload_file(
        self, file_bytes: bytes, file_name: str, content_type: str = "application/octet-stream"
    ) -> Tuple[str, str, int]:
        """
        Uploads a file and returns (storage_path, sha256_hash, file_size).
        Tries S3 → Supabase client → local, in that order.
        """
        sha256_hash = self.calculate_sha256(file_bytes)
        file_size = len(file_bytes)
        safe_path = f"{sha256_hash[:8]}_{file_name}"

        # 1. Supabase S3-compatible API (boto3)
        if self._s3_client:
            try:
                self._s3_client.put_object(
                    Bucket=self.bucket,
                    Key=safe_path,
                    Body=file_bytes,
                    ContentType=content_type,
                )
                return safe_path, sha256_hash, file_size
            except Exception as e:
                print(f"[StorageService] S3 upload error: {e}. Trying Supabase client.")

        # 2. Supabase Python client
        if self._supabase_client:
            try:
                self._supabase_client.storage.from_(self.bucket).upload(
                    path=safe_path,
                    file=file_bytes,
                    file_options={"content-type": content_type, "upsert": "true"},
                )
                return safe_path, sha256_hash, file_size
            except Exception as e:
                print(f"[StorageService] Supabase client upload error: {e}. Falling back to local storage.")

        # 3. Local filesystem
        local_file_path = os.path.join(self.local_dir, safe_path)
        with open(local_file_path, "wb") as f:
            f.write(file_bytes)
        return safe_path, sha256_hash, file_size

    # ── Download ───────────────────────────────────────────────────────────

    async def download_file(self, storage_path: str) -> bytes:
        """
        Downloads a file by its storage_path. Tries S3 → Supabase client → local.
        """
        # 1. Supabase S3-compatible API
        if self._s3_client:
            try:
                response = self._s3_client.get_object(Bucket=self.bucket, Key=storage_path)
                return response["Body"].read()
            except Exception as e:
                print(f"[StorageService] S3 download error: {e}. Trying Supabase client.")

        # 2. Supabase Python client
        if self._supabase_client:
            try:
                data = self._supabase_client.storage.from_(self.bucket).download(storage_path)
                return data
            except Exception as e:
                print(f"[StorageService] Supabase client download error: {e}. Checking local fallback.")

        # 3. Local filesystem
        local_file_path = os.path.join(self.local_dir, storage_path)
        if os.path.exists(local_file_path):
            with open(local_file_path, "rb") as f:
                return f.read()

        raise FileNotFoundError(f"Storage path '{storage_path}' not found in any storage backend.")


storage_service = StorageService()
