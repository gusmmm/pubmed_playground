"""
PubMed Research Agent

This script creates an interactive agent that helps researchers explore PubMed articles.
It uses the PubmedSearcher class to retrieve scientific articles and provides insights
about the importance of each article.

Features:
- Interactive prompt for PubMed searches
- Retrieves article details including titles, authors, journals, and abstracts
- Provides AI-generated insights about each article's importance
- Displays results in a rich formatted table
- Saves all results to JSON for later analysis
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
from utils.pubmed_searcher import PubmedSearcher

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("pubmed_agent")

# Initialize Rich console
console = Console()


class PubMedResearchAgent:
    """
    An agent that searches PubMed using the PubmedSearcher and provides insights
    about the importance of each article for researchers.
    """
    
    def __init__(self, model: str = "gemini-2.0-flash"):
        """
        Initialize the PubMed Research Agent.
        
        Args:
            model: The Gemini model to use for generating insights
        """
        self.console = Console()
        self.model = model
        self.client = GeminiClient(console=self.console, default_model=model)
        self.key_manager = KeyManager()
        
        # Initialize PubMed searcher with API key if available
        pubmed_api_key = self.key_manager.get_key("PUBMED_API_KEY") if self.key_manager.has_key("PUBMED_API_KEY") else None
        self.searcher = PubmedSearcher(
            output_dir=str(project_root / "pubmed_results"),
            api_key=pubmed_api_key
        )
        
        # Create results directory
        self.results_dir = project_root / "search_results"
        self.results_dir.mkdir(exist_ok=True, parents=True)
    
    def welcome(self):
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
                    # Get article details
                    article_details = articles_details.get(article_id, {})
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
                                full_text_links.append(f"https://www.ncbi.nlm.nih.gov/pmc/articles/PMC{pmc_id}")
                    
                    if doi:
                        full_text_links.append(f"https://doi.org/{doi}")
                    
                    # Prepare article data
                    article_data = {
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
                    
                    results.append(article_data)
                
                progress.update(search_task, completed=100)
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching PubMed: {e}", exc_info=True)
            self.console.print(f"[bold red]Error searching PubMed: {e}[/bold red]")
            return []
    
    def analyze_results(self, query: str, results: List[Dict]) -> List[Dict]:
        """
        Add research insights to each result.
        
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
                    
                    # Generate insight
                    response, metrics = self.client.query(
                        query=prompt,
                        model=self.model,
                        temperature=0.2,  # Use a low temperature for factual responses
                        display_response=False
                    )
                    
                    # Add insight to article
                    article['research_insight'] = response.text
                    
                    # Update progress
                    progress.update(analysis_task, advance=1)
            
            return results
            
        except Exception as e:
            logger.error(f"Error generating insights: {e}", exc_info=True)
            self.console.print(f"[bold red]Error generating insights: {e}[/bold red]")
            
            # Still return the results, just without insights
            for article in results:
                article['research_insight'] = "Unable to generate insight for this article."
            return results
    
    def display_results(self, results: List[Dict]):
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
    
    def save_results(self, query: str, results: List[Dict]):
        """
        Save the search results to a JSON file.
        
        Args:
            query: The search query
            results: List of article results
        """
        if not results:
            self.console.print("[yellow]No results to save.[/yellow]")
            return
        
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
            
        except Exception as e:
            logger.error(f"Error saving results: {e}", exc_info=True)
            self.console.print(f"[yellow]Could not save results: {e}[/yellow]")
    
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
                import re
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
    
    def run(self):
        """Run the PubMed research agent workflow."""
        try:
            # Display welcome message
            self.welcome()
            
            # Get the search query from the user
            query = self.get_search_query()
            
            # Ask for max number of results
            max_results = int(Prompt.ask(
                "\n[bold cyan]Maximum number of articles to retrieve[/bold cyan]",
                default="10"
            ))
            
            # Perform the search
            results = self.search_pubmed(query, max_results=max_results)
            
            if results:
                # Ask if they want research insights
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
                
                # Allow the user to view an abstract
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
                        
                        # Use the new formatting function
                        formatted_abstract = self.format_abstract_display(article)
                        
                        # Display in a panel with a nice border
                        self.console.print(Panel(
                            Markdown(formatted_abstract),
                            title=f"[bold]Article #{article_num} Details[/bold]",
                            border_style="green",
                            padding=(1, 2),
                            expand=False
                        ))
                        
                        # Offer to open in browser if links are available
                        if article['full_text_links']:
                            if Confirm.ask(
                                "\n[cyan]Would you like to open this article in your browser?[/cyan]",
                                default=False
                            ):
                                url = article['full_text_links'][0]
                                self.console.print(f"[green]Opening {url} in your browser...[/green]")
                                import webbrowser
                                webbrowser.open(url)
                    else:
                        self.console.print(f"[yellow]Article #{article_num} doesn't exist.[/yellow]")
            
            self.console.print("\n[bold green]Thank you for using the PubMed Research Agent![/bold green]")
            
        except Exception as e:
            logger.error(f"Error in PubMed research agent: {e}", exc_info=True)
            self.console.print(f"\n[bold red]Error: {e}[/bold red]")
            import traceback
            self.console.print(Panel(traceback.format_exc(), title="[bold red]Error Details", border_style="red"))
            
        except KeyboardInterrupt:
            self.console.print("\n\n[yellow]PubMed research agent terminated by user.[/yellow]")


if __name__ == "__main__":
    try:
        # Run the PubMed research agent
        agent = PubMedResearchAgent()
        agent.run()
    except Exception as e:
        console.print(f"[bold red]Fatal error: {e}[/bold red]")
        logger.critical("Fatal error", exc_info=True)
    except KeyboardInterrupt:
        console.print("\n[yellow]Program terminated by user.[/yellow]")