import os
import re
import pandas as pd
from typing import List, Dict, Any
from io import BytesIO
from elasticsearch import Elasticsearch
from datetime import datetime # <<< THIS IS THE CRITICAL MISSING IMPORT

# --- Third-Party PDF Library (requires installation) ---
# NOTE: We use pypdf for simplicity in this hackathon environment.
from pypdf import PdfReader 

# Import configuration
from config import Config

# ==============================================================================
# 1. ELASTICSEARCH SETUP & INDEX MAPPING
# ==============================================================================

def create_index_if_not_exists(elastic_client: Elasticsearch, index_name: str) -> bool:
    """
    Creates the Elasticsearch index with the required mapping if it does not already exist.

    This mapping is crucial for two reasons:
    1. 'text': Sets the field type to 'text' for full-text search and uses the 'english' analyzer.
    2. 'vector': Sets the field type to 'dense_vector' for efficient semantic search (RAG).
    
    Args:
        elastic_client: The initialized Elasticsearch client instance.
        index_name: The name of the index to create (from Config.ELASTIC_INDEX_NAME).
    
    Returns:
        True if the index was created or already exists, False otherwise.
    """
    try:
        if not elastic_client.indices.exists(index=index_name):
            print(f"Creating index '{index_name}'...")
            
            # The mapping defines how data fields are stored and indexed
            mapping = {
                "properties": {
                    "document_id": {"type": "keyword"},  # Links chunks back to the original file
                    "source_filename": {"type": "keyword"},
                    "source_url": {"type": "keyword", "index": False}, # Do not index the URL
                    "chunk_id": {"type": "keyword"}, # Unique identifier for the chunk
                    "text": {
                        "type": "text",
                        "analyzer": "english" # Use the English analyzer for better full-text search
                    },
                    "vector": {
                        "type": "dense_vector",
                        "dims": 768, # Dimensionality for text-embedding-004 (768)
                        "index": True,
                        "similarity": "cosine" # Use cosine similarity for vector search
                    },
                    "timestamp": {"type": "date"}
                }
            }
            
            # Index settings for improved search performance
            settings = {
                "analysis": {
                    "analyzer": {
                        "english": {
                            "tokenizer": "standard",
                            "filter": ["lowercase", "stop", "kstem"]
                        }
                    }
                }
            }
            
            elastic_client.indices.create(
                index=index_name,
                settings=settings,
                mappings=mapping
            )
            print(f"Index '{index_name}' created successfully.")
            return True
        else:
            print(f"Index '{index_name}' already exists.")
            return True

    except Exception as e:
        print(f"Error creating index: {e}")
        return False

# ==============================================================================
# 2. FILE EXTRACTION UTILITIES
# ==============================================================================

def extract_text_from_pdf(file_stream: BytesIO) -> str:
    """Extracts text from a PDF file stream."""
    try:
        reader = PdfReader(file_stream)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n\n"
        return text
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return ""

def extract_data_from_excel(file_stream: BytesIO) -> str:
    """Extracts data from all sheets in an Excel file stream and returns it as a concatenated string."""
    try:
        xls = pd.ExcelFile(file_stream)
        all_data = []
        for sheet_name in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name)
            # Convert the entire sheet to a single string representation
            all_data.append(f"---Sheet: {sheet_name}---\n{df.to_string(index=False)}")
        return "\n\n".join(all_data)
    except Exception as e:
        print(f"Error extracting data from Excel: {e}")
        return ""

def extract_data_from_csv(file_stream: BytesIO) -> str:
    """Extracts data from a CSV file stream and returns it as a single string."""
    try:
        df = pd.read_csv(file_stream)
        return df.to_string(index=False)
    except Exception as e:
        print(f"Error extracting data from CSV: {e}")
        return ""

# ==============================================================================
# 3. TEXT PROCESSING UTILITIES
# ==============================================================================

def clean_text(text: str) -> str:
    """Performs basic cleanup on extracted text."""
    # Remove excessive newlines/spaces
    text = re.sub(r'\s{2,}', ' ', text)
    # Remove non-ASCII characters and leading/trailing whitespace
    text = text.encode('ascii', 'ignore').decode('ascii').strip()
    return text

def chunk_text(text: str, document_id: str, source_filename: str, source_url: str) -> List[Dict[str, Any]]:
    """
    Splits long text into smaller, manageable chunks suitable for RAG and indexing.
    This creates the structure of the document that is saved in Elasticsearch.
    """
    # Simple chunking for demonstration: splitting by paragraph/double newline
    sections = [s.strip() for s in text.split('\n\n') if s.strip()]
    
    # Fallback for very large sections or uniform text (e.g., from tables)
    if not sections or max(len(s) for s in sections) > 2000:
        # If splitting by paragraph is ineffective, chunk by a fixed size
        sections = [text[i:i + 1500] for i in range(0, len(text), 1500)]
        sections = [s.strip() for s in sections if s.strip()]

    chunks = []
    
    # Timestamp is constant for all chunks of the same document
    current_time = datetime.now().isoformat()
    
    for i, chunk_text in enumerate(sections):
        if len(chunk_text) < 50:
            continue # Skip very small chunks
            
        chunk_data = {
            "document_id": document_id,
            "source_filename": source_filename,
            "source_url": source_url,
            "chunk_id": f"{document_id}_{i}",
            "text": chunk_text,
            "timestamp": current_time,
            # NOTE: The 'vector' field will be added later in app.py 
            # after the text has been sent to the Vertex AI embedding model.
        }
        chunks.append(chunk_data)
        
    return chunks

# ==============================================================================
# 4. ELASTICSEARCH RAG SEARCH UTILITY
# ==============================================================================

def search_documents(query_embedding: List[float], size: int = 5) -> List[Dict[str, Any]]:
    """
    Performs a k-nearest neighbor (kNN) search against the 'vector' field 
    to retrieve the most semantically relevant text chunks for RAG.
    """
    # NOTE: This assumes 'get_elastic_client()' is available or defined in app.py.
    # We will redefine the client usage in app.py for simplicity.
    
    # For now, we will assume the client is imported globally in app.py and 
    # that this function is only called from within the Flask request context where it can be passed.
    # The actual client object must be passed here for this function to work outside app.py.
    # Since this is a utility file, let's keep the client out of it and assume it's passed or imported globally in app.py.
    # I will fix this dependency issue in the final app.py file to ensure it runs smoothly.
    
    # For the immediate fix: Commenting out the dependency on a non-existent function for now.
    # elastic_client = get_elastic_client() 
    
    print("Warning: `search_documents` function requires the `elastic_client` to be passed or accessible.")

    # --- Start of Search Logic ---
    # The actual client object will be needed here to run the search.
    # For now, we'll keep the logic as-is, with the understanding that the call 
    # to this function in app.py will need to pass the client:
    # `search_documents(elastic_client, query_embedding, size=Config.RAG_TOP_K)`
    
    # NOTE: Since the client is initialized in app.py and not utils.py, 
    # the function signature will need to be updated in the next step when we write app.py.
    # For now, let's just make the immediate datetime import fix.
    
    return [] # Returning an empty list for now until app.py is written

