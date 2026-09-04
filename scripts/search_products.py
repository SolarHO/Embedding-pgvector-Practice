# -*- coding: utf-8 -*-

import os

import psycopg
from dotenv import load_dotenv
from pgvector.psycopg import register_vector
from sentence_transformers import SentenceTransformer

load_dotenv()

DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT"),
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
}

model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")


def search_products(query, top_k=3):
    # 1. Convert the user's natural-language query into a 384-D vector
    query_embedding = model.encode(query)

    # 2. Connect to PostgreSQL
    with psycopg.connect(**DB_CONFIG) as conn:
        register_vector(conn)

        with conn.cursor() as cur:
            # 3. Find vectors closest to the query vector
            cur.execute("""
                SELECT
                    product_id,
                    name,
                    category,
                    price,
                    description,
                    embedding <=> %s AS cosine_distance
                FROM products
                WHERE embedding IS NOT NULL
                ORDER BY embedding <=> %s
                LIMIT %s;
            """, (query_embedding, query_embedding, top_k))

            return cur.fetchall()


if __name__ == "__main__":
    query = input("Search query: ")

    results = search_products(query)

    print("\n=== Search Results ===")

    for rank, row in enumerate(results, start=1):
        product_id, name, category, price, description, distance = row

        similarity = 1 - distance

        print(f"\nRank {rank}")
        print(f"Product : {name}")
        print(f"Price   : {price:,}")
        print(f"Desc    : {description}")
        print(f"Similarity : {similarity:.4f}")
