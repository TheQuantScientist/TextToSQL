import json

# PostgreSQL Configuration
POSTGRES_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'dbname': 'postgres',
    'user': 'admin',
    'password': ''
}

# Ollama Model Configuration
OLLAMA_CONFIG = {
    'model': 'llama3.2:latest',
    'endpoint': 'http://localhost:11434/'
}

# Data Fields Meaning
DATA_FIELDS_MEANING = {
    "finance_economics_dataset": {
        "data_type": "PostgreSQL Table",
        "fields": {
            "date": "The timestamp of the stock (DATE)",
            "stock_index": "The name of the stock market index being tracked (VARCHAR)",
            "open_price": "The opening price of the stock or asset (FLOAT)",
            "close_price": "The closing price of the stock or asset (FLOAT)",
            "daily_high": "The highest price reached by the stock or asset (FLOAT)",
            "daily_low": "The lowest price reached by the stock or asset (FLOAT)",
            "trading_volume": "The total number of shares or contracts traded (INTEGER)",
            "gdp_growth": "The percentage growth of GDP (FLOAT)",
            "inflation_rate": "The rate of inflation (FLOAT)",
            "unemployment_rate": "The percentage of the labor force unemployed (FLOAT)",
            "interest_rate": "The central bank's policy interest rate (FLOAT)",
            "consumer_confidence_index": "An indicator of consumer optimism (FLOAT)",
            "government_debt": "The total government debt as a percentage of GDP (FLOAT)",
            "corporate_profits": "Profits earned by corporations after taxes (FLOAT)",
            "forex_usd_eur": "The exchange rate between USD and EUR (FLOAT)",
            "forex_usd_jpy": "The exchange rate between USD and JPY (FLOAT)",
            "crude_oil_price": "The price per barrel of crude oil (FLOAT)",
            "gold_price": "The price per ounce of gold (FLOAT)",
            "real_estate_index": "An index of real estate prices (FLOAT)",
            "retail_sales": "The total retail sales value (FLOAT)",
            "bankruptcy_rate": "The rate of bankruptcies (FLOAT)",
            "mergers_acquisitions_deals": "The number of M&A deals (INTEGER)",
            "venture_capital_funding": "The amount of VC funding (FLOAT)",
            "consumer_spending": "Total household expenditure (FLOAT)"
        }
    },

    "country_income": {
        "data_type": "PostgreSQL Table",
        "fields": {
            "country": "The name of the country being tracked (TEXT)",
            "iso": "ISO 3-letter country code (e.g., 'afg' for Afghanistan) (TEXT)",
            "gcam_region_id": "Numerical region ID used in the Global Change Assessment Model (GCAM) (INTEGER)",
            "year": "Year the data corresponds to (INTEGER)",
            "ref": "A reference key combining ISO code and year (e.g., 'afg1967') (TEXT)",
            "gini_reported": "Reported Gini coefficient for income inequality (FLOAT)",
            "gdp_ppp_pc_usd2011": "GDP per capita in PPP, constant 2011 US dollars (FLOAT)",
            "population": "Total population of the country in that year (FLOAT)",
            "category": "Income decile group (e.g., 'd1' = lowest 10%, 'd10' = highest 10%) (TEXT)",
            "income_net": "Share of net income attributed to the specific income decile (FLOAT)",
            "gini_recalculated": "Gini coefficient recalculated from decile data (FLOAT)",
            "data_source": "Origin or method of data derivation (e.g., 'Imputed from GINI coefficient') (TEXT)"
        }
    }
}

def get_data_fields_from_table(table_name:str):
    # Generate json string
    json_str = json.dumps(DATA_FIELDS_MEANING[table_name]['fields'], indent=2)
    
    # Escape curly braces in JSON for prompt formatting
    data_fields = json_str.replace('{', '{{').replace('}', '}}') 
    return data_fields
