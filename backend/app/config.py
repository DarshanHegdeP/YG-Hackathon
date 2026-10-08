from typing import List, Union
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator, model_validator


class Settings(BaseSettings):
    # ── Database ────────────────────────────────────────────────────────────
    # PostgreSQL is the default for production and Supabase deployments.
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/evidence_bot"

    # ── JWT / Auth ───────────────────────────────────────────────────────────
    JWT_SECRET: str = "hackathon-dev-secret-key-32-character-min-key-12345"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    # ── Supabase (core) ─────────────────────────────────────────────────────
    SUPABASE_URL: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""
    SUPABASE_SECRET_KEY: str = ""
    SUPABASE_PUBLISHABLE_KEY: str = ""

    # ── Supabase S3-compatible Storage ──────────────────────────────────────
    SUPABASE_STORAGE_BUCKET: str = "evidence"
    SUPABASE_S3_ENDPOINT: str = ""
    SUPABASE_S3_REGION: str = "ap-northeast-1"
    SUPABASE_S3_ACCESS_KEY_ID: str = ""
    SUPABASE_S3_SECRET_ACCESS_KEY: str = ""

    # ── Local storage fallback ──────────────────────────────────────────────
    LOCAL_STORAGE_DIR: str = "./storage_uploads"

    # ── Gemini AI ───────────────────────────────────────────────────────────
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-1.5-flash"

    # ── Cloudflare AI (CLEF) ────────────────────────────────────────────────
    CLOUDFLARE_ACCOUNT_ID: str = ""
    CLOUDFLARE_API_TOKEN: str = ""
    CLOUDFLARE_AI_GATEWAY_ID: str = "default"
    CLEF_MODEL: str = "@cf/cloudflare/clef"

    # ── Provider Selection ──────────────────────────────────────────────────
    EXTRACTION_PROVIDER: str = "local"
    DECISION_PROVIDER: str = "gemini"

    # ── Email (Resend) ──────────────────────────────────────────────────────
    RESEND_API_KEY: str = ""
    EMAIL_FROM: str = "onboarding@resend.dev"

    # ── Frontend / CORS ─────────────────────────────────────────────────────
    FRONTEND_URL: str = "http://localhost:5173"
    CORS_ORIGINS: Union[str, List[str]] = (
        "http://localhost:5173,http://localhost:3000"
    )

    # ── Scheduler ───────────────────────────────────────────────────────────
    REMINDER_INTERVAL_MINUTES: int = 60
    REMINDER_1_DAYS_BEFORE: int = 2
    REMINDER_2_DAYS_BEFORE: int = 1
    ESCALATION_DAYS_AFTER: int = 1

    # ── Environment configuration ──────────────────────────────────────────
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # ── Database URL normalization ──────────────────────────────────────────
    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def fix_database_url(cls, v: str) -> str:
        if v and v.startswith("postgres://"):
            return v.replace("postgres://", "postgresql://", 1)
        return v

    # ── Derived configuration ──────────────────────────────────────────────
    @model_validator(mode="after")
    def derive_defaults(self) -> "Settings":

        # 1. SUPABASE_SECRET_KEY is an alias for SUPABASE_SERVICE_ROLE_KEY
        if self.SUPABASE_SECRET_KEY and not self.SUPABASE_SERVICE_ROLE_KEY:
            self.SUPABASE_SERVICE_ROLE_KEY = self.SUPABASE_SECRET_KEY

        # 2. Auto-derive DATABASE_URL from Supabase project when the local
        #    PostgreSQL default has not been overridden.
        if (
            self.DATABASE_URL in {"postgresql://postgres:postgres@localhost:5432/evidence_bot", "sqlite:///./evidence_bot.db"}
            and self.SUPABASE_URL
            and self.SUPABASE_SERVICE_ROLE_KEY
        ):
            try:
                project_ref = (
                    self.SUPABASE_URL
                    .replace("https://", "")
                    .split(".")[0]
                )

                region = self.SUPABASE_S3_REGION or "ap-northeast-1"

                self.DATABASE_URL = (
                    f"postgresql://postgres.{project_ref}:"
                    f"{self.SUPABASE_SERVICE_ROLE_KEY}@"
                    f"aws-0-{region}.pooler.supabase.com:6543/postgres"
                )

            except Exception:
                pass

        return self

    # ── CORS ────────────────────────────────────────────────────────────────
    def get_cors_origins(self) -> List[str]:
        if isinstance(self.CORS_ORIGINS, list):
            return self.CORS_ORIGINS

        if isinstance(self.CORS_ORIGINS, str):
            return [
                origin.strip()
                for origin in self.CORS_ORIGINS.split(",")
                if origin.strip()
            ]

        return ["*"]

    # ── Supabase S3 availability ────────────────────────────────────────────
    def has_supabase_s3(self) -> bool:
        return bool(
            self.SUPABASE_S3_ENDPOINT
            and self.SUPABASE_S3_ACCESS_KEY_ID
            and self.SUPABASE_S3_SECRET_ACCESS_KEY
        )

    # ── Cloudflare AI availability ──────────────────────────────────────────
    def has_cloudflare_ai(self) -> bool:
        return bool(
            self.CLOUDFLARE_ACCOUNT_ID
            and self.CLOUDFLARE_API_TOKEN
        )


settings = Settings()