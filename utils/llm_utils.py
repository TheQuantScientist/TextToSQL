import logging
from langchain_ollama import OllamaLLM
import sys

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