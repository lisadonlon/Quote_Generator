
import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import base64
from email.message import EmailMessage
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import google.generativeai as genai
import faiss
import pickle
import numpy as np
from sentence_transformers import SentenceTransformer

# Load environment variables from .env file
load_dotenv()

# Initialize the Flask application
app = Flask(__name__)
CORS(app)

# --- Add Scopes and Credentials Logic ---
SCOPES = ["https://www.googleapis.com/auth/drive.readonly", "https://www.googleapis.com/auth/gmail.modify"]

def load_google_credentials():
    """Load Google credentials from environment variables or fallback to file for development."""
    # Try to load from environment variables first (for production/Railway)
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
    refresh_token = os.getenv("GOOGLE_REFRESH_TOKEN")
    
    if client_id and client_secret and refresh_token:
        # Create credentials from environment variables
        creds_info = {
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": refresh_token,
            "type": "authorized_user"
        }
        return Credentials.from_authorized_user_info(creds_info, SCOPES)
    else:
        # Fallback to token.json file for local development
        try:
            return Credentials.from_authorized_user_file("token.json", SCOPES)
        except FileNotFoundError:
            print("⚠️ Warning: No Google credentials found. Gmail functionality will be disabled.")
            return None

# Load credentials
creds = load_google_credentials()
gmail_available = creds is not None
if gmail_available:
    print("✅ Google credentials loaded successfully.")
# ------------------------------------

# --- Configure the Gemini API ---
# Securely get the API key from the environment variable
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)

# --- System Prompt: The AI's Instructions ---
SYSTEM_PROMPT = """
You are a friendly and professional assistant for a cabinetry business owner. Your goal is to help the owner create a draft quote email.

**Use the provided examples from past quotes as a reference for style, tone, and common items.**

Follow these steps:
1.  When the user starts a new quote, ask for the client's name and what the quote is for (e.g., "Kitchen", "Media Unit").
2.  Ask clarifying questions one at a time to gather all necessary details. Use the examples to suggest common features like "soft-close drawers," "dovetailed drawer boxes," or specific materials.
3.  Prompt the user for the price of each item or option.
4.  Ask for the payment terms, suggesting a common deposit amount from the examples.
5.  Once you have all the details, confirm them with the user.
6.  When the user gives final confirmation, you MUST respond with only the marker "[DRAFT_READY]", followed by the complete and final email body, including the greeting and closing. Do not add any other conversational text.

Maintain a helpful, conversational tone.
"""

# --- Load the Knowledge Base (Vector Store) ---
print("Loading knowledge base...")
try:
    embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
    index = faiss.read_index("faiss_index.bin")
    with open("quote_data.pkl", "rb") as f:
        quote_texts = pickle.load(f)
    print("✅ Knowledge base loaded successfully.")
    knowledge_base_available = True
except Exception as e:
    print(f"⚠️ Warning: Could not load knowledge base: {e}")
    print("Quote search functionality will be limited.")
    embedding_model = None
    index = None
    quote_texts = []
    knowledge_base_available = False
# ---------------------------------------------

# Initialize the Gemini Model and Chat Session
model = genai.GenerativeModel(
    model_name='gemini-1.5-flash',
    system_instruction=SYSTEM_PROMPT
    )
chat = model.start_chat(history=[])

def find_relevant_quotes(query, top_k=3):
    if not knowledge_base_available:
        return ["Knowledge base not available - using general quote templates."]
    
    try:
        query_embedding = embedding_model.encode([query]).astype('float32')
        distances, indices = index.search(query_embedding, top_k)
        return [quote_texts[i] for i in indices[0]]
    except Exception as e:
        print(f"Error searching knowledge base: {e}")
        return ["Error accessing knowledge base - using general templates."]

@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint for Railway monitoring."""
    return jsonify({
        "status": "healthy",
        "gmail_available": gmail_available,
        "knowledge_base_available": knowledge_base_available,
        "timestamp": "2025-09-02"
    })

@app.route("/test", methods=["GET"])
def test_route():
    """Test route to verify routing is working."""
    return jsonify({"message": "Test route working!", "timestamp": "2025-09-03"})

@app.route("/chat", methods=["POST"])
def chat_handler():
    user_message = request.json.get("message", "No message received")
    try:
        relevant_quotes = find_relevant_quotes(user_message)
        context_prompt = "--- RELEVANT EXAMPLES FROM PAST QUOTES ---\n"
        for i, quote in enumerate(relevant_quotes, 1):
            context_prompt += f"\n--- Example {i} ---\n{quote}\n"
        augmented_prompt = f"{context_prompt}\n--- CURRENT CONVERSATION ---\nUser's message: {user_message}"
        response = chat.send_message(augmented_prompt)
        bot_response = response.text
    except Exception as e:
        bot_response = f"Error: {e}"
    return jsonify({"response": bot_response})

# --- Add New Function and Route for Gmail ---
def create_gmail_draft(content, user_creds):
    """Creates and saves a draft email in Gmail using provided credentials."""
    service = build("gmail", "v1", credentials=user_creds)
    message = EmailMessage()
    message.set_content(content)
    
    # Use environment variables for email addresses
    to_email = os.getenv("CLIENT_EMAIL", "client-email@example.com")
    cc_email = os.getenv("BOOKKEEPING_EMAIL", "bookkeeping@example.com")
    
    message["To"] = to_email
    message["Cc"] = cc_email
    message["Subject"] = "Your Quotation from Justin"
    
    encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
    
    create_draft_request = {'message': {'raw': encoded_message}}
    draft = service.users().drafts().create(userId='me', body=create_draft_request).execute()
    print(f"Draft created. Draft ID: {draft['id']}")

@app.route("/create_draft", methods=["POST"])
def create_draft_handler():
    """Receives the final quote text and creates a Gmail draft."""
    if not gmail_available:
        return jsonify({"status": "error", "message": "Gmail functionality is not available. Google credentials not configured."})
    
    email_content = request.json.get("content")
    try:
        # Pass the globally managed credentials to the function
        create_gmail_draft(email_content, creds)
        return jsonify({"status": "success", "message": "✅ Draft created successfully in your Gmail!"})
    except Exception as e:
        return jsonify({"status": "error", "message": f"Failed to create draft: {e}"})
# ---------------------------------------------

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)