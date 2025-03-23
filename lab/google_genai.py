"""
Google Generative AI module for interacting with Gemini models.

This module provides utility functions for initializing the Google GenAI client,
counting tokens, and generating responses from Gemini models.
"""

from typing import Any, Dict, Tuple, Union, Optional, List
import time
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table
from rich.box import ROUNDED
from rich import print as rprint
from google import genai
from google.genai import types
from google.genai.types import HarmCategory, HarmBlockThreshold

from utils.keyManager import KeyManager

# Initialize Rich console for this module
console = Console()

class GeminiClient:
    """
    A wrapper class for the Google Generative AI client with common functionality.
    
    This class provides methods for initializing the client, counting tokens,
    and generating responses from Gemini models.
    """
    
    def __init__(self, 
                 console: Optional[Console] = None,
                 default_model: str = "gemini-1.5-pro"):
        """
        Initialize the GeminiClient with optional console and default model.
        
        Args:
            console: Rich console for output formatting (creates a new one if None)
            default_model: Default model identifier to use for requests
        """
        self.console = console or Console()
        self.default_model = default_model
        self.client = self._initialize_client()
        
    def _initialize_client(self):
        """
        Initialize and return a Google GenAI client with API key from environment.
        
        Returns:
            Initialized Google GenAI client
        """
        # Use the KeyManager to get the Gemini API key
        key_manager = KeyManager()
        
        # Check if the GEMINI_API_KEY exists
        if not key_manager.has_key("GEMINI_API_KEY"):
            self.console.print("[bold red]Error: GEMINI_API_KEY not found in environment variables[/bold red]")
            self.console.print("Please set the GEMINI_API_KEY in your .env file.")
            raise ValueError("GEMINI_API_KEY not found")
            
        gemini_api_key = key_manager.get_key("GEMINI_API_KEY")

        # Set up the API key for Google GenAI
        with self.console.status("[bold blue]Setting up Google GenAI client...", spinner="bouncingBar"):
            client = genai.Client(api_key=gemini_api_key)
            self.console.print("[bold green]Client initialized successfully![/bold green]")
            
        return client
        
    def count_tokens(self, contents: Union[str, Dict, types.Content], 
                    model: Optional[str] = None) -> int:
        """
        Count tokens in the given contents using the specified model.
        
        Args:
            contents: Text, dictionary, or Content object to count tokens for
            model: Model identifier (defaults to the client's default model)
            
        Returns:
            Total token count
        """
        model = model or self.default_model
        
        with self.console.status("[bold cyan]Counting tokens...", spinner="dots"):
            response = self.client.models.count_tokens(model=model, contents=contents)
            
        return response.total_tokens
        
    def generate_response(self, 
                         query: Union[str, Dict, types.Content], 
                         model: Optional[str] = None,
                         temperature: float = 1.0,
                         top_p: float = 0.95,
                         top_k: int = 64,
                         max_output_tokens: Optional[int] = None,
                         safety_settings: Optional[List[Dict[str, Any]]] = None) -> Tuple[Any, int, float]:
        """
        Generate a response from the model for the given query with detailed metrics.
        
        Args:
            query: The query text or structured content
            model: Model identifier (defaults to the client's default model)
            temperature: Controls randomness (0=deterministic, 1=creative)
            top_p: Nucleus sampling parameter
            top_k: Diversity parameter
            max_output_tokens: Maximum output length in tokens
            safety_settings: Custom safety settings as a list of dictionaries
            
        Returns:
            Tuple of (response, token_count, elapsed_time)
        """
        model = model or self.default_model
        
        # Count tokens first
        token_count = self.count_tokens(query, model)
        
        # Set default safety settings if none provided
        if safety_settings is None:
            safety_settings = [
                {
                    "category": HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                    "threshold": HarmBlockThreshold.BLOCK_NONE
                },
                {
                    "category": HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                    "threshold": HarmBlockThreshold.BLOCK_ONLY_HIGH
                },
                {
                    "category": HarmCategory.HARM_CATEGORY_HARASSMENT,
                    "threshold": HarmBlockThreshold.BLOCK_ONLY_HIGH
                },
                {
                    "category": HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                    "threshold": HarmBlockThreshold.BLOCK_ONLY_HIGH
                }
            ]
        
        # Generate the response and time it
        with self.console.status(f"[bold green]Generating response with {model}...", spinner="dots"):
            start_time = time.time()
            response = self.client.models.generate_content(
                model=model, 
                contents=query,
                config=types.GenerateContentConfig(
                    temperature=temperature,
                    top_p=top_p,
                    top_k=top_k,
                    max_output_tokens=max_output_tokens,
                    safety_settings=safety_settings
                ),
            )
            elapsed_time = time.time() - start_time
            
            self.console.print(f"[dim]Response generated in {elapsed_time:.2f} seconds[/dim]")
        
        return response, token_count, elapsed_time
    
    def generate_content_stream(self,
                          query: Union[str, Dict, types.Content],
                          model: Optional[str] = None,
                          temperature: float = 1.0,
                          top_p: float = 0.95,
                          top_k: int = 64,
                          max_output_tokens: Optional[int] = None,
                          safety_settings: Optional[List[Dict[str, Any]]] = None) -> Any:
        """
        Generate a streaming response from the model for the given query.
        
        Args:
            query: The query text or structured content
            model: Model identifier (defaults to the client's default model)
            temperature: Controls randomness (0=deterministic, 1=creative)
            top_p: Nucleus sampling parameter
            top_k: Diversity parameter
            max_output_tokens: Maximum output length in tokens
            safety_settings: Custom safety settings as a list of dictionaries
            
        Returns:
            Generator yielding response chunks
        """
        model = model or self.default_model
        
        # Set default safety settings if none provided
        if safety_settings is None:
            safety_settings = [
                {
                    "category": HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                    "threshold": HarmBlockThreshold.BLOCK_NONE
                },
                {
                    "category": HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                    "threshold": HarmBlockThreshold.BLOCK_ONLY_HIGH
                },
                {
                    "category": HarmCategory.HARM_CATEGORY_HARASSMENT,
                    "threshold": HarmBlockThreshold.BLOCK_ONLY_HIGH
                },
                {
                    "category": HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                    "threshold": HarmBlockThreshold.BLOCK_ONLY_HIGH
                }
            ]
        
        # Generate the streaming response
        response_stream = self.client.models.generate_content_stream(
            model=model,
            contents=query,
            config=types.GenerateContentConfig(
                temperature=temperature,
                top_p=top_p,
                top_k=top_k,
                max_output_tokens=max_output_tokens,
                safety_settings=safety_settings
            ),
        )
        
        return response_stream
    
    def list_available_models(self):
        """
        List all available models from the Google GenAI API.
        
        Returns:
            List of available model information
        """
        with self.console.status("[bold blue]Fetching available models...", spinner="dots"):
            models = self.client.models.list()
            
        return models
        
    def display_formatted_response(self, response, token_count, elapsed_time, query, model=None):
        """
        Display a beautifully formatted response using Rich.
        
        Args:
            response: Response object from Gemini
            token_count: Number of tokens in the query
            elapsed_time: Time taken to generate the response
            query: Original query text
            model: Optional model name (if not available in response)
        """
        # Create a metadata table
        metadata_table = Table(box=ROUNDED, show_header=False, width=90, padding=(0, 2))
        metadata_table.add_column("Metric", style="bold cyan")
        metadata_table.add_column("Value", style="green")
        
        # Get model name
        model_name = model or "Unknown"
        
        # Try to extract model name from response object if not provided
        if not model and response:
            try:
                if hasattr(response, 'model'):
                    model_name = response.model
                elif hasattr(response, 'model_name'):
                    model_name = response.model_name
                elif hasattr(response, 'candidates') and response.candidates:
                    if hasattr(response.candidates[0], 'model'):
                        model_name = response.candidates[0].model
                    elif hasattr(response.candidates[0], 'model_name'):
                        model_name = response.candidates[0].model_name
            except Exception:
                pass
                
        metadata_table.add_row("Model", model_name)
        metadata_table.add_row("Tokens", str(token_count))
        metadata_table.add_row("Response Time", f"{elapsed_time:.2f} seconds")
        
        # Format the query panel
        query_panel = Panel(f"[bold white]{query}", title="[bold blue]Query", border_style="blue")
        
        # Format the response as markdown
        md = Markdown(response.text)
        response_panel = Panel(md, title="[bold green]Response", border_style="green")
        
        # Print everything with spacing
        self.console.print("\n")
        self.console.print(query_panel)
        self.console.print(response_panel)
        self.console.print(metadata_table)
        self.console.print("\n")


