"""
OpenSquare Main Flask Application
Complete backend API with Elasticsearch and Vertex AI
Financial transparency platform using conversational AI
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
from datetime import datetime
from typing import Dict, List, Any

# Import configuration and utilities
from config import Config
from utils import (
    extract_text_from_pdf,
    extract_data_from_excel,
    extract_data_from_csv,
    convert_dataframes_to_text,
    clean_text,
    chunk_text,
    extract_amounts,
    extract_dates,
    format_file_size,
    generate_document_id,
    validate_file_size
)

# Import Google Cloud libraries
from google.cloud import storage
from vertexai.generative_models import GenerativeModel
import vertexai

# Import Elasticsearch
from elasticsearch import Elasticsearch

# ============================================
# APPLICATION INITIALIZATION
# ============================================

# Create Flask application instance
app = Flask(__name__)
app.config.from_object(Config)

# Enable CORS for frontend communication
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Initialize Vertex AI (Google Cloud's AI platform)
vertexai.init(
    project=Config.GOOGLE_CLOUD_PROJECT,
    location=Config.VERTEX_AI_LOCATION
)

# Initialize Gemini model for conversational AI
gemini_model = GenerativeModel(Config.VERTEX_AI_MODEL)

# Initialize Elasticsearch client for document search
elastic_client = Elasticsearch(
    cloud_id=Config.ELASTIC_CLOUD_ID,
    api_key=Config.ELASTIC_API_KEY
)

# Initialize Google Cloud Storage for file uploads
storage_client = storage.Client(project=Config.GOOGLE_CLOUD_PROJECT)

# Create upload folder for temporary file storage
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


# ============================================
# SAMPLE DATA FOR DEMO
# ============================================

SAMPLE_DOCUMENTS = [
    {
        "title": "Ministry of Health Budget 2024",
        "organization": "Ministry of Health",
        "content": "BUDGET ALLOCATION 2024. Total Budget: $450 Million. Healthcare Services: $158M (35%). Infrastructure: $157M (35%). Research & Development: $68M (15%). Administration: $45M (10%). Other: $22M (5%). COVID Relief Fund: $12.5M - Vaccine Distribution: $6M, Testing Centers: $3M, Treatment Facilities: $2.5M, Equipment: $1M",
        "doc_type": "Budget Document",
        "year": 2024
    },
    {
        "title": "Education Ministry Financial Report Q3 2024",
        "organization": "Ministry of Education",
        "content": "QUARTERLY REPORT - Q3 2024. Total Spending: $120 Million. Teacher Salaries: $48M. School Infrastructure: $36M. Learning Materials: $18M. Administration: $10M. Technology: $8M. Notable: Infrastructure increased 40% from Q2. Teacher salaries stable. New IT systems procurement: $5M",
        "doc_type": "Financial Report",
        "year": 2024
    }
]


# ============================================
# HELPER FUNCTIONS
# ============================================

def index_document_to_elastic(doc_id: str, content: Dict[str, Any]) -> bool:
    """Index a document in Elasticsearch"""
    try:
        response = elastic_client.index(
            index=Config.ELASTIC_INDEX_NAME,
            id=doc_id,
            document=content
        )
        return response['result'] in ['created', 'updated']
    except Exception as e:
        print(f"Error indexing to Elastic: {str(e)}")
        return False


def search_documents(query: str, size: int = 5) -> List[Dict]:
    """Search documents using Elasticsearch"""
    try:
        response = elastic_client.search(
            index=Config.ELASTIC_INDEX_NAME,
            body={
                "query": {
                    "multi_match": {
                        "query": query,
                        "fields": ["content", "title", "organization"],
                        "type": "best_fields",
                        "fuzziness": "AUTO"
                    }
                },
                "size": size,
                "highlight": {
                    "fields": {"content": {"number_of_fragments": 3}}
                }
            }
        )
        
        results = []
        for hit in response['hits']['hits']:
            results.append({
                'id': hit['_id'],
                'score': hit['_score'],
                'source': hit['_source'],
                'highlights': hit.get('highlight', {})
            })
        
        return results
    except Exception as e:
        print(f"Error searching Elastic: {str(e)}")
        return []


def generate_ai_response(query: str, context_docs: List[Dict]) -> str:
    """Generate AI response using Gemini with RAG"""
    try:
        # Build context from documents
        context = "Here are relevant documents:\n\n"
        
        for i, doc in enumerate(context_docs, 1):
            source = doc['source']
            context += f"Document {i}: {source.get('title', 'Untitled')}\n"
            context += f"Organization: {source.get('organization', 'Unknown')}\n"
            context += f"Content: {source.get('content', '')[:500]}...\n\n"
        
        # Create prompt for Gemini
        prompt = f"""You are OpenSquare AI, a financial transparency assistant.

