"""
OpenSquare Backend Configuration
Manages all environment variables and application settings
Load from .env file for security
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """
    Configuration class that holds all application settings.
    Values are loaded from environment variables for security.
    Never hardcode secrets - always use environment variables!
    """
    
    # ============================================
    # GOOGLE CLOUD CONFIGURATION
    # ============================================
    
    # Your Google Cloud Project ID (from Google Cloud Console)
    # Format: opensquare-123456 or opensquare
    GOOGLE_CLOUD_PROJECT = os.getenv('GOOGLE_CLOUD_PROJECT')
    
    # Path to service account JSON key file
    # This file contains credentials for authentication
    GOOGLE_APPLICATION_CREDENTIALS = os.getenv('GOOGLE_APPLICATION_CREDENTIALS', './service-account-key.json')
    
    # Vertex AI location (region where AI model is deployed)
    # Common values: us-central1, europe-west1, asia-northeast1
    VERTEX_AI_LOCATION = os.getenv('VERTEX_AI_LOCATION', 'us-central1')
    
    # Vertex AI model name (which LLM to use)
    VERTEX_AI_MODEL = os.getenv('VERTEX_AI_MODEL', 'gemini-1.5-pro')
    
    # Cloud Storage bucket for uploaded documents
    # Format: project-id-documents
    STORAGE_BUCKET_NAME = os.getenv('STORAGE_BUCKET_NAME', f'{GOOGLE_CLOUD_PROJECT}-documents')
    
    # ============================================
    # ELASTIC CONFIGURATION
    # ============================================
    
    # Elastic Cloud ID from your deployment
    # Found in Elasticsearch deployment settings
    ELASTIC_CLOUD_ID = os.getenv('ELASTIC_CLOUD_ID')
    
    # Elasticsearch endpoint URL
    # Format: https://deployment-id.es.region.gcp.elastic.cloud:443
    ELASTIC_ENDPOINT = os.getenv('ELASTIC_ENDPOINT')
    
    # API Key for Elasticsearch authentication
    # More secure than username/password
    ELASTIC_API_KEY = os.getenv('ELASTIC_API_KEY')
    
    # Index name where documents are stored
    # Think of it like a database table name
    ELASTIC_INDEX_NAME = os.getenv('ELASTIC_INDEX_NAME', 'opensquare-documents')
    
    # Alerts index for monitoring watchlists
    ELASTIC_ALERTS_INDEX = os.getenv('ELASTIC_ALERTS_INDEX', 'opensquare-alerts')
    
    # ============================================
    # APPLICATION SETTINGS
    # ============================================
    
    # Flask environment (development or production)
    # development = debug mode on, production = debug mode off
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    
    # Enable debug mode (shows detailed errors)
    # NEVER enable in production!
    FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    
    # Secret key for session management
    # Change this in production!
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Maximum file upload size (50MB in bytes)
    # 50 * 1024 * 1024 = 52,428,800 bytes
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024
    
    # Allowed file extensions for uploads
    # Only these file types can be uploaded
    ALLOWED_EXTENSIONS = {'pdf', 'xlsx', 'xls', 'csv'}
    
    # ============================================
    # AI CONFIGURATION
    # ============================================
    
    # Temperature for AI responses
    # 0.0 = very focused and deterministic
    # 1.0 = creative and random
    # 0.3 = good balance for financial data
    AI_TEMPERATURE = float(os.getenv('AI_TEMPERATURE', '0.3'))
    
    # Maximum tokens for AI responses
    # Token ≈ 1 word, so 2048 tokens ≈ 500 words
    AI_MAX_OUTPUT_TOKENS = int(os.getenv('AI_MAX_OUTPUT_TOKENS', '2048'))
    
    # Number of documents to retrieve for RAG
    # RAG = Retrieval Augmented Generation
    # Gets top K documents to use as context for AI
    RAG_TOP_K = int(os.getenv('RAG_TOP_K', '5'))
    
    # ============================================
    # NOTIFICATION SETTINGS
    # ============================================
    
    # Enable email notifications (requires SendGrid)
    EMAIL_ENABLED = os.getenv('EMAIL_ENABLED', 'False').lower() == 'true'
    
    # SendGrid API key (optional, for email alerts)
    # Only needed if EMAIL_ENABLED = True
    SENDGRID_API_KEY = os.getenv('SENDGRID_API_KEY')
    
    # Default sender email for notifications
    FROM_EMAIL = os.getenv('FROM_EMAIL', 'noreply@opensquare.app')
    
    # ============================================
    # VALIDATION & HELPER METHODS
    # ============================================
    
    @classmethod
    def validate(cls):
        """
        Validates that all required configuration values are set.
        Raises ValueError if any required config is missing.
        
        Call this when app starts to catch config issues early!
        """
        required_vars = [
            ('GOOGLE_CLOUD_PROJECT', cls.GOOGLE_CLOUD_PROJECT),
            ('ELASTIC_CLOUD_ID', cls.ELASTIC_CLOUD_ID),
            ('ELASTIC_API_KEY', cls.ELASTIC_API_KEY),
            ('ELASTIC_ENDPOINT', cls.ELASTIC_ENDPOINT),
        ]
        
        missing_vars = []
        for var_name, var_value in required_vars:
            if not var_value:
                missing_vars.append(var_name)
        
        if missing_vars:
            raise ValueError(
                f"❌ Missing required environment variables: {', '.join(missing_vars)}\n"
                f"Please set them in your .env file and try again."
            )
    
    @classmethod
    def is_development(cls):
        """
        Check if running in development mode.
        
        Returns:
            bool: True if FLASK_ENV is 'development'
        """
        return cls.FLASK_ENV == 'development'
    
    @classmethod
    def is_production(cls):
        """
        Check if running in production mode.
        
        Returns:
            bool: True if FLASK_ENV is 'production'
        """
        return cls.FLASK_ENV == 'production'
    
    @classmethod
    def allowed_file(cls, filename: str) -> bool:
        """
        Check if a file extension is allowed for upload.
        
        Args:
            filename: Name of the file to check
            
        Returns:
            bool: True if file extension is in ALLOWED_EXTENSIONS, False otherwise
            
        Example:
            if Config.allowed_file('budget.pdf'):
                print("PDF allowed")
        """
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in cls.ALLOWED_EXTENSIONS
    
    @classmethod
    def get_config_summary(cls):
        """
        Get a summary of current configuration (for debugging).
        Hides sensitive values like API keys.
        
        Returns:
            dict: Configuration summary with sensitive values masked
        """
        return {
            'environment': cls.FLASK_ENV,
            'debug_mode': cls.FLASK_DEBUG,
            'google_cloud_project': cls.GOOGLE_CLOUD_PROJECT,
            'vertex_ai_model': cls.VERTEX_AI_MODEL,
            'vertex_ai_location': cls.VERTEX_AI_LOCATION,
            'elastic_index': cls.ELASTIC_INDEX_NAME,
            'max_upload_mb': cls.MAX_CONTENT_LENGTH / (1024 * 1024),
            'allowed_extensions': list(cls.ALLOWED_EXTENSIONS),
            'email_enabled': cls.EMAIL_ENABLED,
            'elastic_api_key': '***HIDDEN***' if cls.ELASTIC_API_KEY else 'NOT SET'
        }
