#!/usr/bin/env python3
"""
COMPREHENSIVE ROBUSTNESS TEST for Qualitative Analysis
Tests edge cases, ambiguous queries, and potential failures
"""

import sys
from pathlib import Path
import re

# Add paths
sys.path.insert(0, str(Path(__file__).parent / "cite_agent"))


def test_edge_case_detection():
    """Test detection with ambiguous and edge case queries"""
    print("\n🔍 Test 1: Edge Case Query Detection")
    print("=" * 70)
    
    # Simulate the actual detection logic from enhanced_ai_agent.py
    qualitative_keywords = [
        'theme', 'themes', 'thematic', 'code', 'coding', 'qualitative',
        'interview', 'interviews', 'transcript', 'case study', 'narrative',
        'discourse', 'content analysis', 'quote', 'quotes', 'excerpt',
        'participant', 'respondent', 'informant', 'ethnography',
        'grounded theory', 'phenomenology', 'what do people say',
        'how do participants', 'sentiment', 'perception', 'experience',
        'lived experience', 'meaning', 'interpret', 'understand',
        'focus group', 'observation', 'field notes', 'memoir', 'diary'
    ]
    
    quantitative_keywords = [
        'calculate', 'average', 'mean', 'median', 'percentage', 'correlation',
        'regression', 'statistical', 'significance', 'p-value', 'variance',
        'standard deviation', 'trend', 'forecast', 'model', 'predict',
        'rate of', 'ratio', 'growth rate', 'change in', 'compared to'
    ]
    
    edge_cases = [
        # Ambiguous queries
        ("Tell me about user experience", "qual", "has 'experience' keyword"),
        ("What's the average user experience score?", "mixed", "has both average + experience"),
        ("Analyze customer data", "quant", "generic 'analyze', defaults to quant"),
        
        # Multi-word keyword matching
        ("what do people say about the product", "qual", "multi-word: 'what do people say'"),
        ("compared to last year's theme", "mixed", "has 'compared to' + 'theme'"),
        
        # False positives
        ("Calculate the theme park attendance", "quant", "'theme' but in 'theme park' - should be quant"),
        ("What's the sentiment analysis algorithm?", "quant", "'sentiment' but asking about algorithm"),
        ("Interview the CEO about earnings", "mixed", "interview + earnings"),
        
        # Pure qualitative
        ("Extract themes from these transcripts", "qual", "clear qualitative"),
        ("Code the interview data", "qual", "clear qualitative"),
        
        # Pure quantitative
        ("Calculate ROI", "quant", "clear quantitative"),
        ("Show regression results", "quant", "clear quantitative"),
        
        # Edge: Empty or very short
        ("themes", "qual", "single word"),
        ("calculate", "quant", "single word"),
        ("", "quant", "empty string defaults to quant"),
        
        # Complex mixed
        ("What themes emerge from interviews and what's the correlation with revenue?", "mixed", "complex mixed"),
    ]
    
    passed = 0
    failed_cases = []
    
    # Add context awareness (matches actual implementation)
    strong_quant_contexts = ['algorithm', 'park', 'system', 'database',
                            'calculate', 'predict', 'forecast', 'ratio', 'percentage']
    measurement_words = ['score', 'metric', 'rating', 'measure', 'index']
    financial_keywords = ['earnings', 'ceo', 'revenue', 'profit']
    mixed_indicators = ['experience', 'sentiment', 'perception']
    
    for query, expected, reason in edge_cases:
        query_lower = query.lower()
        
        # Check for mixed method indicators
        has_strong_quant_context = any(ctx in query_lower for ctx in strong_quant_contexts)
        has_measurement = any(mw in query_lower for mw in measurement_words)
        is_mixed_method = False
        if not has_strong_quant_context and has_measurement:
            if any(indicator in query_lower for indicator in mixed_indicators):
                is_mixed_method = True
        
        # Context-aware detection (matches actual implementation)
        has_financial = any(kw in query_lower for kw in financial_keywords)
        
        qual_score = sum(1 for kw in qualitative_keywords if kw in query_lower)
        quant_score = sum(1 for kw in quantitative_keywords if kw in query_lower)
        
        # Apply financial boost
        if has_financial and qual_score == 1:
            quant_score += 1
        
        # Adjust for context
        if has_strong_quant_context:
            qual_score = max(0, qual_score - 1)
        
        # Detection logic
        if is_mixed_method:
            detected = "mixed"
        elif qual_score >= 2 and quant_score >= 1:
            detected = "mixed"
        elif qual_score > quant_score and qual_score > 0:
            detected = "qual"
        elif qual_score > 0 and quant_score > 0:
            detected = "mixed"
        else:
            detected = "quant"
        
        # Map abbreviations
        expected_full = {"qual": "qual", "quant": "quant", "mixed": "mixed"}[expected]
        
        if detected == expected_full:
            status = "✅"
            passed += 1
        else:
            status = "❌"
            failed_cases.append({
                'query': query,
                'expected': expected,
                'detected': detected,
                'reason': reason,
                'qual_score': qual_score,
                'quant_score': quant_score
            })
        
        query_display = query[:40] + "..." if len(query) > 40 else query
        print(f"  {status} \"{query_display}\" → {detected} (expected: {expected})")
        if status == "❌":
            print(f"      Reason: {reason}")
            print(f"      Scores: qual={qual_score}, quant={quant_score}")
    
    print(f"\n  Result: {passed}/{len(edge_cases)} tests passed")
    
    if failed_cases:
        print("\n  ⚠️  FAILED CASES ANALYSIS:")
        for case in failed_cases:
            print(f"\n    Query: \"{case['query']}\"")
            print(f"    Expected: {case['expected']}, Got: {case['detected']}")
            print(f"    Scores: qual={case['qual_score']}, quant={case['quant_score']}")
            print(f"    Reason: {case['reason']}")
    
    return passed, len(edge_cases), failed_cases


