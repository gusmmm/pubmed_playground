"""
PubMed Query Helper

This script uses Google's Gemini AI models to help users create effective
PubMed search queries based on their research interests.

Features:
- Takes user input about their research question
- Uses AI to suggest optimized PubMed search queries at two specificity levels
- Follows proper PubMed query syntax based on reference documentation
- Can optionally search the web for recent relevant information
- Formats suggestions with rich output
"""

import sys
import json
import logging
import requests
from typing import List, Dict, Optional, Tuple
from pathlib import Path
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich.markdown import Markdown
from rich.table import Table
from rich.box import ROUNDED
from rich.progress import Progress
from rich import print as rprint

# Add project root to sys.path if needed
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from utils.google_genai import GeminiClient
from utils.keyManager import KeyManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("pubmed_query_helper")

# Initialize Rich console
console = Console()


class PubMedQueryHelper:
    """
    A helper class that uses Google's Gemini models to assist in
    creating effective PubMed search queries at various specificity levels.
    """
    
    def __init__(self, model: str = "gemini-2.0-flash"):
        """
        Initialize the PubMed Query Helper.
        
        Args:
            model: The Gemini model to use
        """
        self.console = Console()
        self.model = model
        self.client = GeminiClient(console=self.console, default_model=model)
        self.query_instructions = self._load_query_instructions()
        self.key_manager = KeyManager()
        
    def _load_query_instructions(self) -> str:
        """
        Load PubMed query instructions from the reference file.
        
        Returns:
            The content of the instructions file
        """
        instructions_path = project_root / "references" / "pubmed_query_instructions.md"
        try:
            if instructions_path.exists():
                with open(instructions_path, 'r') as f:
                    return f.read()
            else:
                logger.warning(f"Query instructions file not found at {instructions_path}")
                return ""
        except Exception as e:
            logger.error(f"Error loading query instructions: {e}")
            return ""
        
    def welcome(self):
        """Display a welcome message explaining the tool."""
        welcome_text = """
        # 🔍 PubMed Query Helper

        This tool helps you create effective PubMed search queries at different specificity levels:
        
        - **Simple**: Basic search terms with minimal constraints
        - **Medium**: More specific terms with appropriate filters
        
        You can also optionally search the web for recent information on your topic!
        
        Let's find the right search strategy for your research!
        """
        self.console.print(Markdown(welcome_text))
        
    def get_user_query(self) -> str:
        """
        Get the initial query from the user.
        
        Returns:
            User's research question or topic
        """
        return Prompt.ask(
            "\n[bold cyan]What medical or scientific topic are you researching?[/bold cyan]\n"
            "Please describe your research question or area of interest"
        )
    
    def search_web_for_information(self, topic: str) -> str:
        """
        Search the web for recent information about the research topic using SerpAPI.
        
        Args:
            topic: The research topic to search for
            
        Returns:
            String containing summarized web search results
        """
        # Check if we have a SerpApi key
        if not self.key_manager.has_key("SERPAPI_KEY"):
            self.console.print("[yellow]No SerpAPI key found. Web search functionality is disabled.[/yellow]")
            return ""
        
        serpapi_key = self.key_manager.get_key("SERPAPI_KEY")
        
        try:
            with Progress() as progress:
                search_task = progress.add_task("[cyan]Searching the web for recent information...", total=100)
                
                # First search for recent medical news using Google News
                news_search_params = {
                    "q": f"{topic} medical research",
                    "api_key": serpapi_key,
                    "engine": "google",             # Explicitly set the engine to Google
                    "tbm": "nws",                   # News search
                    "num": 5,                       # Get 5 results
                    "gl": "us",                     # Set country to US
                    "hl": "en",                     # Set language to English
                    "safe": "active"                # Safe search
                }
                
                progress.update(search_task, completed=30)
                
                # Make the news search request
                response = requests.get(
                    "https://serpapi.com/search", 
                    params=news_search_params
                )
                response.raise_for_status()
                news_results = response.json()
                
                progress.update(search_task, completed=60)
                
                # Then search for scholarly articles using Google Scholar
                # According to the reference, the correct engine is google_scholar
                scholar_search_params = {
                    "q": f"{topic}",                # Simple query works better for scholar
                    "api_key": serpapi_key,
                    "engine": "google_scholar",     # Use Google Scholar engine
                    "hl": "en",                     # Set language to English
                    "as_ylo": "2020",              # Articles from 2020 or later
                    "num": 5                       # Get 5 results
                }
                
                # Make the scholar search request
                response = requests.get(
                    "https://serpapi.com/search", 
                    params=scholar_search_params
                )
                response.raise_for_status()
                scholar_results = response.json()
                
                progress.update(search_task, completed=100)
            
            # Extract and format the results
            web_info = []
            
            # Add news results
            if "news_results" in news_results:
                web_info.append("## Recent News")
                for idx, result in enumerate(news_results["news_results"][:3], 1):
                    title = result.get("title", "No title")
                    source = result.get("source", "Unknown source")
                    date = result.get("date", "No date")
                    snippet = result.get("snippet", "No description available")
                    
                    web_info.append(f"{idx}. **{title}** - {source}, {date}")
                    web_info.append(f"   {snippet}")
                    web_info.append("")
            
            # Add scholar results based on the specific format from the documentation
            if "organic_results" in scholar_results:
                web_info.append("## Recent Research Papers")
                for idx, result in enumerate(scholar_results["organic_results"][:3], 1):
                    title = result.get("title", "No title")
                    
                    # Extract publication info using the correct path based on the API response structure
                    authors = ""
                    if "publication_info" in result:
                        if "summary" in result["publication_info"]:
                            authors = f" - {result['publication_info']['summary']}"
                        elif "authors" in result["publication_info"]:
                            authors = f" - {result['publication_info']['authors']}"
                    
                    snippet = result.get("snippet", "No abstract available")
                    
                    web_info.append(f"{idx}. **{title}**{authors}")
                    web_info.append(f"   {snippet}")
                    web_info.append("")
            elif "search_results" in scholar_results:
                # Alternative format sometimes returned by Google Scholar API
                web_info.append("## Recent Research Papers")
                for idx, result in enumerate(scholar_results["search_results"][:3], 1):
                    title = result.get("title", "No title")
                    authors = f" - {result.get('authors', '')}" if "authors" in result else ""
                    snippet = result.get("snippet", "No abstract available")
                    
                    web_info.append(f"{idx}. **{title}**{authors}")
                    web_info.append(f"   {snippet}")
                    web_info.append("")
            
            # If no results were found in either search
            if not web_info:
                return "No relevant web information found for this topic."
                
            return "\n".join(web_info)
            
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP Error searching the web: {e}", exc_info=True)
            
            # Extract more detailed error information if available
            error_message = str(e)
            try:
                response_json = e.response.json()
                if "error" in response_json:
                    error_message = f"{error_message} - {response_json['error']}"
            except:
                pass
                
            self.console.print(f"[yellow]Could not retrieve web information (HTTP Error): {error_message}[/yellow]")
            
            # Fallback to just a Google search without SerpAPI if error is with Scholar
            if "google_scholar" in str(e):
                self.console.print("[yellow]Trying fallback to regular Google search...[/yellow]")
                return self._fallback_web_search(topic, serpapi_key)
                
            return ""
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request Error searching the web: {e}", exc_info=True)
            self.console.print(f"[yellow]Could not retrieve web information (Request Error): {e}[/yellow]")
            return ""
            
        except Exception as e:
            logger.error(f"Error searching the web: {e}", exc_info=True)
            self.console.print(f"[yellow]Could not retrieve web information: {e}[/yellow]")
            return ""
        
    def _fallback_web_search(self, topic: str, serpapi_key: str) -> str:
        """
        Fallback method to search the web using regular Google search when other methods fail.
        
        Args:
            topic: The research topic to search for
            serpapi_key: SerpAPI key to use
            
        Returns:
            String containing summarized web search results
        """
        try:
            # Use regular Google search as fallback
            search_params = {
                "q": f"{topic} medical research",
                "api_key": serpapi_key,
                "engine": "google",
                "num": 7,
                "gl": "us",
                "hl": "en"
            }
            
            response = requests.get(
                "https://serpapi.com/search", 
                params=search_params
            )
            response.raise_for_status()
            search_results = response.json()
            
            web_info = []
            
            # Add organic results
            if "organic_results" in search_results:
                web_info.append("## Recent Web Information")
                for idx, result in enumerate(search_results["organic_results"][:5], 1):
                    title = result.get("title", "No title")
                    source = result.get("displayed_link", "Unknown source")
                    snippet = result.get("snippet", "No description available")
                    
                    web_info.append(f"{idx}. **{title}** - {source}")
                    web_info.append(f"   {snippet}")
                    web_info.append("")
            
            if web_info:
                return "\n".join(web_info)
            else:
                return "No relevant web information found using fallback search."
                
        except Exception as e:
            logger.error(f"Error in fallback web search: {e}", exc_info=True)
            return ""
        
    def generate_tiered_queries(self, user_input: str, web_info: str = "") -> Dict[str, Dict[str, str]]:
        """
        Generate two tiers of PubMed search queries based on user input.
        
        Args:
            user_input: The user's research question or topic
            web_info: Optional web search results to incorporate
            
        Returns:
            Dictionary with query tiers and their explanations
        """
        # Create a detailed prompt with instructions from the reference document
        instructions = ""
        if self.query_instructions:
            instructions = f"""
            Use these PubMed query construction guidelines to ensure proper syntax:
            
            {self.query_instructions}
            """
        
        # Add web info if available
        web_info_section = ""
        if web_info:
            web_info_section = f"""
            Here is some recent information from the web about this topic that you might 
            find useful when creating the queries:
            
            {web_info}
            """
        
        prompt = f"""
        You are a PubMed search expert helping a researcher craft effective search queries.
        
        The researcher wants to search for information about: "{user_input}"
        
        {web_info_section}
        
        {instructions}
        
        Please create TWO different PubMed search queries at increasing levels of specificity:
        
        1. SIMPLE QUERY: Basic search with minimal constraints, just the core concepts with proper syntax
        2. MEDIUM QUERY: More specific with appropriate field tags and one or two filters
        
        For each query level, provide:
        - The actual query with correct PubMed syntax
        - A brief explanation of the query's components and why it's appropriate for that specificity level
        
        Format your response EXACTLY like this example:
        
        ## Simple Query
        ```
        diabetes AND insulin
        ```
        
        **Explanation**: This simple query searches for articles that mention both diabetes and insulin anywhere in the article metadata. It uses the basic Boolean operator AND to ensure both terms are present.
        
        ## Medium Query
        ```
        (diabetes mellitus[MeSH Terms]) AND insulin resistance[Title/Abstract] AND ("last 5 years"[PDat])
        ```
        
        **Explanation**: This medium-complexity query uses MeSH terms for more precise results, focuses on insulin resistance in the title or abstract, and limits to recent publications from the last 5 years.
        
        Make sure to follow this format exactly and provide clear, concise explanations for each query.
        """
        
        self.console.print("\n[bold]Generating PubMed queries...[/bold]")
        
        try:
            # Generate response from Gemini
            response, metrics = self.client.query(
                query=prompt,
                model=self.model,
                temperature=0.2,  # Lower temperature for more precise formatting
                display_response=False  # We'll handle our own display
            )
            
            # Extract sections from the response
            response_text = response.text
            
            # Parse the response to extract queries and explanations
            return self._parse_tiered_response(response_text)
            
        except Exception as e:
            logger.error(f"Error generating queries: {e}", exc_info=True)
            self.console.print(f"\n[bold red]Error generating queries: {e}[/bold red]")
            return {
                "simple": {"query": "", "explanation": "Unable to generate query."},
                "medium": {"query": "", "explanation": "Unable to generate query."}
            }
    
    def _parse_tiered_response(self, text: str) -> Dict[str, Dict[str, str]]:
        """
        Parse the tiered query response from the AI.
        
        Args:
            text: The response text from the AI
            
        Returns:
            Dictionary with query tiers and their explanations
        """
        result = {
            "simple": {"query": "", "explanation": ""},
            "medium": {"query": "", "explanation": ""}
        }
        
        # Extract each section
        sections = {
            "Simple Query": "simple",
            "Medium Query": "medium"
        }
        
        current_section = None
        current_part = None
        code_block = False
        explanation_text = []
        query_text = []
        
        lines = text.split("\n")
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Check for section headers
            for header, key in sections.items():
                if line.startswith(f"## {header}"):
                    # Save previous section's explanation if we're moving to a new section
                    if current_section and current_part == "explanation" and explanation_text:
                        result[current_section]["explanation"] = "\n".join(explanation_text).strip()
                    
                    current_section = key
                    current_part = "query"  # Start with query
                    code_block = False
                    explanation_text = []
                    query_text = []
                    break
            
            # Skip if no section is active
            if current_section is None:
                i += 1
                continue
                
            # Check for code block markers
            if line.startswith("```"):
                code_block = not code_block
                if not code_block and query_text:
                    # End of code block - save query
                    result[current_section]["query"] = "\n".join(query_text).strip()
                    query_text = []
                i += 1
                continue
            
            # Check for explanation marker
            if line.startswith("**Explanation**:") or line == "**Explanation**" or line.startswith("Explanation:"):
                current_part = "explanation"
                explanation_text = []
                
                # If this is just the header, move to the next line to get content
                if line.startswith("**Explanation**:"):
                    explanation_text.append(line[16:].strip())  # Skip the "**Explanation**:" part
                elif line.startswith("Explanation:"):
                    explanation_text.append(line[12:].strip())  # Skip the "Explanation:" part
                i += 1
                continue
            
            # Collect text based on current part
            if current_part == "query" and code_block:
                query_text.append(line)
            elif current_part == "explanation":
                explanation_text.append(line)
            
            i += 1
        
        # Save the last section's explanation
        if current_section and current_part == "explanation" and explanation_text:
            result[current_section]["explanation"] = "\n".join(explanation_text).strip()
        
        return result
    
    def display_tiered_results(self, tiered_queries: Dict[str, Dict[str, str]]):
        """
        Display the generated tiered queries in a nicely formatted way.
        
        Args:
            tiered_queries: Dictionary with query tiers and their explanations
        """
        self.console.print("\n")
        
        # Define tier styles
        tier_styles = {
            "simple": {
                "title": "[bold green]Simple Query[/bold green]",
                "border": "green"
            },
            "medium": {
                "title": "[bold blue]Medium Query[/bold blue]",
                "border": "blue"
            }
        }
        
        # Display each tier
        for tier, style in tier_styles.items():
            if tier in tiered_queries and tiered_queries[tier]["query"]:
                query_panel = Panel(
                    f"[bold white]{tiered_queries[tier]['query']}[/bold white]",
                    title=style["title"],
                    border_style=style["border"]
                )
                self.console.print(query_panel)
                
                # Only show explanation panel if there's content
                if tiered_queries[tier]["explanation"]:
                    explanation_panel = Panel(
                        Markdown(tiered_queries[tier]["explanation"]),
                        title=f"[bold {style['border']}]Explanation[/bold {style['border']}]",
                        border_style=style["border"]
                    )
                    self.console.print(explanation_panel)
                
                self.console.print("\n")
    
    def run(self):
        """Run the PubMed query helper workflow."""
        try:
            # Display welcome message
            self.welcome()
            
            # Get user's research question
            user_input = self.get_user_query()
            
            # Ask if user wants to include web search results
            include_web_search = Confirm.ask(
                "\n[cyan]Would you like to search the web for recent information about this topic?[/cyan]",
                default=False
            )
            
            web_info = ""
            if include_web_search:
                web_info = self.search_web_for_information(user_input)
                if web_info:
                    self.console.print(Panel(
                        Markdown(web_info),
                        title="[bold green]Web Search Results[/bold green]",
                        border_style="green"
                    ))
                else:
                    self.console.print("[yellow]No web search results available. Proceeding without them.[/yellow]")
            
            # Generate tiered query suggestions
            tiered_queries = self.generate_tiered_queries(user_input, web_info)
            
            # Display results
            self.display_tiered_results(tiered_queries)
            
            # Ask if user wants to modify a query
            modify = Prompt.ask(
                "\n[bold cyan]Would you like to modify one of these queries?[/bold cyan]",
                choices=["simple", "medium", "no"],
                default="no"
            )
            
            if modify.lower() != "no":
                # Get the selected query for modification
                selected_query = tiered_queries[modify.lower()]["query"]
                
                modification = Prompt.ask(
                    f"\n[bold cyan]How would you like to modify the {modify} query?[/bold cyan]\n"
                    "(e.g., 'add time filter', 'focus on specific population', etc.)"
                )
                
                # Generate modified query with the additional context
                modify_prompt = f"""
                You are a PubMed search expert helping a researcher modify their search query.
                
                Original research topic: "{user_input}"
                Current query: {selected_query}
                
                The researcher wants to modify this query by: "{modification}"
                
                Please provide:
                1. A modified PubMed search query that addresses this feedback
                2. A brief explanation of the changes made
                
                Ensure your query follows proper PubMed syntax as specified in the reference guidelines.
                
                Format your response exactly like this:
                
                ## Modified Query
                ```
                [Modified query with correct PubMed syntax]
                ```
                
                **Explanation**: [Concise explanation of the changes made]
                """
                
                self.console.print(f"\n[bold]Generating modified {modify} query...[/bold]")
                
                try:
                    response, metrics = self.client.query(
                        query=modify_prompt,
                        model=self.model,
                        temperature=0.2,
                        display_response=False
                    )
                    
                    # Parse the response to extract the modified query
                    modified_result = {}
                    current_part = None
                    code_block = False
                    explanation_text = []
                    query_text = []
                    
                    for line in response.text.split("\n"):
                        # Check for section header
                        if line.strip().startswith("## Modified Query"):
                            current_part = "query"
                            continue
                            
                        # Check for code block markers
                        if line.strip().startswith("```"):
                            code_block = not code_block
                            if not code_block and query_text:
                                # End of code block - save query
                                modified_result["query"] = "\n".join(query_text).strip()
                                query_text = []
                            continue
                        
                        # Check for explanation marker
                        if line.strip().startswith("**Explanation**:") or line.strip() == "**Explanation**" or line.strip().startswith("Explanation:"):
                            current_part = "explanation"
                            explanation_text = []
                            if ":" in line:
                                explanation_content = line.split(":", 1)[1].strip()
                                if explanation_content:
                                    explanation_text.append(explanation_content)
                            continue
                        
                        # Collect text based on current part
                        if current_part == "query" and code_block:
                            query_text.append(line)
                        elif current_part == "explanation":
                            explanation_text.append(line)
                    
                    # Save the explanation
                    if explanation_text:
                        modified_result["explanation"] = "\n".join(explanation_text).strip()
                    
                    # Display modified query if found
                    if "query" in modified_result:
                        self.console.print("\n")
                        modified_panel = Panel(
                            f"[bold white]{modified_result['query']}[/bold white]",
                            title=f"[bold cyan]Modified {modify.title()} Query[/bold cyan]",
                            border_style="cyan"
                        )
                        self.console.print(modified_panel)
                        
                        # Display explanation if available
                        if "explanation" in modified_result:
                            explanation_panel = Panel(
                                Markdown(modified_result["explanation"]),
                                title="[bold cyan]Modification Explanation[/bold cyan]",
                                border_style="cyan"
                            )
                            self.console.print(explanation_panel)
                    else:
                        self.console.print("[bold yellow]Could not parse the modified query response.[/bold yellow]")
                    
                except Exception as e:
                    logger.error(f"Error modifying query: {e}", exc_info=True)
                    self.console.print(f"\n[bold red]Error modifying query: {e}[/bold red]")
            
            # Create a summary table
            summary_table = Table(title="Query Summary", box=ROUNDED)
            summary_table.add_column("Tier", style="bold")
            summary_table.add_column("Best For", style="cyan")
            summary_table.add_column("Expected Results", style="green")
            
            summary_table.add_row(
                "Simple", 
                "Quick overview, initial exploration", 
                "Many results, broad coverage"
            )
            summary_table.add_row(
                "Medium", 
                "Focused research, specific aspects", 
                "Moderate number of relevant results"
            )
            
            self.console.print("\n")
            self.console.print(summary_table)
            
            # Final message
            self.console.print("\n[bold green]✨ Happy researching! You can now use these queries on PubMed.[/bold green]")
            self.console.print("[italic]Copy the query you prefer and paste it into the PubMed search box.[/italic]")
            
        except Exception as e:
            logger.error(f"Error in query helper: {e}", exc_info=True)
            self.console.print(f"\n[bold red]Error: {e}[/bold red]")
            import traceback
            self.console.print(Panel(traceback.format_exc(), title="[bold red]Error Details", border_style="red"))
            
        except KeyboardInterrupt:
            self.console.print("\n\n[yellow]Query helper terminated by user.[/yellow]")


if __name__ == "__main__":
    try:
        # Run the PubMed query helper
        helper = PubMedQueryHelper()
        helper.run()
    except Exception as e:
        console.print(f"[bold red]Fatal error: {e}[/bold red]")
        logger.critical("Fatal error", exc_info=True)
    except KeyboardInterrupt:
        console.print("\n[yellow]Program terminated by user.[/yellow]")