import psycopg2
from psycopg2.extras import Json
from datetime import date
import requests
import pandas as pd
import yfinance as yf
from src.financialData import alldata
def insert_standardpoor():
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"
    }

    response = requests.get(url, headers=headers)
    response.raise_for_status()
    tables = pd.read_html(response.text)
    sp500 = tables[0]  # first table is the S&P 500 list
    if "Symbol" in sp500.columns:
        tickers = sp500["Symbol"].tolist()
    tickers = [t.replace(".", "-") for t in tickers]
      
    data = yf.download(
        tickers,
        period="1d",
        interval="1d",
        group_by="ticker",
        auto_adjust=False,
        threads=True,
        progress=False
    )

    # 3️⃣ Build YOUR DataFrame
    rows = []

    for ticker in tickers:
        try:
            price = data[ticker]["Close"].iloc[-1]
            rows.append({
                "ticker": ticker,
                "price": float(price)
            })
        except Exception:
            # Some tickers may fail — skip them
            continue

    df_prices = pd.DataFrame(rows)

    print(df_prices.head())
    return df_prices





def insert_sp500_into_db(df_prices):
    conn = psycopg2.connect(
        host="localhost",
        database="massdcf",
        user="postgres",
        password="taxfraud"
    )
    cur = conn.cursor()

    for _, row in df_prices.iterrows():
        ticker = row["ticker"]
        price = row["price"]

        # 1️⃣ Insert company if it doesn't exist
        cur.execute("""
            INSERT INTO companies (ticker)
            VALUES (%s)
            ON CONFLICT (ticker) DO NOTHING
            RETURNING id;
        """, (ticker,))

        result = cur.fetchone()

        if result:
            company_id = result[0]
        else:
            cur.execute(
                "SELECT id FROM companies WHERE ticker = %s;",
                (ticker,)
            )
            company_id = cur.fetchone()[0]

        # 2️⃣ Insert today's price
        cur.execute("""
            INSERT INTO prices (company_id, price, price_date)
            VALUES (%s, %s, %s)
            ON CONFLICT (company_id, price_date)
            DO UPDATE SET price = EXCLUDED.price;
        """, (
            company_id,
            price,
            date.today()
        ))

    conn.commit()
    cur.close()
    conn.close()