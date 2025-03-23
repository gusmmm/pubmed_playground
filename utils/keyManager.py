"""API Key Management for Scientific Data Retrieval System.

This module provides a KeyManager class that handles loading and retrieving
API keys from a .env file. It implements the singleton pattern to ensure
only one instance manages the keys across the system.

Example:
    Basic usage of the KeyManager class:

    >>> from utils import KeyManager
    >>> key_manager = KeyManager()
    >>> pubmed_key = key_manager.get_key("PUBMED_API_KEY")
    >>> if pubmed_key:
    ...     print("PubMed API key loaded successfully")

    The .env file should be in the project root directory:

    ```
    OPENROUTER_API_KEY=your_key_here
    GEMINI_API_KEY=your_key_here
    GROQ_API_KEY=your_key_here
    MISTRAL_API_KEY=your_key_here
    CODESTRAL_API_KEY=your_key_here
    PUBMED_API_KEY=your_key_here
    ```
"""

from typing import Dict, Optional
import os
from pathlib import Path
from dotenv import load_dotenv

class KeyManager:
    """Manages API keys for various scientific data sources.
    
    This class implements the singleton pattern to ensure only one instance
    manages API keys across the system. It loads keys from a .env file in
    the project root directory and provides methods to access them.
    
    Attributes:
        _instance (KeyManager): Singleton instance of KeyManager
        _keys (Dict[str, str]): Dictionary storing loaded API keys
        
    Examples:
        Initialize and use KeyManager:
        >>> from utils import KeyManager
        >>> key_manager = KeyManager()
        >>> pubmed_key = key_manager.get_key("PUBMED_API_KEY")
        
        Check key availability:
        >>> if key_manager.has_key("PUBMED_API_KEY"):
        ...     print("Ready to use PubMed API")
        
        List available keys:
        >>> print(key_manager.available_keys)
        ['OPENROUTER_API_KEY', 'GEMINI_API_KEY', ...]
    """
    
    _instance = None
    _keys: Dict[str, str] = {}
    
    def __new__(cls) -> 'KeyManager':
        """Implements singleton pattern to ensure one key manager instance."""
        if cls._instance is None:
            cls._instance = super(KeyManager, cls).__new__(cls)
            cls._instance._load_env()
        return cls._instance
    
    def _load_env(self) -> None:
        """Loads environment variables from .env file in project root.
        
        The .env file must be in the project root directory with the following format:
        ```
        OPENROUTER_API_KEY=your_key_here
        GEMINI_API_KEY=your_key_here
        GROQ_API_KEY=your_key_here
        MISTRAL_API_KEY=your_key_here
        CODESTRAL_API_KEY=your_key_here
        PUBMED_API_KEY=your_key_here
        ```
        
        Raises:
            FileNotFoundError: If no .env file is found in project root.
        """
        env_path = self._find_env_file()
        if env_path and load_dotenv(env_path):
            self._keys = {
                "OPENROUTER_API_KEY": os.getenv("OPENROUTER_API_KEY"),
                "GEMINI_API_KEY": os.getenv("GEMINI_API_KEY"),
                "GROQ_API_KEY": os.getenv("GROQ_API_KEY"),
                "MISTRAL_API_KEY": os.getenv("MISTRAL_API_KEY"),
                "CODESTRAL_API_KEY": os.getenv("CODESTRAL_API_KEY"),
                "PUBMED_API_KEY": os.getenv("PUBMED_API_KEY"),
                "SERPAPI_KEY": os.getenv("SERPAPI_KEY"),
                "UNPAYWALL_EMAIL=": os.getenv("UNPAYWALL_EMAIL"),
            }
            print("✅ API keys loaded successfully")
        else:
            raise FileNotFoundError(
                "\n❌ Error: No .env file found in project root directory."
                "\n\nSolution:"
                "\n1. Create a .env file in the project root directory"
                "\n2. Add your API keys in the following format:"
                "\n   OPENROUTER_API_KEY=your_key_here"
                "\n   GEMINI_API_KEY=your_key_here"
                "\n   GROQ_API_KEY=your_key_here"
                "\n   MISTRAL_API_KEY=your_key_here"
                "\n   CODESTRAL_API_KEY=your_key_here"
                "\n   PUBMED_API_KEY=your_key_here"
                "\n   SERPAPI_KEY=your_key_here"
                "\n   UNPAYWALL_EMAIL=your_email_here"
            )
            
    def _find_env_file(self) -> Optional[Path]:
        """Looks for .env file in project root directory.
        
        Returns:
            Path: Path to .env file if found in project root
            None: If no .env file exists in project root
        """
        project_root = Path.cwd().resolve()
        env_path = project_root / '.env'
        return env_path if env_path.exists() else None
    
    def get_key(self, key_name: str) -> Optional[str]:
        """Retrieves specified API key.
        
        Args:
            key_name: Name of the API key to retrieve (e.g., "PUBMED_API_KEY")
            
        Returns:
            str: The API key value if found
            None: If the key doesn't exist or is empty
            
        Example:
            >>> key_manager = KeyManager()
            >>> pubmed_key = key_manager.get_key("PUBMED_API_KEY")
            >>> if pubmed_key:
            ...     print(f"Found key: {pubmed_key[:5]}...")
        """
        key = self._keys.get(key_name)
        if key is None:
            print(f"⚠️  Warning: {key_name} not found in environment variables")
        return key
    
    def has_key(self, key_name: str) -> bool:
        """Checks if specified API key exists and is not empty.
        
        Args:
            key_name: Name of the API key to check
            
        Returns:
            bool: True if key exists and is not empty, False otherwise
            
        Example:
            >>> key_manager = KeyManager()
            >>> if key_manager.has_key("PUBMED_API_KEY"):
            ...     print("PubMed API key is ready")
        """
        return bool(self._keys.get(key_name))
    
    @property
    def available_keys(self) -> list[str]:
        """Lists all available API key names.
        
        Returns:
            list[str]: List of available API key names
            
        Example:
            >>> key_manager = KeyManager()
            >>> print("Available keys:", key_manager.available_keys)
            Available keys: ['OPENROUTER_API_KEY', 'GEMINI_API_KEY', ...]
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
