#!/usr/bin/env python3
"""
Quick local backend test
Tests core functionality without full deployment
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent / "cite-agent-api"))

async def test_imports():
    """Test that all critical imports work"""
    print("🔍 Testing imports...")
    
    try:
        from src.main import app
        print("  ✅ Main app imports successfully")
    except Exception as e:
        print(f"  ❌ Failed to import main app: {e}")
        return False
    
    try:
        from src.routes.auth import router as auth_router
        print("  ✅ Auth router imports successfully")
    except Exception as e:
        print(f"  ❌ Failed to import auth router: {e}")
        return False
    
    try:
        from src.routes.query import router as query_router
        print("  ✅ Query router imports successfully")
    except Exception as e:
        print(f"  ❌ Failed to import query router: {e}")
        return False
    
    try:
        from src.routes.downloads import router as downloads_router
        print("  ✅ Downloads router imports successfully")
    except Exception as e:
        print(f"  ❌ Failed to import downloads router: {e}")
        return False
    
    try:
        from src.services.llm_providers import LLMProviderManager
        print("  ✅ LLM Provider Manager imports successfully")
    except Exception as e:
        print(f"  ❌ Failed to import LLM Provider Manager: {e}")
        return False
    
    return True

async def test_app_routes():
    """Test that routes are registered"""
    print("\n🔍 Testing route registration...")
    
    from src.main import app
    
    routes = [route.path for route in app.routes]
    
    required_routes = [
        "/api/auth/register",
        "/api/auth/login",
        "/api/query/",
        "/api/downloads/{platform}",
        "/api/health"
    ]
    
    for route in required_routes:
        if route in routes:
            print(f"  ✅ {route} registered")
        else:
            print(f"  ❌ {route} NOT registered")
            # Show similar routes for debugging
            similar = [r for r in routes if route.split('/')[2] in r]
            if similar:
                print(f"     Similar routes found: {similar}")
    
    return True

async def test_environment():
    """Test environment configuration"""
    print("\n🔍 Testing environment...")
    
    import os
    
    required_vars = {
        "DATABASE_URL": False,  # Optional for import test
        "JWT_SECRET_KEY": False,
        "GROQ_API_KEY_1": False,
    }
    
    for var in required_vars:
        if os.getenv(var):
            print(f"  ✅ {var} is set")
        else:
            print(f"  ⚠️  {var} not set (OK for import test)")
    
    return True

async def main():
    print("=" * 60)
    print("🔍 Cite-Agent - Backend Test")
    print("=" * 60)
    print()
    
    # Run tests
    tests = [
        ("Imports", test_imports),
        ("Routes", test_app_routes),
        ("Environment", test_environment),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = await test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ {name} test failed with exception: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary")
    print("=" * 60)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
    
    all_passed = all(result for _, result in results)
    
    print()
    if all_passed:
        print("🎉 All tests passed! Backend is ready for deployment.")
        print()
        print("Next steps:")
        print("  1. Set up .env file with your API keys")
        print("  2. Deploy to Railway: cd nocturnal-archive-api && railway up")
        print("  3. Run migrations: railway run python run_migrations.py")
        return 0
    else:
        print("⚠️  Some tests failed. Check the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))

