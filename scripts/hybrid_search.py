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


def hybrid_search(query, max_price=None, category=None, top_k=3):
    query_embedding = model.encode(query)

    conditions = ["embedding IS NOT NULL"]
    params = []

    if max_price is not None:
        conditions.append("price <= %s")
        params.append(max_price)

    if category:
        conditions.append("category = %s")
        params.append(category)

    where_clause = " AND ".join(conditions)

    sql = f"""
        SELECT
            product_id,
            name,
            category,
            price,
            description,
            embedding <=> %s AS cosine_distance
        FROM products
        WHERE {where_clause}
        ORDER BY embedding <=> %s
        LIMIT %s;
    """

    final_params = [
        query_embedding,
        *params,
        query_embedding,
        top_k,
    ]

    with psycopg.connect(**DB_CONFIG) as conn:
        register_vector(conn)

        with conn.cursor() as cur:
            cur.execute(sql, final_params)
            return cur.fetchall()


if __name__ == "__main__":
    query = input("Search query: ").strip()

    max_price_input = input(
        "Max price (press Enter for no limit): "
    ).strip()

    category_input = input(
        "Category (press Enter for all): "
    ).strip()

    max_price = int(max_price_input) if max_price_input else None
    category = category_input if category_input else None

    results = hybrid_search(
        query=query,
        max_price=max_price,
        category=category,
        top_k=3,
    )

    print("\n=== Hybrid Search Results ===")

    if not results:
        print("No matching products.")
    else:
        for rank, row in enumerate(results, start=1):
            (
                product_id,
                name,
                category,
                price,
                description,
                distance,
            ) = row

            similarity = 1 - distance

            print(f"\nRank {rank}")
            print(f"Product    : {name}")
            print(f"Category   : {category}")
            print(f"Price      : {price:,}")
            print(f"Desc       : {description}")
            print(f"Similarity : {similarity:.4f}")
