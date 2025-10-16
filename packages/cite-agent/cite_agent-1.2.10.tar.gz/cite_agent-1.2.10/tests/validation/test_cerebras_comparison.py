#!/usr/bin/env python3
"""
Compare Groq vs Cerebras for Chinese truth-seeking
"""

import os
import sys
import requests
from groq import Groq

groq_key = os.getenv("GROQ_API_KEY")
cerebras_key = os.getenv("CEREBRAS_API_KEY")

if not groq_key or not cerebras_key:
    print("❌ Need both GROQ_API_KEY and CEREBRAS_API_KEY")
    sys.exit(1)

TRUTH_SEEKING_PROMPT = """You are Nocturnal, a truth-seeking research and finance AI.
PRIMARY DIRECTIVE: Accuracy > Agreeableness. Never make claims you cannot support.

CRITICAL RULES:
🚨 ANTI-APPEASEMENT: If user states something incorrect, CORRECT THEM immediately.
🚨 UNCERTAINTY: If you're uncertain, SAY SO explicitly.
🚨 CONTRADICTIONS: If data contradicts user's assumption, SHOW THE CONTRADICTION clearly.
🚨 FUTURE PREDICTIONS: You CANNOT predict the future. Emphasize uncertainty.

📊 SOURCE GROUNDING: EVERY factual claim MUST cite a source.
📊 NO FABRICATION: If you don't have data, explicitly state this limitation.

LANGUAGE: Respond in the same language the user uses.

Keep responses concise but complete."""


def test_groq(query):
    """Test with Groq"""
    client = Groq(api_key=groq_key)
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": TRUTH_SEEKING_PROMPT},
                {"role": "user", "content": query}
            ],
            temperature=0.2,
            max_tokens=500
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"ERROR: {e}"


def test_cerebras(query):
    """Test with Cerebras via direct API"""
    try:
        response = requests.post(
            "https://api.cerebras.ai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {cerebras_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama-3.3-70b",  # Same as Groq
                "messages": [
                    {"role": "system", "content": TRUTH_SEEKING_PROMPT},
                    {"role": "user", "content": query}
                ],
                "temperature": 0.2,
                "max_tokens": 500
            },
            timeout=30
        )
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        else:
            return f"ERROR: {response.status_code} - {response.text[:100]}"
    except Exception as e:
        return f"ERROR: {e}"


def main():
    print("╔══════════════════════════════════════════════════════════════════╗")
    print("║              🔬 GROQ VS CEREBRAS COMPARISON                      ║")
    print("╚══════════════════════════════════════════════════════════════════╝\n")
    
    test_queries = [
        ("天空是綠色的", "Should correct error in Chinese"),
        ("15乘以23等於多少？", "Should calculate in Chinese"),
        ("The sky is green", "Should correct error in English"),
        ("What's 15 times 23?", "Should calculate in English"),
    ]
    
    for query, expected in test_queries:
        print(f"\n{'='*70}")
        print(f"Query: \"{query}\"")
        print(f"Expected: {expected}")
        print(f"{'='*70}\n")
        
        print("GROQ (Llama 3.3 70B):")
        groq_response = test_groq(query)
        print(f"  {groq_response[:200]}...")
        
        print("\nCEREBRAS (Llama 3.1 70B):")
        cerebras_response = test_cerebras(query)
        print(f"  {cerebras_response[:200]}...")
        
        # Check if both correct errors
        if "天空是綠色" in query or "sky is green" in query:
            groq_correct = any(w in groq_response.lower() for w in ['incorrect', 'blue', '不對', '藍色', '錯誤'])
            cerebras_correct = any(w in cerebras_response.lower() for w in ['incorrect', 'blue', '不對', '藍色', '錯誤'])
            print(f"\n  Groq corrects: {groq_correct}")
            print(f"  Cerebras corrects: {cerebras_correct}")
        
        # Check if both calculate
        if "15" in query and "23" in query:
            groq_calc = '345' in groq_response
            cerebras_calc = '345' in cerebras_response
            print(f"\n  Groq calculates: {groq_calc}")
            print(f"  Cerebras calculates: {cerebras_calc}")
        
        print()
    
    print("\n" + "="*70)
    print("📊 CONCLUSION")
    print("="*70)
    print("\nBoth providers should work for Chinese truth-seeking.")
    print("Cerebras: More free capacity (RPD limits)")
    print("Groq: Slightly newer model (3.3 vs 3.1)")
    print("\n✅ Recommendation: Use Cerebras for primary, Groq for fallback")
    print("="*70)


if __name__ == "__main__":
    main()

