"""PubMed and PMC searcher using E-utilities directly."""

import os
import json
import requests
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from pathlib import Path
from time import sleep

class PubmedSearcher:
    """Class to handle PubMed/PMC searches using E-utilities."""
    
    def __init__(self, output_dir: str = "pubmed_results", api_key: Optional[str] = None, use_pmc: bool = False):
        """Initialize with optional API key and output directory.
        
        Args:
            output_dir: Directory to save results
            api_key: NCBI API key for higher rate limits
            use_pmc: If True, search PMC instead of PubMed
        """
        self.base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
        self.api_key = api_key or os.getenv("PUBMED_API_KEY")
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.db = "pmc" if use_pmc else "pubmed"
        # Rate limiting settings (with API key: 10/sec, without: 3/sec)
        self.requests_per_second = 10 if self.api_key else 3
        self.last_request_time = 0
        
    def _make_request(self, endpoint: str, params: Dict) -> requests.Response:
        """Make a request to E-utilities API with proper error handling and rate limiting."""
        # Add API key if available
        if self.api_key:
            params['api_key'] = self.api_key
            
        # Apply rate limiting
        current_time = datetime.now().timestamp()
        time_since_last_request = current_time - self.last_request_time
        if time_since_last_request < 1/self.requests_per_second:
            sleep_time = 1/self.requests_per_second - time_since_last_request
            sleep(sleep_time)
            
        url = f"{self.base_url}/{endpoint}"
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            self.last_request_time = datetime.now().timestamp()
            return response
        except requests.exceptions.RequestException as e:
            if response.status_code == 429:  # Too Many Requests
                print("Rate limit exceeded. Waiting before retrying...")
                sleep(2)  # Wait 2 seconds before retry
                return self._make_request(endpoint, params)  # Retry the request
            raise

    def search(self, query: str, max_results: int = 5, recent_days: Optional[int] = None) -> Tuple[List[str], Dict]:
        """Search PubMed/PMC with a query."""
        if recent_days:
            date_start = (datetime.now() - timedelta(days=recent_days)).strftime("%Y/%m/%d")
            query = f"{query} AND {date_start}:3000[edat]"
        
        params = {
            'db': self.db,
            'term': query,
            'retmax': max_results,
            'usehistory': 'y',
            'retmode': 'json',
            'sort': 'relevance'
        }
        
        response = self._make_request('esearch.fcgi', params)
        result = response.json()
        
        return result['esearchresult'].get('idlist', []), result['esearchresult']
    
    def get_article_details(self, ids: List[str]) -> Dict:
        """Get detailed information for a list of IDs (PMIDs or PMCIDs)."""
        if not ids:
            return {}
            
        params = {
            'db': self.db,
            'id': ','.join(ids),
            'retmode': 'json'
        }
        
        response = self._make_request('esummary.fcgi', params)
        result = response.json()
        
        return result.get('result', {})

    def get_article_abstract(self, article_id: str) -> Optional[str]:
        """Get article abstract using efetch."""
        try:
            # First try to get the abstract directly using the abstract rettype
            params = {
                'db': self.db,
                'id': article_id,
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
                'db': self.db,
                'id': article_id,
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
                    
            # If still no abstract found and we're in PubMed, try medline format
            if self.db == 'pubmed':
                params = {
                    'db': self.db,
                    'id': article_id,
                    'rettype': 'medline',
                    'retmode': 'text'
                }
                
                response = self._make_request('efetch.fcgi', params)
                
                if response.text:
                    # Look for AB field in MEDLINE format
                    medline_match = re.search(r'AB\s+-\s+(.*?)(?:\n\n|\Z)', response.text, re.DOTALL)
                    if medline_match:
                        abstract_text = re.sub(r'\s+', ' ', medline_match.group(1)).strip()
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
                    'db': self.db,
                    'id': article_id,
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
        
        output_file = self.output_dir / f"{self.db}_search_{timestamp}.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
            
        return str(output_file)

def demo_search():
    """Demonstrate PubMed/PMC searching capabilities."""
    
    # Create searcher for PubMed (not PMC)
    searcher = PubmedSearcher(use_pmc=False)
    
    # Example query
    query = "suzetrigine"
    
    print(f"\nExecuting query: {query}")
    print("Searching PubMed for articles...")
    
    try:
        # Perform the search
        ids, metadata = searcher.search(query, max_results=5)
        
        total_found = metadata.get('count', '0')
        print(f"\nFound {total_found} total results")
        
        print(f"Retrieved {len(ids)} articles\n")
        
        if not ids:
            print("No articles found matching the criteria.")
            return
            
        # Get article details and prepare for JSON storage
        articles_data = []
        print("Retrieved articles:")
        
        # Get details for all articles at once to reduce API calls
        articles_details = searcher.get_article_details(ids)
        
        for article_id in ids:
            # Get article details
            article_details = articles_details.get(article_id, {})
            
            # Get and format authors
            first_author, co_authors = searcher.format_authors(article_details.get('authors', []))
            
            # Get abstract with delay between requests
            abstract = searcher.get_article_abstract(article_id)
            
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
                'id': article_id,
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
            print(f"\nArticle ID: {article_id}")
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
    print("🔍 Testing PubMed search functionality...")
    demo_search()
