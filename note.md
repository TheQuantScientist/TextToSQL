# Worklog - Ngan

## 24-05-2025

### Accomplishment

- Clone repo via Github Desktop.
- Install Postgres app and PgAdmin (+ PostgreSQL in Homebrew).
  - Create admin role, give login and superuser permission.
- Connect admin to PgAdmin.
  - Create TABLE in PgAdmin with column description and data type.
  - Edit headers from CamelCASE to underscore in the CSV file.
  - Copy data to the table.

### Detailed Notes

- When running the repo, encountered different configuration
  - No `admin` role from local database
  - Using `llama3.2` instead of `gemma3:4b`
=> Suggestion: import .env to config, instead of hardcoding
=> Suggestion: add `.gitignore`

- Data population:
  - Create table script

```sql
CREATE TABLE finance_economics_dataset (
    date DATE,  -- The timestamp of the stock
    stock_index VARCHAR,  -- The name of the stock market index being tracked
    open_price FLOAT,  -- The opening price of the stock or asset
    close_price FLOAT,  -- The closing price of the stock or asset
    daily_high FLOAT,  -- The highest price reached by the stock or asset
    daily_low FLOAT,  -- The lowest price reached by the stock or asset
    trading_volume INTEGER,  -- The total number of shares or contracts traded
    gdp_growth FLOAT,  -- The percentage growth of GDP
    inflation_rate FLOAT,  -- The rate of inflation
    unemployment_rate FLOAT,  -- The percentage of the labor force unemployed
    interest_rate FLOAT,  -- The central bank’s policy interest rate
    consumer_confidence_index FLOAT,  -- An indicator of consumer optimism
    government_debt FLOAT,  -- The total government debt as a percentage of GDP
    corporate_profits FLOAT,  -- Profits earned by corporations after taxes
    forex_usd_eur FLOAT,  -- The exchange rate between USD and EUR
    forex_usd_jpy FLOAT,  -- The exchange rate between USD and JPY
    crude_oil_price FLOAT,  -- The price per barrel of crude oil
    gold_price FLOAT,  -- The price per ounce of gold
    real_estate_index FLOAT,  -- An index of real estate prices
    retail_sales FLOAT,  -- The total retail sales value
    bankruptcy_rate FLOAT,  -- The rate of bankruptcies
    mergers_acquisitions_deals INTEGER,  -- The number of M&A deals
    venture_capital_funding FLOAT,  -- The amount of VC funding
    consumer_spending FLOAT  -- Total household expenditure
);
```

- Manual convert the header rows to compatible columns format defined in the code

```txt
date,stock_index,open_price,close_price,daily_high,daily_low,trading_volume,gdp_growth,inflation_rate,unemployment_rate,interest_rate,consumer_confidence_index,government_debt,corporate_profits,forex_usd_eur,forex_usd_jpy,crude_oil_price,gold_price,real_estate_index,retail_sales,bankruptcy_rate,mergers_acquisitions_deals,venture_capital_funding,consumer_spending
```

- Run copy script in `psql` to populate the data

```bash
\copy finance_economics_dataset 
FROM '/Users/ngannguyen/Desktop/convobot/economic_cleaned.csv' 
WITH (FORMAT csv, HEADER true)
```

- Input query: "Calculate a trading strategy for gold and stock"
Results

```md
Query: SELECT date, gold_price
FROM finance_economics_dataset
WHERE gold_price BETWEEN (SELECT MAX(gold_price) FROM finance_economics_dataset) - 10 AND (SELECT MAX(gold_price) FROM finance_economics_dataset) + 5;

SELECT date, open_price, close_price, daily_high, daily_low, forex_usd_jpy
FROM finance_economics_dataset
WHERE forex_usd_jpy BETWEEN (SELECT MAX(forex_usd_jpy) FROM finance_economics_dataset) - 0.1 AND (SELECT MAX(forex_usd_jpy) FROM finance_economics_dataset) + 0.1
Raw Results:
| date | open_price | close_price | daily_high | daily_low | forex_usd_jpy |
| --- | --- | --- | --- | --- | --- |
| 2004-06-22 | 2404.88 | 2407.35 | 2440.59 | 2377.98 | 149.96 |
| 2006-04-11 | 1317.12 | 1274.92 | 1317.48 | 1269.21 | 149.94 |
| 2006-04-20 | 1322.46 | 1285.36 | 1368.02 | 1259.52 | 149.92 |
| 2006-09-13 | 1723.57 | 1729.31 | 1749.02 | 1704.19 | 149.94 |

Final Answer:
Based on the provided query results, I'll provide a clear and concise analysis to help develop a trading strategy for gold and stocks.

**Gold Analysis:**

The provided data shows that gold's price movement is not very volatile, with relatively small daily high and low prices. The average daily high price is $2439.19 ($2440.59 + $1368.02), and the average daily low price is $1273.84 ($2377.98 + $1259.52).

However, we notice that gold's forex_usd_jpy rate has been relatively consistent, averaging 149.96 over the three data points.

**Stock Analysis:**

The stock prices in the provided data range from $1317.12 to $1723.57. While there is a significant variation in price, the overall trend appears to be upward, with an average daily high of $1734.42 ($1729.31 + $1749.02).

**Trading Strategy:**

Based on these findings, I would recommend the following trading strategy:

1. **Long-term investing:** Considering gold's relatively stable prices and consistent forex_usd_jpy rate, we can infer that gold is a good long-term investment option.
2. **Diversification:** To minimize risk, it's essential to diversify your portfolio by investing in stocks as well. Given the upward trend in stock prices, it may be wise to focus on growth-oriented stocks.
3. **Stop-loss and take-profit:**
* For gold, consider setting a stop-loss at 10% below the current price ($2424.19) and a take-profit target at 20% above the current price ($2909.51).
* For stocks, set a stop-loss at 5% below the current price ($1641.71) and a take-profit target at 15% above the current price ($1946.95).

**Recommendation:**

Given the data, I would recommend investing in gold as a long-term option and diversifying your portfolio by adding growth-oriented stocks. Be cautious when entering or exiting trades, especially for stocks, due to their higher volatility.

Please note that this analysis is based on historical data and should not be considered as investment advice. It's essential to conduct thorough research and consider individual risk tolerance before making any investment decisions.
```
