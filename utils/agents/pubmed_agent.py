"""
PubMed Research Agent

This module provides an agent for searching and analyzing PubMed articles.
It integrates with the PubmedSearcher to retrieve scientific literature and
uses AI to provide insights on each article's relevance.

Features:
- Interactive PubMed search
- Article metadata retrieval
- Abstract formatting and display
- AI-powered research insights
- Result storage and export
"""

import sys
import json
import logging
import datetime
import re
import webbrowser
import traceback
from typing import List, Dict, Optional, Any
from pathlib import Path

from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich.markdown import Markdown
from rich.table import Table
from rich.box import ROUNDED
from rich.progress import Progress

# Add project root to sys.path if needed
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from utils.google_genai import GeminiClient
from utils.keyManager import KeyManager
from utils.pubmed_searcher.pubmed_searcher import PubmedSearcher
from utils.agents.base_agent import BaseAgent

# Configure logging
logger = logging.getLogger("agents.pubmed")


class PubMedResearchAgent(BaseAgent):
    """
    An agent that searches PubMed using the PubmedSearcher and provides insights
    about the importance of each article for researchers.
    
    This agent helps researchers explore scientific literature by searching PubMed,
    retrieving article details, and providing AI-generated insights about the
    importance of each article for the user's research question.
    
    Attributes:
        model (str): The Gemini model to use for generating insights
        client (GeminiClient): Client for AI text generation
        key_manager (KeyManager): Manager for API keys
        searcher (PubmedSearcher): Tool for searching PubMed
    """
    
    def __init__(
        self,
        model: str = "gemini-2.0-flash",
        output_dir: Optional[Path] = None,
        console: Optional[Console] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the PubMed Research Agent.
        
        Args:
            model: The Gemini model to use for generating insights
            output_dir: Directory to save results (default: project_root/search_results)
            console: Rich console for output formatting (creates a new one if None)
            config: Additional configuration parameters
        """
        # Initialize base agent
        super().__init__(
            name="PubMed Research Agent",
            results_dir=output_dir,
            console=console,
            config=config
        )
        
        # Set up model and clients
        self.model = model
        self.client = GeminiClient(console=self.console, default_model=model)
        self.key_manager = KeyManager()
        
        # Initialize PubMed searcher with API key if available
        pubmed_api_key = self.key_manager.get_key("PUBMED_API_KEY") if self.key_manager.has_key("PUBMED_API_KEY") else None
        self.searcher = PubmedSearcher(
            output_dir=str(self.results_dir / "pubmed_results"),
            api_key=pubmed_api_key
        )
    
    def welcome(self) -> None:
        """Display a welcome message explaining the tool."""
        welcome_text = """
        # 📚 PubMed Research Agent

        This tool helps you search PubMed for scientific articles and provides insights about each paper.
        
        The agent will:
        - Search PubMed based on your query
        - Retrieve article details including titles, authors, and abstracts
        - Analyze each paper's importance for your research
        - Save all results for your reference
        
        Let's explore the scientific literature!
        """
        self.console.print(Markdown(welcome_text))
    
    def get_search_query(self) -> str:
        """
        Get the PubMed search query from the user.
        
        Returns:
            User's search query
        """
        return Prompt.ask(
            "\n[bold cyan]Enter your PubMed search query[/bold cyan]\n"
            "You can use standard PubMed syntax (e.g., 'diabetes AND insulin')"
        )
    
    def search_pubmed(self, query: str, max_results: int = 10) -> List[Dict]:
        """
        Search PubMed using the query and retrieve article details.
        
        Args:
            query: PubMed search query
            max_results: Maximum number of results to retrieve
            
        Returns:
            List of dictionaries containing article details
        """
        self.console.print(f"\n[bold]Searching PubMed for: [cyan]{query}[/cyan][/bold]")
        
        try:
            with Progress() as progress:
                search_task = progress.add_task("[cyan]Searching PubMed...", total=100)
                
                # Perform the search
                ids, metadata = self.searcher.search(query, max_results=max_results)
                
                total_found = metadata.get('count', '0')
                progress.update(search_task, completed=30)
                
                if not ids:
                    self.console.print("[yellow]No articles found matching your query.[/yellow]")
                    return []
                
                self.console.print(f"Found {total_found} total results, retrieving details for {len(ids)} articles")
                
                # Get article details
                articles_details = self.searcher.get_article_details(ids)
                progress.update(search_task, completed=60)
                
                # Process each article and extract relevant information
                results = []
                for article_id in ids:
                    article_data = self._process_article(article_id, articles_details.get(article_id, {}))
                    results.append(article_data)
                
                progress.update(search_task, completed=100)
            
            return results
            
        except Exception as e:
            self.log_error("Error searching PubMed", e)
            return []
    
    def _process_article(self, article_id: str, article_details: Dict) -> Dict:
        """
        Process an article's details into a standardized format.
        
        Args:
            article_id: The article ID (PMID)
            article_details: The raw article details from PubMed
            
        Returns:
            A dictionary with standardized article information
        """
        # Ensure we have a UID
        if 'uid' not in article_details:
            article_details['uid'] = article_id
        
        # Get and format authors
        first_author, co_authors = self.searcher.format_authors(article_details.get('authors', []))
        
        # Get abstract
        abstract = self.searcher.get_article_abstract(article_id)
        
        # Extract MeSH terms and keywords
        mesh_terms = self.searcher.extract_mesh_terms(article_details)
        keywords = self.searcher.extract_keywords(article_details)
        
        # Get DOI and other identifiers
        doi = None
        pmid = article_id
        pmc_id = None
        full_text_links = []
        
        if 'articleids' in article_details:
            for id_info in article_details['articleids']:
                if id_info.get('idtype') == 'doi':
                    doi = id_info['value']
                elif id_info.get('idtype') == 'pmcid':
                    pmc_id = id_info['value']
                    # PMC ID might include the "PMC" prefix, so strip it if needed
                    pmc_id = pmc_id.replace("PMC", "") if pmc_id else None
                    if pmc_id:
                        full_text_links.append(f"https://www.ncbi.nlm.nih.gov/pmc/articles/PMC{pmc_id}")
        
        # Add DOI link if available
        if doi:
            full_text_links.append(f"https://doi.org/{doi}")
        
        # Prepare article data in standardized format
        return {
            'id': article_id,
            'pmid': pmid,
            'title': article_details.get('title', 'Not available'),
            'first_author': first_author,
            'co_authors': co_authors,
            'journal': article_details.get('fulljournalname', article_details.get('source', 'Not available')),
            'publication_date': article_details.get('pubdate', 'Not available'),
            'abstract': abstract,
            'mesh_terms': mesh_terms,
            'keywords': keywords,
            'full_text_links': full_text_links,
            'doi': doi,
            'pmc_id': pmc_id
        }
    
    def analyze_results(self, query: str, results: List[Dict]) -> List[Dict]:
        """
        Add research insights to each result using AI analysis.
        
        Args:
            query: The original search query
            results: List of article results
            
        Returns:
            Updated list of results with research insights
        """
        if not results:
            return results
        
        self.console.print("\n[bold]Analyzing articles for research insights...[/bold]")
        
        try:
            with Progress() as progress:
                analysis_task = progress.add_task("[cyan]Generating insights...", total=len(results))
                
                for i, article in enumerate(results):
                    # Generate insights for this article
                    article['research_insight'] = self._generate_article_insight(query, article)
                    
                    # Update progress
                    progress.update(analysis_task, advance=1)
            
            return results
            
        except Exception as e:
            self.log_error("Error generating insights", e)
            
            # Still return the results, just without insights
            for article in results:
                if 'research_insight' not in article:
                    article['research_insight'] = "Unable to generate insight for this article."
            return results
    
    def _generate_article_insight(self, query: str, article: Dict) -> str:
        """
        Generate an AI-powered insight about the article's importance.
        
        Args:
            query: User's research query
            article: Article data
            
        Returns:
            Insight text
        """
        # Create prompt for analyzing article
        prompt = f"""
        As a research assistant, analyze this scientific article's importance for a researcher.
        
        # User's Research Query:
        {query}
        
        # Article Information:
        Title: {article['title']}
        Authors: {article['first_author']}{"" if not article['co_authors'] else f" et al. ({len(article['co_authors'])} co-authors)"}
        Journal: {article['journal']}
        Published: {article['publication_date']}
        
        # Abstract:
        {article['abstract']}
        
        # MeSH Terms:
        {', '.join(article['mesh_terms']) if article['mesh_terms'] else 'None'}
        
        # Keywords:
        {', '.join(article['keywords']) if article['keywords'] else 'None'}
        
        Provide a concise paragraph (approximately 2-3 sentences) that explains:
        1. Why this paper is important for the researcher's query
        2. What specific aspect deserves further exploration
        3. How it relates to the field
        
        Be specific about the paper's content. Do not use generic statements.
        """
        
        try:
            # Generate insight
            response, metrics = self.client.query(
                query=prompt,
                model=self.model,
                temperature=0.2,  # Use a low temperature for factual responses
                display_response=False
            )
            
            return response.text
            
        except Exception as e:
            logger.warning(f"Failed to generate insight: {e}")
            return "Unable to generate insight for this article."
    
    def display_results(self, results: List[Dict]) -> None:
        """
        Display the search results in a rich table.
        
        Args:
            results: List of article results
        """
        if not results:
            self.console.print("[yellow]No results to display.[/yellow]")
            return
        
        self.console.print("\n[bold]PubMed Search Results:[/bold]")
        
        # Create a table for the results
        table = Table(box=ROUNDED, show_lines=True)
        table.add_column("#", style="bold", width=3, justify="right")
        table.add_column("Title", style="cyan", max_width=40)
        table.add_column("Authors", style="green", max_width=20)
        table.add_column("Journal/Year", max_width=15)
        table.add_column("Research Insight", style="yellow", max_width=50)
        
        # Add each article to the table
        for i, article in enumerate(results, 1):
            # Format authors
            if article['co_authors']:
                authors = f"{article['first_author']} et al."
            else:
                authors = article['first_author']
                
            # Format journal and year
            pub_year = article['publication_date'].split(' ')[-1] if article['publication_date'] != 'Not available' else 'N/A'
            journal_info = f"{article['journal']}\n({pub_year})"
            
            # Add row to table
            table.add_row(
                str(i),
                article['title'],
                authors,
                journal_info,
                article.get('research_insight', 'Not available')
            )
        
        self.console.print(table)
        
        # Display citation information
        self.display_citations(results)
    
    def display_citations(self, results: List[Dict]) -> None:
        """
        Display citation information for articles.
        
        Args:
            results: List of article results
        """
        self.console.print("\n[bold]Article Identifiers:[/bold]")
        id_table = Table(box=ROUNDED)
        id_table.add_column("#", style="bold", width=3, justify="right")
        id_table.add_column("PMID", style="cyan")
        id_table.add_column("DOI", style="green")
        id_table.add_column("Full Text Link", style="blue")
        
        for i, article in enumerate(results, 1):
            pmid = article['pmid'] or 'N/A'
            doi = article['doi'] or 'N/A'
            link = article['full_text_links'][0] if article['full_text_links'] else 'N/A'
            
            id_table.add_row(
                str(i),
                pmid,
                doi,
                f"[link={link}]{link}[/link]" if link != 'N/A' else 'N/A'
            )
        
        self.console.print(id_table)
    
    def save_results(self, query: str, results: List[Dict]) -> Optional[Path]:
        """
        Save the search results to a JSON file.
        
        Args:
            query: The search query
            results: List of article results
            
        Returns:
            Path to the saved file, or None if saving failed
        """
        if not results:
            self.console.print("[yellow]No results to save.[/yellow]")
            return None
        
        try:
            # Create a data structure for the results
            data = {
                "query": query,
                "timestamp": datetime.datetime.now().isoformat(),
                "num_results": len(results),
                "articles": results
            }
            
            # Create a filename based on the query and timestamp
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_query = "".join(c if c.isalnum() else "_" for c in query[:30])
            filename = f"pubmed_{safe_query}_{timestamp}.json"
            filepath = self.results_dir / filename
            
            # Save the results
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            self.console.print(f"[dim]Results saved to: {filepath}[/dim]")
            return filepath
            
        except Exception as e:
            self.log_error("Error saving results", e)
            return None
    
    def format_abstract_display(self, article: Dict) -> str:
        """
        Format an article abstract for beautiful display in the terminal.
        
        Args:
            article: The article dictionary containing abstract and metadata
            
        Returns:
            Formatted string for display
        """
        # Format title with proper capitalization
        title = article['title'].strip()
        if title.isupper():  # Sometimes PubMed titles are all caps
            title = title.title()
        
        # Format authors nicely
        if article['co_authors']:
            all_authors = [article['first_author']] + article['co_authors']
            # Limit to first 5 authors if there are many
            if len(all_authors) > 5:
                authors_text = ", ".join(all_authors[:5]) + f" and {len(all_authors) - 5} others"
            else:
                authors_text = ", ".join(all_authors)
        else:
            authors_text = article['first_author']
        
        # Format journal and date
        journal = article['journal']
        pub_date = article['publication_date']
        
        # Format abstract with proper paragraph breaks
        abstract = article['abstract']
        if abstract == "Not available":
            abstract_formatted = "*Abstract not available for this article.*"
        else:
            # Break into paragraphs if it's not already
            paragraphs = abstract.split('\n')
            if len(paragraphs) == 1 and len(abstract) > 200:
                # Try to intelligently split into paragraphs at sentence boundaries
                sentences = re.split(r'(?<=[.!?])\s+', abstract)
                
                paragraphs = []
                current_paragraph = []
                current_length = 0
                
                # Group sentences into reasonable paragraphs
                for sentence in sentences:
                    if current_length + len(sentence) > 300:  # Start new paragraph if too long
                        if current_paragraph:
                            paragraphs.append(" ".join(current_paragraph))
                        current_paragraph = [sentence]
                        current_length = len(sentence)
                    else:
                        current_paragraph.append(sentence)
                        current_length += len(sentence)
                
                # Add the last paragraph if there's anything left
                if current_paragraph:
                    paragraphs.append(" ".join(current_paragraph))
            
            # Format paragraphs with proper spacing
            abstract_formatted = "\n\n".join(paragraphs)
        
        # Add keywords and MeSH terms if available
        keywords_section = ""
        if article['keywords']:
            keywords_section += "\n\n**Keywords:** " + ", ".join(article['keywords'])
        
        mesh_section = ""
        if article['mesh_terms']:
            mesh_section += "\n\n**MeSH Terms:** " + ", ".join(article['mesh_terms'])
        
        # Add DOI and PMID for reference
        identifiers = []
        if article['doi']:
            identifiers.append(f"DOI: {article['doi']}")
        if article['pmid']:
            identifiers.append(f"PMID: {article['pmid']}")
        if article['pmc_id']:
            identifiers.append(f"PMC: {article['pmc_id']}")
        
        identifiers_text = " | ".join(identifiers) if identifiers else ""
        
        # Combine everything into a beautiful format
        return f"""# {title}

## Authors
{authors_text}

## Journal
{journal} ({pub_date})

## Abstract
{abstract_formatted}
{keywords_section}
{mesh_section}

{identifiers_text}
"""
    
    def display_abstract(self, article: Dict, article_num: int) -> None:
        """
        Display an article abstract in a rich panel.
        
        Args:
            article: Article dictionary
            article_num: Article number in the results list
        """
        # Format the abstract
        formatted_abstract = self.format_abstract_display(article)
        
        # Display in a panel with a nice border
        self.console.print(Panel(
            Markdown(formatted_abstract),
            title=f"[bold]Article #{article_num} Details[/bold]",
            border_style="green",
            padding=(1, 2),
            expand=False
        ))
    
    def interactive_abstract_viewer(self, results: List[Dict]) -> None:
        """
        Interactive loop for viewing abstracts of articles.
        
        Args:
            results: List of article results
        """
        while Confirm.ask(
            "\n[cyan]Would you like to view the full abstract of an article?[/cyan]",
            default=False
        ):
            article_num = int(Prompt.ask(
                "[cyan]Enter the number of the article to view[/cyan]",
                default="1"
            ))
            
            if 1 <= article_num <= len(results):
                article = results[article_num-1]
                
                # Display abstract
                self.display_abstract(article, article_num)
                
                # Offer to open in browser
                if article['full_text_links']:
                    if Confirm.ask(
                        "\n[cyan]Would you like to open this article in your browser?[/cyan]",
                        default=False
                    ):
                        url = article['full_text_links'][0]
                        self.console.print(f"[green]Opening {url} in your browser...[/green]")
                        webbrowser.open(url)
            else:
                self.console.print(f"[yellow]Article #{article_num} doesn't exist.[/yellow]")
    
    def run(self, query: str = None, max_results: int = 10, add_insights: bool = None) -> List[Dict]:
        """
        Run the PubMed research agent workflow.
        
        Args:
            query: Optional search query (if None, will prompt the user)
            max_results: Maximum number of results to retrieve
            add_insights: Whether to add research insights (if None, will prompt)
            
        Returns:
            List of article results
        """
        try:
            # Display welcome message if running interactively
            if query is None:
                self.welcome()
            
            # Get the search query from the user if not provided
            if query is None:
                query = self.get_search_query()
            
            # Ask for max results if running interactively
            if query is None:
                max_results = int(Prompt.ask(
                    "\n[bold cyan]Maximum number of articles to retrieve[/bold cyan]",
                    default=str(max_results)
                ))
            
            # Perform the search
            results = self.search_pubmed(query, max_results=max_results)
            
            if results:
                # Ask if they want research insights if not specified
                if add_insights is None:
                    add_insights = Confirm.ask(
                        "\n[cyan]Would you like AI-generated research insights for each article?[/cyan]",
                        default=True
                    )
                
                if add_insights:
                    results = self.analyze_results(query, results)
                
                # Display the results
                self.display_results(results)
                
                # Save the results
                self.save_results(query, results)
                
                # Allow interactive abstract viewing if running from CLI
                if query is None:  # Interactive mode
                    self.interactive_abstract_viewer(results)
            
            # Final message if running interactively
            if query is None:
                self.console.print("\n[bold green]Thank you for using the PubMed Research Agent![/bold green]")
            
            return results
            
        except Exception as e:
            self.log_error("Error in PubMed research agent", e)
            self.console.print(Panel(traceback.format_exc(), title="[bold red]Error Details", border_style="red"))
            return []
            
        except KeyboardInterrupt:
            self.console.print("\n\n[yellow]PubMed research agent terminated by user.[/yellow]")
            return []


# Create a convenience function for CLI usage
def run_pubmed_agent():
    """Run the PubMed research agent from the command line."""
    try:
        # Create console here to avoid circular import issues
        console = Console()
        
        # Run the PubMed research agent
        agent = PubMedResearchAgent()
        agent.run()
    except Exception as e:
        console = Console()
        console.print(f"[bold red]Fatal error: {e}[/bold red]")
        logger.critical("Fatal error", exc_info=True)
    except KeyboardInterrupt:
        console = Console()
        console.print("\n[yellow]Program terminated by user.[/yellow]")


if __name__ == "__main__":
    run_pubmed_agent()