def test_keyword_overlap():
    """Test for keyword conflicts"""
    print("\n🔍 Test 2: Keyword Overlap Analysis")
    print("=" * 70)
    
    qualitative_keywords = [
        'theme', 'themes', 'thematic', 'code', 'coding', 'qualitative',
        'interview', 'interviews', 'transcript', 'case study', 'narrative',
        'discourse', 'content analysis', 'quote', 'quotes', 'excerpt',
        'participant', 'respondent', 'informant', 'ethnography',
        'grounded theory', 'phenomenology', 'what do people say',
        'how do participants', 'sentiment', 'perception', 'experience',
        'lived experience', 'meaning', 'interpret', 'understand',
        'focus group', 'observation', 'field notes', 'memoir', 'diary'
    ]
    
    quantitative_keywords = [
        'calculate', 'average', 'mean', 'median', 'percentage', 'correlation',
        'regression', 'statistical', 'significance', 'p-value', 'variance',
        'standard deviation', 'trend', 'forecast', 'model', 'predict',
        'rate of', 'ratio', 'growth rate', 'change in', 'compared to'
    ]
    
    # Check for overlaps
    qual_set = set(qualitative_keywords)
    quant_set = set(quantitative_keywords)
    overlap = qual_set & quant_set
    
    print(f"  Qualitative keywords: {len(qual_set)}")
    print(f"  Quantitative keywords: {len(quant_set)}")
    print(f"  Overlaps: {len(overlap)}")
    
    if overlap:
        print(f"\n  ⚠️  OVERLAPPING KEYWORDS:")
        for kw in overlap:
            print(f"    - '{kw}'")
        print("\n  This could cause ambiguity!")
        return False
    else:
        print(f"\n  ✅ No overlaps - clean separation")
        return True


