"""
Web Content Extraction Example

This example demonstrates extracting clean text from web pages.
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'searcher', 'src'))

from FetchPage.fetchWeb import filter_extracted_text


def main():
    """Run content extraction example."""
    print("=== Web Content Extraction Example ===\n")
    
    # Example URL
    url = "https://www.example.com"
    
    print(f"Extracting content from: {url}\n")
    
    # Extract text
    try:
        content = filter_extracted_text(
            url,
            follow_pagination=False,
            timeout=10.0
        )
        
        print("Extracted content:")
        print("=" * 80)
        print(content[:500])  # Show first 500 characters
        print("...")
        print("=" * 80)
        print(f"\nTotal length: {len(content)} characters")
        
    except Exception as e:
        print(f"Error extracting content: {e}")


if __name__ == "__main__":
    main()
