"""
PubMed Query Agent

This module provides a specialized agent for constructing optimized
PubMed search queries following clinical research best practices.
It integrates with Google GenAI to provide intelligent query assistance.

Features:
- Natural language query parsing
- Clinical query optimization
- Filter selection assistance
- PubMed syntax formatting
- Query validation
"""

import sys
import re
import logging
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path

from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich.markdown import Markdown
from rich.table import Table
from rich.box import ROUNDED

# Add project root to sys.path if needed
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from utils.google_genai import GeminiClient
from utils.agents.base_agent import BaseAgent

# Configure logging
logger = logging.getLogger("agents.pubmed_query")


class PubMedQueryAgent(BaseAgent):
    """
    An agent that helps users construct optimized PubMed search queries.
    
    This agent guides users through the process of creating effective PubMed
    queries by translating natural language questions into properly formatted
    search terms with appropriate filters based on clinical research needs.
    
    Attributes:
        model (str): The Gemini model to use for query assistance
        client (GeminiClient): Client for AI text generation
        clinical_categories (List[str]): Available clinical query categories
        filter_scopes (List[str]): Available filter scope options
    """
    
    def __init__(
        self,
        model: str = "gemini-2.0-flash",
        console: Optional[Console] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the PubMed Query Agent.
        
        Args:
            model: The Gemini model to use for query assistance
            console: Rich console for output formatting (creates a new one if None)
            config: Additional configuration parameters
        """
        # Initialize base agent
        super().__init__(
            name="PubMed Query Agent",
            results_dir=None,  # No results to save for this agent
            console=console,
            config=config
        )
        
        # Set up model and client
        self.model = model
        self.client = GeminiClient(console=self.console, default_model=model)
        
        # Define clinical query categories and filter scopes
        self.clinical_categories = [
            "Therapy", 
            "Diagnosis", 
            "Etiology", 
            "Prognosis", 
            "Clinical Prediction Guides"
        ]
        
        self.filter_scopes = ["Broad", "Narrow"]
        
        # Define article types
        self.article_types = [
            "Clinical trial",
            "Meta-analysis",
            "Randomized controlled trial",
            "Review",
            "Systematic review",
            "All types"
        ]
        
        # Define age groups
        self.age_groups = [
            "Adults (18+)",
            "Aged (65+)",
            "Children (<18)",
            "Adults and children",
            "Any age"
        ]
        
        # Define time periods
        self.time_periods = [
            "Last year",
            "Last 5 years",
            "Last 10 years",
            "Custom range",
            "Any time"
        ]
        
        # Define text availability options
        self.text_availability = [
            "All results",
            "Full text",
            "Free full text",
            "Abstract"
        ]
    
    def welcome(self) -> None:
        """Display a welcome message explaining the tool."""
        welcome_text = """
        # 🔍 PubMed Query Generator

        This tool helps you construct optimized PubMed search queries for clinical research.
        
        The agent will:
        - Transform your natural language question into PubMed search syntax
        - Assist with applying appropriate clinical filters
        - Help you narrow or broaden your search as needed
        - Generate a properly formatted query ready for PubMed
        
        Let's create an effective search strategy!
        """
        self.console.print(Markdown(welcome_text))
    
    def get_natural_language_query(self) -> str:
        """
        Get the initial query description from the user in natural language.
        
        Returns:
            User's natural language description of what they want to find
        """
        return Prompt.ask(
            "\n[bold cyan]What are you looking to find in the medical literature?[/bold cyan]\n"
            "Describe your research question in plain language"
        )
    
    def simplify_query(self, natural_query: str) -> str:
        """
        Simplify a natural language query to basic search terms for PubMed.
        
        Uses AI to extract key terms and format according to PubMed best practices:
        - No punctuation
        - No articles, pronouns, etc.
        - Specific nouns and adjectives in singular form
        - Properly enclosed in parentheses
        
        Args:
            natural_query: User's natural language query
            
        Returns:
            Simplified PubMed-optimized search terms
        """
        # Create prompt for simplifying the query
        prompt = f"""
        Convert this natural language medical question into a simple, optimized PubMed search query.

        Natural language question: "{natural_query}"

        Guidelines for the optimized query:
        - Remove all punctuation
        - Remove articles, pronouns, adverbs
        - Keep only relevant nouns and adjectives
        - Use singular form for terms (unless plural is semantically necessary)
        - Don't add any tags or filters yet
        - Focus on the most specific search terms
        - Return ONLY the simplified terms, enclosed in parentheses

        Example:
        Input: "What's the relationship between gut microbiome composition and the development of food allergies in children?"
        Output: (gut microbiome food allergy children)

        Your simplified PubMed query terms:
        """
        
        try:
            # Get simplified query from AI
            self.console.print(Panel("[cyan]Optimizing your query terms...[/cyan]", border_style="blue"))
            response, _ = self.client.query(
                query=prompt,
                model=self.model,
                temperature=0.1,  # Low temperature for consistent results
                display_response=False
            )
            
            # Clean up the response to ensure proper formatting
            simplified = response.text.strip()
            
            # Ensure query is enclosed in parentheses
            if not (simplified.startswith('(') and simplified.endswith(')')):
                simplified = f"({simplified.strip('()')})"
            
            return simplified
            
        except Exception as e:
            self.log_error("Error simplifying query", e)
            # Fallback: basic cleanup
            terms = re.sub(r'[^\w\s]', '', natural_query).split()
            return f"({' '.join(terms)})"
    
    def determine_clinical_category(self, natural_query: str, simplified_query: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Determine if query is clinical and if so, which category and scope.
        
        Args:
            natural_query: User's original query
            simplified_query: Simplified PubMed terms
            
        Returns:
            Tuple of (clinical_category, filter_scope) or (None, None) if not clinical
        """
        # First, check if this is likely a clinical query
        prompt = f"""
        Determine if this medical search query is a clinical query that fits one of these categories:
        {', '.join(self.clinical_categories)}

        Natural language question: "{natural_query}"
        Simplified query terms: {simplified_query}

        If it's a clinical query, specify which ONE category it best fits into.
        If it doesn't fit any category well, state "Not a clinical query".
        
        Respond with ONLY the category name or "Not a clinical query". No explanation.
        """
        
        try:
            self.console.print(Panel("[cyan]Analyzing query type...[/cyan]", border_style="blue"))
            response, _ = self.client.query(
                query=prompt,
                model=self.model,
                temperature=0.1,
                display_response=False
            )
            
            category_response = response.text.strip()
            
            if "not a clinical query" in category_response.lower():
                # Confirm with user
                is_clinical = Confirm.ask(
                    "\n[cyan]Is your query related to clinical practice (therapy, diagnosis, prognosis, etc.)?[/cyan]",
                    default=False
                )
                
                if not is_clinical:
                    return None, None
                    
                # If user says it is clinical, let them choose category
                self.console.print("\n[yellow]Please select the clinical category that best matches your query:[/yellow]")
                for i, category in enumerate(self.clinical_categories, 1):
                    self.console.print(f"  {i}. {category}")
                
                category_choice = Prompt.ask(
                    "\n[cyan]Enter the number of your choice[/cyan]",
                    choices=[str(i) for i in range(1, len(self.clinical_categories) + 1)],
                    default="1"
                )
                
                category = self.clinical_categories[int(category_choice) - 1]
            else:
                # Check if the response matches a known category
                found = False
                for category in self.clinical_categories:
                    if category.lower() in category_response.lower():
                        found = True
                        category = category
                        break
                        
                if not found:
                    # Let user select if AI couldn't determine
                    self.console.print("\n[yellow]Please select the clinical category for your query:[/yellow]")
                    for i, category in enumerate(self.clinical_categories, 1):
                        self.console.print(f"  {i}. {category}")
                    
                    category_choice = Prompt.ask(
                        "\n[cyan]Enter the number of your choice[/cyan]",
                        choices=[str(i) for i in range(1, len(self.clinical_categories) + 1)],
                        default="1"
                    )
                    
                    category = self.clinical_categories[int(category_choice) - 1]
            
            # Now determine scope (broad vs narrow)
            self.console.print(Panel(
                f"[green]Clinical category selected: {category}[/green]\n\n"
                "[cyan]Broad filter:[/cyan] More results (higher sensitivity), but may include less relevant papers\n"
                "[cyan]Narrow filter:[/cyan] Fewer results (higher specificity), more focused on your topic",
                title="[bold]Filter Scope[/bold]",
                border_style="blue"
            ))
            
            scope_choice = Prompt.ask(
                "\n[cyan]Which filter scope would you prefer?[/cyan]",
                choices=["1", "2"],
                default="2",
                show_choices=False
            )
            
            scope = self.filter_scopes[int(scope_choice) - 1]
            
            return category, scope
            
        except Exception as e:
            self.log_error("Error determining clinical category", e)
            return None, None
    
    def select_age_group(self) -> Optional[str]:
        """
        Ask user to specify age group filter.
        
        Returns:
            PubMed filter string for selected age group, or None if any age
        """
        self.console.print("\n[yellow]Select the relevant age group for your search:[/yellow]")
        for i, age_group in enumerate(self.age_groups, 1):
            self.console.print(f"  {i}. {age_group}")
        
        choice = Prompt.ask(
            "\n[cyan]Enter the number of your choice[/cyan]",
            choices=[str(i) for i in range(1, len(self.age_groups) + 1)],
            default=str(len(self.age_groups))  # Default to "Any age"
        )
        
        age_group = self.age_groups[int(choice) - 1]
        
        if age_group == "Adults (18+)":
            return "AND (alladult[Filter])"
        elif age_group == "Aged (65+)":
            return "AND \"adult\"[MeSH Terms] AND (aged[Filter])"
        elif age_group == "Children (<18)":
            return "AND (allchild[Filter])"
        elif age_group == "Adults and children":
            return "AND (alladult[Filter] OR allchild[Filter])"
        else:  # Any age
            return None
    
    def select_time_period(self) -> Optional[str]:
        """
        Ask user to specify time period filter.
        
        Returns:
            PubMed filter string for selected time period, or None if any time
        """
        self.console.print("\n[yellow]Select the publication time period:[/yellow]")
        for i, period in enumerate(self.time_periods, 1):
            self.console.print(f"  {i}. {period}")
        
        choice = Prompt.ask(
            "\n[cyan]Enter the number of your choice[/cyan]",
            choices=[str(i) for i in range(1, len(self.time_periods) + 1)],
            default=str(len(self.time_periods))  # Default to "Any time"
        )
        
        period = self.time_periods[int(choice) - 1]
        
        if period == "Last year":
            return "AND (y_1[Filter])"
        elif period == "Last 5 years":
            return "AND (y_5[Filter])"
        elif period == "Last 10 years":
            return "AND (y_10[Filter])"
        elif period == "Custom range":
            start_year = Prompt.ask("[cyan]Enter start year[/cyan]", default="2000")
            end_year = Prompt.ask("[cyan]Enter end year[/cyan]", default="2023")
            return f"AND ({start_year}:{end_year}[pdat])"
        else:  # Any time
            return None
    
    def select_text_availability(self) -> Optional[str]:
        """
        Ask user to specify text availability filter.
        
        Returns:
            PubMed filter string for text availability, or None if all results
        """
        self.console.print("\n[yellow]Select text availability:[/yellow]")
        for i, option in enumerate(self.text_availability, 1):
            self.console.print(f"  {i}. {option}")
        
        choice = Prompt.ask(
            "\n[cyan]Enter the number of your choice[/cyan]",
            choices=[str(i) for i in range(1, len(self.text_availability) + 1)],
            default="1"  # Default to "All results"
        )
        
        option = self.text_availability[int(choice) - 1]
        
        if option == "Full text":
            return "AND (fft[Filter])"
        elif option == "Free full text":
            return "AND (ffrft[Filter])"
        elif option == "Abstract":
            return "AND (hasabstract[Filter])"
        else:  # All results
            return None
    
    def select_article_type(self) -> Optional[str]:
        """
        Ask user to specify article type filter.
        
        Returns:
            PubMed filter string for article type, or None if all types
        """
        self.console.print("\n[yellow]Select article type:[/yellow]")
        for i, article_type in enumerate(self.article_types, 1):
            self.console.print(f"  {i}. {article_type}")
        
        choice = Prompt.ask(
            "\n[cyan]Enter the number of your choice[/cyan]",
            choices=[str(i) for i in range(1, len(self.article_types) + 1)],
            default=str(len(self.article_types))  # Default to "All types"
        )
        
        article_type = self.article_types[int(choice) - 1]
        
        if article_type == "Clinical trial":
            return "AND (clinicaltrial[Filter])"
        elif article_type == "Meta-analysis":
            return "AND (meta-analysis[Filter])"
        elif article_type == "Randomized controlled trial":
            return "AND (randomizedcontrolledtrial[Filter])"
        elif article_type == "Review":
            return "AND (review[Filter])"
        elif article_type == "Systematic review":
            return "AND (systematicreview[Filter])"
        else:  # All types
            return None
    
    def select_subjects(self) -> List[str]:
        """
        Ask user to specify subject filters (humans, male, female).
        
        Returns:
            List of PubMed filter strings for selected subjects
        """
        filters = []
        
        # Humans only
        if Confirm.ask("\n[cyan]Restrict to human studies only?[/cyan]", default=True):
            filters.append("AND (humans[Filter])")
        
        # Gender filter
        self.console.print("\n[yellow]Select gender filter:[/yellow]")
        self.console.print("  1. All genders")
        self.console.print("  2. Female subjects only")
        self.console.print("  3. Male subjects only")
        
        gender_choice = Prompt.ask(
            "\n[cyan]Enter the number of your choice[/cyan]",
            choices=["1", "2", "3"],
            default="1"
        )
        
        if gender_choice == "2":
            filters.append("AND (female[Filter])")
        elif gender_choice == "3":
            filters.append("AND (male[Filter])")
        
        return filters
    
    def build_final_query(self, components: Dict[str, Any]) -> str:
        """
        Build the final PubMed query from all selected components.
        
        Args:
            components: Dictionary with all query components
            
        Returns:
            Formatted PubMed query string
        """
        query_parts = [components['base_query']]
        
        # Add clinical category if applicable
        if components['clinical_category'] and components['clinical_scope']:
            query_parts.append(
                f"AND ({components['clinical_category']}/{components['clinical_scope']}[filter])"
            )
        
        # Add other filters
        for filter_key in ['age_filter', 'time_filter', 'text_filter', 'article_filter']:
            if components.get(filter_key):
                query_parts.append(components[filter_key])
        
        # Add subject filters
        for subject_filter in components.get('subject_filters', []):
            query_parts.append(subject_filter)
        
        # Combine all parts
        final_query = " ".join(query_parts)
        
        return final_query
    
    def display_final_query(self, query: str) -> None:
        """
        Display the final query to the user.
        
        Args:
            query: The final PubMed query string
        """
        self.console.print("\n[bold green]Your optimized PubMed query:[/bold green]")
        
        self.console.print(Panel(
            query,
            title="[bold]PubMed Query[/bold]",
            border_style="green",
            padding=(1, 2)
        ))
        
        self.console.print(
            "\n[dim]Copy this query and paste it directly into PubMed's search box,[/dim]"
            "\n[dim]or use it with the PubMed Research Agent for automated searching.[/dim]"
        )
    
    def run(self) -> str:
        """
        Run the PubMed query agent workflow.
        
        Returns:
            The final formatted PubMed query string
        """
        try:
            # Display welcome message
            self.welcome()
            
            # Get natural language query from user
            natural_query = self.get_natural_language_query()
            
            # Simplify query to basic PubMed format
            base_query = self.simplify_query(natural_query)
            self.console.print(f"\n[bold]Base query terms:[/bold] {base_query}")
            
            # Check if this is a clinical query and get category
            clinical_category, clinical_scope = self.determine_clinical_category(natural_query, base_query)
            
            # Collect all query components
            components = {
                'base_query': base_query,
                'clinical_category': clinical_category,
                'clinical_scope': clinical_scope,
            }
            
            # Get age group filter
            components['age_filter'] = self.select_age_group()
            
            # Get time period filter
            components['time_filter'] = self.select_time_period()
            
            # Get text availability filter
            components['text_filter'] = self.select_text_availability()
            
            # Get article type filter
            components['article_filter'] = self.select_article_type()
            
            # Get subject filters
            components['subject_filters'] = self.select_subjects()
            
            # Build the final query
            final_query = self.build_final_query(components)
            
            # Display the query
            self.display_final_query(final_query)
            
            # Thank the user
            self.console.print("\n[bold green]Thank you for using the PubMed Query Generator![/bold green]")
            
            # Return the final query
            return final_query
            
        except Exception as e:
            self.log_error("Error in PubMed query agent", e)
            # Return a simple version of the query as fallback
            return f"({' '.join(natural_query.split()[:5])})"
            
        except KeyboardInterrupt:
            self.console.print("\n\n[yellow]PubMed query generation terminated by user.[/yellow]")
            return ""


# Create a convenience function for CLI usage
def run_pubmed_query_agent() -> str:
    """
    Run the PubMed query agent from the command line.
    
    Returns:
        The generated PubMed query string
    """
    try:
        # Create console
        console = Console()
        
        # Run the PubMed query agent
        agent = PubMedQueryAgent()
        return agent.run()
        
    except Exception as e:
        console = Console()
        console.print(f"[bold red]Fatal error: {e}[/bold red]")
        logger.critical("Fatal error", exc_info=True)
        return ""
        
    except KeyboardInterrupt:
        console = Console()
        console.print("\n[yellow]Program terminated by user.[/yellow]")
        return ""


if __name__ == "__main__":
    query = run_pubmed_query_agent()
    print(f"\nGenerated query: {query}")