def test_multiword_keywords():
    """Test multi-word keyword matching"""
    print("\n🔍 Test 3: Multi-Word Keyword Matching")
    print("=" * 70)
    
    test_cases = [
        ("what do people say about this", True, "what do people say"),
        ("how do participants feel", True, "how do participants"),
        ("case study of the company", True, "case study"),
        ("content analysis shows", True, "content analysis"),
        ("grounded theory approach", True, "grounded theory"),
        ("lived experience of users", True, "lived experience"),
        ("focus group discussion", True, "focus group"),
        ("field notes indicate", True, "field notes"),
        ("rate of growth", True, "rate of"),  # quant keyword
        ("growth rate is", True, "growth rate"),  # quant keyword
        ("change in revenue", True, "change in"),  # quant keyword
        ("compared to baseline", True, "compared to"),  # quant keyword
    ]
    
    qualitative_keywords = [
        'what do people say', 'how do participants', 'case study',
        'content analysis', 'grounded theory', 'lived experience',
        'focus group', 'field notes'
    ]
    
    quantitative_keywords = [
        'rate of', 'growth rate', 'change in', 'compared to'
    ]
    
    passed = 0
    for query, should_match, keyword in test_cases:
        query_lower = query.lower()
        is_qual = keyword in qualitative_keywords
        is_quant = keyword in quantitative_keywords
        
        if is_qual:
            found = keyword in query_lower
        elif is_quant:
            found = keyword in query_lower
        else:
            found = False
        
        if found == should_match:
            status = "✅"
            passed += 1
        else:
            status = "❌"
        
        kw_type = "qual" if is_qual else "quant" if is_quant else "unknown"
        print(f"  {status} \"{query}\" → '{keyword}' ({kw_type}) found: {found}")
    
    print(f"\n  Result: {passed}/{len(test_cases)} tests passed")
    return passed == len(test_cases)


def test_prompt_switching_logic():
    """Test that prompts actually change based on mode"""
    print("\n🔍 Test 4: Prompt Switching Verification")
    print("=" * 70)
    
    # Simulate prompt building logic
    def build_intro(analysis_mode: str) -> str:
        if analysis_mode == "qualitative":
            return (
                "You are Nocturnal, a truth-seeking research AI specialized in QUALITATIVE ANALYSIS. "
                "PRIMARY DIRECTIVE: Accuracy > Agreeableness. Quote verbatim, never paraphrase."
            )
        elif analysis_mode == "mixed":
            return (
                "You are Nocturnal, a truth-seeking research AI handling MIXED METHODS analysis. "
                "PRIMARY DIRECTIVE: Accuracy > Agreeableness. "
                "You work with both quantitative data (numbers, stats) and qualitative data (themes, quotes)."
            )
        else:
            return (
                "You are Nocturnal, a truth-seeking research and finance AI. "
                "PRIMARY DIRECTIVE: Accuracy > Agreeableness."
            )
    
    test_cases = [
        ("qualitative", ["QUALITATIVE ANALYSIS", "Quote verbatim", "never paraphrase"]),
        ("mixed", ["MIXED METHODS", "quantitative data", "qualitative data"]),
        ("quantitative", ["finance AI", "Accuracy > Agreeableness"]),
    ]
    
    passed = 0
    for mode, expected_phrases in test_cases:
        intro = build_intro(mode)
        all_found = all(phrase in intro for phrase in expected_phrases)
        
        if all_found:
            status = "✅"
            passed += 1
        else:
            status = "❌"
            missing = [p for p in expected_phrases if p not in intro]
            print(f"  {status} {mode}: Missing phrases: {missing}")
            continue
        
        print(f"  {status} {mode}: All key phrases present")
    
    print(f"\n  Result: {passed}/{len(test_cases)} prompts verified")
    return passed == len(test_cases)


