#!/usr/bin/env python3
"""
Scientific Paper Agent Demo Script

This script demonstrates the working functionality of the scientific paper agent
using the direct search method (bypassing A2A for reliability).

Usage:
    python demo.py
    python demo.py "quantum computing" 3
"""

import sys
import os
import asyncio
from pathlib import Path

def setup_environment():
    """Setup the Python path and environment."""
    # Add the scientific paper agent to the path
    script_dir = Path(__file__).parent
    agent_path = script_dir / 'a2a' / 'agents' / 'scientific_paper_agent'
    sys.path.insert(0, str(agent_path))
    
    # Load environment variables from .env if it exists
    env_file = script_dir / '.env'
    if env_file.exists():
        from dotenv import load_dotenv
        load_dotenv(env_file)
    
    # Check required environment variable
    if not os.getenv('GOOGLE_API_KEY'):
        print("❌ Error: GOOGLE_API_KEY environment variable is required")
        print("Please set your Gemini API key:")
        print("   set GOOGLE_API_KEY=your_api_key_here")
        print("   or add it to the .env file")
        sys.exit(1)

async def demo_search(query="machine learning", max_results=3):
    """Demonstrate the paper search functionality."""
    try:
        print("🔍 Scientific Paper Agent Demo")
        print("=" * 50)
        print(f"Query: {query}")
        print(f"Max results: {max_results}")
        print()
        
        # Import the search function
        from agent import search_and_parse_papers
        
        print("📡 Connecting to ArXiv MCP server...")
        print("🔎 Searching for papers...")
        
        # Run the search
        result = await search_and_parse_papers(query, max_results)
        
        print(f"✅ Search completed!")
        print()
        
        if hasattr(result, 'papers') and result.papers:
            papers = result.papers
            print(f"📚 Found {len(papers)} papers:")
            print()
            
            for i, paper in enumerate(papers, 1):
                print(f"{i}. 📄 {paper.title}")
                print(f"   👥 Authors: {', '.join(paper.authors)}")
                print(f"   🏷️  Topics: {', '.join(paper.topics[:3])}{'...' if len(paper.topics) > 3 else ''}")
                print(f"   ⭐ Useful: {'Yes' if paper.useful else 'No'}")
                print(f"   📝 Overview: {paper.overview[:150]}...")
                if hasattr(paper, 'pdf_url'):
                    print(f"   🔗 PDF: {paper.pdf_url}")
                print()
                
            print(f"💾 Results saved to: {os.getenv('PAPER_OUTPUT_DIR', './data')}/")
            print(f"   📁 PDFs: ./data/pdf/")
            print(f"   📋 Metadata: ./data/metadata/")
            
        else:
            print("❌ No papers found for the given query")
            
        return result
        
    except Exception as e:
        print(f"❌ Error during search: {e}")
        import traceback
        print("\nFull error:")
        traceback.print_exc()
        return None

async def demo_mcp_connection():
    """Test MCP server connection."""
    try:
        print("🔗 Testing MCP Server Connection")
        print("-" * 30)
        
        import httpx
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get("http://localhost:8000/health")
            if response.status_code == 200:
                print("✅ ArXiv MCP Server is running on port 8000")
            else:
                print(f"⚠️  MCP Server responded with status: {response.status_code}")
    except Exception as e:
        print(f"❌ MCP Server not accessible: {e}")
        print("💡 Please start the MCP server first:")
        print("   python a2a/agents/scientific_paper_agent/arxiv_server.py")
        return False
    return True

def print_usage():
    """Print usage instructions."""
    print("📖 Usage Instructions")
    print("=" * 50)
    print()
    print("🚀 Quick Start (Direct Search - Recommended):")
    print("   python demo.py")
    print("   python demo.py 'quantum computing' 5")
    print()
    print("🏗️  Full A2A Workflow:")
    print("   1. Start MCP Server:")
    print("      python a2a/agents/scientific_paper_agent/arxiv_server.py")
    print()
    print("   2. Start A2A SDK Agent:")  
    print("      python agents/orchestrator_agent/__main___a2a_sdk.py")
    print()
    print("   3. Use A2A Client:")
    print("      python a2a/client/client.py")
    print()
    print("📋 Available Make Commands:")
    print("   make search QUERY='your query' RESULTS=3")
    print("   make run-mcp-server")
    print("   make run-scientific-agent-sdk") 
    print("   make a2a-client")
    print()

def main():
    """Main demo function."""
    setup_environment()
    
    # Parse command line arguments
    if len(sys.argv) == 1:
        query = "machine learning"
        max_results = 3
    elif len(sys.argv) == 2 and sys.argv[1] in ['-h', '--help', 'help']:
        print_usage()
        return
    elif len(sys.argv) == 2:
        query = sys.argv[1]
        max_results = 3
    elif len(sys.argv) == 3:
        query = sys.argv[1]
        try:
            max_results = int(sys.argv[2])
        except ValueError:
            print("❌ Error: max_results must be a number")
            sys.exit(1)
    else:
        print("❌ Error: Too many arguments")
        print("Usage: python demo.py [query] [max_results]")
        sys.exit(1)
    
    async def run_demo():
        print("🧪 Scientific Paper Agent Demo")
        print("=" * 50)
        print()
        
        # Test MCP connection first (optional)
        # await demo_mcp_connection()
        # print()
        
        # Run the main demo
        result = await demo_search(query, max_results)
        
        if result:
            print()
            print("✨ Demo completed successfully!")
            print("📖 Check the README.md for more details and advanced usage")
        else:
            print()
            print("❌ Demo failed - check the error messages above")
    
    # Run the demo
    asyncio.run(run_demo())

if __name__ == "__main__":
    main()