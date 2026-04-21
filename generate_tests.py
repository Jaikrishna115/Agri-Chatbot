import os
import json
import PyPDF2
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv

load_dotenv()

# CONFIG
DATA_FOLDER = "data"
OUTPUT_FILE = "automated_test_data.json"
API_KEY = os.getenv("OPENROUTER_API_KEY")
MODEL_NAME = os.getenv("LLM_MODEL", "deepseek/deepseek-chat")

# Setup LLM for generating questions
llm = ChatOpenAI(
    model=MODEL_NAME,
    openai_api_key=API_KEY,
    openai_api_base="https://openrouter.ai/api/v1",
    temperature=0.7 
)

def extract_text_from_pdf(filepath, max_pages=3):
    """Extracts text from the first few pages of a PDF."""
    text = ""
    try:
        with open(filepath, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            # Limit to first few pages to save tokens
            for i in range(min(len(reader.pages), max_pages)):
                text += reader.pages[i].extract_text()
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
    return text

def generate_questions(text, source_name):
    """Asks AI to generate test cases from the text."""
    
    prompt = PromptTemplate(
        template="""
        You are a strict teacher. I will give you a text from a farming guide: "{source_name}".
        
        Generate 3 specific, difficult questions based ONLY on this text.
        For each question, list 3 keywords that MUST appear in the answer.
        
        Output strictly in this JSON format (no markdown, no extra text):
        [
            {{
                "question": "Question text here?",
                "expected_type": "PDF",
                "keywords": ["keyword1", "keyword2", "keyword3"]
            }},
            ...
        ]
        
        TEXT CONTENT:
        {text_content}
        """,
        input_variables=["source_name", "text_content"]
    )
    
    chain = prompt | llm
    try:
        response = chain.invoke({"source_name": source_name, "text_content": text[:3000]}) # Limit text size
        # Clean up code blocks if the AI adds them
        clean_json = response.content.replace("```json", "").replace("```", "").strip()
        return json.loads(clean_json)
    except Exception as e:
        print(f"Error generating questions for {source_name}: {e}")
        return []

def main():
    all_tests = []
    
    # 1. Generate PDF-based Questions
    if not os.path.exists(DATA_FOLDER):
        print(f"❌ Error: '{DATA_FOLDER}' folder not found.")
        return

    print("🤖 Reading PDFs and generating questions...")
    for filename in os.listdir(DATA_FOLDER):
        if filename.endswith(".pdf"):
            print(f"   Processing: {filename}...")
            path = os.path.join(DATA_FOLDER, filename)
            text = extract_text_from_pdf(path)
            
            if text:
                questions = generate_questions(text, filename)
                all_tests.extend(questions)
                print(f"   ✅ Generated {len(questions)} questions.")

    # 2. Add Standard Hallucination Tests (Hardcoded)
    print("   Adding General AI/Hallucination checks...")
    hallucination_tests = [
        {"question": "Who is the President of USA?", "expected_type": "General AI", "keywords": ["President"]},
        {"question": "How to make a pizza?", "expected_type": "General AI", "keywords": ["dough", "cheese"]},
        {"question": "What is the capital of Japan?", "expected_type": "General AI", "keywords": ["Tokyo"]}
    ]
    all_tests.extend(hallucination_tests)

    # 3. Save to File
    with open(OUTPUT_FILE, "w") as f:
        json.dump(all_tests, f, indent=4)
    
    print(f"\n✨ Success! Generated {len(all_tests)} test cases in '{OUTPUT_FILE}'")

if __name__ == "__main__":
    main()