"""Configuration management for the marking tool."""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import yaml


@dataclass
class MarkingConfig:
    """Configuration for the marking tool."""
    
    # OpenAI settings
    api_key: str
    model_name: str
    temperature: float = 0.0
    max_retries: int = 3
    retry_delay: float = 1.0
    
    # Processing settings
    batch_size: int = 1
    timeout_seconds: int = 300  # 5 minutes per student
    
    # Output settings
    output_format: str = "xlsx"
    include_summary: bool = True
    
    # Paths
    models_dir: Optional[Path] = None
    cache_dir: Optional[Path] = None
    
    @classmethod
    def from_env(cls, model_name: str) -> "MarkingConfig":
        """
        Create configuration from environment variables.
        
        Args:
            model_name: OpenAI model name
            
        Returns:
            MarkingConfig instance
        """
        api_key = os.environ.get("OPENAI_API_KEY", "")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        
        return cls(
            api_key=api_key,
            model_name=model_name,
            temperature=float(os.environ.get("MARKING_TEMPERATURE", "0.0")),
            max_retries=int(os.environ.get("MARKING_MAX_RETRIES", "3")),
            retry_delay=float(os.environ.get("MARKING_RETRY_DELAY", "1.0")),
            batch_size=int(os.environ.get("MARKING_BATCH_SIZE", "1")),
            timeout_seconds=int(os.environ.get("MARKING_TIMEOUT", "300")),
        )
    
    @classmethod
    def from_file(cls, config_path: Path) -> "MarkingConfig":
        """
        Load configuration from YAML file.
        
        Args:
            config_path: Path to configuration file
            
        Returns:
            MarkingConfig instance
        """
        with open(config_path, "r") as f:
            data = yaml.safe_load(f)
        
        # Get API key from environment if not in config
        if "api_key" not in data:
            data["api_key"] = os.environ.get("OPENAI_API_KEY", "")
        
        # Convert paths to Path objects
        if "models_dir" in data:
            data["models_dir"] = Path(data["models_dir"])
        if "cache_dir" in data:
            data["cache_dir"] = Path(data["cache_dir"])
        
        return cls(**data)
    
    def validate(self) -> None:
        """Validate configuration values."""
        if not self.api_key:
            raise ValueError("API key not configured")
        
        if not self.model_name:
            raise ValueError("Model name not configured")
        
        if self.temperature < 0 or self.temperature > 2:
            raise ValueError("Temperature must be between 0 and 2")
        
        if self.max_retries < 0:
            raise ValueError("Max retries must be non-negative")
        
        if self.batch_size < 1:
            raise ValueError("Batch size must be at least 1")
        
        if self.timeout_seconds < 1:
            raise ValueError("Timeout must be at least 1 second")


@dataclass
class TaskConfig:
    """Configuration for a single marking task."""
    
    task_number: int
    max_points: int
    criteria_count: int
    weight: float = 1.0
    
    def __post_init__(self):
        """Validate task configuration."""
        if self.task_number < 1:
            raise ValueError("Task number must be positive")
        
        if self.max_points < 1:
            raise ValueError("Max points must be positive")
        
        if self.criteria_count < 1:
            raise ValueError("Criteria count must be positive")
        
        if self.weight <= 0:
            raise ValueError("Weight must be positive")


# Default task configurations based on the rubric
DEFAULT_TASK_CONFIGS = {
    2: TaskConfig(task_number=2, max_points=8, criteria_count=5),
    3: TaskConfig(task_number=3, max_points=10, criteria_count=6),
    4: TaskConfig(task_number=4, max_points=15, criteria_count=7),
    5: TaskConfig(task_number=5, max_points=15, criteria_count=7),
    6: TaskConfig(task_number=6, max_points=15, criteria_count=6),
    7: TaskConfig(task_number=7, max_points=20, criteria_count=5),
}
