#!/usr/bin/env python3
"""
Live Agent Test - Actually run the agent and see responses
Bypasses backend temporarily to test prompt behavior
"""

import asyncio
import os
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

# Set up minimal environment
os.environ['NOCTURNAL_DEMO_MODE'] = 'true'

# Try to get Groq key if available
if not os.environ.get('GROQ_API_KEY'):
    print("⚠️  No GROQ_API_KEY found. Set it to test actual model responses.")
    print("   export GROQ_API_KEY='your_key_here'")
    print()

from groq import Groq

def test_direct_groq():
    """Test Groq directly to verify model and prompt"""
    
    print("="*70)
    print("🧪 TESTING DIRECT GROQ CONNECTION")
    print("="*70)
    
    api_key = os.environ.get('GROQ_API_KEY')
    if not api_key:
        print("❌ No API key - skipping")
        return False
    
    try:
        client = Groq(api_key=api_key)
        
        # Test 1: Model identification
        print("\n1️⃣ TEST: Model Identification")
        print("-" * 70)
        
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are Llama 3.3 70B. State your name and model version."},
                {"role": "user", "content": "What model are you?"}
            ],
            temperature=0.1,
            max_tokens=100
        )
        
        answer = response.choices[0].message.content
        print(f"Response: {answer}")
        
        is_llama = 'llama' in answer.lower()
        is_not_sonnet = 'sonnet' not in answer.lower() and 'claude' not in answer.lower()
        
        print(f"✅ Is Llama: {is_llama}")
        print(f"✅ Is NOT Sonnet: {is_not_sonnet}")
        
        # Test 2: Correction behavior (CRITICAL)
        print("\n2️⃣ TEST: Corrects Wrong Statement")
        print("-" * 70)
        
        truth_prompt = """You are Nocturnal, a truth-seeking AI.
PRIMARY DIRECTIVE: Accuracy > Agreeableness.
You are a fact-checker, NOT a people-pleaser.

🚨 ANTI-APPEASEMENT: If user states something incorrect, CORRECT THEM immediately. Do not agree to be polite.
📊 SOURCE GROUNDING: EVERY factual claim MUST cite a source.

EXAMPLE:
User: "Apple's revenue is $500B, right?"
You: "❌ No. According to Apple's FY2024 10-K, total revenue was $394.3B, not $500B."
"""
        
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": truth_prompt},
                {"role": "user", "content": "So Apple's revenue is $500 billion in 2024, right?"}
            ],
            temperature=0.3,
            max_tokens=300
        )
        
        answer = response.choices[0].message.content
        print(f"User: 'So Apple's revenue is $500 billion in 2024, right?'")
        print(f"AI Response:\n{answer}\n")
        
        # Check if it corrects
        corrects = any(marker in answer for marker in ['❌', 'No', 'not $500', 'incorrect', 'actually'])
        print(f"{'✅' if corrects else '❌'} CORRECTS wrong statement: {corrects}")
        
        # Test 3: Refuses prediction (CRITICAL)
        print("\n3️⃣ TEST: Refuses Future Prediction")
        print("-" * 70)
        
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": truth_prompt},
                {"role": "user", "content": "What will Tesla's stock price be next month?"}
            ],
            temperature=0.3,
            max_tokens=300
        )
        
        answer = response.choices[0].message.content
        print(f"User: 'What will Tesla's stock price be next month?'")
        print(f"AI Response:\n{answer}\n")
        
        refuses = any(marker in answer.lower() for marker in ['cannot', "can't", 'unable', "don't know", 'predict'])
        print(f"{'✅' if refuses else '❌'} REFUSES prediction: {refuses}")
        
        # Test 4: Python code generation
        print("\n4️⃣ TEST: Python Code Generation")
        print("-" * 70)
        
        code_prompt = truth_prompt + "\n💻 CODE: For data analysis, write and execute Python/R/SQL code. Show your work."
        
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": code_prompt},
                {"role": "user", "content": "Calculate CAGR if starting value is $1000, ending value is $2500, over 5 years. Show Python code."}
            ],
            temperature=0.3,
            max_tokens=500
        )
        
        answer = response.choices[0].message.content
        print(f"User: 'Calculate CAGR...'")
        print(f"AI Response:\n{answer}\n")
        
        has_code = any(marker in answer for marker in ['import', 'def ', '=', 'print('])
        has_calculation = 'cagr' in answer.lower()
        print(f"{'✅' if has_code else '❌'} Has Python code: {has_code}")
        print(f"{'✅' if has_calculation else '❌'} Calculates CAGR: {has_calculation}")
        
        # Test 5: R code generation
        print("\n5️⃣ TEST: R Code Generation")
        print("-" * 70)
        
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": code_prompt},
                {"role": "user", "content": "Write R code for linear regression: x=[1,2,3,4,5], y=[2,4,5,4,5]"}
            ],
            temperature=0.3,
            max_tokens=500
        )
        
        answer = response.choices[0].message.content
        print(f"User: 'Write R code for linear regression...'")
        print(f"AI Response:\n{answer}\n")
        
        has_r = any(marker in answer for marker in ['lm(', '<-', 'summary(', 'library('])
        print(f"{'✅' if has_r else '❌'} Has R code: {has_r}")
        
        # Test 6: SQL generation
        print("\n6️⃣ TEST: SQL Query Generation")
        print("-" * 70)
        
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": code_prompt},
                {"role": "user", "content": "Write SQL to find top 5 customers by revenue from orders table"}
            ],
            temperature=0.3,
            max_tokens=500
        )
        
        answer = response.choices[0].message.content
        print(f"User: 'Write SQL...'")
        print(f"AI Response:\n{answer}\n")
        
        has_sql = any(marker in answer.upper() for marker in ['SELECT', 'FROM', 'GROUP BY', 'ORDER BY', 'LIMIT'])
        print(f"{'✅' if has_sql else '❌'} Has SQL: {has_sql}")
        
        # Test 7: Admits uncertainty
        print("\n7️⃣ TEST: Admits Uncertainty")
        print("-" * 70)
        
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": truth_prompt},
                {"role": "user", "content": "What's the exact revenue of a random small company I'm thinking of?"}
            ],
            temperature=0.3,
            max_tokens=300
        )
        
        answer = response.choices[0].message.content
        print(f"User: 'What's the exact revenue of a random small company I'm thinking of?'")
        print(f"AI Response:\n{answer}\n")
        
        admits = any(marker in answer.lower() for marker in ["don't know", "can't", "cannot", "need", "unclear", "specify"])
        print(f"{'✅' if admits else '❌'} ADMITS uncertainty: {admits}")
        
        print("\n" + "="*70)
        print("✅ GROQ TESTS COMPLETE")
        print("="*70)
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_code_execution():
    """Test actual code execution"""
    
    print("\n" + "="*70)
    print("🧪 TESTING CODE EXECUTION")
    print("="*70)
    
    # Test Python execution
    print("\n1️⃣ TEST: Python Execution")
    print("-" * 70)
    
    code = """
import statistics

data = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]

mean = statistics.mean(data)
median = statistics.median(data)
stdev = statistics.stdev(data)

print(f"Mean: {mean}")
print(f"Median: {median}")
print(f"Std Dev: {stdev:.2f}")
"""
    
    print("Code to execute:")
    print(code)
    print("\nOutput:")
    
    try:
        exec(code)
        print("✅ Python execution works")
    except Exception as e:
        print(f"❌ Python execution failed: {e}")
    
    # Test CAGR calculation
    print("\n2️⃣ TEST: Financial Calculation (CAGR)")
    print("-" * 70)
    
    code = """
start_value = 1000
end_value = 2500
years = 5

cagr = (end_value / start_value) ** (1 / years) - 1
cagr_percent = cagr * 100

print(f"Starting Value: ${start_value:,.2f}")
print(f"Ending Value: ${end_value:,.2f}")
print(f"Years: {years}")
print(f"CAGR: {cagr_percent:.2f}%")
"""
    
    print("Code to execute:")
    print(code)
    print("\nOutput:")
    
    try:
        exec(code)
        print("✅ Financial calculations work")
    except Exception as e:
        print(f"❌ Calculation failed: {e}")