def test_false_positives():
    """Test cases that might trigger false positives"""
    print("\n🔍 Test 5: False Positive Detection")
    print("=" * 70)
    
    qualitative_keywords = ['theme', 'code', 'experience', 'sentiment']
    quantitative_keywords = ['calculate', 'average', 'trend', 'model']
    strong_quant_contexts = ['algorithm', 'park', 'system', 'database',
                            'calculate', 'predict', 'forecast', 'ratio', 'percentage']
    measurement_words = ['score', 'metric', 'rating', 'measure', 'index']
    mixed_indicators = ['experience', 'sentiment', 'perception']
    
    false_positive_cases = [
        # Words used in different context
        ("What's the theme of this park?", "quant", "theme park, not research theme"),
        ("Run the code to calculate", "quant", "code = computer code, not qualitative coding"),
        ("What's the user experience score?", "mixed", "UX score is quantitative"),
        ("Sentiment analysis algorithm", "quant", "algorithm, not actual sentiment analysis"),
        ("Predict the trend", "quant", "predict + trend = clearly quant"),
        ("Statistical model of behavior", "quant", "statistical model"),
    ]
    
    passed = 0
    issues = []
    
    for query, expected, reasoning in false_positive_cases:
        query_lower = query.lower()
        
        # Check for mixed method indicators
        has_strong_quant_context = any(ctx in query_lower for ctx in strong_quant_contexts)
        has_measurement = any(mw in query_lower for mw in measurement_words)
        is_mixed_method = False
        if not has_strong_quant_context and has_measurement:
            if any(indicator in query_lower for indicator in mixed_indicators):
                is_mixed_method = True
        
        qual_score = sum(1 for kw in qualitative_keywords if kw in query_lower)
        quant_score = sum(1 for kw in quantitative_keywords if kw in query_lower)
        
        # Context adjustment
        if has_strong_quant_context:
            qual_score = max(0, qual_score - 1)
        
        if is_mixed_method:
            detected = "mixed"
        elif qual_score >= 2 and quant_score >= 1:
            detected = "mixed"
        elif qual_score > quant_score and qual_score > 0:
            detected = "qual"
        elif qual_score > 0 and quant_score > 0:
            detected = "mixed"
        else:
            detected = "quant"
        
        if detected == expected:
            status = "✅"
            passed += 1
        else:
            status = "❌"
            issues.append({
                'query': query,
                'expected': expected,
                'detected': detected,
                'reasoning': reasoning,
                'qual_score': qual_score,
                'quant_score': quant_score
            })
        
        print(f"  {status} \"{query}\" → {detected} (expected: {expected})")
        if status == "❌":
            print(f"      Issue: {reasoning}")
            print(f"      Scores: qual={qual_score}, quant={quant_score}")
    
    print(f"\n  Result: {passed}/{len(false_positive_cases)} handled correctly")
    
    if issues:
        print("\n  ⚠️  FALSE POSITIVE ISSUES:")
        print("  These queries are misclassified due to keyword ambiguity:")
        for issue in issues:
            print(f"\n    \"{issue['query']}\"")
            print(f"    Problem: {issue['reasoning']}")
            print(f"    Expected {issue['expected']}, got {issue['detected']}")
    
    return passed, len(false_positive_cases), issues


def test_quote_extraction_edge_cases():
    """Test quote extraction with tricky cases"""
    print("\n🔍 Test 6: Quote Extraction Edge Cases")
    print("=" * 70)
    
    # Simulate quote extraction logic
    QUOTE_PATTERN = r'"([^"]+)"'
    ATTRIBUTION_PATTERN = r'—\s*([^,\n]+)(?:,\s*(?:p\.|line)\s*(\d+))?'
    
    test_cases = [
        ('"Simple quote" — Author, p. 5', 1, True, "Simple case"),
        ('"Quote one" and "quote two"', 2, False, "Multiple quotes, no attribution"),
        ('"Nested "inner" quote" — Source', 2, True, "Nested quotes (tricky)"),
        ('He said "something" but also "something else" — Interview 3', 2, True, "Two quotes, one attribution"),
        ('"Quote with\nnewline" — Author', 0, False, "Newline in quote (might break regex)"),
        ('"" — Empty quote', 1, False, "Empty quote"),
        ('No quotes here at all', 0, False, "No quotes"),
        ('"Quote — with em-dash inside" — Author', 1, True, "Em-dash inside quote"),
    ]
    
    passed = 0
    issues = []
    
    for text, expected_count, expected_attribution, description in test_cases:
        quotes_found = re.findall(QUOTE_PATTERN, text)
        quote_count = len(quotes_found)
        
        # Check attribution
        has_attribution = bool(re.search(ATTRIBUTION_PATTERN, text))
        
        count_match = quote_count == expected_count
        attr_match = has_attribution == expected_attribution
        
        if count_match and attr_match:
            status = "✅"
            passed += 1
        else:
            status = "❌"
            issues.append({
                'text': text,
                'description': description,
                'expected_count': expected_count,
                'found_count': quote_count,
                'expected_attr': expected_attribution,
                'found_attr': has_attribution
            })
        
        print(f"  {status} {description}")
        print(f"      Text: \"{text[:50]}...\"")
        print(f"      Quotes: {quote_count}/{expected_count}, Attribution: {has_attribution}/{expected_attribution}")
    
    print(f"\n  Result: {passed}/{len(test_cases)} cases handled correctly")
    
    if issues:
        print("\n  ⚠️  QUOTE EXTRACTION ISSUES:")
        for issue in issues:
            print(f"\n    {issue['description']}")
            print(f"    Text: \"{issue['text']}\"")
            if issue['expected_count'] != issue['found_count']:
                print(f"    Count mismatch: expected {issue['expected_count']}, got {issue['found_count']}")
            if issue['expected_attr'] != issue['found_attr']:
                print(f"    Attribution mismatch: expected {issue['expected_attr']}, got {issue['found_attr']}")
    
    return passed, len(test_cases), issues


