"""
Configuration management for PyDCov.

This module handles storing and retrieving configuration settings,
particularly the build root path for incremental coverage operations.
"""

import json
from pathlib import Path
from typing import Optional, Dict, Any

from pydcov.utils.logging_config import get_logger


class PyDCovConfig:
    """Manages PyDCov configuration persistence."""
    
    CONFIG_FILE_NAME = '.pydcov.json'
    
    def __init__(self, project_root: Optional[Path] = None):
        """
        Initialize configuration manager.
        
        Args:
            project_root: Project root directory. If None, uses current directory.
        """
        self.logger = get_logger()
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.config_file = self.project_root / self.CONFIG_FILE_NAME
        
    def save_config(self, config: Dict[str, Any]) -> bool:
        """
        Save configuration to file.
        
        Args:
            config: Configuration dictionary to save
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Ensure project root exists
            self.project_root.mkdir(parents=True, exist_ok=True)
            
            # Convert Path objects to strings for JSON serialization
            serializable_config = {}
            for key, value in config.items():
                if isinstance(value, Path):
                    serializable_config[key] = str(value.resolve())
                else:
                    serializable_config[key] = value
            
            with open(self.config_file, 'w') as f:
                json.dump(serializable_config, f, indent=2)
            
            self.logger.debug(f"Configuration saved to {self.config_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save configuration: {e}")
            return False
    
    def load_config(self) -> Dict[str, Any]:
        """
        Load configuration from file.
        
        Returns:
            Configuration dictionary, empty if file doesn't exist or can't be read
        """
        if not self.config_file.exists():
            self.logger.debug(f"Configuration file not found: {self.config_file}")
            return {}
        
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
            
            self.logger.debug(f"Configuration loaded from {self.config_file}")
            return config
            
        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
            return {}
    
    def get_build_root(self) -> Optional[Path]:
        """
        Get the stored build root path.

        Returns:
            Build root path if configured, None otherwise
        """
        config = self.load_config()
        build_root_str = config.get('build_root')

        if build_root_str:
            build_root = Path(build_root_str)
            if build_root.exists():
                return build_root
            else:
                self.logger.warning(f"Configured build root does not exist: {build_root}")
                return None

        return None

    def get_pydcov_dir(self) -> Optional[Path]:
        """
        Get the stored pydcov directory path.

        Returns:
            PyDCov directory path if configured, None otherwise
        """
        config = self.load_config()
        pydcov_dir_str = config.get('pydcov_dir')

        if pydcov_dir_str:
            pydcov_dir = Path(pydcov_dir_str)
            if pydcov_dir.exists():
                return pydcov_dir
            else:
                self.logger.warning(f"Configured pydcov directory does not exist: {pydcov_dir}")
                return None

        return None
    
    def set_build_root(self, build_root: Path) -> bool:
        """
        Set and save the build root path.

        Args:
            build_root: Build root path to store

        Returns:
            True if successful, False otherwise
        """
        config = self.load_config()
        config['build_root'] = build_root
        return self.save_config(config)

    def set_pydcov_dir(self, pydcov_dir: Path) -> bool:
        """
        Set and save the pydcov directory path.

        Args:
            pydcov_dir: PyDCov directory path to store

        Returns:
            True if successful, False otherwise
        """
        config = self.load_config()
        config['pydcov_dir'] = pydcov_dir
        return self.save_config(config)
    
    def config_exists(self) -> bool:
        """
        Check if configuration file exists.
        
        Returns:
            True if configuration file exists, False otherwise
        """
        return self.config_file.exists()
    
    def remove_config(self) -> bool:
        """
        Remove configuration file.
        
        Returns:
            True if successful or file doesn't exist, False on error
        """
        if not self.config_file.exists():
            return True
        
        try:
            self.config_file.unlink()
            self.logger.debug(f"Configuration file removed: {self.config_file}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to remove configuration file: {e}")
            return False
