"""Configuration management using environment variables and dataclasses"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import yaml


@dataclass 
class Settings:
    """Application settings with environment variable support"""
    
    # Application settings
    app_name: str = "IOSG Crypto News Analysis"
    app_version: str = "1.0.0"
    secret_key: str = field(default="crypto-news-analyzer-secret-key")
    debug: bool = field(default=False)
    host: str = field(default="0.0.0.0")
    port: int = field(default=8080)
    
    # AI API settings
    openai_api_key: Optional[str] = field(default=None)
    deepseek_api_key: Optional[str] = field(default=None) 
    deepseek_base_url: str = field(default="https://api.deepseek.com")
    default_ai_provider: str = field(default="openai")
    ai_batch_size: int = field(default=20)
    
    # Email settings
    mail_server: str = field(default="smtp.gmail.com")
    mail_port: int = field(default=587)
    mail_username: str = field(default="your-email@gmail.com")
    mail_password: str = field(default="your-app-password")
    mail_use_tls: bool = field(default=True)
    mail_use_ssl: bool = field(default=False)
    
    # Data paths
    data_dir: Path = field(default_factory=lambda: Path("."))
    crypto_config_file: Path = field(default_factory=lambda: Path("crypto_config.yaml"))
    
    # Processing settings
    max_log_entries: int = field(default=1000)
    process_timeout: int = field(default=3600)  # seconds
    
    def __post_init__(self):
        """Load environment variables after initialization"""
        self.secret_key = os.getenv("SECRET_KEY", self.secret_key)
        self.debug = os.getenv("DEBUG", "").lower() in ('true', '1', 'yes')
        self.host = os.getenv("HOST", self.host)
        self.port = int(os.getenv("PORT", str(self.port)))
        
        self.openai_api_key = os.getenv("OPENAI_API_KEY", self.openai_api_key)
        self.deepseek_api_key = os.getenv("DEEPSEEK_API_KEY", self.deepseek_api_key)
        self.deepseek_base_url = os.getenv("DEEPSEEK_BASE_URL", self.deepseek_base_url)
        self.default_ai_provider = os.getenv("DEFAULT_AI_PROVIDER", self.default_ai_provider)
        self.ai_batch_size = int(os.getenv("AI_BATCH_SIZE", str(self.ai_batch_size)))
        
        self.mail_server = os.getenv("MAIL_SERVER", self.mail_server)
        self.mail_port = int(os.getenv("MAIL_PORT", str(self.mail_port)))
        self.mail_username = os.getenv("MAIL_USERNAME", self.mail_username)
        self.mail_password = os.getenv("MAIL_PASSWORD", self.mail_password)
        self.mail_use_tls = os.getenv("MAIL_USE_TLS", "").lower() in ('true', '1', 'yes')
        self.mail_use_ssl = os.getenv("MAIL_USE_SSL", "").lower() in ('true', '1', 'yes')
        
        self.data_dir = Path(os.getenv("DATA_DIR", str(self.data_dir)))
        self.crypto_config_file = Path(os.getenv("CRYPTO_CONFIG_FILE", str(self.crypto_config_file)))
        
        self.max_log_entries = int(os.getenv("MAX_LOG_ENTRIES", str(self.max_log_entries)))
        self.process_timeout = int(os.getenv("PROCESS_TIMEOUT", str(self.process_timeout)))
        
        # Ensure data directory exists
        self.data_dir.mkdir(exist_ok=True)
        # Resolve crypto config file path
        self.crypto_config_file = self.crypto_config_file.resolve()
    
    def get_mail_config(self) -> Dict[str, Any]:
        """Get Flask-Mail configuration"""
        return {
            'MAIL_SERVER': self.mail_server,
            'MAIL_PORT': self.mail_port,
            'MAIL_USE_TLS': self.mail_use_tls,
            'MAIL_USE_SSL': self.mail_use_ssl,
            'MAIL_USERNAME': self.mail_username,
            'MAIL_PASSWORD': self.mail_password,
            'MAIL_DEFAULT_SENDER': self.mail_username
        }
    
    def get_ai_config(self) -> Dict[str, Any]:
        """Get AI provider configuration"""
        return {
            'openai_api_key': self.openai_api_key,
            'deepseek_api_key': self.deepseek_api_key,
            'deepseek_base_url': self.deepseek_base_url,
            'default_provider': self.default_ai_provider,
            'batch_size': self.ai_batch_size
        }


class CryptoConfig:
    """Crypto-specific configuration loader"""
    
    def __init__(self, config_file: Path):
        self.config_file = config_file
        self._config_data = None
        self._load_config()
    
    def _load_config(self):
        """Load crypto configuration from YAML file"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                self._config_data = yaml.safe_load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Crypto config file not found: {self.config_file}")
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in config file: {e}")
    
    def get_portfolio_projects(self) -> List[str]:
        """Get list of portfolio projects"""
        return self._config_data.get('portfolio_projects', [])
    
    def get_classification_config(self) -> Dict[str, Any]:
        """Get classification configuration"""
        return self._config_data.get('classification', {})
    
    def get_categories(self) -> Dict[str, Any]:
        """Get article categories configuration"""
        return self.get_classification_config().get('categories', {})
    
    def get_ai_prompts(self) -> Dict[str, Any]:
        """Get AI prompts configuration"""
        return self._config_data.get('ai_prompts', {})
    
    def get_category_list(self, exclude: Optional[List[str]] = None) -> List[str]:
        """Get list of category names, optionally excluding some"""
        categories = list(self.get_categories().keys())
        if exclude:
            categories = [cat for cat in categories if cat not in exclude]
        return categories


# Global settings instance
_settings = None
_crypto_config = None


def get_settings() -> Settings:
    """Get global settings instance"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def get_crypto_config() -> CryptoConfig:
    """Get global crypto config instance"""
    global _crypto_config
    if _crypto_config is None:
        settings = get_settings()
        _crypto_config = CryptoConfig(settings.crypto_config_file)
    return _crypto_config


def reload_settings():
    """Reload settings (useful for testing)"""
    global _settings, _crypto_config
    _settings = None
    _crypto_config = None