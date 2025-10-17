#!/usr/bin/env python
"""
OpenSquare Application Starter
Run this file to start the Flask backend server
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import Flask app
from app import app
from config import Config

print("\n" + "="*60)
print("🚀 OpenSquare Backend Starting")
print("="*60 + "\n")

# Validate configuration
try:
    Config.validate()
    print("✅ Configuration validated successfully\n")
except ValueError as e:
    print(f"❌ Configuration Error: {str(e)}")
    sys.exit(1)

# Show config
print("📋 Configuration Summary:")
config_summary = Config.get_config_summary()
for key, value in config_summary.items():
    print(f"   {key}: {value}")
print()

# Run the app
if __name__ == '__main__':
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', 5000))
    debug = Config.FLASK_DEBUG
    
    print(f"🌐 Server starting on http://{host}:{port}")
    print(f"📊 Environment: {Config.FLASK_ENV}")
    print(f"🔧 Debug mode: {debug}\n")
    
    app.run(
        host=host,
        port=port,
        debug=debug,
        use_reloader=debug
    )
