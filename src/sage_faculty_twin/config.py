from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[2]


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="DIGITAL_TWIN_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    owner_name: str = Field(default="张书豪")
    owner_role: str = Field(default="华中科技大学计算机学院教师")
    model_name: str = Field(default="meta-llama/Llama-3.1-8B-Instruct")
    llm_base_url: str = Field(default="http://127.0.0.1:8000/v1")
    api_key: str = Field(default="EMPTY")
    llm_timeout_seconds: int = Field(default=60, ge=1, le=300)
    llm_retry_attempts: int = Field(default=2, ge=0, le=5)
    llm_retry_backoff_seconds: float = Field(default=1.0, ge=0.0, le=30.0)
    llm_cache_ttl_seconds: int = Field(default=3600, ge=0, le=86400)
    llm_cache_max_entries: int = Field(default=512, ge=0, le=4096)
    system_prompt: str = Field(
        default=(
            "You are a trusted academic digital twin. Answer clearly, avoid fabricating policy, "
            "and route scheduling requests into structured booking guidance."
        )
    )
    owner_style_profile_path: Path = Field(default=Path("data/persona/style_profile.md"))
    homepage_dir: Path = Field(default=REPO_ROOT / "data/homepage")
    homepage_public_url: str = Field(default="")
    booking_timezone: str = Field(default="Asia/Shanghai")
    booking_start_hour: int = Field(default=9, ge=0, le=23)
    booking_end_hour: int = Field(default=18, ge=1, le=24)
    meeting_duration_minutes: int = Field(default=30, ge=15, le=120)
    availability_schedule_path: Path = Field(default=Path("data/availability/current_week.json"))
    booking_notification_email: str = Field(default="faculty@example.edu")
    smtp_host: str | None = Field(default=None)
    smtp_port: int = Field(default=587, ge=1, le=65535)
    smtp_username: str | None = Field(default=None)
    smtp_password: str | None = Field(default=None)
    smtp_sender: str | None = Field(default=None)
    smtp_use_tls: bool = Field(default=True)
    smtp_use_ssl: bool = Field(default=False)
    smtp_timeout_seconds: int = Field(default=15, ge=1, le=120)
    knowledge_base_dir: Path = Field(default=Path("data/knowledge_base"))
    knowledge_backend: str = Field(default="neuromem")
    retrieval_top_k: int = Field(default=3, ge=1, le=10)
    conversation_memory_dir: Path = Field(default=Path("data/conversation_memory"))
    artifact_memory_draft_dir: Path = Field(default=Path("data/artifact_memory_drafts"))
    knowledge_gap_draft_dir: Path = Field(default=Path("data/knowledge_gap_drafts"))
    escalation_queue_dir: Path = Field(default=Path("data/escalations"))
    follow_up_queue_dir: Path = Field(default=Path("data/follow_up_actions"))
    operations_task_state_dir: Path = Field(default=Path("data/operations_task_state"))
    suggestion_board_dir: Path = Field(default=Path("data/suggestions"))
    user_account_store_dir: Path = Field(default=Path("data/user_accounts"))
    workflow_policy_path: Path = Field(
        default=Path("data/workflow_policies/faculty-default-2026-05.json")
    )
    planner_comparison_dir: Path | None = Field(default=None)
    planner_metrics_dir: Path | None = Field(default=None)
    shadow_planner_enabled: bool = Field(default=True)
    shadow_planner_temperature: float = Field(default=0.0, ge=0.0, le=1.0)
    shadow_planner_max_tokens: int = Field(default=384, ge=64, le=2048)
    conversation_memory_top_k: int = Field(default=4, ge=1, le=10)
    sagevdb_embedding_backend: str = Field(default="sentence-transformers")
    sagevdb_embedding_model: str = Field(default="sentence-transformers/all-MiniLM-L6-v2")
    sagevdb_dimension: int = Field(default=256, ge=32, le=4096)
    sagevdb_backend: str = Field(default="cpp")
    sagevdb_anns_algorithm: str = Field(default="faiss_hnsw")
    service_manager_script: Path = Field(default=REPO_ROOT / "manage.sh")
    admin_username: str = Field(default="admin")
    admin_password: str = Field(default="change-me-admin-password")
    admin_session_secret: str = Field(default="change-me-admin-session-secret")
    admin_session_ttl_seconds: int = Field(default=43200, ge=300, le=604800)
    user_session_secret: str = Field(default="change-me-user-session-secret")
    user_session_ttl_seconds: int = Field(default=2592000, ge=300, le=7776000)


settings = AppSettings()
