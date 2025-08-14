# import os
# import tempfile
# import threading
# import time
# from dotenv import load_dotenv
# import speech_recognition as sr
# from langdetect import detect
# from gtts import gTTS
# from playsound import playsound

# from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
# from langchain_community.vectorstores import FAISS
# from langchain.text_splitter import RecursiveCharacterTextSplitter
# from langchain_community.document_loaders import PyPDFLoader
# from langchain.prompts import PromptTemplate
# from langchain.memory import ConversationBufferMemory
# from langchain.chains import ConversationalRetrievalChain

# # FastAPI imports
# from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware
# from pydantic import BaseModel

# # FastAPI app setup
# app = FastAPI(title="Voice AI Assistant", description="AI Assistant with voice interaction")

# # Add CORS middleware
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # Pydantic models
# class ChatMessage(BaseModel):
#     message: str

# class ChatResponse(BaseModel):
#     success: bool
#     answer: str = ""
#     error: str = ""

# class ConversationStatus(BaseModel):
#     active: bool
#     listening: bool
#     processing: bool

# class ApiResponse(BaseModel):
#     success: bool
#     message: str = ""
#     error: str = ""

# # Global state
# conversation_active = False
# is_listening = False
# is_processing = False
# conversation_thread = None

# # Load API key
# load_dotenv()
# api_key = os.getenv("GOOGLE_API_KEY")
# if not api_key:
#     raise ValueError("GOOGLE_API_KEY not found in .env file.")
# os.environ["GOOGLE_API_KEY"] = api_key
# print("Gemini API key loaded")

# # Load PDF into FAISS
# def load_pdf(file_path):
#     loader = PyPDFLoader(file_path)
#     pages = loader.load()
#     splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
#     chunks = splitter.split_documents(pages)
#     return chunks

# pdf_path = "Make your own document and then upload it here in pdf format."
# documents = load_pdf(pdf_path)
# print(f"Loaded and split into {len(documents)} chunks.")

# embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
# vector_db = FAISS.from_documents(documents, embeddings)
# retriever = vector_db.as_retriever(search_type="similarity", search_kwargs={"k": 5})
# print("Vector store created.")

# # Prompt templates
# prompt_en = PromptTemplate.from_template("""
# You're an AI assistant helping with delivery instructions based on past chat history and helpful context. 
# Respond in a professional tone and don't be too friendly.
# Don't say things like "based on the provided text" — just give the answer naturally.
# Provide the answer only from the context, if it is out of the context just say "I Don't Know".
# If you don't know the answer, say so honestly. 
# Answer naturally in English.

# Context:
# {context}

# Chat History:
# {chat_history}

# Question:
# {question}
# """)

# prompt_hi = PromptTemplate.from_template("""
# You're an AI assistant helping with delivery instructions based on past chat history and helpful context. 
# Respond in a professional tone and don't be too friendly.
# Don't say things like "based on the provided text" — just give the answer naturally.
# Provide the answer only from the context, if it is out of the context just say "I Don't Know".
# If you don't know the answer, say so honestly.
# Answer naturally in Hindi.

# Context:
# {context}

# Chat History:
# {chat_history}

# Question:
# {question}
# """)

# # LLM
# llm = ChatGoogleGenerativeAI(
#     model="models/gemini-1.5-flash",
#     temperature=0.3,
#     max_output_tokens=1024,
#     top_p=0.8,
#     top_k=40
# )

# # Memory
# memory = ConversationBufferMemory(
#     memory_key="chat_history",
#     return_messages=True,
#     output_key="answer"
# )

# # QA Chains for English and Hindi
# qa_chain_en = ConversationalRetrievalChain.from_llm(
#     llm=llm,
#     retriever=retriever,
#     memory=memory,
#     combine_docs_chain_kwargs={"prompt": prompt_en},
#     output_key="answer"
# )

# qa_chain_hi = ConversationalRetrievalChain.from_llm(
#     llm=llm,
#     retriever=retriever,
#     memory=memory,
#     combine_docs_chain_kwargs={"prompt": prompt_hi},
#     output_key="answer"
# )

# # Speech recognizer
# recognizer = sr.Recognizer()
# mic = sr.Microphone()

# # Normalize language code for TTS
# def normalize_lang_for_response(detected_lang):
#     if detected_lang.startswith("en"):
#         return "en"
#     else:
#         return "hi"

# # Listen and transcribe speech
# def listen_and_transcribe():
#     global is_listening
#     with mic as source:
#         print("Listening...")
#         recognizer.adjust_for_ambient_noise(source)
#         is_listening = True
#         audio = recognizer.listen(source)
#         is_listening = False
#     try:
#         text = recognizer.recognize_google(audio)  # auto language detection
#         print(f"You said: {text}")
#         return text
#     except sr.UnknownValueError:
#         print("Sorry, I could not understand.")
#         return None
#     except sr.RequestError as e:
#         print(f"Speech Recognition error: {e}")
#         return None

