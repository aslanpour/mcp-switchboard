"""Configuration file loader."""
from pathlib import Path
from typing import Optional
import yaml
from .models import SwitchboardConfig


class ConfigLoader:
    """Load and validate configuration files."""
    
    DEFAULT_CONFIG_PATH = Path.home() / ".mcp-switchboard" / "config.yaml"
    
    @classmethod
    def load(cls, config_path: Optional[Path] = None) -> SwitchboardConfig:
        """Load configuration from file or use defaults."""
        path = config_path or cls.DEFAULT_CONFIG_PATH
        
        if not path.exists():
            return SwitchboardConfig()
        
        with open(path) as f:
            data = yaml.safe_load(f)
        
        return SwitchboardConfig(**data) if data else SwitchboardConfig()
    
    @classmethod
    def save(cls, config: SwitchboardConfig, config_path: Optional[Path] = None) -> None:
        """Save configuration to file."""
        path = config_path or cls.DEFAULT_CONFIG_PATH
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, "w") as f:
            yaml.dump(config.model_dump(), f, default_flow_style=False)
