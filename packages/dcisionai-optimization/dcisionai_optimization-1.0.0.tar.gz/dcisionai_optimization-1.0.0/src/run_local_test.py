#!/usr/bin/env python3
"""
Local Test Server for DcisionAI Manufacturing MCP Server
======================================================

This script runs the MCP server locally for testing with the UI.
It starts an HTTP server that exposes the MCP tools as REST endpoints.
"""

import sys
import os
from pathlib import Path

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def run_http_server():
    """Run the HTTP server for local testing."""
    try:
        from src.servers.http import app
        print("🚀 Starting Local Test Server...")
        print("📡 Server will be available at: http://localhost:5001")
        print("🔧 MCP tools exposed as REST endpoints:")
        print("   - GET  /health - Health check")
        print("   - POST /intent - Intent classification")
        print("   - POST /data - Data analysis")
        print("   - POST /model - Model building")
        print("   - POST /solve - Optimization solving")
        print("   - POST /mcp - Full optimization flow")
        print("\n🌐 Open your browser to test the UI!")
        print("   Frontend: http://localhost:3000 (if you have the React app running)")
        print("   Backend:  http://localhost:5001")
        print("\n⏹️  Press Ctrl+C to stop the server")
        print("=" * 60)
        
        # Run the Flask app
        app.run(host='0.0.0.0', port=5001, debug=True)
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure you're in the correct directory and have installed dependencies:")
        print("   pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)

def run_mcp_server():
    """Run the MCP server directly (for MCP clients)."""
    try:
        from src.mcp_server import mcp
        print("🚀 Starting MCP Server...")
        print("📡 MCP server will be available for MCP clients")
        print("⏹️  Press Ctrl+C to stop the server")
        print("=" * 60)
        
        mcp.run()
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure you're in the correct directory and have installed dependencies:")
        print("   pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error starting MCP server: {e}")
        sys.exit(1)

def main():
    """Main entry point."""
    print("🏭 DcisionAI Manufacturing MCP Server - Local Test")
    print("=" * 60)
    print("Choose how to run the server:")
    print("1. HTTP Server (for UI testing) - Recommended")
    print("2. MCP Server (for MCP clients)")
    print()
    
    choice = input("Enter your choice (1 or 2): ").strip()
    
    if choice == "1":
        run_http_server()
    elif choice == "2":
        run_mcp_server()
    else:
        print("❌ Invalid choice. Please run again and choose 1 or 2.")
        sys.exit(1)

if __name__ == "__main__":
    main()
