#!/usr/bin/env python3
"""
DcisionAI MCP Server - Environment Setup Script
==============================================

Automatically creates .env file with proper configuration.
"""

import os
import shutil
from pathlib import Path

def setup_environment():
    """Set up the environment configuration."""
    print("🔧 Setting up DcisionAI MCP Server environment...")
    
    # Check if .env already exists
    env_file = Path('.env')
    if env_file.exists():
        print("✅ .env file already exists")
        return True
    
    # Check if env.example exists
    example_file = Path('env.example')
    if not example_file.exists():
        print("❌ env.example file not found")
        return False
    
    # Copy env.example to .env
    try:
        shutil.copy(example_file, env_file)
        print("✅ Created .env file from template")
        
        # Set environment variables for current session
        os.environ['DCISIONAI_ACCESS_TOKEN'] = "eyJraWQiOiJLMWZEMFwvXC9qaGtJSHlZd2IyM2NsMkRSK0dEQ2tFaHVWZVd0djdFMERkOUk9IiwiYWxnIjoiUlMyNTYifQ.eyJzdWIiOiI1cjdyaXJqdmI0OTZpam1rMDNtanNrNTNtOCIsInRva2VuX3VzZSI6ImFjY2VzcyIsInNjb3BlIjoiRGNpc2lvbkFJLUdhdGV3YXktMGRlMWE2NTVcL2ludm9rZSIsImF1dGhfdGltZSI6MTc2MDU0NzgwOCwiaXNzIjoiaHR0cHM6XC9cL2NvZ25pdG8taWRwLnVzLWVhc3QtMS5hbWF6b25hd3MuY29tXC91cy1lYXN0LTFfdjlDSmJRMWVKIiwiZXhwIjoxNzYwNTUxNDA4LCJpYXQiOjE3NjA1NDc4MDgsInZlcnNpb24iOjIsImp0aSI6IjIzMDAwOTBmLWZjNzYtNDI1NC1hZjQ3LTY2ZDA5MGVkNzRiMiIsImNsaWVudF9pZCI6IjVyN3Jpcmp2YjQ5NmlqbWswM21qc2s1M204In0.nOgW15NAgzd-fB3Vn8fx0030rmX3_h9nKRkIM_JK3mXdATw-K0rCrinzll9XrN1m4pAOmVJFdoq0YbH7SOI6bMIl840TnN9hSxnKVy1zx5nOPn98btAKzP41UbLVJ8PGE3zAfrkOPtMaqvoMDzgCZP0fFF_FiCPFUWUvSs-OmbR2TnuVmdnuFCXLAQ_CMTJVpwVMk13P3mfJgkSPY33ly3GbtaVN9LDq11ZzVCAvsRbA7DvEWdSc9GVpHYmRwfEJYZZW4KNeOFZZRqZuryY57mBgcUaZ06deesl_ySN72a2CgJ1xnVCeK5VYcwdlUmQrSvEYxAJJGvF-ZacgQC6qUA"
        os.environ['DCISIONAI_GATEWAY_URL'] = "https://dcisionai-gateway-0de1a655-ja1rhlcqjx.gateway.bedrock-agentcore.us-east-1.amazonaws.com/mcp"
        os.environ['DCISIONAI_GATEWAY_TARGET'] = "DcisionAI-Optimization-Tools-Fixed"
        
        print("✅ Environment variables set for current session")
        print("⚠️  Please edit .env file with your actual AWS credentials")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating .env file: {e}")
        return False

if __name__ == "__main__":
    setup_environment()
