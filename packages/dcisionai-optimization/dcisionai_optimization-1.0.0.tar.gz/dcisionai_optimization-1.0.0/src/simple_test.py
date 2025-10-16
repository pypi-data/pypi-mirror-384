#!/usr/bin/env python3
"""
Simple Test for Reorganized MCP Server
=====================================

This script tests the reorganized structure without starting the server.
"""

import sys
import os

def test_imports():
    """Test that all imports work correctly."""
    print("🧪 Testing imports...")
    
    try:
        # Add src to path
        sys.path.insert(0, 'src')
        
        # Test main imports
        from src.mcp_server import mcp
        print("✅ MCP server import successful!")
        
        from src.agents.memory import agent_memory
        print("✅ Agent memory import successful!")
        
        from src.agents.cache import model_cache
        print("✅ Model cache import successful!")
        
        from src.agents.coordinator import agent_coordinator
        print("✅ Agent coordinator import successful!")
        
        return True
        
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_agent_systems():
    """Test individual agent systems."""
    print("🤖 Testing agent systems...")
    
    try:
        sys.path.insert(0, 'src')
        from src.agents.memory import agent_memory
        from src.agents.cache import model_cache
        from src.agents.coordinator import agent_coordinator
        
        # Test memory system
        memory_insights = agent_memory.get_optimization_insights()
        print(f"  🧠 Memory: {memory_insights.get('total_optimizations', 0)} optimizations")
        
        # Test cache system
        cache_insights = model_cache.get_cache_insights()
        print(f"  💾 Cache: {cache_insights.get('cached_models', 0)} models cached")
        
        # Test coordinator system
        coord_insights = agent_coordinator.get_coordination_insights()
        print(f"  🎯 Coordinator: {coord_insights.get('system_metrics', {}).get('active_requests', 0)} active requests")
        
        print("✅ All agent systems working!")
        return True
        
    except Exception as e:
        print(f"❌ Agent systems test failed: {e}")
        return False

def test_file_structure():
    """Test that all expected files exist."""
    print("📁 Testing file structure...")
    
    expected_files = [
        "src/mcp_server.py",
        "src/agents/coordinator.py",
        "src/agents/memory.py", 
        "src/agents/cache.py",
        "src/integrations/bedrock.py",
        "src/integrations/agentcore.py",
        "src/integrations/runtime.py",
        "src/servers/http.py",
        "deployment/deploy_agentcore.py",
        "tests/test_bedrock_agentcore_client.py",
        "infrastructure/Dockerfile",
        "main.py"
    ]
    
    all_exist = True
    for file_path in expected_files:
        if os.path.exists(file_path):
            print(f"  ✅ {file_path}")
        else:
            print(f"  ❌ {file_path} missing")
            all_exist = False
    
    if all_exist:
        print("✅ All expected files exist!")
        return True
    else:
        print("❌ Some files are missing!")
        return False

def main():
    """Run simple tests."""
    print("🔄 Simple Test for Reorganized MCP Server")
    print("=" * 50)
    
    tests = [
        ("File Structure Test", test_file_structure),
        ("Import Test", test_imports),
        ("Agent Systems Test", test_agent_systems)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🧪 Running {test_name}...")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall Result: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Reorganized MCP server structure is working!")
        return True
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
