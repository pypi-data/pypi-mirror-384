from pathlib import Path
from pydantic import BaseModel, Field

class Config(BaseModel):
    """Configuration model with Pydantic validation"""
    backend_api_base_url: str = Field(..., description="Backend API base URL")
    agent_instance_id: str = Field(..., description="Agent instance identifier")
    secret_key: str = Field(..., description="Secret key for authentication")
    
    model_config = {
        "extra": "ignore",  # Ignore extra fields in JSON
        "validate_assignment": True,  # Validate on attribute assignment
    }
    
    
# Global settings instance
_config: Config | None = None
    
def init_config_from_json_file(config_path: str | Path):
    """Load configuration from a JSON file using Pydantic's native JSON parsing"""
    config_path = Path(config_path)
    
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    # Use Pydantic v2 method for JSON deserialization
    json_content = config_path.read_text(encoding="utf-8")
    
    global _config
    _config = Config.model_validate_json(json_content)


def get_config() -> Config:
    """Get the global configuration instance"""
    if _config is None:
        raise RuntimeError("Config not initialized")
    return _config

