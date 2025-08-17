import os
from typing import Optional, List, Dict, Any
from pydantic import Field, validator
from pydantic_settings import BaseSettings
from pathlib import Path
import yaml

class RepositoryConfig(BaseSettings):
    """Configuration for a single repository"""
    name: str
    url: str
    branch: str = "main"
    mkdocs_config: str = "mkdocs.yml"
    deployment: str = "github-pages"
    docs_dir: str = "docs"
    site_dir: str = "site"
    
    class Config:
        env_prefix = "REPO_"

class GoogleDocsConfig(BaseSettings):
    """Configuration for Google Docs integration"""
    credentials_file: str = Field(default="google_credentials.json", env="GOOGLE_CREDENTIALS_FILE")
    scopes: List[str] = Field(default=["https://www.googleapis.com/auth/documents.readonly"], env="GOOGLE_SCOPES")
    
    class Config:
        env_prefix = "GOOGLE_"

class OpenAIConfig(BaseSettings):
    """Configuration for OpenAI integration"""
    api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    model: str = Field(default="gpt-4o-mini", env="OPENAI_MODEL")
    temperature: float = Field(default=0.3, env="OPENAI_TEMPERATURE")
    max_tokens: int = Field(default=4000, env="OPENAI_MAX_TOKENS")
    
    class Config:
        env_prefix = "OPENAI_"

class GitHubConfig(BaseSettings):
    """Configuration for GitHub integration"""
    token: Optional[str] = Field(default=None, env="GITHUB_TOKEN")
    repo_name: Optional[str] = Field(default=None, env="GITHUB_REPO")
    default_branch: str = Field(default="main", env="GITHUB_DEFAULT_BRANCH")
    
    class Config:
        env_prefix = "GITHUB_"

class NotificationConfig(BaseSettings):
    """Configuration for notifications"""
    email_enabled: bool = Field(default=False, env="NOTIFICATION_EMAIL_ENABLED")
    webhook_enabled: bool = Field(default=False, env="NOTIFICATION_WEBHOOK_ENABLED")
    webhook_url: Optional[str] = Field(default=None, env="NOTIFICATION_WEBHOOK_URL")
    
    class Config:
        env_prefix = "NOTIFICATION_"

class AppSettings(BaseSettings):
    """Main application settings"""
    
    # App configuration
    app_name: str = "Google Docs to MkDocs Converter"
    app_version: str = "1.0.0"
    debug: bool = Field(default=False, env="DEBUG")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    # Paths
    base_dir: Path = Field(default=Path.cwd(), env="BASE_DIR")
    config_dir: Path = Field(default=Path.cwd() / "config", env="CONFIG_DIR")
    templates_dir: Path = Field(default=Path.cwd() / "templates", env="TEMPLATES_DIR")
    output_dir: Path = Field(default=Path.cwd() / "output", env="OUTPUT_DIR")
    
    # Service configurations - make them optional for CLI usage
    google_docs: Optional[GoogleDocsConfig] = None
    openai: Optional[OpenAIConfig] = None
    github: Optional[GitHubConfig] = None
    notification: Optional[NotificationConfig] = None
    
    # Repository configurations
    repositories: List[RepositoryConfig] = []
    
    # Template configuration
    default_template: str = Field(default="standard_docs", env="DEFAULT_TEMPLATE")
    auto_detect_template: bool = Field(default=True, env="AUTO_DETECT_TEMPLATE")
    
    # Processing configuration
    max_file_size: int = Field(default=10 * 1024 * 1024, env="MAX_FILE_SIZE")  # 10MB
    supported_formats: List[str] = Field(default=[".md", ".txt", ".html"], env="SUPPORTED_FORMATS")
    
    # Validation
    @validator('repositories', pre=True)
    def load_repositories(cls, v):
        """Load repositories from config file if not provided"""
        if isinstance(v, list):
            return v
        
        # Try to load from config file
        config_file = Path.cwd() / "repositories.yml"
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    config_data = yaml.safe_load(f)
                    if 'repositories' in config_data:
                        return [RepositoryConfig(**repo) for repo in config_data['repositories']]
            except Exception as e:
                print(f"Warning: Could not load repositories from {config_file}: {e}")
        
        return []
    
    @validator('base_dir', 'config_dir', 'templates_dir', 'output_dir', pre=True)
    def ensure_directories_exist(cls, v):
        """Ensure directories exist"""
        if isinstance(v, str):
            v = Path(v)
        v.mkdir(parents=True, exist_ok=True)
        return v
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Initialize service configs only if environment variables are available
        try:
            if os.getenv('OPENAI_API_KEY'):
                self.openai = OpenAIConfig()
        except Exception:
            pass
        
        try:
            if os.getenv('GITHUB_TOKEN') and os.getenv('GITHUB_REPO'):
                self.github = GitHubConfig()
        except Exception:
            pass
        
        try:
            if os.getenv('GOOGLE_CREDENTIALS_FILE'):
                self.google_docs = GoogleDocsConfig()
        except Exception:
            pass
        
        try:
            self.notification = NotificationConfig()
        except Exception:
            pass
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"

