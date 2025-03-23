"""
Research Agents for PubMed Playground

This package provides specialized agents for interacting with scientific literature
and research databases like PubMed.
"""

from .base_agent import BaseAgent

# Don't import PubMedResearchAgent directly here to avoid circular imports
# Instead, provide a function to get it when needed

def get_pubmed_agent():
    """Get the PubMed research agent class."""
    from .pubmed_agent import PubMedResearchAgent
    return PubMedResearchAgent

def run_pubmed_agent():
    """Run the PubMed research agent from the command line."""
    from .pubmed_agent import run_pubmed_agent as _run_agent
    _run_agent()

__all__ = ['BaseAgent', 'get_pubmed_agent', 'run_pubmed_agent']

"""
If you're using this code in other parts of your project, make sure to import the agent like this:"

from utils.agents import get_pubmed_agent
PubMedResearchAgent = get_pubmed_agent()

# Then use it
agent = PubMedResearchAgent()

"""

