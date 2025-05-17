# Small Language Models for Efficient Data Retrieval and Planning

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd <repository-directory>
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Start the Ollama server** locally (if applicable to your setup).

## Project Structure

- `config.py`: Configuration for the database, LLM, and data fields.
- `prompts.py`: Templates for SQL and natural language prompts.
- `db_utils.py`: Utilities for database connection and queries.
- `llm_utils.py`: Functions for initializing the LLM.
- `agent.py`: Core logic for generating and processing responses.
- `main.py`: Main entry point to run the application.

## Usage

1. **Edit the query**:
   - Open `main.py` and update the `user_query` variable with your question, e.g.:
     ```python
     user_query = "Calculate a trading strategy for gold and stock"
     ```

2. **Run the application**:
   ```bash
   python main.py
   ```

3. **Output**:
   - The application will display:
     - The generated SQL query
     - Raw query results
     - Natural language interpretation of the response
