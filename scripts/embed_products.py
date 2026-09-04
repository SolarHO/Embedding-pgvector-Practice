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

with psycopg.connect(**DB_CONFIG) as conn:
    register_vector(conn)

    with conn.cursor() as cur:
        cur.execute("""
            SELECT product_id, name, description
            FROM products
            WHERE embedding IS NULL
            ORDER BY product_id;
        """)

        products = cur.fetchall()

        print(f"Products to embed: {len(products)}")

        for product_id, name, description in products:
            text = f"{name}. {description}"

            embedding = model.encode(text)

            cur.execute("""
                UPDATE products
                SET embedding = %s
                WHERE product_id = %s;
            """, (embedding, product_id))

            print(f"[DONE] {product_id}: {name}")

    conn.commit()

print("All product embeddings saved.")
