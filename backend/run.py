"""
OpenSquare Application Starter
Run this file to start the Flask backend server
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Import the Flask app and configuration
from app import app
from config import Config

# ============================================
# CONFIGURATION VALIDATION
# ============================================

print("\n" + "="*60)
print("🚀 OpenSquare Backend Starting")
print("="*60 + "\n")

# Validate all required settings are present
try:
    Config.validate()
    print("✅ Configuration validated successfully\n")
except ValueError as e:
    print(f"❌ Configuration Error: {str(e)}")
    print("\n⚠️  Please check your .env file and ensure all required variables are set.")
    sys.exit(1)

# Print configuration summary (no sensitive data)
print("📋 Configuration Summary:")
config_summary = Config.get_config_summary()
for key, value in config_summary.items():
    print(f"   {key}: {value}")
print()

# ============================================
# START THE APPLICATION
# ============================================

if __name__ == '__main__':
    # Determine host and port
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', 5000))
    debug = Config.FLASK_DEBUG
    
    print(f"🌐 Server starting on http://{host}:{port}")
    print(f"📊 Environment: {Config.FLASK_ENV}")
    print(f"🔧 Debug mode: {debug}\n")
    
    # Start Flask development server
    app.run(
        host=host,
        port=port,
        debug=debug,
        use_reloader=debug
    )