# For backwards compatibility with original functional interface
def initialize_client():
    """Initialize and return a Google GenAI client with API key from environment"""
    gemini_client = GeminiClient()
    return gemini_client.client

def count_tokens(client, model, contents):
    """Count tokens in the given contents using the specified model"""
    gemini_client = GeminiClient()
    gemini_client.client = client  # Use the provided client
    return gemini_client.count_tokens(contents, model)

def generate_response(client, model, query, temperature=1.0):
    """Generate a response from the model for the given query"""
    gemini_client = GeminiClient()
    gemini_client.client = client  # Use the provided client
    return gemini_client.generate_response(query, model, temperature)


# Example usage
if __name__ == "__main__":
    try:
        # Example using the class-based approach
        gemini = GeminiClient()
        
        # List available models
        models = gemini.list_available_models()
        
        # Create a table to display models
        model_table = Table(title="Available Gemini Models", box=ROUNDED)
        model_table.add_column("Model Name", style="cyan")
        model_table.add_column("Version", style="green")
        model_table.add_column("Display Name", style="yellow")
        
        # Add model data to the table
        for model in models:
            name_parts = model.name.split('/')
            model_name = name_parts[-1] if len(name_parts) > 1 else model.name
            version = model.version if hasattr(model, 'version') else "-"
            display_name = model.display_name if hasattr(model, 'display_name') else model_name
            model_table.add_row(model_name, version, display_name)
        
        # Display the model table
        console.print(model_table)
        
        # Example query
        query = "What are the latest advancements in PubMed search techniques?"
        
        # Define model to use
        model_to_use = 'gemini-2.0-flash'
        
        # Generate response
        response, token_count, elapsed_time = gemini.generate_response(
            model=model_to_use,
            query=query,
            temperature=0.7,
        )
        
        # Display beautifully formatted response with explicit model name
        gemini.display_formatted_response(
            response, 
            token_count, 
            elapsed_time, 
            query,
            model=model_to_use  # Pass the model explicitly
        )
    
    except Exception as e:
        console.print(f"[bold red]Error running Gemini client: {e}[/bold red]")
        import traceback
        console.print(Panel(traceback.format_exc(), title="[bold red]Error Details", border_style="red"))