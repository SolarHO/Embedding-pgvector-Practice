# Embedding & pgvector Practice

Sentence Embedding과 PostgreSQL의 `pgvector`를 직접 사용하여  
Vector Search의 기본 원리를 학습하기 위한 실습 프로젝트입니다.

라이브러리가 검색 과정을 추상화하도록 맡기기보다 Python, PostgreSQL,
SentenceTransformer를 직접 연결하여 **Embedding → Vector 저장 → Semantic Search → Metadata Filtering**의 흐름을 구현하는 것을 목표로 했습니다.

---

## 1. 학습 목표

이번 프로젝트에서는 다음 내용을 직접 구현하고 학습했습니다.

- 자연어를 Embedding Vector로 변환하는 과정
- Embedding의 차원과 Vector 표현의 의미
- PostgreSQL에서 `pgvector` Extension 사용
- PostgreSQL에 Embedding Vector 저장
- Cosine Distance를 이용한 Vector Similarity Search
- Keyword Search와 Semantic Search의 차이
- SQL Metadata Filtering과 Vector Search 결합
- RAG에서 Retriever가 담당하는 역할

---

## 2. Tech Stack

| Category | Technology |
|---|---|
| Language | Python 3.12 |
| Database | PostgreSQL 16 |
| Vector Extension | pgvector |
| Embedding Model | sentence-transformers/all-MiniLM-L6-v2 |
| Python DB Client | psycopg |
| Container | Docker / Docker Compose |

---

## 3. 프로젝트 구조

```text
embedding-pgvector-practice/
│
├── app/
├── data/
├── scripts/
│   ├── embed_products.py
│   ├── search_products.py
│   ├── keyword_search.py
│   └── hybrid_search.py
│
├── tests/
├── .env.example
├── .gitignore
├── docker-compose.yml
├── requirements.txt
└── README.md
```

---

# What I Learned

## 4. Embedding

기존에는 Embedding을 단순히 "문장을 숫자로 변환하는 것" 정도로 이해하고 있었습니다.

이번 실습에서는 SentenceTransformer를 사용하여 상품명과 상품 설명을 실제 Vector로 변환하고 PostgreSQL에 저장하면서 Embedding이 **텍스트의 의미를 Vector Space에 표현하기 위한 방법**이라는 점을 학습했습니다.

사용한 모델은 다음과 같습니다.

```text
sentence-transformers/all-MiniLM-L6-v2
```

이 모델은 입력 텍스트를 **384차원의 Vector**로 변환합니다.

따라서 PostgreSQL의 컬럼도 동일한 차원으로 생성했습니다.

```sql
embedding vector(384)
```

이를 통해 Embedding Model의 출력 차원과 Vector DB에 정의하는 Vector 차원이 일치해야 한다는 점을 확인했습니다.

### Embedding Pipeline

```text
Product Name + Description
            ↓
    SentenceTransformer
            ↓
     384-d Embedding
            ↓
 PostgreSQL vector(384)
```

---

## 5. PostgreSQL + pgvector

Vector Database를 별도의 제품으로만 생각했지만, PostgreSQL에서도 `pgvector` Extension을 사용하면 Vector 데이터를 저장하고 검색할 수 있다는 것을 학습했습니다.

Docker를 이용해 `pgvector/pgvector:pg16` 이미지를 실행하고 PostgreSQL에 Vector Extension을 활성화했습니다.

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

상품 테이블에는 일반적인 정형 데이터와 Embedding을 함께 저장했습니다.

```sql
CREATE TABLE products (
    product_id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    category VARCHAR(100),
    price INTEGER,
    description TEXT,
    embedding vector(384)
);
```

이 구조를 통해 하나의 PostgreSQL 테이블에서 다음 두 종류의 데이터를 함께 관리할 수 있었습니다.

```text
Structured Data
- price
- category
- product_id

Vector Data
- embedding
```

---

## 6. Semantic Search

사용자가 입력한 검색 문장도 동일한 SentenceTransformer 모델을 이용하여 Embedding으로 변환했습니다.

```text
User Query
    ↓
SentenceTransformer
    ↓
Query Embedding
    ↓
pgvector Similarity Search
    ↓
Top-K Products
```

pgvector의 Cosine Distance 연산자인 `<=>`를 사용했습니다.

```sql
SELECT
    name,
    description,
    embedding <=> %s AS cosine_distance
FROM products
ORDER BY embedding <=> %s
LIMIT 3;
```

Cosine Distance를 사람이 이해하기 쉬운 Similarity 형태로 확인하기 위해 Python에서는 다음과 같이 계산했습니다.

```python
similarity = 1 - distance
```

이를 통해 정확히 동일한 Keyword가 포함되지 않아도 의미적으로 유사한 상품을 검색할 수 있다는 것을 확인했습니다.

### Semantic Search Test

> 📷 **Screenshot Placeholder**
>
> Semantic Search 쿼리 및 검색 결과 캡처 추가 예정

<!--
추후 이미지 추가 예시:

![Semantic Search Test](docs/images/semantic-search-test.png)
-->

---

## 7. Keyword Search vs Semantic Search

기존 SQL 검색 방식인 `ILIKE`와 Vector Search의 차이도 비교했습니다.

Keyword Search는 문자열이 실제 데이터에 존재하는지를 기준으로 검색합니다.

```sql
WHERE name ILIKE '%keyword%'
   OR description ILIKE '%keyword%'
```

