"""
Base Agent class for PubMed Playground

This module provides a foundation for creating specialized research agents.
All specific agents should inherit from this base class.
"""

import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, Optional
from rich.console import Console

# Configure logging
logger = logging.getLogger("agents.base")

class BaseAgent(ABC):
    """
    Abstract base class for all research agents in the platform.
    
    This class defines the interface and common functionality that all
    agents should implement, including initialization, configuration,
    and output management.
    
    Attributes:
        name (str): The name of the agent
        console (Console): Rich console for formatted output
        results_dir (Path): Directory to save results
        config (Dict[str, Any]): Configuration parameters
    """
    
    def __init__(
        self, 
        name: str,
        results_dir: Optional[Path] = None,
        console: Optional[Console] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the base agent.
        
        Args:
            name: The name of the agent
            results_dir: Directory to save results (default: project_root/search_results)
            console: Rich console for output (creates new one if None)
            config: Additional configuration parameters
        """
        self.name = name
        self.console = console or Console()
        self.config = config or {}
        
        # Set up results directory
        project_root = Path(__file__).resolve().parent.parent.parent
        self.results_dir = results_dir or (project_root / "search_results")
        self.results_dir.mkdir(exist_ok=True, parents=True)
            
    @abstractmethod
    def run(self, **kwargs) -> Any:
        """
        Run the agent's main workflow.
        Must be implemented by subclasses.
        
        Returns:
            Results of the agent's operation
        """
        raise NotImplementedError("Subclasses must implement run()")
        
    @abstractmethod
    def welcome(self) -> None:
        """
        Display a welcome message explaining the agent's purpose.
        Must be implemented by subclasses.
        """
        raise NotImplementedError("Subclasses must implement welcome()")
    
    def log_error(self, message: str, exception: Exception = None) -> None:
        """
        Log an error and display it in the console.
        
        Args:
            message: Error message
            exception: Exception that was raised (optional)
        """
        if exception:
            logger.error(f"{message}: {exception}", exc_info=True)
            self.console.print(f"\n[bold red]{message}: {exception}[/bold red]")
        else:
            logger.error(message)
            self.console.print(f"\n[bold red]{message}[/bold red]")