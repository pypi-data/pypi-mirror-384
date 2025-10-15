"""
Configuration Management for OS Forge

Centralized configuration settings and environment variables.
"""

import os
from typing import List


class Config:
    """
    Application configuration settings
    """
    
    # API Configuration
    API_TITLE = "OS Forge"
    API_DESCRIPTION = "Multi-Platform System Hardening Tool with Security Validation"
    API_VERSION = "1.0.0"
    
    # Security Configuration
    API_KEY = os.getenv("OS_FORGE_API_KEY", "dev-key-change-in-production")
    
    # Database Configuration
    MONGODB_URI = os.getenv("MONGODB_URI", "")
    MONGODB_DATABASE = os.getenv("MONGODB_DATABASE", "Os-forge")
    
    # CORS Configuration
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://frontend:3000"
    ]
    
    # Logging Configuration
    LOG_LEVEL = os.getenv("OS_FORGE_LOG_LEVEL", "INFO")
    
    # Server Configuration
    DEFAULT_HOST = "127.0.0.1"
    DEFAULT_PORT = 8000
    
    @classmethod
    def get_cors_origins(cls) -> List[str]:
        """Get CORS origins from environment or use defaults"""
        env_origins = os.getenv("OS_FORGE_CORS_ORIGINS")
        if env_origins:
            return env_origins.split(",")
        return cls.CORS_ORIGINS
    
    @classmethod
    def validate_config(cls) -> bool:
        """Validate required configuration values"""
        try:
            # Check if API key is set (not default)
            if cls.API_KEY == "dev-key-change-in-production":
                print("WARNING: Using default API key. Set OS_FORGE_API_KEY environment variable for production.")
            
            # Check MongoDB configuration
            if not cls.MONGODB_URI:
                print("WARNING: MONGODB_URI not set. MongoDB features will be disabled.")
            
            return True
        except Exception as e:
            print(f"Configuration validation error: {e}")
            return False

