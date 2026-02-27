#!/usr/bin/env python3
"""
⚙️ CYBERHOUND CONFIGURATION MANAGER
Centralized configuration with .env file support.
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

# Try to load python-dotenv if available
try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False


@dataclass
class Config:
    """Application configuration."""
    
    # Telegram
    telegram_bot_token: Optional[str] = None
    telegram_chat_id: Optional[str] = None
    
    # Scraping
    rate_limit_delay: float = 1.0
    max_retries: int = 3
    request_timeout: int = 30
    
    # Cron/Loop
    cycle_interval: int = 1800  # 30 minutes
    max_hunt_runtime: int = 1800  # 30 minutes
    
    # Alerts
    alert_webhook_url: Optional[str] = None
    alert_email: Optional[str] = None
    
    # Paths
    data_dir: Path = Path(__file__).parent / "data"
    
    # Logging
    log_level: str = "INFO"
    
    # Proxy (optional)
    http_proxy: Optional[str] = None
    https_proxy: Optional[str] = None
    
    @classmethod
    def from_env(cls, env_file: Optional[Path] = None) -> "Config":
        """Load configuration from environment variables."""
        
        # Load .env file if available
        if DOTENV_AVAILABLE:
            if env_file:
                load_dotenv(env_file)
            else:
                # Try to find .env in project root
                project_root = Path(__file__).parent.parent
                env_path = project_root / ".env"
                if env_path.exists():
                    load_dotenv(env_path)
        
        # Build config from environment
        return cls(
            telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN"),
            telegram_chat_id=os.getenv("TELEGRAM_CHAT_ID"),
            rate_limit_delay=float(os.getenv("RATE_LIMIT_DELAY", "1.0")),
            max_retries=int(os.getenv("MAX_RETRIES", "3")),
            request_timeout=int(os.getenv("REQUEST_TIMEOUT", "30")),
            cycle_interval=int(os.getenv("CYCLE_INTERVAL", "1800")),
            max_hunt_runtime=int(os.getenv("MAX_HUNT_RUNTIME", "1800")),
            alert_webhook_url=os.getenv("ALERT_WEBHOOK_URL"),
            alert_email=os.getenv("ALERT_EMAIL"),
            data_dir=Path(os.getenv("DATA_DIR", Path(__file__).parent / "data")),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            http_proxy=os.getenv("HTTP_PROXY"),
            https_proxy=os.getenv("HTTPS_PROXY"),
        )
    
    def is_telegram_configured(self) -> bool:
        """Check if Telegram is properly configured."""
        return bool(
            self.telegram_bot_token 
            and self.telegram_chat_id 
            and self.telegram_bot_token != "YOUR_BOT_TOKEN"
        )
    
    def is_alert_webhook_configured(self) -> bool:
        """Check if alert webhook is configured."""
        return bool(self.alert_webhook_url)
    
    def get_proxy_dict(self) -> Optional[dict]:
        """Get proxy configuration as dict for requests/aiohttp."""
        if self.http_proxy or self.https_proxy:
            return {
                "http": self.http_proxy,
                "https": self.https_proxy or self.http_proxy,
            }
        return None
    
    def validate(self) -> list:
        """Validate configuration and return list of issues."""
        issues = []
        
        # Check data directory
        if not self.data_dir.exists():
            issues.append(f"Data directory does not exist: {self.data_dir}")
        
        # Check rate limiting
        if self.rate_limit_delay < 0:
            issues.append("RATE_LIMIT_DELAY cannot be negative")
        if self.rate_limit_delay < 0.1:
            issues.append("RATE_LIMIT_DELAY < 0.1s may get you blocked")
        
        # Check timeouts
        if self.request_timeout < 5:
            issues.append("REQUEST_TIMEOUT < 5s may cause frequent timeouts")
        
        # Check cycle interval
        if self.cycle_interval < 60:
            issues.append("CYCLE_INTERVAL < 60s is very aggressive")
        
        return issues
    
    def to_dict(self) -> dict:
        """Convert config to dictionary (for serialization)."""
        return {
            "telegram_configured": self.is_telegram_configured(),
            "rate_limit_delay": self.rate_limit_delay,
            "max_retries": self.max_retries,
            "request_timeout": self.request_timeout,
            "cycle_interval": self.cycle_interval,
            "log_level": self.log_level,
            "data_dir": str(self.data_dir),
        }
    
    def __str__(self) -> str:
        """String representation for debugging."""
        lines = ["Cyberhound Configuration:"]
        lines.append(f"  Telegram: {'✅' if self.is_telegram_configured() else '❌'}")
        lines.append(f"  Rate Limit: {self.rate_limit_delay}s")
        lines.append(f"  Retries: {self.max_retries}")
        lines.append(f"  Cycle: {self.cycle_interval}s ({self.cycle_interval//60}min)")
        lines.append(f"  Log Level: {self.log_level}")
        lines.append(f"  Data Dir: {self.data_dir}")
        return "\n".join(lines)


# Global config instance (lazy loaded)
_config: Optional[Config] = None


def get_config() -> Config:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        _config = Config.from_env()
    return _config


def reload_config() -> Config:
    """Reload configuration from environment."""
    global _config
    _config = Config.from_env()
    return _config


if __name__ == "__main__":
    # When run directly, print config
    config = get_config()
    print(config)
    print()
    
    issues = config.validate()
    if issues:
        print("⚠️  Issues found:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("✅ Configuration valid")
