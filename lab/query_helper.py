"""
PubMed Query Helper

This script uses Google's Gemini AI models to help users create effective
PubMed search queries based on their research interests.

Features:
- Takes user input about their research question
- Uses AI to suggest optimized PubMed search queries at two specificity levels
- Follows proper PubMed query syntax based on reference documentation
- Can search the web for recent relevant information with detailed source tracking
- Saves search results to JSON for future reference
- Formats suggestions with rich output
"""

import sys
import json
import logging
import requests
import datetime
from typing import List, Dict, Optional, Tuple, Any
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
        self.search_results_dir = project_root / "search_results"
        
        # Create search results directory if it doesn't exist
        self.search_results_dir.mkdir(exist_ok=True, parents=True)
        
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
        
        You can also search the web for recent information on your topic!
        All search results are saved for your reference.
        
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
    
    def search_web_for_information(self, topic: str) -> Tuple[str, Dict[str, Any]]:
        """
        Search the web for recent information about the research topic using SerpAPI.
        
        Args:
            topic: The research topic to search for
            
        Returns:
            Tuple of (formatted results string, raw results dictionary)
        """
        # Check if we have a SerpApi key
        if not self.key_manager.has_key("SERPAPI_KEY"):
            self.console.print("[yellow]No SerpAPI key found. Web search functionality is disabled.[/yellow]")
            return "", {}
        
        serpapi_key = self.key_manager.get_key("SERPAPI_KEY")
        search_results = {
            "query": topic,
            "timestamp": datetime.datetime.now().isoformat(),
            "news_results": [],
            "scholar_results": [],
            "fallback_results": []
        }
        
        try:
            with Progress() as progress:
                search_task = progress.add_task("[cyan]Searching the web for recent information...", total=100)
                
                # First search for recent medical news using Google News
                news_search_params = {
                    "q": f"{topic} medical research",
                    "api_key": serpapi_key,
                    "engine": "google",
                    "tbm": "nws",
                    "num": 5,
                    "gl": "us",
                    "hl": "en",
                    "safe": "active"
                }
                
                # Print API usage information
                self.console.print("[bold blue]► Using Google Search News API to find recent news[/bold blue]")
                
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
                scholar_search_params = {
                    "q": f"{topic}",
                    "api_key": serpapi_key,
                    "engine": "google_scholar",
                    "hl": "en",
                    "as_ylo": "2020",
                    "num": 5
                }
                
                # Print API usage information
                self.console.print("[bold blue]► Using Google Scholar API to find research papers[/bold blue]")
                
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
            
            # Process news results
            if "news_results" in news_results:
                web_info.append("## Recent News")
                self.console.print("\n[bold green]Found news articles:[/bold green]")
                
                for idx, result in enumerate(news_results["news_results"][:5], 1):
                    title = result.get("title", "No title")
                    source = result.get("source", "Unknown source")
                    date = result.get("date", "No date")
                    snippet = result.get("snippet", "No description available")
                    link = result.get("link", "")
                    
                    # Add to formatted results
                    web_info.append(f"{idx}. **{title}** - {source}, {date}")
                    web_info.append(f"   {snippet}")
                    web_info.append(f"   [Link]({link})")
                    web_info.append("")
                    
                    # Print more detailed results to terminal
                    self.console.print(f"  {idx}. [cyan]{title}[/cyan]")
                    self.console.print(f"     Source: {source} ({date})")
                    self.console.print(f"     URL: [link={link}]{link}[/link]")
                    
                    # Store in results dict
                    search_results["news_results"].append({
                        "title": title,
                        "source": source,
                        "date": date,
                        "snippet": snippet,
                        "url": link
                    })
                
                self.console.print("")
            
            # Process scholar results
            scholar_found = False
            
            if "organic_results" in scholar_results:
                web_info.append("## Recent Research Papers")
                self.console.print("[bold green]Found research papers:[/bold green]")
                scholar_found = True
                
                for idx, result in enumerate(scholar_results["organic_results"][:5], 1):
                    title = result.get("title", "No title")
                    link = result.get("link", "")
                    
                    # Extract identifiers
                    doi = None
                    pmid = None
                    
                    # Try to find DOI in the link or result
                    if "doi.org" in link:
                        doi = link.split("doi.org/")[-1]
                    
                    # Extract publication info
                    authors = ""
                    publication_info = {}
                    if "publication_info" in result:
                        if "summary" in result["publication_info"]:
                            authors = result["publication_info"]["summary"]
                        elif "authors" in result["publication_info"]:
                            authors = result["publication_info"]["authors"]
                            
                        # Get additional publication info
                        for key in ["name", "year", "publisher"]:
                            if key in result["publication_info"]:
                                publication_info[key] = result["publication_info"][key]
                    
                    snippet = result.get("snippet", "No abstract available")
                    
                    # Ask user if they want to attempt to retrieve full text (only for the first 2 papers)
                    full_text = None
                    if idx <= 2 and Confirm.ask(
                        f"[cyan]Would you like to attempt to retrieve full text for paper {idx}?[/cyan] ({title})",
                        default=False
                    ):
                        self.console.print(f"[cyan]Attempting to retrieve full text for paper {idx}...[/cyan]")
                        full_text = self._attempt_full_text_retrieval(link, doi)
                    
                    # Add to formatted results
                    web_info.append(f"{idx}. **{title}**")
                    if authors:
                        web_info.append(f"   Authors: {authors}")
                    web_info.append(f"   {snippet}")
                    if doi:
                        web_info.append(f"   DOI: {doi}")
                    web_info.append(f"   [Link]({link})")
                    if full_text:
                        web_info.append(f"   **Full Text Extract:**")
                        web_info.append(f"   ```")
                        web_info.append(f"   {full_text}")
                        web_info.append(f"   ```")
                    web_info.append("")
                    
                    # Print more detailed results to terminal
                    self.console.print(f"  {idx}. [cyan]{title}[/cyan]")
                    if authors:
                        self.console.print(f"     Authors: {authors}")
                    if doi:
                        self.console.print(f"     DOI: [green]{doi}[/green]")
                    elif pmid:
                        self.console.print(f"     PMID: [green]{pmid}[/green]")
                    self.console.print(f"     URL: [link={link}]{link}[/link]")
                    if full_text:
                        self.console.print(f"     [green]Full text extract available[/green]")
                    
                    # Store in results dict
                    paper_info = {
                        "title": title,
                        "authors": authors,
                        "snippet": snippet,
                        "url": link,
                        "publication_info": publication_info
                    }
                    if doi:
                        paper_info["doi"] = doi
                    if pmid:
                        paper_info["pmid"] = pmid
                    if full_text:
                        paper_info["full_text_extract"] = full_text
                    
                    search_results["scholar_results"].append(paper_info)
                
                self.console.print("")
                
            elif "search_results" in scholar_results:
                web_info.append("## Recent Research Papers")
                self.console.print("[bold green]Found research papers:[/bold green]")
                scholar_found = True
                
                for idx, result in enumerate(scholar_results["search_results"][:5], 1):
                    title = result.get("title", "No title")
                    link = result.get("link", "")
                    authors = result.get("authors", "")
                    publication_info = result.get("publication_info", {})
                    snippet = result.get("snippet", "No abstract available")
                    
                    # Try to extract DOI from link
                    doi = None
                    pmid = None
                    if "doi.org" in link:
                        doi = link.split("doi.org/")[-1]
                    
                    # Add to formatted results
                    web_info.append(f"{idx}. **{title}**")
                    if authors:
                        web_info.append(f"   Authors: {authors}")
                    web_info.append(f"   {snippet}")
                    if doi:
                        web_info.append(f"   DOI: {doi}")
                    web_info.append(f"   [Link]({link})")
                    web_info.append("")
                    
                    # Print more detailed results to terminal
                    self.console.print(f"  {idx}. [cyan]{title}[/cyan]")
                    if authors:
                        self.console.print(f"     Authors: {authors}")
                    if doi:
                        self.console.print(f"     DOI: [green]{doi}[/green]")
                    elif pmid:
                        self.console.print(f"     PMID: [green]{pmid}[/green]")
                    self.console.print(f"     URL: [link={link}]{link}[/link]")
                    
                    # Store in results dict
                    paper_info = {
                        "title": title,
                        "authors": authors,
                        "snippet": snippet,
                        "url": link,
                        "publication_info": publication_info
                    }
                    if doi:
                        paper_info["doi"] = doi
                    if pmid:
                        paper_info["pmid"] = pmid
                        
                    search_results["scholar_results"].append(paper_info)
                
                self.console.print("")
            
            if not scholar_found:
                self.console.print("[yellow]No Google Scholar results found. You may need to try a different query.[/yellow]")
            
            # If no results were found
            if not web_info:
                return "No relevant web information found for this topic.", search_results
            
            # Save the search results
            self._save_search_results(topic, search_results)
                
            return "\n".join(web_info), search_results
            
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
                fallback_text, fallback_results = self._fallback_web_search(topic, serpapi_key)
                search_results["fallback_results"] = fallback_results
                self._save_search_results(topic, search_results)
                return fallback_text, search_results
                
            return "", search_results
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request Error searching the web: {e}", exc_info=True)
            self.console.print(f"[yellow]Could not retrieve web information (Request Error): {e}[/yellow]")
            return "", search_results
            
        except Exception as e:
            logger.error(f"Error searching the web: {e}", exc_info=True)
            self.console.print(f"[yellow]Could not retrieve web information: {e}[/yellow]")
            return "", search_results
        
    def _fallback_web_search(self, topic: str, serpapi_key: str) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Fallback method to search the web using regular Google search when other methods fail.
        
        Args:
            topic: The research topic to search for
            serpapi_key: SerpAPI key to use
            
        Returns:
            Tuple of (formatted results string, list of result dictionaries)
        """
        fallback_results = []
        
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
            
            # Print API usage information
            self.console.print("[bold blue]► Using Google Search API as fallback[/bold blue]")
            
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
                self.console.print("\n[bold green]Found web results (fallback):[/bold green]")
                
                for idx, result in enumerate(search_results["organic_results"][:5], 1):
                    title = result.get("title", "No title")
                    source = result.get("displayed_link", "Unknown source")
                    snippet = result.get("snippet", "No description available")
                    link = result.get("link", "")
                    
                    # Add to formatted results
                    web_info.append(f"{idx}. **{title}** - {source}")
                    web_info.append(f"   {snippet}")
                    web_info.append(f"   [Link]({link})")
                    web_info.append("")
                    
                    # Print more detailed results to terminal
                    self.console.print(f"  {idx}. [cyan]{title}[/cyan]")
                    self.console.print(f"     Source: {source}")
                    self.console.print(f"     URL: [link={link}]{link}[/link]")
                    
                    # Store in results list
                    fallback_results.append({
                        "title": title,
                        "source": source,
                        "snippet": snippet,
                        "url": link
                    })
                
                self.console.print("")
            
            if web_info:
                return "\n".join(web_info), fallback_results
            else:
                return "No relevant web information found using fallback search.", fallback_results
                
        except Exception as e:
            logger.error(f"Error in fallback web search: {e}", exc_info=True)
            return "", fallback_results
    
    def _save_search_results(self, topic: str, results: Dict[str, Any]) -> None:
        """
        Save search results to a JSON file.
        
        Args:
            topic: The research topic
            results: The search results dictionary
        """
        try:
            # Create a filename based on the topic and timestamp
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_topic = "".join(c if c.isalnum() else "_" for c in topic[:30])
            filename = f"{safe_topic}_{timestamp}.json"
            filepath = self.search_results_dir / filename
            
            # Format the results to ensure all data is captured
            formatted_results = {
                "query": topic,
                "timestamp": results.get("timestamp", datetime.datetime.now().isoformat()),
                "news_results": results.get("news_results", []),
                "scholar_results": results.get("scholar_results", []),
                "fallback_results": results.get("fallback_results", [])
            }
            
            # Verify all scholar results have their full text included
            for paper in formatted_results["scholar_results"]:
                # Ensure the full_text_extract key exists if it was generated
                if "full_text_extract" in paper:
                    # Make sure it's not None or empty
                    if not paper["full_text_extract"]:
                        paper["full_text_extract"] = "Full text was extracted but not saved"
            
            # Save the results
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(formatted_results, f, indent=2, ensure_ascii=False)
            
            self.console.print(f"[dim]Search results saved to: {filepath}[/dim]")
            
        except Exception as e:
            logger.error(f"Error saving search results: {e}", exc_info=True)
            self.console.print(f"[yellow]Could not save search results: {e}[/yellow]")
        
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
            
            # Parse the response to extract queries and explanations
            tiered_queries = self._parse_tiered_response(response.text)
            
            # Save the queries to JSON
            self._save_query_results(user_input, web_info, tiered_queries, response.text)
            
            return tiered_queries
            
        except Exception as e:
            logger.error(f"Error generating queries: {e}", exc_info=True)
            self.console.print(f"\n[bold red]Error generating queries: {e}[/bold red]")
            return {
                "simple": {"query": "", "explanation": "Unable to generate query."},
                "medium": {"query": "", "explanation": "Unable to generate query."}
            }
    
    def _save_query_results(self, user_input: str, web_info: str, 
                            tiered_queries: Dict[str, Dict[str, str]], 
                            raw_response: str) -> None:
        """
        Save generated queries and explanations to a JSON file.
        
        Args:
            user_input: The user's research question
            web_info: Web search information used
            tiered_queries: The generated queries
            raw_response: Raw response from the AI
        """
        try:
            # Create a result dictionary
            result = {
                "user_query": user_input,
                "timestamp": datetime.datetime.now().isoformat(),
                "model_used": self.model,
                "tiered_queries": tiered_queries,
                "raw_ai_response": raw_response,
                "web_info_provided": bool(web_info)
            }
            
            # Create a filename based on the query and timestamp
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_query = "".join(c if c.isalnum() else "_" for c in user_input[:30])
            filename = f"query_{safe_query}_{timestamp}.json"
            filepath = self.search_results_dir / filename
            
            # Save the results
            with open(filepath, 'w') as f:
                json.dump(result, f, indent=2)
            
            self.console.print(f"[dim]Query results saved to: {filepath}[/dim]")
            
        except Exception as e:
            logger.error(f"Error saving query results: {e}", exc_info=True)
            self.console.print(f"[yellow]Could not save query results: {e}[/yellow]")
    
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
                    explanation_text.append(line[16:].strip())  # Fixed: changed trip() to strip()
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
            web_results = {}
            if include_web_search:
                web_info, web_results = self.search_web_for_information(user_input)
                if web_info:
                    self.console.print(Panel(
                        Markdown(web_info),
                        title="[bold green]Web Search Results Summary[/bold green]",
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
                    
                    # Save the modified query result
                    if "query" in modified_result:
                        # Add to the tiered queries and save
                        tiered_queries[f"modified_{modify}"] = modified_result
                        self._save_query_results(
                            f"{user_input} (modified: {modification})", 
                            web_info, 
                            {f"modified_{modify}": modified_result},
                            response.text
                        )
                        
                        # Display modified query
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
            
            # Final message with path to saved results
            self.console.print("\n[bold green]✨ Happy researching! You can now use these queries on PubMed.[/bold green]")
            self.console.print(f"[italic]All search results and queries have been saved in: {self.search_results_dir}[/italic]")
            self.console.print("[italic]Copy the query you prefer and paste it into the PubMed search box.[/italic]")
            
        except Exception as e:
            logger.error(f"Error in query helper: {e}", exc_info=True)
            self.console.print(f"\n[bold red]Error: {e}[/bold red]")
            import traceback
            self.console.print(Panel(traceback.format_exc(), title="[bold red]Error Details", border_style="red"))
            
        except KeyboardInterrupt:
            self.console.print("\n\n[yellow]Query helper terminated by user.[/yellow]")

    def _attempt_full_text_retrieval(self, url: str, doi: str = None) -> str:
        """
        Attempt to retrieve full text of an article using various methods.
        
        Args:
            url: The URL of the article
            doi: The DOI of the article if available
            
        Returns:
            The full text if available, or a message indicating it's not available
        """
        try:
            self.console.print("[cyan]Attempting full text retrieval...[/cyan]")
            
            # Try to use Unpaywall API if we have a DOI
            if doi and self.key_manager.has_key("UNPAYWALL_EMAIL"):
                unpaywall_email = self.key_manager.get_key("UNPAYWALL_EMAIL")
                unpaywall_url = f"https://api.unpaywall.org/v2/{doi}?email={unpaywall_email}"
                
                self.console.print(f"[dim]Checking Unpaywall for open access version of DOI {doi}...[/dim]")
                response = requests.get(unpaywall_url, timeout=5)
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("is_oa") and data.get("best_oa_location", {}).get("url"):
                        oa_url = data["best_oa_location"]["url"]
                        self.console.print(f"[green]Found open access version: {oa_url}[/green]")
                        
                        # Try to retrieve the actual content from the open access URL
                        try:
                            oa_response = requests.get(oa_url, timeout=10)
                            if oa_response.status_code == 200:
                                # Try to use newspaper3k for extraction
                                try:
                                    from newspaper import Article
                                    article = Article(oa_url)
                                    article.download()
                                    article.parse()
                                    
                                    if article.text:
                                        # Return a summary (first 1000 chars)
                                        text_extract = article.text[:1000] + "..." if len(article.text) > 1000 else article.text
                                        return f"Open access full text extract from {oa_url}:\n\n{text_extract}"
                                except ImportError:
                                    pass
                        except Exception:
                            pass
                        
                        return f"Open access version available at: {oa_url}"
            
            # For PubMed Central articles, we can attempt to get the full text
            if "ncbi.nlm.nih.gov/pmc/" in url:
                self.console.print("[dim]Article appears to be in PubMed Central, attempting direct retrieval...[/dim]")
                try:
                    # Extract PMC ID
                    pmc_id = None
                    if "/pmc/articles/PMC" in url:
                        pmc_id = url.split("/pmc/articles/PMC")[1].split("/")[0]
                    
                    if pmc_id:
                        pubmed_api_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pmc&id={pmc_id}&rettype=text"
                        response = requests.get(pubmed_api_url, timeout=10)
                        if response.status_code == 200:
                            # Only return a summary of the full text (first 1000 chars)
                            full_text = response.text[:1000] + "..." if len(response.text) > 1000 else response.text
                            return f"PMC Full text extract (PMC ID: {pmc_id}):\n\n{full_text}"
                except Exception as e:
                    logger.warning(f"Failed to retrieve PMC full text: {e}")
            
            # For arXiv papers
            if "arxiv.org" in url:
                self.console.print("[dim]Article appears to be on arXiv, attempting to retrieve abstract...[/dim]")
                try:
                    # Extract arXiv ID
                    arxiv_id = None
                    if "/abs/" in url:
                        arxiv_id = url.split("/abs/")[1].split(".")[0].split("v")[0]
                    
                    if arxiv_id:
                        arxiv_api_url = f"http://export.arxiv.org/api/query?id_list={arxiv_id}"
                        response = requests.get(arxiv_api_url, timeout=10)
                        if response.status_code == 200:
                            # Parse XML to extract abstract
                            import xml.etree.ElementTree as ET
                            root = ET.fromstring(response.text)
                            
                            # Find the abstract using namespace
                            ns = {'arxiv': 'http://arxiv.org/schemas/atom'}
                            entry = root.find('.//arxiv:entry', ns)
                            if entry:
                                abstract = entry.find('.//arxiv:summary', ns)
                                if abstract is not None and abstract.text:
                                    return f"arXiv Abstract (ID: {arxiv_id}):\n\n{abstract.text}"
                except Exception as e:
                    logger.warning(f"Failed to retrieve arXiv details: {e}")
            
            # For general websites, try to extract the main content
            self.console.print("[dim]Attempting general web page content extraction...[/dim]")
            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
                response = requests.get(url, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    try:
                        # Try to use newspaper3k for extraction if available
                        from newspaper import Article
                        
                        article = Article(url)
                        article.download()
                        article.parse()
                        
                        if article.text:
                            # Return a summary (first 1000 chars)
                            text_extract = article.text[:1000] + "..." if len(article.text) > 1000 else article.text
                            self.console.print("[green]Successfully extracted content using newspaper3k[/green]")
                            return f"Extracted content from {url}:\n\n{text_extract}"
                    except ImportError:
                        # If newspaper3k is not installed, try a simple extraction
                        self.console.print("[dim]newspaper3k not available, falling back to BeautifulSoup...[/dim]")
                        try:
                            from bs4 import BeautifulSoup
                            soup = BeautifulSoup(response.text, 'html.parser')
                            
                            # Try to find the main content
                            main_content = ""
                            for tag in ['article', 'main', '.content', '#content']:
                                content = soup.select_one(tag) if not tag.startswith('.') and not tag.startswith('#') else soup.select_one(tag)
                                if content:
                                    main_content = content.get_text(strip=True)
                                    break
                            
                            if not main_content:
                                # Get all paragraphs if we couldn't find main content
                                paragraphs = soup.find_all('p')
                                main_content = ' '.join([p.get_text(strip=True) for p in paragraphs[:5]])
                            
                            if main_content:
                                # Return a summary (first 1000 chars)
                                text_extract = main_content[:1000] + "..." if len(main_content) > 1000 else main_content
                                self.console.print("[green]Successfully extracted content using BeautifulSoup[/green]")
                                return f"Extracted content from {url}:\n\n{text_extract}"
                        except ImportError:
                            self.console.print("[yellow]BeautifulSoup not available for content extraction[/yellow]")
                            
                else:
                    self.console.print(f"[yellow]Failed to retrieve page: HTTP {response.status_code}[/yellow]")
                    
            except Exception as e:
                logger.warning(f"Failed to scrape website: {e}")
            
            self.console.print("[yellow]Full text extraction unsuccessful[/yellow]")
            return "Full text not available automatically. Access may require subscription or manual browsing."
        
        except Exception as e:
            logger.error(f"Error retrieving full text: {e}", exc_info=True)
            return f"Error retrieving full text information: {str(e)}"


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