# # Speak text with gTTS in proper language
# def speak_with_gtts(text, lang_code):
#     try:
#         lang_code = normalize_lang_for_response(lang_code)
#         with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
#             temp_filename = tmp_file.name
#         tts = gTTS(text=text, lang=lang_code, tld="co.in", slow=False)
#         tts.save(temp_filename)
#         playsound(temp_filename)
#         os.remove(temp_filename)
#     except Exception as e:
#         print(f"TTS error: {e}")

# # Conversation loop
# def conversation_loop():
#     global conversation_active, is_listening, is_processing
#     print("Starting conversation loop...")
#     speak_with_gtts("Hello! How can I help you?", "en")

#     while conversation_active:
#         try:
#             user_input = listen_and_transcribe()
#             if not user_input:
#                 time.sleep(1)
#                 continue

#             if any(word in user_input.lower() for word in ["exit", "quit", "stop", "bye", "goodbye"]):
#                 speak_with_gtts("Goodbye! Thank you for using the assistant.", "en")
#                 break

#             is_processing = True

#             try:
#                 detected_lang = detect(user_input)
#             except:
#                 detected_lang = "en"

#             print(f"Detected language: {detected_lang}")

#             # Choose chain and TTS language based on detected language
#             if detected_lang.startswith("en"):
#                 response = qa_chain_en.invoke({"question": user_input})
#                 tts_lang = "en"
#             else:
#                 response = qa_chain_hi.invoke({"question": user_input})
#                 tts_lang = "hi"

#             ai_text = response["answer"]
#             print("AI:", ai_text)

#             speak_with_gtts(ai_text, tts_lang)
#             is_processing = False

#         except Exception as e:
#             print(f"Error in conversation loop: {e}")
#             is_listening = False
#             is_processing = False
#             time.sleep(2)

#     conversation_active = False
#     is_listening = False
#     is_processing = False
#     print("Conversation loop ended")

# # FastAPI routes
# @app.get("/", summary="Health Check")
# async def root():
#     return {"message": "Voice AI Assistant API is running", "chatbot_ready": qa_chain_en is not None and qa_chain_hi is not None}

# @app.post("/start-conversation", response_model=ApiResponse)
# async def start_conversation():
#     global conversation_active, conversation_thread
#     if not qa_chain_en or not qa_chain_hi:
#         return ApiResponse(success=False, error="Chatbot not initialized.")
#     if conversation_active:
#         return ApiResponse(success=False, error="Conversation already active.")
#     conversation_active = True
#     conversation_thread = threading.Thread(target=conversation_loop, daemon=True)
#     conversation_thread.start()
#     return ApiResponse(success=True, message="Conversation started successfully.")

# @app.post("/stop-conversation", response_model=ApiResponse)
# async def stop_conversation():
#     global conversation_active
#     if not conversation_active:
#         return ApiResponse(success=False, error="No active conversation.")
#     conversation_active = False
#     time.sleep(1)
#     return ApiResponse(success=True, message="Conversation stopped successfully.")

# @app.get("/status", response_model=ConversationStatus)
# async def get_status():
#     return ConversationStatus(active=conversation_active, listening=is_listening, processing=is_processing)

# @app.post("/chat", response_model=ChatResponse)
# async def chat(message: ChatMessage):
#     if not qa_chain_en or not qa_chain_hi:
#         return ChatResponse(success=False, error="Chatbot not initialized")
#     if not message.message:
#         return ChatResponse(success=False, error="No message provided")

#     try:
#         detected_lang = detect(message.message)
#     except:
#         detected_lang = "en"

#     print(f"Detected language: {detected_lang}")

#     if detected_lang.startswith("en"):
#         response = qa_chain_en.invoke({"question": message.message})
#         tts_lang = "en"
#     else:
#         response = qa_chain_hi.invoke({"question": message.message})
#         tts_lang = "hi"

#     return ChatResponse(success=True, answer=response["answer"])

# # Run FastAPI
# if __name__ == "_main_":
#     import uvicorn
#     print("Starting FastAPI server...")
#     uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)



import os
import tempfile
import base64
from io import BytesIO
from dotenv import load_dotenv
import speech_recognition as sr
from langdetect import detect
from gtts import gTTS

from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain

# FastAPI imports
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app setup
app = FastAPI(title="RAG-Based Delivery Agent", description="AI Assistant with delivery manual knowledge")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://rag-based-delivery-agent.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class ChatMessage(BaseModel):
    message: str
    language: str = "auto"  # auto, en, hi

class ChatResponse(BaseModel):
    success: bool
    answer: str = ""
    detected_language: str = ""
    error: str = ""

