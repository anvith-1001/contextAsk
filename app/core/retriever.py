from typing import List

domain_keywords = {
    "backend": ["api", "server", "database", "microservice"],
    "finance": ["stock", "investment", "market", "equity"],
    "sports": ["cricket", "ipl", "football", "match"],
    "legal": ["law", "contract", "court", "compliance"]
}


def detect_domain(query):
    query = query.lower()

    for domain, keywords in domain_keywords.items():
        if any(word in query for word in keywords):
            return domain

    return "general"


class Retriever:

    def __init__(self, vectordb, reranker=None):
        self.vectordb = vectordb
        self.reranker = reranker

    def hybrid_search(
        self,
        query: str,
        user_id: str,
        chat_id: str,
        k: int = 3
    ):

        vector_results = self.vectordb.search(
            query=query,
            user_id=user_id,
            chat_id=chat_id,
            k=k
        )


        seen = set()
        combined = []


# one of the search logic was removed in order to reduce latency. ( working on it )
        for doc in vector_results:
            if doc.page_content not in seen:
                seen.add(doc.page_content)
                combined.append(doc)


        return combined



    def rerank_results(self, query: str, docs, k: int = 5):

        query_words = query.lower().split()
        domain = detect_domain(query)

        def score(doc):

            content = doc.page_content.lower()

            keyword_score = sum(
                2 for w in query_words if w in content
            )

            length_score = min(len(content) / 500, 2)

            domain_bonus = 0

            if domain != "general":
                for keyword in domain_keywords[domain]:
                    if keyword in content:
                        domain_bonus += 1

            return keyword_score + length_score + domain_bonus

        ranked = sorted(docs, key=score, reverse=True)

        return ranked[:k]


# all res.
    def retrieve(
        self,
        query: str,
        user_id: str,
        chat_id: str,
        k: int = 3
    ):

        docs = self.hybrid_search(
            query=query,
            user_id=user_id,
            chat_id=chat_id,
            k=k
        )

        docs = self.rerank_results(query, docs, k)
        return docs