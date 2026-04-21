import pandas as pd
import json
import os
from chatbot import ask_bot

# --- CONFIGURATION ---
AUTOMATED_FILE = "automated_test_data.json"

def load_test_data():
    """Loads questions from the JSON file if it exists."""
    if os.path.exists(AUTOMATED_FILE):
        try:
            with open(AUTOMATED_FILE, "r") as f:
                data = json.load(f)
                print(f"\n📂 SUCCESS: Loaded {len(data)} questions from '{AUTOMATED_FILE}'")
                return data
        except Exception as e:
            print(f"⚠️ Error reading JSON file: {e}")
    
    print("\n⚠️ WARNING: Automated test file not found or empty.")
    print("   -> Using default hardcoded questions instead.")
    return [
        # Fallback data if file is missing
        {"question": "What is the fertilizer dose for rice?", "expected_type": "PDF", "keywords": ["nitrogen"]},
        {"question": "Who is the Prime Minister of India?", "expected_type": "General AI", "keywords": ["Modi"]}
    ]

def run_evaluation():
    # 1. Load Data
    test_data = load_test_data()
    
    if not test_data:
        print("❌ No test data available to run.")
        return

    print("🚀 Starting Accuracy Evaluation...\n")
    
    total_tests = len(test_data)
    correct_retrievals = 0
    hallucination_prevention_success = 0
    hallucination_tests = 0
    
    results = []

    for i, test in enumerate(test_data):
        print(f"Test {i+1}: {test['question']}")
        
        # Ask the Bot
        response, sources = ask_bot(test["question"])
        
        # --- METRIC 1: RETRIEVAL ACCURACY ---
        is_correct_source = False
        
        # Check based on Expected Type
        if test["expected_type"] == "PDF":
            # Pass if sources is NOT empty
            if sources and len(sources) > 0:
                is_correct_source = True
                correct_retrievals += 1
            else:
                print(f"   ❌ Failed Retrieval. Expected PDF, got General AI.")
        
        elif test["expected_type"] == "General AI":
            hallucination_tests += 1
            # Pass if sources IS empty
            if not sources or len(sources) == 0:
                is_correct_source = True
                hallucination_prevention_success += 1
            else:
                 print(f"   ❌ Failed Hallucination Check. Expected General AI, got PDF.")
        
        # --- METRIC 2: KEYWORD CHECK ---
        # Ensure keywords exist and are strings
        keywords = test.get("keywords", [])
        if isinstance(keywords, str): keywords = [keywords] # Handle errors if JSON has string instead of list
        
        has_keywords = False
        if not keywords:
            has_keywords = True # Pass if no keywords defined
        else:
            has_keywords = any(str(k).lower() in response.lower() for k in keywords)
        
        status = "✅ PASS" if (is_correct_source and has_keywords) else "❌ FAIL"
        print(f"   Result: {status}\n")
        
        results.append({
            "Question": test["question"],
            "Expected": test["expected_type"],
            "Actual Source": "PDF" if sources else "General AI",
            "Result": status
        })

    # --- CALCULATION ---
    # Avoid division by zero
    valid_pdf_tests = total_tests - hallucination_tests
    
    retrieval_acc = (correct_retrievals / valid_pdf_tests * 100) if valid_pdf_tests > 0 else 0
    prevention_rate = (hallucination_prevention_success / hallucination_tests * 100) if hallucination_tests > 0 else 0
    total_acc = (correct_retrievals + hallucination_prevention_success) / total_tests * 100

    print("="*30)
    print("📊 FINAL EVALUATION REPORT")
    print("="*30)
    print(f"Total Questions:             {total_tests}")
    print(f"Retrieval Accuracy (PDFs):   {retrieval_acc:.2f}%")
    print(f"Hallucination Prevention:    {prevention_rate:.2f}%")
    print(f"Overall System Accuracy:     {total_acc:.2f}%")
    print("="*30)
    
    pd.DataFrame(results).to_csv("accuracy_report.csv", index=False)
    print("Detailed report saved to 'accuracy_report.csv'")

if __name__ == "__main__":
    run_evaluation()