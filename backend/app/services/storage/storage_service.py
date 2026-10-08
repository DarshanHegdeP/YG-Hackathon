import os
import hashlib
from typing import Tuple
from app.config import settings

class StorageService:
    def __init__(self):
        self.supabase_client = None
        self.bucket = settings.SUPABASE_STORAGE_BUCKET
        self.local_dir = settings.LOCAL_STORAGE_DIR

        # Initialize local storage directory
        os.makedirs(self.local_dir, exist_ok=True)

        if settings.SUPABASE_URL and settings.SUPABASE_SERVICE_ROLE_KEY:
            try:
                from supabase import create_client
                self.supabase_client = create_client(
                    settings.SUPABASE_URL,
                    settings.SUPABASE_SERVICE_ROLE_KEY
                )
            except Exception as e:
                print(f"[StorageService] Failed to initialize Supabase client: {e}. Falling back to local storage.")
                self.supabase_client = None

    def calculate_sha256(self, file_bytes: bytes) -> str:
        return hashlib.sha256(file_bytes).hexdigest()

    async def upload_file(self, file_bytes: bytes, file_name: str, content_type: str = "application/octet-stream") -> Tuple[str, str, int]:
        """
        Uploads file to Supabase Storage or local storage fallback.
        Returns: (storage_path, sha256_hash, file_size)
        """
        sha256_hash = self.calculate_sha256(file_bytes)
        file_size = len(file_bytes)
        safe_path = f"{sha256_hash[:8]}_{file_name}"

        # 1. Try Supabase Storage
        if self.supabase_client:
            try:
                # Ensure bucket exists or attempt upload
                self.supabase_client.storage.from_(self.bucket).upload(
                    path=safe_path,
                    file=file_bytes,
                    file_options={"content-type": content_type, "upsert": "true"}
                )
                return safe_path, sha256_hash, file_size
            except Exception as e:
                print(f"[StorageService] Supabase upload error: {e}. Falling back to local storage.")

        # 2. Local fallback
        local_file_path = os.path.join(self.local_dir, safe_path)
        with open(local_file_path, "wb") as f:
            f.write(file_bytes)

        return safe_path, sha256_hash, file_size

    async def download_file(self, storage_path: str) -> bytes:
        """
        Downloads / retrieves file bytes by storage_path.
        """
        if self.supabase_client:
            try:
                data = self.supabase_client.storage.from_(self.bucket).download(storage_path)
                return data
            except Exception as e:
                print(f"[StorageService] Supabase download error: {e}. Checking local fallback.")

        local_file_path = os.path.join(self.local_dir, storage_path)
        if os.path.exists(local_file_path):
            with open(local_file_path, "rb") as f:
                return f.read()

        raise FileNotFoundError(f"Storage path {storage_path} not found.")

storage_service = StorageService()