class ConfigManager:
    """Manages application configuration"""
    
    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file
        self.settings = AppSettings()
        self._load_config_file()
    
    def _load_config_file(self):
        """Load configuration from file if specified"""
        if self.config_file and Path(self.config_file).exists():
            try:
                with open(self.config_file, 'r') as f:
                    config_data = yaml.safe_load(f)
                    # Update settings with file data
                    for key, value in config_data.items():
                        if hasattr(self.settings, key):
                            setattr(self.settings, key, value)
            except Exception as e:
                print(f"Warning: Could not load config file {self.config_file}: {e}")
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a setting value"""
        return getattr(self.settings, key, default)
    
    def update_setting(self, key: str, value: Any) -> bool:
        """Update a setting value"""
        try:
            setattr(self.settings, key, value)
            return True
        except Exception:
            return False
    
    def save_config(self, file_path: Optional[str] = None) -> bool:
        """Save current configuration to file"""
        try:
            save_path = file_path or self.config_file or "config.yml"
            
            # Convert settings to dict
            config_data = {}
            for field in self.settings.__fields__:
                value = getattr(self.settings, field)
                if not field.startswith('_'):
                    config_data[field] = value
            
            with open(save_path, 'w') as f:
                yaml.dump(config_data, f, default_flow_style=False, sort_keys=False)
            
            return True
        except Exception as e:
            print(f"Error saving config: {e}")
            return False
    
    def validate_config(self) -> Dict[str, Any]:
        """Validate current configuration"""
        validation = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "missing_required": []
        }
        
        # Check required fields only if they're needed
        if self.settings.openai and not self.settings.openai.api_key:
            validation["is_valid"] = False
            validation["missing_required"].append("OpenAI API Key")
        
        if self.settings.github and not self.settings.github.token:
            validation["is_valid"] = False
            validation["missing_required"].append("GitHub Token")
        
        if self.settings.github and not self.settings.github.repo_name:
            validation["is_valid"] = False
            validation["missing_required"].append("GitHub Repository Name")
        
        # Check file paths
        for path_field in ["base_dir", "config_dir", "templates_dir", "output_dir"]:
            path = getattr(self.settings, path_field)
            if not path.exists():
                validation["warnings"].append(f"Directory {path} does not exist")
        
        # Check repository configurations
        if not self.settings.repositories:
            validation["warnings"].append("No repositories configured")
        
        return validation
    
    def _get_nested_value(self, key_path: str) -> Any:
        """Get nested value from settings using dot notation"""
        keys = key_path.split('.')
        value = self.settings
        
        for key in keys:
            if hasattr(value, key):
                value = getattr(value, key)
            else:
                return None
        
        return value
    
    def get_repository_config(self, repo_name: str) -> Optional[RepositoryConfig]:
        """Get configuration for a specific repository"""
        for repo in self.settings.repositories:
            if repo.name == repo_name:
                return repo
        return None
    
    def add_repository(self, repo_config: RepositoryConfig) -> bool:
        """Add a new repository configuration"""
        try:
            self.settings.repositories.append(repo_config)
            return True
        except Exception:
            return False
    
    def remove_repository(self, repo_name: str) -> bool:
        """Remove a repository configuration"""
        try:
            self.settings.repositories = [
                repo for repo in self.settings.repositories 
                if repo.name != repo_name
            ]
            return True
        except Exception:
            return False

# Global configuration instance
config_manager = ConfigManager()

def get_settings() -> AppSettings:
    """Get application settings"""
    return config_manager.settings

def get_config_manager() -> ConfigManager:
    """Get configuration manager"""
    return config_manager
