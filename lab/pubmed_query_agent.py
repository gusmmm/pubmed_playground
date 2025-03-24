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
                f"AND ({components['clinical_category']}/{components['clinical_scope']}[Filter])"
                # Fixed: Changed [filter] to [Filter] to ensure proper capitalization
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
            
            # Analyze the query for implicit parameters
            detected_params = self.analyze_natural_query(natural_query)
            
            # Simplify query to basic PubMed format
            base_query = self.simplify_query(natural_query)
            self.console.print(f"\n[bold]Base query terms:[/bold] {base_query}")
            
            # Track terms to remove from base query
            terms_to_remove = []
            
            # Check if we detected the clinical category with high confidence
            clinical_category = None
            clinical_scope = None
            
            if detected_params and 'clinical_category' in detected_params:
                param = detected_params['clinical_category']
                if self.should_use_detected_parameter(param):
                    # Map the detected category to one of our categories
                    detected_value = param['value'].capitalize()
                    for category in self.clinical_categories:
                        if category.lower() == detected_value.lower():
                            clinical_category = category
                            clinical_scope = "Narrow"  # Default to narrow scope for more specific results
                            
                            # Add terms to remove based on category
                            if category.lower() == "therapy":
                                terms_to_remove.extend(["treatment", "therapy", "intervention"])
                            elif category.lower() == "diagnosis":
                                terms_to_remove.extend(["diagnosis", "diagnostic"])
                            elif category.lower() == "etiology":
                                terms_to_remove.extend(["cause", "etiology", "factor"])
                            elif category.lower() == "prognosis":
                                terms_to_remove.extend(["prognosis", "outcome", "survival"])
                            
                            # Inform the user about the automatic selection
                            self.console.print(f"[green]Detected clinical category:[/green] {clinical_category} (Narrow scope)")
                            
                            # Offer chance to change
                            if not Confirm.ask("\n[cyan]Use this clinical category?[/cyan]", default=True):
                                clinical_category = None
                                terms_to_remove = [t for t in terms_to_remove if t not in ["treatment", "therapy", "intervention", 
                                                                                           "diagnosis", "diagnostic", "cause", "etiology", 
                                                                                           "factor", "prognosis", "outcome", "survival"]]
                            break
            
            # If not detected or user rejected, ask explicitly
            if not clinical_category:
                clinical_category, clinical_scope = self.determine_clinical_category(natural_query, base_query)
                
                # If user selected a category, add terms to remove
                if clinical_category:
                    if clinical_category.lower() == "therapy":
                        terms_to_remove.extend(["treatment", "therapy", "intervention"])
                    elif clinical_category.lower() == "diagnosis":
                        terms_to_remove.extend(["diagnosis", "diagnostic"])
                    elif clinical_category.lower() == "etiology":
                        terms_to_remove.extend(["cause", "etiology", "factor"])
                    elif clinical_category.lower() == "prognosis":
                        terms_to_remove.extend(["prognosis", "outcome", "survival"])
            
            # Age group - check if detected first
            age_filter = None
            if detected_params and 'age_group' in detected_params:
                param = detected_params['age_group']
                if self.should_use_detected_parameter(param):
                    detected_value = param['value'].lower()
                    
                    if "adult" in detected_value and not "elder" in detected_value:
                        age_filter = "AND (alladult[Filter])"
                        terms_to_remove.extend(["adult", "adults"])
                        self.console.print("[green]Detected age group:[/green] Adults (18+)")
                    elif "elder" in detected_value or "aged" in detected_value:
                        age_filter = "AND \"adult\"[MeSH Terms] AND (aged[Filter])"
                        terms_to_remove.extend(["elderly", "aged", "elder", "older"])
                        self.console.print("[green]Detected age group:[/green] Elderly (65+)")
                    elif "child" in detected_value:
                        age_filter = "AND (allchild[Filter])"
                        terms_to_remove.extend(["child", "children", "pediatric"])
                        self.console.print("[green]Detected age group:[/green] Children (<18)")
                    
                    # Offer chance to change
                    if age_filter and not Confirm.ask("\n[cyan]Use this age filter?[/cyan]", default=True):
                        age_filter = None
                        # Remove the age terms from terms_to_remove
                        terms_to_remove = [t for t in terms_to_remove if t not in 
                                         ["adult", "adults", "elderly", "aged", "elder", "older", "child", "children", "pediatric"]]
            
            # Time period - check if detected first
            time_filter = None
            if detected_params and 'time_period' in detected_params:
                param = detected_params['time_period']
                if self.should_use_detected_parameter(param):
                    detected_value = param['value'].lower()
                    
                    if "recent" in detected_value or "last 5" in detected_value:
                        time_filter = "AND (y_5[Filter])"
                        terms_to_remove.extend(["recent", "new", "latest", "last"])
                        self.console.print("[green]Detected time period:[/green] Last 5 years")
                    elif "last year" in detected_value or "past year" in detected_value:
                        time_filter = "AND (y_1[Filter])"
                        terms_to_remove.extend(["recent", "new", "latest", "last", "year"])
                        self.console.print("[green]Detected time period:[/green] Last year")
                    elif "last 10" in detected_value or "past 10" in detected_value:
                        time_filter = "AND (y_10[Filter])"
                        terms_to_remove.extend(["decade", "ten", "years"])
                        self.console.print("[green]Detected time period:[/green] Last 10 years")
                    
                    # Offer chance to change
                    if time_filter and not Confirm.ask("\n[cyan]Use this time period?[/cyan]", default=True):
                        time_filter = None
                        # Remove the time terms from terms_to_remove
                        terms_to_remove = [t for t in terms_to_remove if t not in 
                                         ["recent", "new", "latest", "last", "year", "decade", "ten", "years"]]
                        
            # Article type - check if detected
            article_filter = None
            if detected_params and 'article_type' in detected_params:
                param = detected_params['article_type']
                if self.should_use_detected_parameter(param):
                    detected_value = param['value'].lower()
                    
                    if "clinical trial" in detected_value:
                        article_filter = "AND (clinicaltrial[Filter])"
                        terms_to_remove.extend(["trial", "trials", "clinical"])
                        self.console.print("[green]Detected article type:[/green] Clinical trial")
                    elif "meta" in detected_value and "analysis" in detected_value:
                        article_filter = "AND (meta-analysis[Filter])"
                        terms_to_remove.extend(["meta", "analysis", "meta-analysis"])
                        self.console.print("[green]Detected article type:[/green] Meta-analysis")
                    elif "review" in detected_value and "systematic" in detected_value:
                        article_filter = "AND (systematicreview[Filter])"
                        terms_to_remove.extend(["review", "systematic"])
                        self.console.print("[green]Detected article type:[/green] Systematic review")
                    elif "review" in detected_value:
                        article_filter = "AND (review[Filter])"
                        terms_to_remove.extend(["review", "overview"])
                        self.console.print("[green]Detected article type:[/green] Review")
                    elif "rct" in detected_value or "randomized" in detected_value:
                        article_filter = "AND (randomizedcontrolledtrial[Filter])"
                        terms_to_remove.extend(["rct", "randomized", "controlled"])
                        self.console.print("[green]Detected article type:[/green] Randomized controlled trial")
                    
                    # Offer chance to change
                    if article_filter and not Confirm.ask("\n[cyan]Use this article type?[/cyan]", default=True):
                        article_filter = None
                        # Remove the article type terms from terms_to_remove
                        terms_to_remove = [t for t in terms_to_remove if t not in 
                                         ["trial", "trials", "clinical", "meta", "analysis", "meta-analysis", 
                                          "review", "systematic", "overview", "rct", "randomized", "controlled"]]
                        
            # Now clean up the base query by removing redundant terms
            cleaned_base_query = self.remove_detected_parameters_from_query(base_query, terms_to_remove)
            
            if cleaned_base_query != base_query:
                self.console.print(f"\n[bold]Refined query terms:[/bold] {cleaned_base_query}")
                self.console.print("[dim](Removed terms that are handled by filters)[/dim]")
                    
            # Collect all query components
            components = {
                'base_query': cleaned_base_query,  # Use the cleaned query
                'clinical_category': clinical_category,
                'clinical_scope': clinical_scope,
            }
            
            # Continue with the rest of the method as before
            
            # Age filter (already detected above)
            components['age_filter'] = age_filter or self.select_age_group()
            
            # Time filter (already detected above)
            components['time_filter'] = time_filter or self.select_time_period()
            
            # Article filter (already detected above)
            components['article_filter'] = article_filter or self.select_article_type()
            
            # Text availability - always ask explicitly
            components['text_filter'] = self.select_text_availability()
            
            # Subject filters - check if detected
            subject_filters = []
            
            # Human studies
            if detected_params and 'humans_only' in detected_params:
                param = detected_params['humans_only']
                if self.should_use_detected_parameter(param):
                    detected_value = param['value'].lower()
                    if detected_value == "yes":
                        subject_filters.append("AND (humans[Filter])")
                        self.console.print("[green]Detected subject filter:[/green] Human studies only")
            
            # Gender filter
            if detected_params and 'gender' in detected_params:
                param = detected_params['gender']
                if self.should_use_detected_parameter(param):
                    detected_value = param['value'].lower()
                    if "female" in detected_value:
                        subject_filters.append("AND (female[Filter])")
                        self.console.print("[green]Detected gender filter:[/green] Female subjects")
                    elif "male" in detected_value:
                        subject_filters.append("AND (male[Filter])")
                        self.console.print("[green]Detected gender filter:[/green] Male subjects")
            
            # If any filters were detected, ask if user wants to keep them
            if subject_filters:
                if Confirm.ask("\n[cyan]Use these subject filters?[/cyan]", default=True):
                    components['subject_filters'] = subject_filters
                else:
                    # Ask explicitly if the user rejected the detected filters
                    components['subject_filters'] = self.select_subjects()
            else:
                # Ask explicitly if nothing was detected
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
    
    def analyze_natural_query(self, natural_query: str) -> Dict[str, Any]:
        """
        Analyze the natural language query to extract implicit parameters.
        
        Args:
            natural_query: User's natural language query
            
        Returns:
            Dictionary of detected parameters with confidence scores
        """
        # Create a prompt to analyze the query with EXPLICIT formatting instructions
        prompt = f"""
        Analyze this medical literature search query and extract key search parameters.
        Query: "{natural_query}"
        
        Identify the following elements and output ONLY a valid JSON object:

        1. Clinical category: (Therapy, Diagnosis, Etiology, Prognosis, or null)
        2. Age group: (Adults, Children, Elderly, or null)
        3. Time period: (Recent, Last year, Last 5 years, Last 10 years, or null)
        4. Article types: (Review, Clinical trial, Meta-analysis, etc., or null)
        5. Gender focus: (Male, Female, or null)
        6. Human studies only: (Yes, No, or null)
        7. Confidence: (High, Medium, Low) for each detected parameter

        You must output a valid JSON object like this - with no additional text before or after:

        {{
          "clinical_category": {{
            "value": "Therapy",
            "confidence": "High"
          }},
          "age_group": {{
            "value": "Adults",
            "confidence": "High"
          }},
          "time_period": {{
            "value": "Recent",
            "confidence": "Medium"
          }},
          "article_type": {{
            "value": "Clinical trial",
            "confidence": "Low"
          }},
          "gender": {{
            "value": null,
            "confidence": "Low"
          }},
          "humans_only": {{
            "value": "Yes",
            "confidence": "Medium"
          }}
        }}
        
        Output ONLY the JSON object with no explanations or additional text.
        """
        
        try:
            # Query the AI
            self.console.print(Panel("[cyan]Analyzing your query for parameters...[/cyan]", border_style="blue"))
            response, _ = self.client.query(
                query=prompt,
                model=self.model,
                temperature=0.1,
                display_response=False
            )
            
            # Clean up the response to ensure it's valid JSON
            response_text = response.text.strip()
            
            # Remove any markdown code block markers
            response_text = re.sub(r'^```json\s*', '', response_text)
            response_text = re.sub(r'\s*```$', '', response_text)
            
            # Remove any extraneous text before or after the JSON object
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                response_text = response_text[json_start:json_end]
            
            # Parse the JSON response
            import json
            try:
                detected_params = json.loads(response_text)
                return detected_params
            except json.JSONDecodeError as e:
                self.console.print(f"[yellow]Warning: Could not parse AI response as JSON: {e}[/yellow]")
                self.log_error("JSON parsing error", e)
                
                # Debug information
                self.console.print(f"[dim]Response text: {response_text[:100]}...[/dim]")
                
                # Return empty dict so the rest of the function works
                return {}
            
        except Exception as e:
            self.log_error("Error analyzing natural query", e)
            return {}
        
    def should_use_detected_parameter(self, param: Dict[str, str]) -> bool:
        """
        Determine if a detected parameter should be used automatically.
        
        Args:
            param: Parameter dict with value and confidence
            
        Returns:
            True if the parameter should be used automatically
        """
        # Only use parameters with high confidence
        if not param or 'value' not in param or 'confidence' not in param:
            return False
            
        if param['value'] is None or param['value'] == "null":
            return False
            
        return param['confidence'].lower() == "high"

    def remove_detected_parameters_from_query(self, base_query: str, detected_terms: List[str]) -> str:
        """
        Remove redundant terms from base query that are already handled by filters.
        
        Args:
            base_query: The original simplified query string
            detected_terms: List of terms to remove
            
        Returns:
            Cleaned query without redundant filter terms
        """
        if not detected_terms or not base_query:
            return base_query
            
        # Remove parentheses for processing
        query_text = base_query.strip('()')
        query_terms = query_text.split()
        
        # Create a list of normalized terms for case-insensitive comparison
        normalized_terms = [term.lower() for term in query_terms]
        
        # Create a list to track which terms to keep
        keep_terms = [True] * len(query_terms)
        
        # For each detected term, mark corresponding query terms for removal
        for term in detected_terms:
            term_lower = term.lower()
            # Handle both singular and plural forms
            term_variants = [term_lower, f"{term_lower}s", f"{term_lower}es"]
            
            for i, norm_term in enumerate(normalized_terms):
                if norm_term in term_variants or any(variant in norm_term for variant in term_variants):
                    keep_terms[i] = False
        
        # Rebuild query with only the terms to keep
        cleaned_terms = [term for i, term in enumerate(query_terms) if keep_terms[i]]
        
        # If we removed everything, keep at least the most important terms
        if not cleaned_terms and query_terms:
            # Keep nouns and medical terms which are likely the core topic
            for i, term in enumerate(query_terms):
                if len(term) > 4 and term.lower() not in ['adult', 'child', 'recent', 'study', 'paper', 'review', 
                                                         'treatment', 'therapy', 'diagnosis', 'year', 'years']:
                    cleaned_terms.append(term)
        
        # If still empty, keep the original terms as fallback
        if not cleaned_terms:
            cleaned_terms = query_terms
        
        # Return with parentheses
        return f"({' '.join(cleaned_terms)})"


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