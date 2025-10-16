"""
AI-Powered Search Example

This example demonstrates the AI-enhanced search with reranking.
Requires DASHSCOPE_API_KEY environment variable.
"""

import asyncio
import json
import sys
import os
from time import time

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'searcher', 'src'))

from useAI2Search.SearchAgent import filterAnswer


async def main():
    """Run AI-powered search example."""
    print("=== AI-Powered Search Example ===\n")
    
    # Check for API key
    if not os.getenv("DASHSCOPE_API_KEY"):
        print("ERROR: DASHSCOPE_API_KEY environment variable not set!")
        print("Please set it with: export DASHSCOPE_API_KEY='your-key'")
        return
    
    query = "AI发展趋势 2025"
    max_results = 12
    
    print(f"Searching for: {query}")
    print(f"Max results: {max_results}")
    print("Note: This may take 20-60 seconds due to AI processing...\n")
    
    # Measure time
    start_time = time()
    
    # Get AI-enhanced results
    results = await filterAnswer(query, max_results, "zh")
    
    end_time = time()
    elapsed = end_time - start_time
    
    # Display results
    print(f"\n✓ Completed in {elapsed:.2f} seconds")
    print(f"Found {len(results)} ranked results:\n")
    
    for result in results:
        print(f"Rank {result['rank']}: {result['title']}")
        print(f"   URL: {result['url']}")
        
        # Show content preview
        content = result.get('Content', '')
        if content:
            preview = content[:150].replace('\n', ' ')
            print(f"   Content: {preview}...")
        print()


if __name__ == "__main__":
    asyncio.run(main())
