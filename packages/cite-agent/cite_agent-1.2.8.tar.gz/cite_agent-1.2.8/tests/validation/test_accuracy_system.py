#!/usr/bin/env python3
"""
Test accuracy improvements locally
"""

import sys
import asyncio
from pathlib import Path

# Add cite-agent-api to path
sys.path.insert(0, str(Path(__file__).parent / "cite-agent-api"))


async def test_citation_verifier():
    """Test citation extraction and verification"""
    print("\n🔍 Testing Citation Verifier...")
    
    from src.services.citation_verifier import CitationVerifier
    
    verifier = CitationVerifier()
    
    # Test text with various citation types
    test_text = """
    According to Smith et al. 2024, the results show significant improvement.
    The data is available at https://arxiv.org/abs/2301.12345 and the DOI is 10.1234/example.2024.
    See also [Jones 2023] for background information.
    """
    
    # Extract citations
    citations = verifier.extract_citations(test_text)
    print(f"  ✅ Extracted citations:")
    print(f"     - URLs: {len(citations['urls'])}")
    print(f"     - DOIs: {len(citations['dois'])}")
    print(f"     - arXiv: {len(citations['arxiv_ids'])}")
    print(f"     - Author-year: {len(citations['author_year'])}")
    
    # Check has_citations
    has_cites = verifier.has_citations(test_text)
    print(f"  ✅ Has citations: {has_cites}")
    
    # Count
    count = verifier.count_citations(test_text)
    print(f"  ✅ Total citations: {count}")
    
    # Verify a real URL
    print(f"\n  🌐 Verifying URL: https://arxiv.org/")
    result = await verifier.verify_url("https://arxiv.org/")
    print(f"     Status: {result['status']} (code: {result['status_code']})")
    
    # Full response verification
    print(f"\n  📊 Full verification...")
    full_result = await verifier.verify_response(test_text)
    print(f"     Quality score: {full_result['quality_score']:.2f}")
    print(f"     Verified URLs: {full_result['url_verification']['verified']}")
    print(f"     Broken URLs: {full_result['url_verification']['broken']}")
    
    return True


async def test_temperature_setting():
    """Test that temperature is set correctly"""
    print("\n🌡️  Testing Temperature Setting...")
    
    from src.services.llm_providers import LLMProviderManager
    
    # Check default temperature in code
    import inspect
    source = inspect.getsource(LLMProviderManager.query_with_fallback)
    
    if "temperature: float = 0.2" in source:
        print("  ✅ Temperature default is 0.2 (factual mode)")
        return True
    else:
        print("  ❌ Temperature default is NOT 0.2")
        return False


def test_sql_migration():
    """Test SQL migration syntax"""
    print("\n📊 Testing SQL Migration...")
    
    sql_file = Path(__file__).parent / "cite-agent-api/migrations/002_accuracy_tracking.sql"
    
    if not sql_file.exists():
        print("  ❌ Migration file not found")
        return False
    
    content = sql_file.read_text()
    
    # Check for required tables
    required = [
        "CREATE TABLE IF NOT EXISTS response_quality",
        "CREATE TABLE IF NOT EXISTS citation_details",
        "CREATE OR REPLACE VIEW accuracy_metrics",
        "CREATE OR REPLACE VIEW accuracy_weekly",
        "CREATE OR REPLACE VIEW user_accuracy",
        "CREATE OR REPLACE FUNCTION get_accuracy_stats"
    ]
    
    for item in required:
        if item in content:
            print(f"  ✅ Found: {item[:40]}...")
        else:
            print(f"  ❌ Missing: {item}")
            return False
    
    print(f"  ✅ Migration file complete ({len(content)} chars)")
    return True


def test_accuracy_routes():
    """Test that accuracy routes exist"""
    print("\n🛣️  Testing Accuracy Routes...")
    
    from src.routes import accuracy
    
    # Check for required endpoints
    endpoints = [
        'get_accuracy_stats',
        'get_daily_accuracy',
        'get_weekly_accuracy',
        'get_user_accuracy_leaderboard',
        'get_citation_details',
        'get_accuracy_trends',
        'record_response_quality'
    ]
    
    for endpoint in endpoints:
        if hasattr(accuracy, endpoint):
            print(f"  ✅ Endpoint exists: {endpoint}")
        else:
            print(f"  ❌ Missing endpoint: {endpoint}")
            return False
    
    return True


async def main():
    """Run all tests"""
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║       🧪 ACCURACY SYSTEM TEST SUITE                         ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    
    results = {}
    
    # Test 1: Citation Verifier
    try:
        results['citation_verifier'] = await test_citation_verifier()
    except Exception as e:
        print(f"  ❌ Citation verifier failed: {e}")
        results['citation_verifier'] = False
    
    # Test 2: Temperature
    try:
        results['temperature'] = await test_temperature_setting()
    except Exception as e:
        print(f"  ❌ Temperature test failed: {e}")
        results['temperature'] = False
    
    # Test 3: SQL Migration
    try:
        results['sql_migration'] = test_sql_migration()
    except Exception as e:
        print(f"  ❌ SQL test failed: {e}")
        results['sql_migration'] = False
    
    # Test 4: Accuracy Routes
    try:
        results['accuracy_routes'] = test_accuracy_routes()
    except Exception as e:
        print(f"  ❌ Routes test failed: {e}")
        results['accuracy_routes'] = False
    
    # Summary
    print("\n" + "━" * 60)
    print("📊 TEST SUMMARY:")
    print("━" * 60)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status} - {test_name}")
    
    all_passed = all(results.values())
    
    print("\n" + "━" * 60)
    if all_passed:
        print("✅ ALL TESTS PASSED - Ready for deployment!")
    else:
        print("❌ SOME TESTS FAILED - Review errors above")
    print("━" * 60)
    
    return all_passed


if __name__ == "__main__":
    # Check dependencies
    try:
        import httpx
        import structlog
        print("✅ Required packages installed")
    except ImportError as e:
        print(f"⚠️  Missing package: {e}")
        print("   Run: pip install httpx structlog")
        print("   (Tests will continue, some may fail)")
    
    # Run tests
    success = asyncio.run(main())
    sys.exit(0 if success else 1)

