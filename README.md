🌱 Agri-Advisor: AI-Powered Smart Farming Assistant
Agri-Advisor is a Retrieval-Augmented Generation (RAG) chatbot designed to assist farmers by providing accurate, localized agricultural advice. Unlike standard chatbots, it grounds its answers in verified PDF manuals to prevent misinformation, while featuring a "Smart Fallback" mechanism to handle general queries safely. It supports voice interaction in multiple Indian languages, making it accessible to rural users.

🚀 Key Features
📚 RAG-Based Knowledge Base: Upload farming guides (PDFs) to create a custom knowledge base. The bot retrieves exact fertilizer dosages, pest control methods, and sowing times from these documents.

🧠 Smart Fallback & Anti-Hallucination: Uses a strict "Two-Step Verification" system. If the uploaded PDF (e.g., Chilli) does not match the user's query (e.g., Cotton), the bot automatically switches to "General AI Mode" to avoid citing false sources.

🗣️ Multi-Lingual Voice Support:

Input: Listens to queries in English, Hindi, Telugu, Tamil, and Kannada.

Output: Hybrid Voice Engine using Google TTS (for high-quality native languages) and Offline System Voice (for instant English response).

🌍 Language Translation: Automatically translates vernacular queries to English for processing and the response back to the user's native language.

💻 Modern UI: Responsive, glassmorphism-inspired interface with real-time status updates and weather integration.

🛠️ Tech Stack
Frontend: HTML5, CSS3, JavaScript (Web Speech API).

Backend: Python, Flask.

AI & LLM: LangChain, DeepSeek-Chat (via OpenRouter), HuggingFace Embeddings.

Database: ChromaDB (Vector Store for PDFs), SQLite (Chat History).

Audio: gTTS (Google Text-to-Speech), pyttsx3 (Offline TTS).

Tools: pypdf, deep-translator, python-dotenv.

📂 Project Structure
Bash
Agri-Advisor/
│
├── app.py                 # Main Flask Backend Server
├── chatbot.py             # RAG Logic, LangChain & Prompt Engineering
├── ingest.py              # Script to process PDFs and store in Vector DB
├── requirements.txt       # List of Python dependencies
├── .env                   # Environment variables (API Keys)
│
├── static/                # CSS, Images, and Audio files
│   ├── images/            # Backgrounds and icons
│   └── audio/             # Temporary generated audio files
│
├── templates/
│   └── index.html         # Main User Interface
│
├── data/                  # Folder where uploaded PDFs are saved
└── vector_db/             # ChromaDB storage (Auto-generated)
⚙️ Installation & Setup
1. Prerequisites
Python 3.8 or higher installed.

An API Key for DeepSeek (or OpenAI) via OpenRouter.

2. Clone the Repository
Bash
git clone https://github.com/your-username/agri-advisor.git
cd agri-advisor
3. Create a Virtual Environment (Optional but Recommended)
Bash
python -m venv venv
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate
4. Install Dependencies
Create a requirements.txt file with the following content, or install manually:

Bash
pip install flask langchain langchain-huggingface langchain-chroma langchain-openai python-dotenv gTTS pyttsx3 deep-translator pypdf sentence-transformers
5. Configure Environment Variables
Create a file named .env in the root folder and add your API key:

Ini, TOML
OPENROUTER_API_KEY=sk-or-v1-your-key-here
LLM_MODEL=deepseek/deepseek-chat
▶️ Usage Guide
1. Start the Server
Run the application using Python:

Bash
python app.py
You should see: 🚀 Starting Smart Agri-Bot Server...

2. Access the App
Open your browser and go to: http://127.0.0.1:5001

3. How to Demo
Upload Knowledge: Click the Paperclip Icon and upload a PDF (e.g., cotton_guide.pdf). Wait for the "✅ Learned!" notification.

Ask Specifics: Type or speak: "What are the pests in Cotton?". The bot will answer citing the PDF.

Test Fallback: Ask about a crop you didn't upload (e.g., "How to grow Wheat?"). The bot will answer using General Knowledge and remove the citation.

Test Voice: Select "Tamil" from the dropdown, click the Mic, and speak in Tamil.

⚠️ Troubleshooting
Error: ModuleNotFoundError: No module named 'PyPDF2'

Fix: Run pip install pypdf (or PyPDF2).

Voice is not working for Tamil/Telugu?

Ensure you have an active internet connection (as native languages use Google TTS).

For the "Offline" mode, ensure your Windows Language Settings have the specific Language Pack installed.

"Quota Exceeded" / API Errors:

Check your .env file and ensure your OpenRouter API key has credits.

🔮 Future Scope
📱 WhatsApp Integration: Deploying the bot on WhatsApp using Twilio API for easier access.

📸 Disease Detection: Integrating Computer Vision (CNNs) to diagnose plant diseases from leaf photos.

☁️ Cloud Deployment: Hosting the application on AWS or Render for public access.

📜 License
This project is developed for educational purposes as a Final Year B.Tech Project.

Developed by: [R Jai Krishna] Batch: [2022-2026]