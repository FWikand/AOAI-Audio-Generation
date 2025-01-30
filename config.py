import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('keys.env')

# Azure OpenAI Configuration
AZURE_CONFIG = {
    'api_version': '2025-01-01-preview',
    'api_key': os.getenv('AZURE_OPENAI_API_KEY'),
    'azure_endpoint': os.getenv('AZURE_OPENAI_ENDPOINT'),
}

# Model Deployments
# Your name in AI Foundry for the deployment
AZURE_MODELS = {
    'text': os.getenv('AZURE_OPENAI_TEXT_DEPLOYMENT', 'gpt-4o'),
    'audio': os.getenv('AZURE_OPENAI_AUDIO_DEPLOYMENT', 'gpt-4o-audio-preview'),
}

# Application Configuration
MAX_FILE_SIZE = 64 * 1024 * 1024  # 64MB max file size
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'doc', 'docx'} 