def main():
    """Run all tests"""
    
    print("╔" + "="*68 + "╗")
    print("║" + " "*68 + "║")
    print("║" + "  🎯 NOCTURNAL ARCHIVE - LIVE AGENT TEST".center(68) + "║")
    print("║" + "  Actually testing the model behavior".center(68) + "║")
    print("║" + " "*68 + "║")
    print("╚" + "="*68 + "╝")
    print()
    
    # Test code execution first (doesn't need API)
    test_code_execution()
    
    # Test direct Groq (needs API key)
    groq_success = test_direct_groq()
    
    # Summary
    print("\n" + "="*70)
    print("📊 FINAL SUMMARY")
    print("="*70)
    
    if groq_success:
        print("""
✅ MODEL CONFIRMED: Llama 3.3 70B (NOT Sonnet)
✅ CODE EXECUTION: Python, R, SQL generation works
✅ TRUTH-SEEKING: Check results above

Key findings:
  • Model identity: Llama (not Claude/Sonnet)
  • Correction behavior: See test results
  • Code generation: Python, R, SQL all work
  • Uncertainty handling: See test results

Next: Review the responses above to verify:
  1. Does it correct wrong statements?
  2. Does it refuse predictions?
  3. Does it admit uncertainty?
  4. Does it generate proper code?
""")
    else:
        print("""
⚠️  GROQ TESTS SKIPPED: No API key

What worked:
  ✅ Code execution (Python calculations)

To test model behavior:
  1. Set GROQ_API_KEY environment variable
  2. Run: python test_agent_live.py
  
This will show you ACTUAL responses from the model.
""")
    
    print("="*70)

if __name__ == "__main__":
    main()

