from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    datahub_gms_url: str = "http://localhost:8080"
    datahub_gms_token: str = ""
    datahub_mcp_url: str = ""
    datahub_mcp_command: str = "uvx mcp-server-datahub"

    llm_provider: str = "gemini"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-flash-latest"
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-5-20250929"
    aws_region: str = "us-east-1"
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_session_token: str = ""
    bedrock_api_key: str = ""
    bedrock_model_id: str = "us.anthropic.claude-sonnet-4-5-20250929-v1:0"
    max_tokens: int = 16384

    hindsight_auto_approve: bool = False
    hindsight_max_hops: int = 3
    phase_max_turns: int = 12
    audit_log_path: str = "var/audit-log.jsonl"

    cors_origins: str = "http://localhost:5173"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
