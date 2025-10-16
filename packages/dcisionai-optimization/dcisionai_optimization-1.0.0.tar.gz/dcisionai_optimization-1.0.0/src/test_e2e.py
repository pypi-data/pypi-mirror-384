#!/usr/bin/env python3
"""
End-to-End Test for Reorganized MCP Server
==========================================

This script tests the complete flow of the reorganized MCP server to ensure
everything works correctly after the restructuring.
"""

import sys
import os
import asyncio
import json
from datetime import datetime

def test_imports():
    """Test that all imports work correctly."""
    print("🧪 Testing imports...")
    
    try:
        # Add src to path
        sys.path.insert(0, 'src')
        
        # Test main imports
        from src.mcp_server import mcp
        from src.agents.memory import agent_memory
        from src.agents.cache import model_cache
        from src.agents.coordinator import agent_coordinator
        
        print("✅ All imports successful!")
        return True
        
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_mcp_tools():
    """Test that MCP tools are available."""
    print("🔧 Testing MCP tools...")
    
    try:
        sys.path.insert(0, 'src')
        from src.mcp_server import mcp
        
        # Check if tools are registered
        tools = mcp.list_tools()
        print(f"📋 Available tools: {len(tools)}")
        
        for tool in tools:
            print(f"  - {tool.name}: {tool.description}")
        
        expected_tools = [
            "manufacturing_optimize",
            "manufacturing_health_check", 
            "get_optimization_insights",
            "get_cache_insights",
            "get_coordination_insights"
        ]
        
        tool_names = [tool.name for tool in tools]
        for expected in expected_tools:
            if expected in tool_names:
                print(f"  ✅ {expected}")
            else:
                print(f"  ❌ {expected} missing")
                return False
        
        print("✅ All MCP tools available!")
        return True
        
    except Exception as e:
        print(f"❌ MCP tools test failed: {e}")
        return False

async def test_health_check():
    """Test the health check tool."""
    print("🏥 Testing health check...")
    
    try:
        sys.path.insert(0, 'src')
        from src.mcp_server import mcp
        
        # Call health check tool
        result = await mcp.call_tool("manufacturing_health_check", {})
        
        print(f"📊 Health check result:")
        print(f"  Status: {result.get('status', 'unknown')}")
        print(f"  Tools available: {result.get('tools_available', 0)}")
        print(f"  Version: {result.get('version', 'unknown')}")
        print(f"  Architecture: {result.get('architecture', 'unknown')}")
        
        if result.get('status') == 'healthy':
            print("✅ Health check passed!")
            return True
        else:
            print("❌ Health check failed!")
            return False
            
    except Exception as e:
        print(f"❌ Health check test failed: {e}")
        return False

async def test_optimization_flow():
    """Test a complete optimization flow."""
    print("🚀 Testing optimization flow...")
    
    try:
        sys.path.insert(0, 'src')
        from src.mcp_server import mcp
        
        # Test with a simple manufacturing problem
        test_problem = "Optimize production line efficiency with 10 workers across 2 manufacturing lines"
        
        print(f"📝 Test problem: {test_problem}")
        
        # Call optimization tool
        result = await mcp.call_tool("manufacturing_optimize", {
            "problem_description": test_problem
        })
        
        print(f"📊 Optimization result:")
        print(f"  Status: {result.get('status', 'unknown')}")
        print(f"  Timestamp: {result.get('timestamp', 'unknown')}")
        
        if 'intent_classification' in result:
            intent = result['intent_classification']
            print(f"  Intent: {intent.get('intent', 'unknown')}")
            print(f"  Confidence: {intent.get('confidence', 0):.2f}")
        
        if 'optimization_solution' in result:
            solution = result['optimization_solution']
            print(f"  Solution Status: {solution.get('status', 'unknown')}")
            print(f"  Objective Value: {solution.get('objective_value', 'N/A')}")
        
        if result.get('status') == 'success':
            print("✅ Optimization flow successful!")
            return True
        else:
            print("❌ Optimization flow failed!")
            return False
            
    except Exception as e:
        print(f"❌ Optimization flow test failed: {e}")
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

async def main():
    """Run all E2E tests."""
    print("🔄 Starting End-to-End Test for Reorganized MCP Server")
    print("=" * 60)
    
    tests = [
        ("Import Test", test_imports),
        ("MCP Tools Test", test_mcp_tools),
        ("Health Check Test", test_health_check),
        ("Agent Systems Test", test_agent_systems),
        ("Optimization Flow Test", test_optimization_flow)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🧪 Running {test_name}...")
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 60)
    print("📊 E2E Test Results:")
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall Result: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All E2E tests passed! Reorganized MCP server is working perfectly!")
        return True
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
