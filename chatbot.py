import os
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_openai import ChatOpenAI
from langchain_classic.chains import RetrievalQA
from langchain_core.prompts import PromptTemplate

# Load environment variables
load_dotenv()

DB_PATH = "vector_db"
API_KEY = os.getenv("OPENROUTER_API_KEY") 
MODEL_NAME = os.getenv("LLM_MODEL", "deepseek/deepseek-chat")

def get_agri_bot():
    # 1. Load the Vector Database
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    vectordb = Chroma(persist_directory=DB_PATH, embedding_function=embeddings)
    
    # 2. Setup the Retriever
    retriever = vectordb.as_retriever(search_kwargs={"k": 5})

    # 3. Setup DeepSeek via OpenRouter
    llm = ChatOpenAI(
        model=MODEL_NAME, 
        openai_api_key=API_KEY,
        openai_api_base="https://openrouter.ai/api/v1",
        temperature=0.3
    )

    # 4. Create the Prompt Template (With GEN_AI_MODE Signal Restored)
    template = """You are an expert agricultural advisor.

INTERNAL INSTRUCTIONS:
Evaluate if the provided Context mentions the specific crop or topic asked in the Question.
- If YES: Formulate your answer using the Context.
- If NO: Formulate your answer using your expert general knowledge AND you MUST start your response with the exact hidden signal: "GEN_AI_MODE: "

STRICT COMMUNICATION RULES (YOU MUST OBEY THESE):
1. NEVER narrate your thought process. 
2. NEVER use the words "Context", "provided text", or "General Knowledge" in your response.
3. NEVER write phrases like "The context does not mention..."
4. Start your answer immediately and directly (immediately after the GEN_AI_MODE tag if applicable).

STRICT FORMATTING RULES:
1. HTML ONLY: Use <b> for headings and <ul>/<li> for lists. Do NOT use Markdown (no ** or #).
2. NO CITATIONS: Do NOT write "(Source: ...)" or anything similar in your output.

Context: {context}

Question: {question}

Helpful Answer:"""
    
    prompt = PromptTemplate(
        template=template, 
        input_variables=["context", "question"]
    )

    # 5. Create the Chain
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        chain_type_kwargs={"prompt": prompt},
        return_source_documents=True
    )
    
    return qa_chain

# Initialize once to save time
agri_bot_chain = get_agri_bot()

def ask_bot(query):
    try:
        response = agri_bot_chain.invoke({"query": query})
        answer = response['result']
        
        # --- DETECT THE SECRET SIGNAL ---
        if "GEN_AI_MODE:" in answer:
            # Bot admitted it used General AI.
            # 1. Remove the tag so the user doesn't see it
            clean_answer = answer.replace("GEN_AI_MODE:", "").strip()
            # 2. FORCE SOURCES TO BE EMPTY (So frontend shows "General AI Knowledge")
            return clean_answer, []

        # Extract source pages if Context was used
        sources = [doc.metadata.get('source', 'Unknown') for doc in response['source_documents']]
        unique_sources = list(set(sources))
        
        return answer, unique_sources
        
    except Exception as e:
        return f"Error: {str(e)}", []