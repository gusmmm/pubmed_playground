"""PubMed Central searcher using E-utilities directly."""

import os
import json
import requests
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from pathlib import Path

class PMCSearcher:
    """Class to handle PubMed Central searches using E-utilities."""
    
    def __init__(self, output_dir: str = "pmc_results", api_key: Optional[str] = None):
        """Initialize with optional API key and output directory."""
        self.base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
        self.api_key = api_key or os.getenv("PUBMED_API_KEY")
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
    def _make_request(self, endpoint: str, params: Dict) -> requests.Response:
        """Make a request to E-utilities API with proper error handling."""
        if self.api_key:
            params['api_key'] = self.api_key
            
        url = f"{self.base_url}/{endpoint}"
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response

    def search(self, query: str, max_results: int = 5, recent_days: Optional[int] = None) -> Tuple[List[str], Dict]:
        """Search PubMed Central with a query."""
        if recent_days:
            date_start = (datetime.now() - timedelta(days=recent_days)).strftime("%Y/%m/%d")
            query = f"{query} AND {date_start}:3000[edat]"
        
        params = {
            'db': 'pmc',
            'term': query,
            'retmax': max_results,
            'usehistory': 'y',
            'retmode': 'json',
            'sort': 'relevance'
        }
        
        response = self._make_request('esearch.fcgi', params)
        result = response.json()
        
        return result['esearchresult'].get('idlist', []), result['esearchresult']
    
    def get_article_details(self, pmids: List[str]) -> Dict:
        """Get detailed information for a list of PMIDs."""
        if not pmids:
            return {}
            
        params = {
            'db': 'pmc',
            'id': ','.join(pmids),
            'retmode': 'json'
        }
        
        response = self._make_request('esummary.fcgi', params)
        result = response.json()
        
        return result.get('result', {})

    def get_article_abstract(self, pmid: str) -> Optional[str]:
        """Get article abstract using efetch."""
        try:
            # First try to get the abstract directly using the abstract rettype
            params = {
                'db': 'pmc',
                'id': pmid,
                'rettype': 'abstract',
                'retmode': 'xml'
            }
            
            response = self._make_request('efetch.fcgi', params)
            
            if not response.text:
                return None
                
            # Import regex here to avoid global import
            import re
            
            # Try different patterns to extract the abstract
            
            # Pattern 1: Look for abstract section
            abstract_match = re.search(r'<abstract[^>]*>(.*?)</abstract>', response.text, re.DOTALL)
            if abstract_match:
                # Extract text from the abstract, removing XML tags
                abstract_text = re.sub(r'<[^>]+>', ' ', abstract_match.group(1))
                # Clean up whitespace
                abstract_text = re.sub(r'\s+', ' ', abstract_text).strip()
                if abstract_text and len(abstract_text) > 20:  # Ensure it's a meaningful abstract
                    return abstract_text
            
            # If that fails, try getting the full article
            params = {
                'db': 'pmc',
                'id': pmid,
                'rettype': 'full',
                'retmode': 'xml'
            }
            
            response = self._make_request('efetch.fcgi', params)
            
            if not response.text:
                return None
            
            # Pattern 2: Look for abstract-sec section (common in PMC XML)
            abstract_sec_match = re.search(r'<sec[^>]*sec-type="abstract"[^>]*>(.*?)</sec>', response.text, re.DOTALL)
            if abstract_sec_match:
                abstract_text = re.sub(r'<[^>]+>', ' ', abstract_sec_match.group(1))
                abstract_text = re.sub(r'\s+', ' ', abstract_text).strip()
                if abstract_text and len(abstract_text) > 20:
                    return abstract_text
            
            # Pattern 3: Look for abstract section again in full article
            abstract_match = re.search(r'<abstract[^>]*>(.*?)</abstract>', response.text, re.DOTALL)
            if abstract_match:
                abstract_text = re.sub(r'<[^>]+>', ' ', abstract_match.group(1))
                abstract_text = re.sub(r'\s+', ' ', abstract_text).strip()
                if abstract_text and len(abstract_text) > 20:
                    return abstract_text
            
            # Pattern 4: Look for p tags within abstract
            abstract_p_match = re.search(r'<abstract[^>]*>.*?<p>(.*?)</p>.*?</abstract>', response.text, re.DOTALL)
            if abstract_p_match:
                abstract_text = re.sub(r'<[^>]+>', ' ', abstract_p_match.group(1))
                abstract_text = re.sub(r'\s+', ' ', abstract_text).strip()
                if abstract_text and len(abstract_text) > 20:
                    return abstract_text
            
            # Pattern 5: Look for the first paragraph that might contain the abstract
            p_match = re.search(r'<p[^>]*>(.*?)</p>', response.text, re.DOTALL)
            if p_match:
                p_text = re.sub(r'<[^>]+>', ' ', p_match.group(1))
                p_text = re.sub(r'\s+', ' ', p_text).strip()
                if p_text and len(p_text) > 50:  # Longer threshold for paragraphs
                    return p_text
            
            # Try a different approach - use the summary endpoint
            try:
                params = {
                    'db': 'pmc',
                    'id': pmid,
                    'retmode': 'xml'
                }
                
                summary_response = self._make_request('esummary.fcgi', params)
                
                # Look for description or caption that might contain abstract info
                desc_match = re.search(r'<Item Name="Description"[^>]*>(.*?)</Item>', summary_response.text, re.DOTALL)
                if desc_match:
                    desc_text = desc_match.group(1).strip()
                    if desc_text and len(desc_text) > 50:
                        return desc_text
            except Exception:
                pass  # Silently continue if summary approach fails
                
            return "Abstract not available"
            
        except Exception as e:
            print(f"Error retrieving abstract: {e}")
            return None

    def format_authors(self, authors_data: List[Dict]) -> Tuple[Optional[str], List[str]]:
        """Format authors into first author and co-authors."""
        if not authors_data:
            return None, []
            
        try:
            authors = []
            for author in authors_data:
                if isinstance(author, dict):
                    name = author.get('name', '')
                    if name:
                        authors.append(name)
                elif isinstance(author, str):
                    authors.append(author)
            
            return authors[0] if authors else None, authors[1:] if len(authors) > 1 else []
        except Exception:
            return None, []

    def save_search_results(self, query: str, metadata: Dict, articles: List[Dict]) -> str:
        """Save search results to JSON file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results = {
            "query": query,
            "search_date": datetime.now().isoformat(),
            "metadata": metadata,
            "articles": articles
        }
        
        output_file = self.output_dir / f"pmc_search_{timestamp}.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
            
        return str(output_file)

def demo_pmc_search():
    """Demonstrate PMC searching capabilities."""
    
    searcher = PMCSearcher()
    
    # More specific query for fMRI articles
    query = '("fMRI"[Title] OR "functional magnetic resonance imaging"[Title]) AND "open access"[filter]'
    
    print(f"\nExecuting query: {query}")
    print("Searching PubMed Central for recent open access articles...")
    
    try:
        # Perform the search with last 90 days filter
        pmids, metadata = searcher.search(query, max_results=5, recent_days=90)
        
        total_found = metadata.get('count', '0')
        print(f"\nFound {total_found} total results")
        
        if total_found == '0':
            print("\nTrying broader search without date restriction...")
            pmids, metadata = searcher.search(query, max_results=5)
            print(f"Found {metadata.get('count', '0')} total results with broader search")
        
        print(f"Retrieved {len(pmids)} articles\n")
        
        if not pmids:
            print("No articles found matching the criteria.")
            return
            
        # Get article details and prepare for JSON storage
        articles_data = []
        print("Retrieved articles:")
        
        for pmid in pmids:
            # Get basic article details
            article_details = searcher.get_article_details(pmids).get(pmid, {})
            
            # Get and format authors
            first_author, co_authors = searcher.format_authors(article_details.get('authors', []))
            
            # Get abstract
            abstract = searcher.get_article_abstract(pmid)
            
            # Get full text links if available
            full_text_links = []
            if 'articleids' in article_details:
                for id_info in article_details['articleids']:
                    if id_info.get('idtype') == 'pmcid':
                        full_text_links.append(f"https://www.ncbi.nlm.nih.gov/pmc/articles/PMC{id_info['value']}")
                    elif id_info.get('idtype') == 'doi':
                        full_text_links.append(f"https://doi.org/{id_info['value']}")
            
            # Prepare article data
            article_data = {
                'pmcid': pmid,
                'title': article_details.get('title', 'Not available'),
                'first_author': first_author,
                'co_authors': co_authors,
                'journal': article_details.get('fulljournalname', 'Not available'),
                'publication_date': article_details.get('pubdate', 'Not available'),
                'abstract': abstract,
                'full_text_links': full_text_links,
                'doi': next((id_info['value'] for id_info in article_details.get('articleids', []) 
                           if id_info.get('idtype') == 'doi'), 'Not available')
            }
            
            articles_data.append(article_data)
            
            # Print article details
            print(f"\nPMC ID: {pmid}")
            print(f"Title: {article_data['title']}")
            print(f"First Author: {article_data['first_author']}")
            if co_authors:
                print(f"Co-Authors: {', '.join(co_authors)}")
            print(f"Journal: {article_data['journal']}")
            print(f"Publication Date: {article_data['publication_date']}")
            if abstract:
                print(f"Abstract: {abstract[:200]}...")
            if full_text_links:
                print("Full Text Links:")
                for link in full_text_links:
                    print(f"- {link}")
            print(f"DOI: {article_data['doi']}")
        
        # Save results to JSON
        output_file = searcher.save_search_results(query, metadata, articles_data)
        print(f"\nResults saved to: {output_file}")
        
    except requests.exceptions.RequestException as e:
        print(f"Error making request: {e}")
    except KeyError as e:
        print(f"Error parsing response: {e}")
    except Exception as e:
        print(f"Unexpected error: {str(e)}")

if __name__ == "__main__":
    print("🔍 Testing direct PMC search functionality...")
    demo_pmc_search()