class TTSRequest(BaseModel):
    text: str
    language: str = "en"

class TTSResponse(BaseModel):
    success: bool
    audio_base64: str = ""
    error: str = ""

class ApiResponse(BaseModel):
    success: bool
    message: str = ""
    error: str = ""

# Global variables
qa_chain_en = None
qa_chain_hi = None
vector_db = None
is_initialized = False

# Load API key
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    logger.error("GOOGLE_API_KEY not found in environment variables")
    raise ValueError("GOOGLE_API_KEY is required")
else:
    os.environ["GOOGLE_API_KEY"] = api_key
    logger.info("Google API key loaded successfully")

def load_bundled_pdf():
    """Load the bundled PDF document"""
    try:
        # Get the directory where this script is located
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Look for PDF in documents folder
        documents_dir = os.path.join(current_dir, "documents")
        pdf_files = []
        
        if os.path.exists(documents_dir):
            pdf_files = [f for f in os.listdir(documents_dir) if f.endswith('.pdf')]
        
        if not pdf_files:
            # If no documents folder, look in current directory
            pdf_files = [f for f in os.listdir(current_dir) if f.endswith('.pdf')]
            pdf_path = os.path.join(current_dir, pdf_files[0]) if pdf_files else None
        else:
            pdf_path = os.path.join(documents_dir, pdf_files[0])
        
        if not pdf_path or not os.path.exists(pdf_path):
            logger.error("No PDF document found. Please add your PDF to the documents/ folder")
            return []
        
        logger.info(f"Loading PDF from: {pdf_path}")
        
        # Load PDF
        loader = PyPDFLoader(pdf_path)
        pages = loader.load()
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000, 
            chunk_overlap=100,
            separators=["\n\n", "\n", " ", ""]
        )
        chunks = splitter.split_documents(pages)
        
        logger.info(f"Successfully loaded PDF with {len(chunks)} chunks")
        logger.info(f"Sample content: {chunks[0].page_content[:200]}..." if chunks else "No content found")
        
        return chunks
        
    except Exception as e:
        logger.error(f"Error loading bundled PDF: {e}")
        return []

def initialize_chains(documents):
    """Initialize QA chains with documents"""
    global qa_chain_en, qa_chain_hi, vector_db, is_initialized
    
    try:
        if not documents:
            logger.error("No documents provided for initialization")
            return False
            
        # Create embeddings and vector store
        embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
        vector_db = FAISS.from_documents(documents, embeddings)
        retriever = vector_db.as_retriever(search_type="similarity", search_kwargs={"k": 5})
        logger.info("Vector store created successfully")

        # Prompt templates
        prompt_en = PromptTemplate.from_template("""
        You are a professional delivery assistant with access to delivery manual and guidelines.
        Use the provided context to answer questions about deliveries, routes, procedures, and policies.
        
        Important instructions:
        - Answer only based on the provided context
        - If the information is not in the context, say "I don't have that information in my delivery manual"
        - Be helpful, clear, and professional
        - Provide step-by-step instructions when applicable
        - Answer in English

        Context from delivery manual:
        {context}

        Previous conversation:
        {chat_history}

        Customer question: {question}
        
        Answer:""")

        prompt_hi = PromptTemplate.from_template("""
        आप एक पेशेवर डिलीवरी सहायक हैं जिसके पास डिलीवरी मैनुअल और दिशा-निर्देशों तक पहुंच है।
        डिलीवरी, मार्गों, प्रक्रियाओं और नीतियों के बारे में प्रश्नों का उत्तर देने के लिए प्रदान किए गए संदर्भ का उपयोग करें।
        
        महत्वपूर्ण निर्देश:
        - केवल प्रदान किए गए संदर्भ के आधार पर उत्तर दें
        - यदि जानकारी संदर्भ में नहीं है, तो कहें "मेरे पास अपने डिलीवरी मैनुअल में यह जानकारी नहीं है"
        - सहायक, स्पष्ट और पेशेवर बनें
        - जब लागू हो तो चरण-दर-चरण निर्देश प्रदान करें
        - हिंदी में उत्तर दें

        डिलीवरी मैनुअल से संदर्भ:
        {context}

        पिछली बातचीत:
        {chat_history}

        ग्राहक का प्रश्न: {question}
        
        उत्तर:""")

        # LLM
        llm = ChatGoogleGenerativeAI(
            model="models/gemini-1.5-flash",
            temperature=0.2,
            max_output_tokens=1024,
            top_p=0.8,
            top_k=40
        )

        # Memory
        memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            output_key="answer"
        )

        # QA Chains
        qa_chain_en = ConversationalRetrievalChain.from_llm(
            llm=llm,
            retriever=retriever,
            memory=memory,
            combine_docs_chain_kwargs={"prompt": prompt_en},
            output_key="answer"
        )

        qa_chain_hi = ConversationalRetrievalChain.from_llm(
            llm=llm,
            retriever=retriever,
            memory=memory,
            combine_docs_chain_kwargs={"prompt": prompt_hi},
            output_key="answer"
        )

        is_initialized = True
        logger.info("QA chains initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error initializing chains: {e}")
        return False

