"""Configuration constants for Shotgun agents."""

from enum import StrEnum, auto

# Field names
API_KEY_FIELD = "api_key"
SUPABASE_JWT_FIELD = "supabase_jwt"
SHOTGUN_INSTANCE_ID_FIELD = "shotgun_instance_id"
CONFIG_VERSION_FIELD = "config_version"


class ConfigSection(StrEnum):
    """Configuration file section names (JSON keys)."""

    OPENAI = auto()
    ANTHROPIC = auto()
    GOOGLE = auto()
    SHOTGUN = auto()


# Backwards compatibility - deprecated
OPENAI_PROVIDER = ConfigSection.OPENAI.value
ANTHROPIC_PROVIDER = ConfigSection.ANTHROPIC.value
GOOGLE_PROVIDER = ConfigSection.GOOGLE.value
SHOTGUN_PROVIDER = ConfigSection.SHOTGUN.value

# Environment variable names
OPENAI_API_KEY_ENV = "OPENAI_API_KEY"
ANTHROPIC_API_KEY_ENV = "ANTHROPIC_API_KEY"
GEMINI_API_KEY_ENV = "GEMINI_API_KEY"
SHOTGUN_API_KEY_ENV = "SHOTGUN_API_KEY"

# Token limits
MEDIUM_TEXT_8K_TOKENS = 8192  # Default max_tokens for web search requests
