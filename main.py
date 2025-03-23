"""Scientific Data Retrieval System

This is the main entry point for the scientific data retrieval system.
It demonstrates the basic usage of system components.
"""

from utils import KeyManager

def main() -> None:
    """Main entry point of the application."""
    try:
        # Initialize key manager
        key_manager = KeyManager()
        
        # Display available keys and their status
        print("\nAPI Key Status")
        print("-------------")
        for key_name in key_manager.available_keys:
            status = "✅ Ready" if key_manager.has_key(key_name) else "❌ Missing"
            print(f"{key_name}: {status}")
            
        # Example of accessing specific keys
        if key_manager.has_key("PUBMED_API_KEY"):
            pubmed_key = key_manager.get_key("PUBMED_API_KEY")
            print(f"\nPubMed API Key loaded: {pubmed_key[:5]}...")
            
        if key_manager.has_key("CROSSREF_EMAIL"):
            crossref_email = key_manager.get_key("CROSSREF_EMAIL")
            print(f"CrossRef Email loaded: {crossref_email}")
            
    except FileNotFoundError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    main()
