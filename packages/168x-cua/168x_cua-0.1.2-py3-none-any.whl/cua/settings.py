import logging
logger = logging.getLogger(__name__)

import os

def get_env_var(name: str, default: str | None = None) -> str:
    value = os.getenv(name)
    
    if value is None:
        if default is not None:
            return default
        else:
            raise ValueError(f"Environment variable {name} is not set")
    else:
        return value


class Settings:
    """Application configuration settings"""
    
    CUA_ENVIRONMENT: str = get_env_var("CUA_ENVIRONMENT")
    CUA_ROOT_DIR: str = get_env_var("CUA_ROOT_DIR")
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def log_all(self):
        """Log all configuration values (masking any overly long ones)."""
        # Attributes are defined at the *class* level, so iterate over the class dict
        for key, value in self.__class__.__dict__.items():
            # Skip private/dunder and callables
            if key.startswith("_") or callable(value):
                continue
            # Only include uppercase settings constants
            if not key.isupper():
                continue
            logger.debug(f"{key}: {str(value)[:5]}")

# Global settings instance
settings = Settings()

# Only export the singleton instance, not the class
__all__ = ['settings'] 