import os
import uuid
import json
from datetime import datetime
from io import BytesIO
from typing import Dict, List, Any

# Flask imports
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename

# Import configuration and utilities
from config import Config
from utils import (
    create_index_if_not_exists,
    extract_text_from_pdf,
    extract_data_from_excel,
    extract_data_from_csv,
    clean_text,
    chunk_text
)

# Import Google Cloud and Vertex AI libraries
from google.cloud import storage, aiplatform
from vertexai.generative_models import GenerativeModel
import vertexai

# Import Elastic library and related utilities
from elasticsearch import Elasticsearch, helpers

# ============================================================
# APPLICATION INITIALIZATION
# ============================================================
app = Flask(__name__)
app.config.from_object(Config)

# Enable CORS for frontend communication
CORS(app)

# Create a temporary directory for local file processing if it doesn't exist
if not os.path.exists(Config.UPLOAD_FOLDER):
    os.makedirs(Config.UPLOAD_FOLDER)

# --- Service Initialization ---

# Initialize Vertex AI
try:
    vertexai.init(
        project=Config.GOOGLE_CLOUD_PROJECT,
        location=Config.VERTEX_AI_LOCATION
    )
    # Initialize Gemini model for RAG generation
    gemini_model = GenerativeModel(Config.VERTEX_AI_MODEL)
    print(f"Vertex AI Initialized with project: {Config.GOOGLE_CLOUD_PROJECT}")
except Exception as e:
    print(f"Error initializing Vertex AI. Check GOOGLE_CLOUD_PROJECT: {e}")
    gemini_model = None

# Initialize Elastic client
try:
    elastic_client = Elasticsearch(
        cloud_id=Config.ELASTIC_CLOUD_ID,
        api_key=Config.ELASTIC_API_KEY
    )
    elastic_client.info() # Check connection
    print(f"Elasticsearch Client Initialized and connected successfully.")
except Exception as e:
    print(f"Error initializing Elasticsearch Client. Check API Key/Cloud ID: {e}")
    elastic_client = None

# Initialize Google Cloud Storage client
try:
    storage_client = storage.Client()
    print("Google Cloud Storage Client Initialized.")
except Exception as e:
    print(f"Error initializing Google Cloud Storage Client: {e}")
    storage_client = None


# --- Model and Utility Functions ---

def get_embedding(text: str) -> List[float]:
    """Retrieves a vector embedding for a given text using Vertex AI's text-embedding-004 model."""
    try:
        # We use the fast and efficient text-embedding-004 model
        embeddings = aiplatform.predict.PredictionClient(
            client_options={"api_endpoint": f"{Config.VERTEX_AI_LOCATION}-aiplatform.googleapis.com"}
        ).predict(
            endpoint=aiplatform.Endpoint.from_id(
                project=Config.GOOGLE_CLOUD_PROJECT,
                location=Config.VERTEX_AI_LOCATION,
                endpoint_id="text-embedding-004"
            ),
            instances=[{"content": text}]
        )
        return embeddings.predictions[0]['embeddings']
    except Exception as e:
        print(f"Error generating embedding: {e}")
        return []

