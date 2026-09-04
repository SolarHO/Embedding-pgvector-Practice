# -*- coding: utf-8 -*-

import os
import psycopg
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT"),
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
}

def keyword_search(query):
    keyword = f"%{query}%"

    with psycopg.connect(**DB_CONFIG) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    product_id,
                    name,
                    category,
                    price,
                    description
                FROM products
                WHERE name ILIKE %s
                   OR description ILIKE %s
                ORDER BY product_id;
            """, (keyword, keyword))

            return cur.fetchall()

if __name__ == "__main__":
    query = input("Keyword query: ")

    results = keyword_search(query)

    print("\n=== Keyword Search Results ===")

    if not results:
        print("No results.")
    else:
        for row in results:
            product_id, name, category, price, description = row

            print()
            print(f"Product : {name}")
            print(f"Price   : {price:,}")
            print(f"Desc    : {description}")
