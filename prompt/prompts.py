import json
import sys

sys.path.append('.')

# PostgreSQL Configuration
POSTGRES_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'dbname': 'text2sql',
    'user': 'postgres',
    'password': 'admin'
}

# Groq Model Configuration
GROQ_CONFIG = {
    'model': 'llama3-70b-8192',
    'api_key': 'YOUR_API_KEY',  # Replace with your actual Groq API key
}

# Ollama Model Configuration
OLLAMA_CONFIG = {
    'model': 'gemma3:12b',
    'endpoint': 'http://localhost:11434/'
}

# Data Fields Meaning 1
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
            "confidence_in_national_government": "Public confidence in the national government (FLOAT)"
        }
    }, 

    "global_development_indicators": {
        "data_type": "PostgreSQL Table",
        "fields": {
            "year": "The year of the survey (INTEGER)",
            "country_code": "The geographic region the country belongs to (VARCHAR)",
            "country_name": "The name of the country (VARCHAR)",
            "region": "Overall life evaluation score on a scale from 0 to 10 (FLOAT)",
            "income_group": "Logarithm of GDP per capita (FLOAT)",
            "currency_unit": "Perceived social support availability (FLOAT)",
            "gdp_usd": "Average healthy life expectancy at birth (FLOAT)",
            "population": "Perceived freedom to make life decisions (FLOAT)",
            "gdp_per_capita": "Perceived generosity based on donation behavior (FLOAT)",
            "unemployment_rate": "Perceived level of corruption in society (FLOAT)",
            "fdi_pct_gdp": "Share of people who experienced positive emotions the previous day (FLOAT)",
            "co2_emissions_kt": "Share of people who experienced negative emotions the previous day (FLOAT)",
            "energy_use_per_capita": "Public confidence in the national government (FLOAT)",
            "internet_usage_pct": "Percentage of the population using the internet (FLOAT)",
            "forest_area_pct": "The percentage of land area covered by forests (FLOAT)",
            "inflation_rate": "No description provided (FLOAT or VARCHAR depending on context)",
            "renewable_energy_pct": "No description provided (FLOAT or VARCHAR depending on context)",
            "electricity_access_pct": "No description provided (FLOAT or VARCHAR depending on context)",
            "life_expectancy": "No description provided (FLOAT or VARCHAR depending on context)",
            "child_mortality": "No description provided (FLOAT or VARCHAR depending on context)",
            "school_enrollment_secondary": "No description provided (FLOAT or VARCHAR depending on context)",
            "health_expenditure_pct_gdp": "No description provided (FLOAT or VARCHAR depending on context)",
            "hospital_beds_per_1000": "No description provided (FLOAT or VARCHAR depending on context)",
            "physicians_per_1000": "No description provided (FLOAT or VARCHAR depending on context)",
            "mobile_subscriptions_per_100": "No description provided (FLOAT or VARCHAR depending on context)",
            "calculated_gdp_per_capita": "No description provided (FLOAT or VARCHAR depending on context)",
            "real_economic_growth_indicator": "No description provided (FLOAT or VARCHAR depending on context)",
            "econ_opportunity_index": "No description provided (FLOAT or VARCHAR depending on context)",
            "co2_emissions_per_capita_tons": "No description provided (FLOAT or VARCHAR depending on context)",
            "co2_intensity_per_million_gdp": "No description provided (FLOAT or VARCHAR depending on context)",
            "green_transition_score": "No description provided (FLOAT or VARCHAR depending on context)",
            "ecological_preservation_index": "No description provided (FLOAT or VARCHAR depending on context)",
            "renewable_energy_efficiency": "No description provided (FLOAT or VARCHAR depending on context)",
            "human_development_composite": "No description provided (FLOAT or VARCHAR depending on context)",
            "healthcare_capacity_index": "No description provided (FLOAT or VARCHAR depending on context)",
            "digital_connectivity_index": "No description provided (FLOAT or VARCHAR depending on context)",
            "health_development_ratio": "No description provided (FLOAT or VARCHAR depending on context)",
            "education_health_ratio": "No description provided (FLOAT or VARCHAR depending on context)",
            "years_since_2000": "No description provided (FLOAT or VARCHAR depending on context)",
            "years_since_century": "No description provided (FLOAT or VARCHAR depending on context)",
            "is_pandemic_period": "No description provided (FLOAT or VARCHAR depending on context)",
            "human_development_index": "No description provided (FLOAT or VARCHAR depending on context)",
            "climate_vulnerability_index": "No description provided (FLOAT or VARCHAR depending on context)",
            "digital_readiness_score": "No description provided (FLOAT or VARCHAR depending on context)",
            "governance_quality_index": "No description provided (FLOAT or VARCHAR depending on context)",
            "global_resilience_score": "No description provided (FLOAT or VARCHAR depending on context)",
            "global_development_resilience_index": "No description provided (FLOAT or VARCHAR depending on context)"
        }
    },

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


NL_RESPONSE_PROMPT = """
You are an expert data analyst. 
Given the query results, provide a clear, concise, and natural language response that answers the question using the queried results.
Use the query results to inform your answer and present the information in a user-friendly way.
"""

def get_system_prompt(table_name: str):
    system_prompt = f"""
        You are a SQL expert for PostgreSQL.
        Only generate a valid SQL query for a table named '{table_name}'.
        Your goal is to generate precise SQL query.
        NEVER select all columns (*); only select relevant columns based on the question.
        NEVER answer in natural language. ONLY write SQL for query purposes.
        Limit query results to 50 rows only.
        The table has the following fields:
        {get_data_fields_from_table(table_name)}
    """
    return system_prompt
