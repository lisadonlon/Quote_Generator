# AI Quote Agent

A Flask-based AI assistant for creating cabinetry quotes with Gmail integration.

## Features

- AI-powered quote generation using Google Gemini
- Gmail draft creation for quotes
- Vector search through past quotes for context
- RESTful API endpoints

## Railway Deployment

### Prerequisites

1. Railway account
2. Google Cloud Project with Gmail API enabled
3. OAuth 2.0 credentials

### Environment Variables

Set these environment variables in your Railway project:

#### Required
- `GOOGLE_API_KEY` - Your Google Gemini API key
- `GOOGLE_CLIENT_ID` - OAuth client ID from Google Cloud
- `GOOGLE_CLIENT_SECRET` - OAuth client secret from Google Cloud
- `GOOGLE_REFRESH_TOKEN` - OAuth refresh token

#### Optional
- `CLIENT_EMAIL` - Default client email for drafts (default: client-email@example.com)
- `BOOKKEEPING_EMAIL` - Default bookkeeping email for drafts (default: bookkeeping@example.com)
- `PORT` - Port for the application (automatically set by Railway)

### Deployment Steps

1. **Connect Repository**
   - Connect your GitHub repository to Railway

2. **Set Environment Variables**
   - In Railway dashboard, go to Variables
   - Add all required environment variables listed above

3. **Deploy**
   - Railway will automatically detect the Python app and deploy it
   - The `railway.json` file configures the build and deployment

### API Endpoints

- `GET /` - Health check
- `GET /health` - Detailed health status
- `POST /chat` - Send message to AI assistant
- `POST /create_draft` - Create Gmail draft (requires Google auth)

### Local Development

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set up environment variables in `.env` file

3. Run locally:
   ```bash
   python app.py
   ```

### File Structure

- `app.py` - Main Flask application
- `requirements.txt` - Python dependencies
- `railway.json` - Railway deployment configuration
- `Procfile` - Alternative deployment configuration
- `faiss_index.bin` - Vector search index
- `quote_data.pkl` - Quote data for context
- `token.json` - Local OAuth credentials (not for production)

### Troubleshooting

- **App crashes on startup**: Check that all required environment variables are set
- **Gmail not working**: Verify Google OAuth credentials and refresh token
- **Knowledge base not loading**: Ensure `faiss_index.bin` and `quote_data.pkl` are present
- **Port issues**: Railway automatically sets the PORT environment variable
