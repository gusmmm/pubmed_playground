"""
PubmedSearcher: A class for interacting with PubMed and PMC databases via E-utilities API.

This module provides a comprehensive interface for searching PubMed and PMC,
retrieving article metadata, abstracts, MeSH terms, keywords, and more.
"""

import os
import json
import re
import requests
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from pathlib import Path
from time import sleep


class PubmedSearcher:
    """
    Class to handle PubMed/PMC searches using NCBI's E-utilities API.
    
    This class provides methods for searching PubMed/PMC, retrieving article details,
    extracting abstracts, MeSH terms, keywords, and saving results.
    
    Attributes:
        base_url: Base URL for NCBI's E-utilities API
        api_key: API key for higher rate limits
        output_dir: Directory to save search results
        db: Database to search (pubmed or pmc)
        requests_per_second: Rate limiting for API requests
    """
    
    def __init__(self, output_dir: str = "pubmed_results", api_key: Optional[str] = None, use_pmc: bool = False):
        """
        Initialize the PubmedSearcher with configuration options.
        
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
    
    # =========================================================================
    # Core API Interaction Methods
    # =========================================================================
    
    def _make_request(self, endpoint: str, params: Dict) -> requests.Response:
        """
        Make a request to E-utilities API with error handling and rate limiting.
        
        Args:
            endpoint: API endpoint (e.g., 'esearch.fcgi')
            params: Dictionary of query parameters
            
        Returns:
            Response object from requests library
            
        Raises:
            RequestException: If the API request fails
        """
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
            if hasattr(e, 'response') and e.response and e.response.status_code == 429:  # Too Many Requests
                print("Rate limit exceeded. Waiting before retrying...")
                sleep(2)  # Wait 2 seconds before retry
                return self._make_request(endpoint, params)  # Retry the request
            raise
    
    # =========================================================================
    # Search and Retrieval Methods
    # =========================================================================
    
    def search(self, query: str, max_results: int = 5, recent_days: Optional[int] = None, 
               sort: str = "relevance") -> Tuple[List[str], Dict]:
        """
        Search PubMed/PMC with a query.
        
        Args:
            query: Search query string
            max_results: Maximum number of results to return
            recent_days: If set, limit to articles from last N days
            sort: Sort order - options: "relevance" (default), "pub_date" (most recent),
                  "first_author", "journal", "title"
                  
        Returns:
            Tuple of (list of article IDs, search metadata)
        """
        if recent_days:
            date_start = (datetime.now() - timedelta(days=recent_days)).strftime("%Y/%m/%d")
            query = f"{query} AND {date_start}:3000[edat]"
        
        # Map sort options to API parameters
        sort_options = {
            "relevance": "relevance",
            "pub_date": "date",
            "first_author": "author",
            "journal": "journal",
            "title": "title"
        }
        
        # Default to relevance if invalid sort option provided
        sort_param = sort_options.get(sort.lower(), "relevance")
        
        params = {
            'db': self.db,
            'term': query,
            'retmax': max_results,
            'usehistory': 'y',
            'retmode': 'json',
            'sort': sort_param
        }
        
        response = self._make_request('esearch.fcgi', params)
        result = response.json()
        
        return result['esearchresult'].get('idlist', []), result['esearchresult']
    
    def get_article_details(self, ids: List[str]) -> Dict:
        """
        Get detailed information for a list of article IDs.
        
        Args:
            ids: List of PubMed IDs (PMIDs) or PMC IDs
            
        Returns:
            Dictionary of article details indexed by article ID
        """
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
        """
        Get article abstract using multiple fallback methods.
        
        Args:
            article_id: PubMed ID (PMID) or PMC ID
            
        Returns:
            Abstract text or None if not available
        """
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
            
            # Try alternative methods if first approach fails
            alternative_methods = [
                self._get_abstract_from_full_xml,
                self._get_abstract_from_medline,
                self._get_abstract_from_summary
            ]
            
            for method in alternative_methods:
                abstract = method(article_id)
                if abstract:
                    return abstract
                    
            return "Abstract not available"
            
        except Exception as e:
            print(f"Error retrieving abstract: {e}")
            return None
            
    def _get_abstract_from_full_xml(self, article_id: str) -> Optional[str]:
        """
        Try to extract abstract from full article XML.
        
        Args:
            article_id: PubMed ID (PMID) or PMC ID
            
        Returns:
            Abstract text or None if not found
        """
        try:
            params = {
                'db': self.db,
                'id': article_id,
                'rettype': 'full',
                'retmode': 'xml'
            }
            
            response = self._make_request('efetch.fcgi', params)
            
            if not response.text:
                return None
                
            # Look for abstract-sec section (common in PMC XML)
            abstract_sec_match = re.search(r'<sec[^>]*sec-type="abstract"[^>]*>(.*?)</sec>', response.text, re.DOTALL)
            if abstract_sec_match:
                abstract_text = re.sub(r'<[^>]+>', ' ', abstract_sec_match.group(1))
                abstract_text = re.sub(r'\s+', ' ', abstract_text).strip()
                if abstract_text and len(abstract_text) > 20:
                    return abstract_text
                    
            # Look for abstract section again in full article
            abstract_match = re.search(r'<abstract[^>]*>(.*?)</abstract>', response.text, re.DOTALL)
            if abstract_match:
                abstract_text = re.sub(r'<[^>]+>', ' ', abstract_match.group(1))
                abstract_text = re.sub(r'\s+', ' ', abstract_text).strip()
                if abstract_text and len(abstract_text) > 20:
                    return abstract_text
                    
            # Look for p tags within abstract
            abstract_p_match = re.search(r'<abstract[^>]*>.*?<p>(.*?)</p>.*?</abstract>', response.text, re.DOTALL)
            if abstract_p_match:
                abstract_text = re.sub(r'<[^>]+>', ' ', abstract_p_match.group(1))
                abstract_text = re.sub(r'\s+', ' ', abstract_text).strip()
                if abstract_text and len(abstract_text) > 20:
                    return abstract_text
                    
            # Look for the first paragraph that might contain the abstract
            p_match = re.search(r'<p[^>]*>(.*?)</p>', response.text, re.DOTALL)
            if p_match:
                p_text = re.sub(r'<[^>]+>', ' ', p_match.group(1))
                p_text = re.sub(r'\s+', ' ', p_text).strip()
                if p_text and len(p_text) > 50:  # Longer threshold for paragraphs
                    return p_text
                    
            return None
            
        except Exception:
            return None
            
    def _get_abstract_from_medline(self, article_id: str) -> Optional[str]:
        """
        Try to extract abstract from MEDLINE format.
        
        Args:
            article_id: PubMed ID (PMID) or PMC ID
            
        Returns:
            Abstract text or None if not found
        """
        if self.db != 'pubmed':
            return None
            
        try:
            params = {
                'db': 'pubmed',
                'id': article_id,
                'rettype': 'medline',
                'retmode': 'text'
            }
            
            response = self._make_request('efetch.fcgi', params)
            
            if not response.text:
                return None
                
            # Look for AB field in MEDLINE format
            medline_match = re.search(r'AB\s+-\s+(.*?)(?:\n\n|\Z)', response.text, re.DOTALL)
            if medline_match:
                abstract_text = re.sub(r'\s+', ' ', medline_match.group(1)).strip()
                if abstract_text and len(abstract_text) > 20:
                    return abstract_text
                    
            return None
            
        except Exception:
            return None
            
    def _get_abstract_from_summary(self, article_id: str) -> Optional[str]:
        """
        Try to extract abstract from summary endpoint.
        
        Args:
            article_id: PubMed ID (PMID) or PMC ID
            
        Returns:
            Abstract text or None if not found
        """
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
                    
            return None
            
        except Exception:
            return None
    
    # =========================================================================
    # Data Extraction and Formatting Methods
    # =========================================================================
    
    def format_authors(self, authors_data: List[Dict]) -> Tuple[Optional[str], List[str]]:
        """
        Format authors into first author and co-authors.
        
        Args:
            authors_data: List of author data (dictionaries or strings)
            
        Returns:
            Tuple of (first author name, list of co-author names)
        """
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

    def extract_mesh_terms(self, article_details: Dict) -> List[str]:
        """
        Extract MeSH terms from article details.
        
        Args:
            article_details: Dictionary of article details
            
        Returns:
            List of MeSH terms
        """
        mesh_terms = []
        
        # Try to get MeSH terms from the details if available
        if 'meshheadinglist' in article_details and article_details['meshheadinglist']:
            mesh_list = article_details['meshheadinglist']
            for mesh_item in mesh_list:
                if isinstance(mesh_item, dict) and 'name' in mesh_item:
                    mesh_terms.append(mesh_item['name'])
        
        # If empty and we have an article ID, try to get from XML
        if not mesh_terms and 'uid' in article_details:
            article_id = article_details['uid']
            try:
                params = {
                    'db': self.db,
                    'id': article_id,
                    'retmode': 'xml'
                }
                
                response = self._make_request('efetch.fcgi', params)
                
                if response.text:
                    # Extract MeshHeading elements from XML
                    mesh_matches = re.findall(r'<DescriptorName[^>]*>([^<]+)</DescriptorName>', response.text)
                    mesh_terms.extend([term.strip() for term in mesh_matches if term.strip()])
            except Exception as e:
                print(f"Error fetching MeSH terms from XML: {e}")
        
        return mesh_terms

    def extract_keywords(self, article_details: Dict) -> List[str]:
        """
        Extract keywords from article details.
        
        Args:
            article_details: Dictionary of article details
            
        Returns:
            List of keywords
        """
        keywords = []
        
        # Try to get keywords from the details if available
        if 'keywordlist' in article_details and article_details['keywordlist']:
            keyword_data = article_details['keywordlist']
            
            if isinstance(keyword_data, list):
                for keyword in keyword_data:
                    if isinstance(keyword, str):
                        keywords.append(keyword)
                    elif isinstance(keyword, dict) and 'keyword' in keyword:
                        keywords.append(keyword['keyword'])
            elif isinstance(keyword_data, dict) and 'keywords' in keyword_data:
                for keyword in keyword_data['keywords']:
                    if isinstance(keyword, str):
                        keywords.append(keyword)
                    elif isinstance(keyword, dict) and 'keyword' in keyword:
                        keywords.append(keyword['keyword'])
        
        # If empty and we have an article ID, try to get from XML
        if not keywords and 'uid' in article_details:
            article_id = article_details['uid']
            try:
                params = {
                    'db': self.db,
                    'id': article_id,
                    'retmode': 'xml'
                }
                
                response = self._make_request('efetch.fcgi', params)
                
                if response.text:
                    # Extract Keyword elements from XML
                    keyword_matches = re.findall(r'<Keyword[^>]*>([^<]+)</Keyword>', response.text)
                    keywords.extend([kw.strip() for kw in keyword_matches if kw.strip()])
            except Exception as e:
                print(f"Error fetching keywords from XML: {e}")
        
        return keywords
    
    # =========================================================================
    # Output and Storage Methods
    # =========================================================================

    def save_search_results(self, query: str, metadata: Dict, articles: List[Dict]) -> str:
        """
        Save search results to JSON file.
        
        Args:
            query: Original search query
            metadata: Search metadata
            articles: List of article data dictionaries
            
        Returns:
            Path to the saved file
        """
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
    
    # =========================================================================
    # Debugging and Development Methods
    # =========================================================================

    def debug_article_structure(self, article_id: str) -> Optional[Dict]:
        """
        Debug the structure of an article response.
        
        Args:
            article_id: PubMed ID (PMID) or PMC ID
            
        Returns:
            Article data dictionary or None if not found
        """
        try:
            params = {
                'db': self.db,
                'id': article_id,
                'retmode': 'json'
            }
            
            response = self._make_request('esummary.fcgi', params)
            result = response.json()
            
            if 'result' in result and article_id in result['result']:
                article = result['result'][article_id]
                
                print("\nArticle Structure Debug:")
                print(f"Available top-level keys: {', '.join(article.keys())}")
                
                # Look for MeSH-related fields
                mesh_related = [key for key in article.keys() if 'mesh' in key.lower()]
                if mesh_related:
                    print(f"Potential MeSH fields: {', '.join(mesh_related)}")
                    for field in mesh_related:
                        print(f"\nStructure of '{field}':")
                        print(json.dumps(article[field], indent=2)[:500])
                else:
                    print("No MeSH-related fields found.")
                
                # Look for Keyword-related fields
                keyword_related = [key for key in article.keys() if 'keyword' in key.lower()]
                if keyword_related:
                    print(f"Potential keyword fields: {', '.join(keyword_related)}")
                    for field in keyword_related:
                        print(f"\nStructure of '{field}':")
                        print(json.dumps(article[field], indent=2)[:500])
                else:
                    print("No keyword-related fields found.")
                    
                return article
        except Exception as e:
            print(f"Error debugging article structure: {e}")
            return None


# Demo function for testing the class
def demo_search():
    """Demonstrate PubMed/PMC searching capabilities."""
    
    # Create searcher for PubMed (not PMC)
    searcher = PubmedSearcher(use_pmc=False)
    
    # Example query
    query = "suzetrigine"
    sort_by = "relevance"  # Options: relevance, pub_date, Author, JournalName
    
    print(f"\nExecuting query: {query}")
    print(f"Sorting results by: {sort_by}")
    print("Searching PubMed for articles...")
    
    try:
        # Perform the search with sort option
        ids, metadata = searcher.search(query, max_results=5, sort=sort_by)
        
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
            if 'uid' not in article_details:
                article_details['uid'] = article_id
            
            # Get and format authors
            first_author, co_authors = searcher.format_authors(article_details.get('authors', []))
            
            # Get abstract with delay between requests
            abstract = searcher.get_article_abstract(article_id)
            
            # Extract MeSH terms and keywords using the improved methods
            mesh_terms = searcher.extract_mesh_terms(article_details)
            keywords = searcher.extract_keywords(article_details)
            
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
                'mesh_terms': mesh_terms,
                'keywords': keywords,
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
            if abstract and abstract != "Abstract not available":
                print(f"Abstract: {abstract[:200]}...")
            if mesh_terms:
                print(f"MeSH Terms: {', '.join(mesh_terms)}")
            if keywords:
                print(f"Keywords: {', '.join(keywords)}")
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


# Allow script to be run standalone
if __name__ == "__main__":
    print("🔍 Testing PubMed search functionality...")
    demo_search()
