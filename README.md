# TextToSQL

A Python-based application that leverages Small Language Models (SLMs) for domain-related Text-to-SQL tasks. This tool converts natural language queries into SQL statements and provides natural language interpretations of the results.

## Table of Contents

- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [File Structure](#file-structure)
- [Contributing](#contributing)
- [License](#license)

## Features

- **Natural Language to SQL**: Convert plain English queries into SQL statements
- **SQL Execution**: Execute generated SQL queries against your database
- **Natural Language Response**: Get human-readable interpretations of query results
- **Domain-Specific**: Optimized for specific domain tasks (e.g., trading, finance)
- **Local LLM Integration**: Uses Ollama for local language model processing

## Prerequisites

Before setting up this repository, ensure you have the following installed:

- Python 3.8 or higher
- pip (Python package installer)
- Ollama (for local LLM processing)
- PostgreSQL database server ([Download](https://www.postgresql.org/download/))

## Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/TheQuantScientist/TextToSQL.git
   cd TextToSQL
   ```

2. **Create a virtual environment (recommended):**

   ```bash
   python -m venv texttosql_env
   source texttosql_env/bin/activate  # On Windows: texttosql_env\Scripts\activate
   ```

3. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

4. **Set up PostgreSQL database:**
   - Install PostgreSQL on your system
   - Create a database for the application
   - Note down the database credentials (host, port, database name, username, password)

5. **Set up Ollama:**
   - Install Ollama on your system
   - Start the Ollama server locally
   - Pull the required language model (refer to `config.py` for model specifications)

## Configuration

Before running the application, you need to configure the database connection and LLM settings:

1. **PostgreSQL Database Configuration**: Update the database connection settings in `config.py`:

   ```python
   DATABASE_CONFIG = {
       'host': 'localhost',
       'port': 5432,
       'database': 'your_database_name',
       'username': 'your_username',
       'password': 'your_password'
   }
   ```

2. **LLM Configuration**: Ensure the correct model is specified in `config.py`
3. **Prompt Templates**: Customize prompts in `prompts.py` if needed for your specific domain

## Usage

1. **Edit your query**: Open `main.py` and update the `user_query` variable with your question:

   ```python
   user_query = "Calculate a trading strategy for gold and stock"
   ```

2. **Run the application:**

   ```bash
   python main.py
   ```

3. **View the output**: The application will display:
   - The generated SQL query
   - Raw query results from the database
   - Natural language interpretation of the response

## File Structure

### Core Files

#### `main.py`

The main entry point of the application. This file orchestrates the entire Text-to-SQL pipeline:

- Accepts user queries
- Coordinates between different modules
- Displays the final results
- Contains the primary execution logic

#### `config.py`

Configuration management for the entire application:

- **Database Configuration**: Credentials, and database-specific settings
- **LLM Configuration**: Model specifications, API endpoints, and language model parameters
- **Data Field Configuration**: Defines the structure and mapping of data fields
- **Environment Variables**: Manages environment-specific settings

#### `prompts.py`

Template management for prompt engineering:

- **SQL Generation Prompts**: Prompt remplate for converting natural language to SQL
- **Imports FIELDS_JSON from config**: This contains the names and details of the columns in the finance_economics_dataset for SQL generation agent to understand.
- **Natural Language Prompts**: Prompt template for converting SQL results back to human-readable text

#### `db_utils.py`

Database utility functions and connection management:

- **Database Connection**: Establishes and manages database connections
- **Schema Introspection**: Retrieves database schema information for context
- **Query Execution**: Executes SQL queries with error handling
- **Result Processing**: Formats and processes query results

#### `llm_utils.py`

Language Model utility functions and initialization:

- **LLM Initialization**: Sets up and configures the language model (Ollama)
- **Error Handling**: Manages LLM-related errors and fallbacks

#### `agent.py`

The core intelligence of the application:

- **Query Processing**: Analyzes and processes natural language queries
- **SQL Generation**: Coordinates the conversion from natural language to SQL
- **Query Execution**: Runs the SQL against the database
- **Result Interpretation**: Converts SQL results into natural language responses

### Supporting Files

#### `requirements.txt`

Lists all Python dependencies required for the project. Install these using:

```bash
pip install -r requirements.txt
```

## Example Usage

Here's a typical workflow:

1. **Input Query**: "Calculate and come up with a trading strategy for gold and stock, provide clear analysis"

2. **Generated SQL**:

   ```sql
   SELECT date, gold_price
   FROM 
    finance_economics_dataset
   ORDER BY date
   LIMIT 50;
   ```

3. **Result:**

<details><summary>Based on the provided query results, I've analyzed the historical gold prices from January 2000 to February 2000. Here's a summary of my findings:</summary>

**Gold Price Trends:**

The gold price has fluctuated significantly throughout the period, with some periods showing an upward trend and others experiencing a downward trend.

- The highest price reached on January 21st, 2000, was $2477.43.
- The lowest price reached on February 17th, 2000, was $980.56.
- There's no clear indication of a specific pattern or trend in the data, but some peaks and valleys are noticeable.

**Trading Strategy:**

Considering the historical data, I recommend a trading strategy that focuses on identifying potential buying opportunities during upward trends and avoiding overbought markets.

1. **Buy Signal:** When gold prices are consistently above their 50-day moving average (currently around $2100) for at least three consecutive days, it could be a buy signal.
2. **Sell Signal:** Conversely, when gold prices fall below the 50-day moving average for three consecutive days, it might be a sell signal.

3. **Stop Loss and Take Profit:**
   Set stop-loss levels 10-15% below the entry point to limit potential losses. Consider setting take-profit targets at 20-25% above the entry point to capture price appreciation.
4. **Position Sizing:** Allocate 2-3% of your portfolio value to each trade, depending on your risk tolerance and market conditions.

**Some Specific Buy/Sell Recommendations:**

Based on my analysis, here are some specific buy/sell recommendations for January and February:

1. Buy gold on January 15th (current price: $1063.49) if the price stays above the 50-day moving average.
2. Sell gold on January 21st (current price: $2477.43) if the price falls below the 50-day moving average.

**Important Considerations:**

1. **Market Volatility:** Keep in mind that gold prices can be volatile, and rapid changes may occur due to external factors like economic news or global events.
2. **Risk Management:** Always prioritize risk management by setting clear stop-loss levels, adjusting position sizing based on market conditions, and avoiding over-leveraging.
"</details>

## Customization

### Adding Domain-Specific Queries

1. Update `prompts.py` with domain-specific examples
2. Modify `config.py` to include relevant data fields
3. Adjust `agent.py` logic if needed for specialized processing

### Database Integration

1. Update connection parameters in `config.py`
2. Modify `db_utils.py` for database-specific optimizations
3. Test with your specific database schema

## Troubleshooting

### Common Issues

1. **Ollama Connection Error**: Ensure Ollama server is running locally
2. **PostgreSQL Connection Error**:
   - Verify PostgreSQL service is running
   - Check database credentials in `config.py`
   - Ensure the database exists and user has proper permissions
   - Test connection using: `psql -h localhost -U your_username -d your_database`
   - Show `SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';`
3. **Model Loading Error**: Check if the specified model is downloaded in Ollama
4. **Dependency Issues**: Ensure all requirements are installed correctly

## Acknowledgments

- Built with Ollama for local LLM processing
- Utilizes prompt engineering techniques
- Designed for domain-specific Text-to-SQL applications

## Support

For issues and questions:

1. Check the troubleshooting section
2. Open an issue on GitHub
3. Review the documentation in each Python file for detailed implementation notes

---

**Note**: This application is designed for domain-specific use cases. Customize the prompts and configuration files according to your specific requirements and database schema.