def detect_language(text):
    """Detect language of text"""
    try:
        detected = detect(text)
        return "hi" if detected == "hi" else "en"
    except:
        return "en"

def create_tts_audio(text, lang_code):
    """Create TTS audio and return as base64"""
    try:
        # Normalize language
        tts_lang = "hi" if lang_code == "hi" else "en"
        
        # Create TTS
        tts = gTTS(text=text, lang=tts_lang, tld="co.in", slow=False)
        
        # Save to BytesIO
        audio_buffer = BytesIO()
        tts.write_to_fp(audio_buffer)
        audio_buffer.seek(0)
        
        # Convert to base64
        audio_base64 = base64.b64encode(audio_buffer.read()).decode('utf-8')
        return audio_base64
        
    except Exception as e:
        logger.error(f"TTS error: {e}")
        return None

# Initialize on startup
@app.on_event("startup")
async def startup_event():
    """Initialize the system with bundled PDF on startup"""
    global is_initialized
    
    logger.info("Starting up RAG Delivery Agent...")
    
    # Load the bundled PDF
    documents = load_bundled_pdf()
    
    if documents:
        success = initialize_chains(documents)
        if success:
            logger.info("System initialized successfully with delivery manual")
        else:
            logger.error("Failed to initialize AI chains")
    else:
        logger.error("Failed to load delivery manual PDF")

# FastAPI routes
@app.get("/")
async def root():
    return {
        "message": "RAG-Based Delivery Agent API", 
        "status": "running",
        "initialized": is_initialized,
        "description": "AI assistant trained on delivery manual - ready to help with delivery questions!"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "initialized": is_initialized,
        "api_key_loaded": bool(api_key),
        "ready_for_chat": is_initialized
    }

@app.post("/chat", response_model=ChatResponse)
async def chat(message: ChatMessage):
    """Chat with the delivery assistant"""
    if not is_initialized:
        return ChatResponse(
            success=False, 
            error="Delivery assistant is not ready. The delivery manual may not have loaded properly."
        )
    
    if not message.message.strip():
        return ChatResponse(success=False, error="Please provide a message")

    try:
        # Detect language
        if message.language == "auto":
            detected_lang = detect_language(message.message)
        else:
            detected_lang = message.language

        logger.info(f"Processing message in {detected_lang}: {message.message[:50]}...")

        # Choose appropriate chain
        chain = qa_chain_hi if detected_lang == "hi" else qa_chain_en
        
        # Get response
        response = chain.invoke({"question": message.message})
        
        return ChatResponse(
            success=True, 
            answer=response["answer"],
            detected_language=detected_lang
        )
        
    except Exception as e:
        logger.error(f"Error in chat: {e}")
        return ChatResponse(success=False, error=f"Error processing your question: {str(e)}")

@app.post("/tts", response_model=TTSResponse)
async def text_to_speech(request: TTSRequest):
    """Convert text to speech"""
    if not request.text.strip():
        return TTSResponse(success=False, error="No text provided")
        
    try:
        audio_base64 = create_tts_audio(request.text, request.language)
        
        if audio_base64:
            return TTSResponse(success=True, audio_base64=audio_base64)
        else:
            return TTSResponse(success=False, error="Failed to generate audio")
            
    except Exception as e:
        logger.error(f"Error in TTS: {e}")
        return TTSResponse(success=False, error=f"TTS error: {str(e)}")

@app.get("/clear-memory", response_model=ApiResponse)
async def clear_memory():
    """Clear conversation memory"""
    try:
        if qa_chain_en and qa_chain_hi:
            qa_chain_en.memory.clear()
            qa_chain_hi.memory.clear()
            return ApiResponse(success=True, message="Conversation history cleared")
        else:
            return ApiResponse(success=False, error="System not initialized")
    except Exception as e:
        return ApiResponse(success=False, error=f"Error clearing memory: {str(e)}")

@app.get("/system-info")
async def get_system_info():
    """Get information about the loaded document and system status"""
    info = {
        "initialized": is_initialized,
        "api_ready": bool(api_key),
        "chains_loaded": bool(qa_chain_en and qa_chain_hi),
        "vector_db_loaded": bool(vector_db),
    }
    
    if vector_db:
        try:
            info["document_chunks"] = vector_db.index.ntotal
        except:
            info["document_chunks"] = "unknown"
    
    return info

# Run the app
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
