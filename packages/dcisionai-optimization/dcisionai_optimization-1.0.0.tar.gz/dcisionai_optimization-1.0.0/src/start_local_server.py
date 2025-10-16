#!/usr/bin/env python3
"""
Direct Local Server Startup for DcisionAI Manufacturing MCP Server
================================================================

This script directly starts the HTTP server for local testing.
"""

import sys
import os
from pathlib import Path

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def main():
    """Start the HTTP server directly."""
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
        print("\n🌐 Test the server:")
        print("   curl http://localhost:5001/health")
        print("\n⏹️  Press Ctrl+C to stop the server")
        print("=" * 60)
        
        # Run the Flask app
        app.run(host='0.0.0.0', port=5001, debug=False)
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure you're in the correct directory and have installed dependencies:")
        print("   pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
