import os
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_openai import ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate

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

    # 4. Create the Prompt Template (With GEN_AI_MODE Signal)
    # This strict prompt prevents the "Chilli vs Cotton" mix-up
    template = """
    You are an expert agricultural advisor. 
    
    Step 1: Analyze the Context. Does it specifically mention the CROP asked in the Question? 
    (e.g., if user asks about Cotton, does the Context mention Cotton?)
    
    Step 2: 
    - If YES (Context matches Crop): Answer strictly using the Context.
    - If NO (Context is about a different Crop, e.g., Chilli): IGNORE the Context completely. Answer from your General Knowledge and start your response with "GEN_AI_MODE: ".
    
    CRITICAL: Do NOT fake a citation. If the context is about Chilli but the question is Cotton, you MUST switch to General AI.

    STRICT FORMATTING RULES:
    1. **HTML Only:** Use <b> for headings and <ul>/<li> for lists. Do NOT use Markdown.
    2. **No Source Tags:** Do NOT write "(Source: ...)" in your output. Just give the answer.

    Context: {context}
    
    Question: {question}
    
    Helpful Answer:
    """
    
    # --- FIX: THIS PART WAS MISSING ---
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

        # Optional: Extract source pages if Context was used
        sources = [doc.metadata.get('source', 'Unknown') for doc in response['source_documents']]
        unique_sources = list(set(sources))
        
        return answer, unique_sources
        
    except Exception as e:
        return f"Error: {str(e)}", []
