import json

# PostgreSQL Configuration
POSTGRES_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'dbname': 'text2sql',
    'user': 'postgres',
    'password': 'admin'
}

# Ollama Model Configuration
OLLAMA_CONFIG = {
    'model': 'gemma3:12b',
    'endpoint': 'http://localhost:11434/'
}

# Data Fields Meaning
DATA_FIELDS_MEANING = {
    "world_happiness_report": {
        "data_type": "PostgreSQL Table",
        "fields": {
            "country_name": "The name of the country (VARCHAR)",
            "regional_indicator": "The geographic region the country belongs to (VARCHAR)",
            "year": "The year of the survey (INTEGER)",
            "life_ladder": "Overall life evaluation score on a scale from 0 to 10 (FLOAT)",
            "log_GDP_per_capital": "Logarithm of GDP per capita (FLOAT)",
            "social_support": "Perceived social support availability (FLOAT)",
            "healthy_life_expectancy_at_birth": "Average healthy life expectancy at birth (FLOAT)",
            "freedom_to_make_life_choices": "Perceived freedom to make life decisions (FLOAT)",
            "generosity": "Perceived generosity based on donation behavior (FLOAT)",
            "perceptions_of_corruption": "Perceived level of corruption in society (FLOAT)",
            "positive_affect": "Share of people who experienced positive emotions the previous day (FLOAT)",
            "negative_affect": "Share of people who experienced negative emotions the previous day (FLOAT)",
            "confidence_in_national_government": "Public confidence in the national government (FLOAT)",
            # "corporate_profits": "Profits earned by corporations after taxes (FLOAT)",
            # "forex_usd_eur": "The exchange rate between USD and EUR (FLOAT)",
            # "forex_usd_jpy": "The exchange rate between USD and JPY (FLOAT)",
            # "crude_oil_price": "The price per barrel of crude oil (FLOAT)",
            # "gold_price": "The price per ounce of gold (FLOAT)",
            # "real_estate_index": "An index of real estate prices (FLOAT)",
            # "retail_sales": "The total retail sales value (FLOAT)",
            # "bankruptcy_rate": "The rate of bankruptcies (FLOAT)",
            # "mergers_acquisitions_deals": "The number of M&A deals (INTEGER)",
            # "venture_capital_funding": "The amount of VC funding (FLOAT)",
            # "consumer_spending": "Total household expenditure (FLOAT)"
        }
    }
}

# Escape curly braces in JSON for prompt formatting
FIELDS_JSON = json.dumps(DATA_FIELDS_MEANING['world_happiness_report']['fields'], indent=2).replace('{', '{{').replace('}', '}}')