"""Demo of using pubget to query PubMed Central."""

import os
import pathlib
import json
import requests
from pubget import download_query_results, ExitCode

def fetch_article_details(pmids):
    """Fetch article details from PubMed using E-utilities."""
    if not pmids:
        return {}
    
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
    params = {
        "db": "pubmed",
        "id": ",".join(pmids),
        "retmode": "json",
        "version": "2.0"
    }
    
    if api_key := os.getenv("PUBMED_API_KEY"):
        params["api_key"] = api_key
    
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()
        
        details = {}
        result = data.get('result', {})
        uids = result.get('uids', [])
        
        for pmid in uids:
            article_data = result.get(pmid, {})
            details[pmid] = {
                'title': article_data.get('title', 'Title not available'),
                'pubdate': article_data.get('pubdate', 'Date not available'),
                'journal': article_data.get('fulljournalname', 'Journal not available'),
                'doi': article_data.get('elocationid', '').replace('doi: ', '') if article_data.get('elocationid') else 'Not available'
            }
        return details
    except Exception as e:
        print(f"Error fetching details: {e}")
        return {}

def demo_pubget_query():
    """Run a demo PubMed Central query using pubget."""
    
    # Create a data directory for pubget
    data_dir = pathlib.Path("pubget_data")
    data_dir.mkdir(exist_ok=True)
    
    # Basic PMC search for fMRI articles
    query = 'fMRI[All Fields] AND open access[filter]'
    
    print(f"\nExecuting query: {query}")
    print("Searching PubMed Central for open access articles...")
    
    # Download articles matching the query
    output_dir, status = download_query_results(
        query=query,
        data_dir=data_dir,
        n_docs=5,  # Limit to 5 documents for demo
        api_key=os.getenv("PUBMED_API_KEY")
    )
    
    if status == ExitCode.ERROR:
        print("❌ Error downloading articles")
        return
    
    print(f"\n✅ Articles downloaded to: {output_dir}")
    print("\nQuery results summary:")
    
    try:
        info_file = output_dir / "info.json"
        if info_file.exists():
            with open(info_file, 'r') as f:
                info = json.load(f)
                search_result = info['search_result']
                
                print(f"\nTotal matches found: {search_result['count']}")
                print(f"Retrieved articles: {len(search_result['idlist'])}")
                
                if not search_result['idlist']:
                    print("\nNo articles found matching the criteria.")
                    print("\nDebug information:")
                    print("Query translation:", search_result.get('querytranslation', 'Not available'))
                    warninglist = search_result.get('warninglist', {})
                    if warninglist:
                        print("\nWarnings:")
                        for key, warnings in warninglist.items():
                            if warnings:
                                print(f"{key}:")
                                for warning in warnings:
                                    print(f"- {warning}")
                    return
                
                # Fetch and display article details
                details = fetch_article_details(search_result['idlist'])
                print(f"\nRetrieved articles details:")
                for pmid in search_result['idlist']:
                    article = details.get(pmid, {})
                    print(f"\nPMID: {pmid}")
                    print(f"Title: {article.get('title', 'Not available')}")
                    print(f"Published: {article.get('pubdate', 'Not available')}")
                    print(f"Journal: {article.get('journal', 'Not available')}")
                    print(f"DOI: {article.get('doi', 'Not available')}")
                
                print(f"\nTranslated query: {search_result['querytranslation']}")
                
    except Exception as e:
        print(f"Error processing results: {e}")

if __name__ == "__main__":
    print("🔍 Testing pubget PubMed Central query functionality...")
    demo_pubget_query()
