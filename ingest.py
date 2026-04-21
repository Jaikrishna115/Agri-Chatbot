import os
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

DB_PATH = "vector_db"

def add_file_to_db(file_path):
    print(f"🔄 Processing single file: {file_path}...")
    
    # 1. Load ONLY the new file
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return False

    loader = PyPDFLoader(file_path)
    documents = loader.load()
    
    # 2. Split into chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    chunks = text_splitter.split_documents(documents)
    print(f"🧩 Split new file into {len(chunks)} text chunks.")

    # 3. Add to EXISTING Database (Do not delete the old one!)
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    
    # This loads the DB and appends the new data
    vectordb = Chroma(persist_directory=DB_PATH, embedding_function=embeddings)
    vectordb.add_documents(chunks)
    
    print(f"✅ Success! Added {os.path.basename(file_path)} to the Brain.")
    return True

if __name__ == "__main__":
    # Test run
    print("Run this via app.py, not directly.")