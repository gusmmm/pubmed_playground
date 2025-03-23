"""API Key Management for Scientific Data Retrieval System.

This module provides a KeyManager class that handles loading and retrieving
API keys from a .env file. It implements the singleton pattern to ensure
only one instance manages the keys across the system.
"""

from typing import Dict, Optional
import os
from pathlib import Path
from dotenv import load_dotenv

class KeyManager:
    """Manages API keys for various scientific data sources.
    
    This class implements the singleton pattern to ensure only one instance
    manages API keys across the system. It loads keys from a .env file and
    provides methods to access them.
    
    Attributes:
        _instance: Singleton instance of KeyManager
        _keys: Dictionary storing loaded API keys
        
    Example:
        >>> key_manager = KeyManager()
        >>> pubmed_key = key_manager.get_key("PUBMED_API_KEY")
        >>> if pubmed_key:
        ...     print("PubMed API key loaded successfully")
    """
    
    _instance = None
    _keys: Dict[str, str] = {}
    
    def __new__(cls) -> 'KeyManager':
        """Implements singleton pattern."""
        if cls._instance is None:
            cls._instance = super(KeyManager, cls).__new__(cls)
            cls._instance._load_env()
        return cls._instance
    
    def _load_env(self) -> None:
        """Loads environment variables from .env file.
        
        Looks for .env file in project root directory.
        Raises FileNotFoundError if no .env file is found.
        """
        env_path = self._find_env_file()
        if env_path and load_dotenv(env_path):
            self._keys = {
                "PUBMED_API_KEY": os.getenv("PUBMED_API_KEY"),
                "CROSSREF_EMAIL": os.getenv("CROSSREF_EMAIL"),
                "OPENROUTER_API_KEY": os.getenv("OPENROUTER_API_KEY"),
                "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
                "GEMINI_API_KEY": os.getenv("GEMINI_API_KEY"),
                "GROQ_API_KEY": os.getenv("GROQ_API_KEY"),
                "MISTRAL_API_KEY": os.getenv("MISTRAL_API_KEY"),
                "CODESTRAL_API_KEY": os.getenv("CODESTRAL_API_KEY"),
                # Add other API keys as needed
            }
            print("✅ API keys loaded successfully")
        else:
            raise FileNotFoundError(
                "\n❌ Error: No .env file found in project root directory."
                "\n\nSolution:"
                "\n1. Create a .env file in the project root directory"
                "\n2. Add your API keys in the following format:"
                "\n   PUBMED_API_KEY=your_key_here"
                "\n   CROSSREF_EMAIL=your_email_here"
            )
            
    def _find_env_file(self) -> Optional[Path]:
        """Looks for .env file in project root directory.
        
        Returns:
            Path to .env file if found in project root, None otherwise.
        """
        project_root = Path.cwd().resolve()
        env_path = project_root / '.env'
        return env_path if env_path.exists() else None
    
    def get_key(self, key_name: str) -> Optional[str]:
        """Retrieves specified API key.
        
        Args:
            key_name: Name of the API key to retrieve.
            
        Returns:
            The API key if found, None otherwise.
            
        Example:
            >>> manager = KeyManager()
            >>> pubmed_key = manager.get_key("PUBMED_API_KEY")
        """
        key = self._keys.get(key_name)
        if key is None:
            print(f"⚠️  Warning: {key_name} not found in environment variables")
        return key
    
    def has_key(self, key_name: str) -> bool:
        """Checks if specified API key exists and is not empty.
        
        Args:
            key_name: Name of the API key to check.
            
        Returns:
            True if key exists and is not empty, False otherwise.
        """
        return bool(self._keys.get(key_name))
    
    @property
    def available_keys(self) -> list[str]:
        """Lists all available API key names.
        
        Returns:
            List of available API key names.
            
        Example:
            >>> manager = KeyManager()
            >>> print(manager.available_keys)
            ['PUBMED_API_KEY', 'CROSSREF_EMAIL']
        """
        return list(self._keys.keys())

# Example usage
if __name__ == "__main__":
    try:
        key_manager = KeyManager()
        print("\nAvailable API Keys:")
        print("------------------")
        for key_name in key_manager.available_keys:
            status = "✅ Set" if key_manager.has_key(key_name) else "❌ Not Set"
            print(f"{key_name}: {status}")
    except FileNotFoundError as e:
        print(f"Error: {e}")