CONTEXT:
{context}

USER QUESTION: {query}

INSTRUCTIONS:
1. Answer ONLY using provided documents
2. Cite sources (e.g., "According to Document 1...")
3. Highlight suspicious patterns or red flags
4. Be concise (2-3 paragraphs)
5. Use bullet points for key findings

ANSWER:"""
        
        # Generate response
        response = gemini_model.generate_content(
            prompt,
            generation_config={
                'temperature': Config.AI_TEMPERATURE,
                'max_output_tokens': Config.AI_MAX_OUTPUT_TOKENS,
            }
        )
        
        return response.text
    except Exception as e:
        print(f"Error generating AI response: {str(e)}")
        return "I encountered an error processing your request."


def load_sample_documents():
    """Load sample documents into Elasticsearch"""
    try:
        for i, doc in enumerate(SAMPLE_DOCUMENTS):
            doc_id = f"sample_doc_{i}"
            index_document_to_elastic(doc_id, doc)
        print("✅ Sample documents loaded")
        return True
    except Exception as e:
        print(f"Error loading samples: {str(e)}")
        return False


# ============================================
# API ENDPOINTS - HEALTH & STATUS
# ============================================

@app.route('/')
def home():
    """API health check"""
    return jsonify({
        'status': 'success',
        'message': 'OpenSquare API is running',
        'version': '1.0.0',
        'environment': Config.FLASK_ENV
    })


@app.route('/api/health')
def health():
    """Detailed health check"""
    try:
        elastic_health = elastic_client.info()
        elastic_ok = elastic_health is not None
    except:
        elastic_ok = False
    
    return jsonify({
        'status': 'success',
        'services': {
            'api': 'online',
            'elasticsearch': 'online' if elastic_ok else 'offline',
            'vertex_ai': 'online'
        },
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/config')
def get_config():
    """Get configuration summary (no sensitive data)"""
    return jsonify(Config.get_config_summary())


# ============================================
# API ENDPOINTS - DOCUMENT MANAGEMENT
# ============================================

@app.route('/api/upload', methods=['POST'])
def upload_document():
    """
    Upload and process a financial document
    Accepts: PDF, Excel, CSV
    """
    try:
        # Validate file provided
        if 'file' not in request.files:
            return jsonify({'status': 'error', 'message': 'No file provided'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'status': 'error', 'message': 'No file selected'}), 400
        
        # Validate file type
        if not Config.allowed_file(file.filename):
            return jsonify({
                'status': 'error',
                'message': f'File type not allowed. Supported: {", ".join(Config.ALLOWED_EXTENSIONS)}'
            }), 400
        
        # Save file with unique name
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_filename = f"{timestamp}_{filename}"
        file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
        file.save(file_path)
        
        # Validate file size
        file_size = os.path.getsize(file_path)
        if file_size > Config.MAX_CONTENT_LENGTH:
            os.remove(file_path)
            return jsonify({'status': 'error', 'message': 'File exceeds 50MB limit'}), 400
        
        # Extract content based on file type
        file_ext = filename.rsplit('.', 1)[1].lower()
        
        if file_ext == 'pdf':
            content = extract_text_from_pdf(file_path)
        elif file_ext in ['xlsx', 'xls']:
            sheets = extract_data_from_excel(file_path)
            content = convert_dataframes_to_text(sheets)
        elif file_ext == 'csv':
            df = extract_data_from_csv(file_path)
            content = df.to_string()
        else:
            content = ""
        
        # Clean content
        content = clean_text(content)
        
        # Get metadata
        organization = request.form.get('organization', 'Unknown')
        doc_type = request.form.get('doc_type', 'General')
        year = request.form.get('year', datetime.now().year)
        
        # Create document
        doc_id = generate_document_id(filename, datetime.now().isoformat())
        document = {
            'title': filename,
            'content': content,
            'organization': organization,
            'doc_type': doc_type,
            'year': year,
            'uploaded_at': datetime.now().isoformat(),
            'file_size': file_size
        }
        
        # Index in Elasticsearch
        if not index_document_to_elastic(doc_id, document):
            os.remove(file_path)
            return jsonify({'status': 'error', 'message': 'Failed to index document'}), 500
        
        # Clean up local file
        os.remove(file_path)
        
        return jsonify({
            'status': 'success',
            'message': 'Document processed successfully',
            'document_id': doc_id,
            'filename': filename,
            'size': format_file_size(file_size),
            'organization': organization
        })
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Error: {str(e)}'}), 500


@app.route('/api/documents', methods=['GET'])
def list_documents():
    """List all indexed documents"""
    try:
        response = elastic_client.search(
            index=Config.ELASTIC_INDEX_NAME,
            body={"query": {"match_all": {}}, "size": 100}
        )
        
        documents = []
        for hit in response['hits']['hits']:
            doc = hit['_source']
            doc['id'] = hit['_id']
            documents.append(doc)
        
        return jsonify({
            'status': 'success',
            'count': len(documents),
            'documents': documents
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


# ============================================
# API ENDPOINTS - CONVERSATIONAL AI
# ============================================

@app.route('/api/chat', methods=['POST'])
def chat():
    """
    Conversational AI endpoint
    User asks question, AI searches documents and responds
    """
    try:
        data = request.get_json()
        query = data.get('query', '')
        
        if not query:
            return jsonify({'status': 'error', 'message': 'No query provided'}), 400
        
        # Search for relevant documents
        search_results = search_documents(query, size=Config.RAG_TOP_K)
        
        if not search_results:
            return jsonify({
                'status': 'success',
                'answer': 'I couldn\'t find relevant documents. Please upload documents or try a different query.',
                'sources': [],
                'query': query
            })
        
        # Generate AI response
        answer = generate_ai_response(query, search_results)
        
        # Format sources
        sources = []
        for result in search_results:
            source = result['source']
            sources.append({
                'title': source.get('title', 'Untitled'),
                'organization': source.get('organization', 'Unknown'),
                'doc_type': source.get('doc_type', 'General'),
                'relevance_score': round(result['score'], 2)
            })
        
        return jsonify({
            'status': 'success',
            'answer': answer,
            'sources': sources,
            'query': query
        })
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/search', methods=['POST'])
def search():
    """Search endpoint for document search"""
    try:
        data = request.get_json()
        query = data.get('query', '')
        
        if not query:
            return jsonify({'status': 'error', 'message': 'No query provided'}), 400
        
        results = search_documents(query, size=10)
        
        return jsonify({
            'status': 'success',
            'query': query,
            'count': len(results),
            'results': results
        })
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


# ============================================
# API ENDPOINTS - INITIALIZATION
# ============================================

@app.route('/api/init', methods=['POST'])
def initialize():
    """Load sample documents for demo"""
    try:
        load_sample_documents()
        return jsonify({
            'status': 'success',
            'message': 'Sample documents loaded successfully'
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


# ============================================
# ERROR HANDLERS
# ============================================

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({
        'status': 'error',
        'message': 'Endpoint not found'
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({
        'status': 'error',
        'message': 'Internal server error'
    }), 500


if __name__ == '__main__':
    app.run(debug=True)
