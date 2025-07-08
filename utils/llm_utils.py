import logging
from langchain_ollama import OllamaLLM
import sys
import os
from groq import Groq
from prompt.prompts import GROQ_CONFIG

sys.path.append('.')

from prompt.prompts import OLLAMA_CONFIG

# Logging Configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_llm_model():
    try:
        llm = OllamaLLM(model=OLLAMA_CONFIG['model'], base_url=OLLAMA_CONFIG['endpoint'])
        logger.info("LLM initialized successfully")
        return llm
    except Exception as e:
        logger.error(f"Failed to initialize LLM: {str(e)}")
        return None
    
def get_groq_llm_model():
    try:
        api_key = GROQ_CONFIG.get("api_key")
        model = GROQ_CONFIG.get("model")
        if not api_key or api_key == "YOUR_API_KEY":
            raise ValueError("GROQ_CONFIG['api_key'] is not set. Please update it in prompts.py.")
        llm = Groq(api_key=api_key)
        logger.info(f"Groq LLM initialized successfully with model: {model}")
        return llm
    except Exception as e:
        logger.error(f"Failed to initialize Groq LLM: {str(e)}")
        return None