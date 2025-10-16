"""
Basic Search Example

This example demonstrates how to use the basic Baidu search functionality.
"""

import json
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'searcher', 'src'))

from WebSearch.baiduSearchTool import BaiduSearchTools


def main():
    """Run basic search example."""
    print("=== Basic Baidu Search Example ===\n")
    
    # Initialize the search tool
    tool = BaiduSearchTools(debug=True)
    
    # Perform a search
    query = "人工智能发展现状"
    max_results = 5
    
    print(f"Searching for: {query}")
    print(f"Max results: {max_results}\n")
    
    # Get results
    results_json = tool.baidu_search(query, max_results=max_results, language="zh")
    results = json.loads(results_json)
    
    # Display results
    print(f"Found {len(results)} results:\n")
    
    for idx, result in enumerate(results, 1):
        print(f"{idx}. {result['title']}")
        print(f"   URL: {result['url']}")
        print(f"   Abstract: {result['abstract'][:100]}...")
        print()


if __name__ == "__main__":
    main()
