import os.path
import pickle
from email import message_from_bytes
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

# --- Configuration ---
SCOPES = ["https://www.googleapis.com/auth/drive.readonly", "https://www.googleapis.com/auth/gmail.modify"]
DRIVE_FOLDER_NAME = "AI Quote Knowledge Base"
# ---------------------

def get_drive_service():
    """Authenticates with Google Drive and returns the service object."""
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        with open("token.json", "w") as token:
            token.write(creds.to_json())
    return build("drive", "v3", credentials=creds)

def get_email_contents(service):
    """Fetches and parses all .eml files from the specified Drive folder."""
    # 1. Find the folder ID.
    folder_id = None
    response = service.files().list(
        q=f"mimeType='application/vnd.google-apps.folder' and name='{DRIVE_FOLDER_NAME}'",
        spaces='drive',
        fields='files(id, name)'
    ).execute()
    if not response['files']:
        print(f"Folder '{DRIVE_FOLDER_NAME}' not found.")
        return []
    folder_id = response['files'][0].get('id')

    # 2. List all '.eml' files.
    results = service.files().list(
        q=f"'{folder_id}' in parents and name contains '.eml'",
        fields="files(id, name)"
    ).execute()
    items = results.get("files", [])
    
    email_texts = []
    for item in items:
        print(f"Processing: {item['name']}")
        file_content = service.files().get_media(fileId=item['id']).execute()
        msg = message_from_bytes(file_content)
        
        # Combine subject and body for a comprehensive text chunk.
        subject = msg.get('subject', '')
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == 'text/plain':
                    body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                    break
        else:
            body = msg.get_payload(decode=True).decode('utf-8', errors='ignore')
        
        full_text = f"Subject: {subject}\n\n{body}"
        email_texts.append(full_text)
        
    return email_texts

def main():
    print("Connecting to Google Drive...")
    drive_service = get_drive_service()
    
    print("\nFetching and parsing quote emails...")
    quote_texts = get_email_contents(drive_service)
    
    if not quote_texts:
        print("No quotes found. Exiting.")
        return

    print(f"\nFound {len(quote_texts)} quotes. Creating embeddings...")
    # Load a pre-trained model for creating embeddings.
    model = SentenceTransformer('all-MiniLM-L6-v2')
    embeddings = model.encode(quote_texts, show_progress_bar=True)

    # Convert to float32 for FAISS.
    embeddings = np.array(embeddings).astype('float32')

    # Create a FAISS index.
    index = faiss.IndexFlatL2(embeddings.shape[1])
    index.add(embeddings)
    
    print("\nSaving the vector store and quote data to local files...")
    # Save the FAISS index.
    faiss.write_index(index, "faiss_index.bin")
    
    # Save the corresponding quote texts.
    with open("quote_data.pkl", "wb") as f:
        pickle.dump(quote_texts, f)
        
    print("\n✅ Knowledge base created successfully!")
    print("Files 'faiss_index.bin' and 'quote_data.pkl' have been saved.")

if __name__ == "__main__":
    main()