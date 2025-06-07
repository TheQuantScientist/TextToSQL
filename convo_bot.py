import os  
from langchain_ollama import ChatOllama  
from langchain_core.prompts import ChatPromptTemplate  
from dotenv import load_dotenv

load_dotenv()

OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:latest")

# Define model
llm = ChatOllama(
    model = OLLAMA_MODEL,
    temparature = 0.5,
    base_url = "http://localhost:11434/",
    num_ctx = 8192
)

# Define Prompt
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful AI conversation assistant."),
    ("user", "{input}")
])

# Create function for user input
def get_response(user_input):
    if not user_input.strip(): 
        return "User input is empty !"
    try: 
        response = llm.invoke(prompt.format_messages(input=user_input)).content  # Get the AI's response text
        return response  # Return the response to the caller
    except Exception as e:  # If an error occurs (e.g., AI server is down)
        return f"Error: {str(e)}"

# Main 
if __name__ == "__main__":
    while True:
        user_input = input("You: ")
        if user_input.lower() in {"exit", "quit"}:
            print("end conversation!")
            break
        response = get_response(user_input)
        print("Bot:", response)