반면 Semantic Search는 Query와 상품 설명을 각각 Vector로 표현하고 Vector 간의 거리를 비교합니다.

```text
Keyword Search
    → 문자열 일치 중심

Semantic Search
    → 의미적 유사성 중심
```

이를 통해 자연어 검색에서는 사용자가 데이터에 저장된 정확한 표현을 알지 못하더라도 의미적으로 관련된 결과를 찾을 수 있다는 점을 학습했습니다.

### Keyword / Semantic Search Comparison

> 📷 **Screenshot Placeholder**
>
> Keyword Search와 Semantic Search 비교 화면 추가 예정

---

## 8. Metadata Filtering + Vector Search

Vector Search만 사용하는 것보다 가격이나 카테고리처럼 명확한 조건은 SQL로 처리하는 것이 적합하다는 점을 학습했습니다.

예를 들어 다음과 같은 검색 조건이 있다고 가정했습니다.

```text
Query:
shoes for mountain hiking

Max Price:
100000

Category:
shoes
```

이 경우:

```text
price <= 100000
category = 'shoes'
```

과 같은 정형 조건은 SQL Metadata Filter가 처리하고,

```text
shoes for mountain hiking
```

와 같은 자연어 의미 검색은 Vector Search가 처리하도록 구성했습니다.

```text
User Query
     ↓
Query Embedding
     ↓
SQL Metadata Filtering
price <= 100000
category = shoes
     ↓
Vector Similarity Search
     ↓
Top-K Products
```

SQL에서는 다음과 같이 두 방식을 함께 적용했습니다.

```sql
SELECT
    product_id,
    name,
    category,
    price,
    description,
    embedding <=> %s AS cosine_distance
FROM products
WHERE embedding IS NOT NULL
  AND price <= %s
  AND category = %s
ORDER BY embedding <=> %s
LIMIT %s;
```

이를 통해 의미적으로 가장 유사한 상품이라도 가격 조건을 만족하지 않으면 검색 후보에서 제외되는 것을 확인했습니다.

> **Note**
>
> 이 프로젝트에서 현재 구현한 방식은 정확히는 **Metadata-filtered Semantic Search**입니다.
> 향후 Keyword/BM25와 Vector Search를 결합한 Lexical + Semantic Hybrid Search로 확장할 예정입니다.

### Metadata-filtered Search Test

> 📷 **Screenshot Placeholder**
>
> 가격 및 카테고리 조건을 적용한 검색 결과 캡처 추가 예정

---

## 9. 지금까지 이해한 Retrieval 구조

이번 실습을 통해 자연어 기반 검색이 다음과 같은 과정으로 동작한다는 것을 직접 확인했습니다.

```text
                  ┌─────────────────┐
                  │   User Query    │
                  └────────┬────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │ Embedding Model │
                  └────────┬────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │  Query Vector   │
                  └────────┬────────┘
                           │
                           ▼
            ┌─────────────────────────────┐
            │ PostgreSQL + pgvector       │
            │                             │
            │ Metadata Filtering          │
            │ + Vector Similarity Search  │
            └──────────────┬──────────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │ Top-K Products  │
                  └─────────────────┘
```

특히 **Embedding 자체가 검색 결과를 생성하는 것이 아니라**, Embedding은 의미를 Vector로 표현하고 pgvector가 Vector 간의 거리를 계산하여 관련 데이터를 검색한다는 역할 구분을 이해할 수 있었습니다.

---

## 10. RAG와의 관계

현재 프로젝트에서는 아직 LLM을 이용한 Generation은 구현하지 않았습니다.

현재까지 구현한 범위는 RAG 구조 중 **Retrieval에 해당하는 기반 기능**입니다.

```text
[현재 구현]

User Query
    ↓
Embedding
    ↓
Vector DB
    ↓
Retrieval
    ↓
Top-K Context


[향후 구현]

User Query
    ↓
Retrieval
    ↓
Relevant Context
    ↓
LLM
    ↓
Generated Answer
```

따라서 다음 단계에서는 현재 구현한 Retriever의 검색 결과를 LLM의 Context로 전달하여 실제 RAG 구조를 구현할 예정입니다.

---

## 11. 실행 방법

### Environment

`.env.example`을 참고하여 `.env` 파일을 생성합니다.

```text
DB_HOST=localhost
DB_PORT=5432
DB_NAME=ecommerce
DB_USER=ecommerce_user
DB_PASSWORD=your_password
```

### PostgreSQL 실행

```bash
docker compose up -d
```

### Embedding 생성

```bash
python scripts/embed_products.py
```

### Semantic Search

```bash
python scripts/search_products.py
```

### Keyword Search

```bash
python scripts/keyword_search.py
```

### Metadata-filtered Semantic Search

```bash
python scripts/hybrid_search.py
```

---

## 12. Roadmap

- [x] PostgreSQL + pgvector 환경 구축
- [x] Product Schema 생성
- [x] SentenceTransformer Embedding 생성
- [x] Embedding PostgreSQL 저장
- [x] Cosine Similarity 기반 Semantic Search
- [x] Keyword Search 비교
- [x] Metadata Filtering + Vector Search
- [ ] 실제 E-commerce Dataset 적용
- [ ] Vector Index (HNSW) 적용
- [ ] 검색 성능 및 품질 평가
- [ ] RAG Generator 연결
- [ ] API 구현
- [ ] Agent 기반 검색 구조 확장