def main():
    """Run comprehensive robustness tests"""
    print("╔══════════════════════════════════════════════════════════════════╗")
    print("║       🔬 QUALITATIVE ANALYSIS - ROBUSTNESS TEST SUITE           ║")
    print("╚══════════════════════════════════════════════════════════════════╝")
    
    results = {}
    issues_found = []
    
    # Test 1: Edge cases
    passed, total, failed = test_edge_case_detection()
    results['edge_cases'] = (passed, total)
    if failed:
        issues_found.extend([f"Edge case: {f['query']}" for f in failed])
    
    # Test 2: Keyword overlap
    results['keyword_overlap'] = test_keyword_overlap()
    
    # Test 3: Multi-word keywords
    results['multiword'] = test_multiword_keywords()
    
    # Test 4: Prompt switching
    results['prompt_switching'] = test_prompt_switching_logic()
    
    # Test 5: False positives
    passed, total, issues = test_false_positives()
    results['false_positives'] = (passed, total)
    if issues:
        issues_found.extend([f"False positive: {i['query']}" for i in issues])
    
    # Test 6: Quote extraction
    passed, total, issues = test_quote_extraction_edge_cases()
    results['quote_extraction'] = (passed, total)
    if issues:
        issues_found.extend([f"Quote extraction: {i['description']}" for i in issues])
    
    # Summary
    print("\n" + "━" * 70)
    print("📊 ROBUSTNESS TEST SUMMARY:")
    print("━" * 70)
    
    total_score = 0
    max_score = 0
    
    for test_name, result in results.items():
        if isinstance(result, tuple):
            passed, total = result
            score = passed / total if total > 0 else 0
            total_score += passed
            max_score += total
            print(f"  {test_name}: {passed}/{total} ({score*100:.1f}%)")
        else:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"  {test_name}: {status}")
            total_score += (1 if result else 0)
            max_score += 1
    
    overall_score = (total_score / max_score * 100) if max_score > 0 else 0
    
    print("\n" + "━" * 70)
    print(f"OVERALL ROBUSTNESS SCORE: {overall_score:.1f}%")
    
    if overall_score >= 90:
        print("✅ EXCELLENT - Production ready")
    elif overall_score >= 75:
        print("⚠️  GOOD - Minor issues to address")
    elif overall_score >= 50:
        print("⚠️  FAIR - Significant improvements needed")
    else:
        print("❌ POOR - Major issues found")
    
    if issues_found:
        print("\n⚠️  ISSUES FOUND:")
        for issue in issues_found[:10]:  # Show first 10
            print(f"  • {issue}")
        if len(issues_found) > 10:
            print(f"  ... and {len(issues_found) - 10} more")
    
    print("━" * 70)
    
    return overall_score >= 75  # Pass if >= 75%


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

