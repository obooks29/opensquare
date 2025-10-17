# 🔐 OpenSquare

## AI-Powered Financial Transparency Platform

**No Hidden Space for Financial Misappropriation**

### 🎯 Mission

OpenSquare makes public spending data accessible and understandable through conversational AI, empowering citizens, journalists, and donors to hold organizations accountable.

---

## ✨ Features

### 🤖 Conversational AI
- Ask questions in plain language about public spending
- Natural language understanding powered by Google Vertex AI (Gemini)
- Multi-turn conversations with context awareness

### 📄 Document Management
- Upload financial documents (PDF, Excel, CSV)
- Automatic text extraction and processing
- Full-text search powered by Elasticsearch

### 🔔 Smart Alerts
- Set watchlists for keywords and topics
- Get notified when matching documents appear
- Monitor organizations in real-time

### 📊 Data Analysis
- Automatic anomaly detection
- Spending pattern analysis
- Comparative metrics across organizations

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│         Frontend (React)                 │
│  - Chat Interface                       │
│  - Document Upload                      │
│  - Visualization                        │
└──────────────┬──────────────────────────┘
               │ HTTP/REST API
┌──────────────▼──────────────────────────┐
│      Backend (Flask Python)              │
│  - API Endpoints                        │
│  - RAG Pipeline                         │
│  - Document Processing                  │
└──────────────┬──────────────────────────┘
     ┌────────┼────────┐
     │        │        │
┌────▼──┐ ┌───▼────┐ ┌─▼──────┐
│Elastic│ │Vertex  │ │ Cloud  │
│Search │ │  AI    │ │Storage │
│       │ │(Gemini)│ │        │
└───────┘ └────────┘ └────────┘
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- Node.js 16+
- Google Cloud Account with billing enabled
- Elasticsearch Cloud account
- GitHub account

### Backend Setup

1. **Clone the repository:**
```bash
git clone https://github.com/YOUR_USERNAME/opensquare.git
cd opensquare/backend
```

2. **Create virtual environment:**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Configure environment:**
   - Copy `.env.example` to `.env`
   - Fill in your credentials:
     - `GOOGLE_CLOUD_PROJECT`: Your GCP project ID
     - `ELASTIC_CLOUD_ID`: From Elastic deployment
     - `ELASTIC_API_KEY`: From Elastic
     - `ELASTIC_ENDPOINT`: Your Elastic URL

5. **Download service account key:**
   - Download JSON key from Google Cloud Service Accounts
   - Place in backend folder as `service-account-key.json`
   - Update `.env` with path

6. **Run the backend:**
```bash
python run.py
```

Server runs on `http://localhost:5000`

### Frontend Setup

1. **Navigate to frontend:**
```bash
cd ../frontend
```

2. **Install dependencies:**
```bash
npm install
```

3. **Configure API URL:**
   - Update `src/App.js` if backend is on different server
   - Default: `http://localhost:5000/api`

4. **Start development server:**
```bash
npm start
```

App opens on `http://localhost:3000`

---

## 📚 API Endpoints

### Health Check
```
GET /api/health
Response: { status, services, timestamp }
```

### Documents
```
GET /api/documents
Response: { count, documents[] }

POST /api/upload
Body: multipart/form-data with file
Response: { document_id, filename, size }
```

### Chat (Main Feature)
```
POST /api/chat
Body: { query: "string" }
Response: { answer, sources[], query }
```

### Search
```
POST /api/search
Body: { query: "string" }
Response: { results[], count }
```

### Initialize Demo
```
POST /api/init
Response: Load sample documents
```

---

## 🔧 Configuration

### Environment Variables (.env)

```bash
# Google Cloud
GOOGLE_CLOUD_PROJECT=opensquare-123456
GOOGLE_APPLICATION_CREDENTIALS=./service-account-key.json
VERTEX_AI_LOCATION=us-central1
VERTEX_AI_MODEL=gemini-1.5-pro

# Elasticsearch
ELASTIC_CLOUD_ID=your-cloud-id
ELASTIC_ENDPOINT=https://...
ELASTIC_API_KEY=your-api-key

# Application
FLASK_ENV=development
FLASK_DEBUG=True
SECRET_KEY=dev-secret-key

# AI Configuration
AI_TEMPERATURE=0.3
AI_MAX_OUTPUT_TOKENS=2048
RAG_TOP_K=5
```

---

## 🎓 How to Use

### 1. Start the Application

**Terminal 1 - Backend:**
```bash
cd backend
python run.py
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm start
```

### 2. Load Sample Data

Click "Load Sample Data" button in the app to populate with demo documents.

### 3. Ask Questions

Examples:
- "How much did Ministry of Health spend on COVID relief?"
- "Which organization has the lowest overhead costs?"
- "Show me spending trends over time"
- "Are there any suspicious patterns in the budget?"

### 4. Upload Documents

Click the upload icon to add your own financial documents (PDF, Excel, CSV).

### 5. Create Alerts

Set watchlists to monitor keywords and get notifications when new documents match.

---

## 🧪 Testing

### Test Backend
```bash
cd backend
python -m pytest
```

### Test Frontend
```bash
cd frontend
npm test
```

---

## 📦 Deployment

### Deploy Backend to Google Cloud Run

```bash
cd backend
gcloud run deploy opensquare-backend \
  --source . \
  --platform managed \
  --region us-central1 \
  --set-env-vars GOOGLE_CLOUD_PROJECT=YOUR_PROJECT_ID
```

### Deploy Frontend to Firebase

```bash
cd frontend
npm run build
firebase deploy --only hosting
```

---

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📋 Tech Stack

### Frontend
- React 18
- Axios (HTTP client)
- Recharts (data visualization)
- Lucide React (icons)

### Backend
- Flask (web framework)
- Elasticsearch (search engine)
- Google Vertex AI (LLM)
- Google Cloud Storage (file storage)

### AI/ML
- Gemini 1.5 Pro (language model)
- Elastic ML (anomaly detection)
- RAG (Retrieval Augmented Generation)

### Cloud Services
- Google Cloud Platform
- Elasticsearch Cloud
- GitHub (version control)

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 🙋 Support

For issues and questions:
1. Check existing GitHub issues
2. Create a new issue with details
3. Contact the maintainers

---

## 🎯 Roadmap

- [ ] Mobile app (iOS/Android)
- [ ] Advanced alert system
- [ ] Multi-language support
- [ ] Integration with government APIs
- [ ] Blockchain verification
- [ ] Community features
- [ ] Export to reports

---

## 🙏 Acknowledgments

- Built for AI Accelerate Hackathon
- Powered by Elastic and Google Cloud
- Inspired by financial transparency advocates worldwide

---

## 📞 Contact

**OpenSquare Team**
- GitHub: [@opensquare](https://github.com/opensquare)
- Email: info@opensquare.app

---

**Made with ❤️ for financial transparency**