def allowed_file(filename: str) -> bool:
    """Checks if a file extension is allowed."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

# ============================================================
# FLASK HOOKS (RUN BEFORE FIRST REQUEST)
# ============================================================

@app.before_first_request
def setup_application():
    """Runs setup tasks before the first request, like ensuring the Elasticsearch index exists."""
    if elastic_client:
        create_index_if_not_exists(elastic_client, Config.ELASTIC_INDEX_NAME)

# ============================================================
# API ENDPOINTS
# ============================================================

@app.route('/api/upload', methods=['POST'])
def upload_document():
    """Handles document upload, processing, vector creation, and indexing."""
    if not elastic_client or not storage_client or not gemini_model:
        return jsonify({'status': 'error', 'message': 'Backend services failed to initialize.'}), 500

    if 'file' not in request.files:
        return jsonify({'status': 'error', 'message': 'No file part in the request'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'status': 'error', 'message': 'No selected file'}), 400

    if file and allowed_file(file.filename):
        # 1. Setup metadata
        original_filename = secure_filename(file.filename)
        file_extension = original_filename.rsplit('.', 1)[1].lower()
        document_id = str(uuid.uuid4())
        gcs_filename = f"{document_id}/{original_filename}"

        # 2. Upload to Google Cloud Storage (GCS)
        try:
            bucket = storage_client.bucket(Config.GCS_BUCKET_NAME)
            blob = bucket.blob(gcs_filename)
            file.stream.seek(0) # Rewind stream after checking for file extension
            blob.upload_from_file(file.stream, content_type=file.content_type)
            gcs_url = blob.public_url
        except Exception as e:
            print(f"GCS Upload Error: {e}")
            return jsonify({'status': 'error', 'message': f'Failed to upload to GCS: {e}'}), 500

        # 3. Extract text/data from file stream
        file.stream.seek(0) # Rewind stream again for text extraction
        file_bytes = BytesIO(file.stream.read())
        
        extracted_text = ""
        if file_extension == 'pdf':
            extracted_text = extract_text_from_pdf(file_bytes)
        elif file_extension == 'xlsx':
            extracted_text = extract_data_from_excel(file_bytes)
        elif file_extension == 'csv':
            extracted_text = extract_data_from_csv(file_bytes)
        
        if not extracted_text:
            return jsonify({'status': 'error', 'message': 'Failed to extract content from file'}), 500
        
        # 4. Process and chunk text
        clean_content = clean_text(extracted_text)
        chunks = chunk_text(clean_content, document_id, original_filename, gcs_url)

        if not chunks:
            return jsonify({'status': 'error', 'message': 'Document content was too sparse to process.'}), 500

        # 5. Generate embeddings and prepare for bulk indexing
        actions = []
        for chunk in chunks:
            try:
                # Generate vector embedding for the chunk text
                vector = get_embedding(chunk['text'])
                if vector:
                    chunk['vector'] = vector
                    
                    actions.append({
                        '_index': Config.ELASTIC_INDEX_NAME,
                        '_id': chunk['chunk_id'],
                        '_source': chunk
                    })
                else:
                    print(f"Skipping chunk {chunk['chunk_id']} due to empty vector.")
            except Exception as e:
                print(f"Error processing chunk {chunk['chunk_id']}: {e}")
                continue
        
        # 6. Bulk Indexing to Elasticsearch
        try:
            success, errors = helpers.bulk(elastic_client, actions, raise_on_error=False)
            if errors:
                print(f"Elasticsearch Bulk Indexing Errors: {errors}")
            
            return jsonify({
                'status': 'success',
                'message': f'Document "{original_filename}" indexed successfully.',
                'chunks_indexed': success
            })
        except Exception as e:
            print(f"Elasticsearch Bulk Error: {e}")
            return jsonify({'status': 'error', 'message': f'Failed to index chunks into Elasticsearch: {e}'}), 500
    
    return jsonify({'status': 'error', 'message': 'File type not allowed'}), 400

@app.route('/api/query', methods=['POST'])
def query_documents():
    """
    Handles RAG query: generates embedding for query, searches Elasticsearch for 
    context, and sends context + query to Gemini for a final answer.
    """
    if not elastic_client or not gemini_model:
        return jsonify({'status': 'error', 'message': 'Backend services failed to initialize.'}), 500

    try:
        # Get query from request
        data = request.get_json()
        query = data.get('query', '')
        
        if not query:
            return jsonify({
                'status': 'error',
                'message': 'No query provided'
            }), 400
        
        # 1. Generate embedding for the user's query
        query_embedding = get_embedding(query)
        if not query_embedding:
            return jsonify({'status': 'error', 'message': 'Failed to generate query embedding.'}), 500

        # 2. Search Elasticsearch for relevant documents (kNN search)
        # We need to explicitly redefine search_documents here or update utils.py
        # For simplicity, let's include the search logic directly here since it depends on the client.
        
        knn_query = {
            "field": "vector",
            "query_vector": query_embedding,
            "k": Config.RAG_TOP_K,
            "num_candidates": Config.RAG_TOP_K * 20 
        }

        search_response = elastic_client.search(
            index=Config.ELASTIC_INDEX_NAME,
            knn=knn_query,
            _source=["text", "source_filename", "source_url"]
        )

        search_results = []
        for hit in search_response['hits']['hits']:
            search_results.append({
                "score": hit['_score'],
                "text": hit['_source']['text'],
                "source_filename": hit['_source']['source_filename'],
                "source_url": hit['_source']['source_url']
            })
        
        if not search_results:
            # If no relevant documents found, use Gemini to answer generically (without RAG)
            context = "No relevant documents found in the database. Answer based on general knowledge."
            sources = []
        else:
            # 3. Construct the RAG prompt from search results
            context = "\n---\n".join([result['text'] for result in search_results])
            
            # 4. Extract unique sources for citation
            unique_sources = {}
            for result in search_results:
                key = (result['source_filename'], result['source_url'])
                unique_sources[key] = True

            sources = [{"filename": k[0], "url": k[1]} for k in unique_sources.keys()]

        # 5. Construct the final prompt for Gemini
        system_prompt = (
            "You are a professional financial analyst AI. Your task is to provide a concise, factual answer "
            "to the user's query ONLY based on the context provided below. "
            "Do not use external knowledge. If the context does not contain the answer, state that clearly. "
            "Maintain a professional and objective tone. Do not include a conversational closing."
        )

        rag_prompt = (
            f"{system_prompt}\n\n"
            f"--- CONTEXT ---\n"
            f"{context}\n\n"
            f"--- USER QUERY ---\n"
            f"{query}"
        )
        
        # 6. Call Gemini model for RAG generation
        response = gemini_model.generate_content(
            rag_prompt,
            config=aiplatform.types.GenerateContentConfig(
                temperature=Config.AI_TEMPERATURE,
                max_output_tokens=Config.AI_MAX_OUTPUT_TOKENS
            )
        )

        return jsonify({
            'status': 'success',
            'answer': response.text,
            'sources': sources,
            'context': context
        })

    except Exception as e:
        print(f"Error during query_documents: {e}")
        return jsonify({'status': 'error', 'message': f'An unexpected error occurred: {e}'}), 500


@app.route('/api/status', methods=['GET'])
def get_status():
    """Provides a simple status check for the API."""
    return jsonify({
        'status': 'ok',
        'model': Config.VERTEX_AI_MODEL,
        'project': Config.GOOGLE_CLOUD_PROJECT,
        'index': Config.ELASTIC_INDEX_NAME
    })


if __name__ == '__main__':
    # Flask is run in a simple environment for development purposes
    app.run(host='0.0.0.0', port=5000)

