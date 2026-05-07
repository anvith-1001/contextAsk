import time
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
import os
import re

load_dotenv()


class Generator:

    CHARS_PER_TOKEN = 4
    CONTENT_WORD_RE = re.compile(r"[a-zA-Z0-9]+")
    STOP_WORDS = {
        "a", "an", "and", "are", "as", "at", "be", "by", "for", "from",
        "has", "he", "her", "his", "i", "in", "is", "it", "its", "of",
        "on", "or", "that", "the", "their", "there", "this", "to", "was",
        "were", "with", "you", "your", "name", "names", "called", "known",
        "mentioned", "character", "characters", "story", "other", "answer"
    }

    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=os.getenv("GOOGLE_API_KEY"),
            temperature=0
        )

    def _extract_token_usage(self, result):
        usage = getattr(result, "usage_metadata", None) or {}
        response_metadata = getattr(result, "response_metadata", None) or {}

        if not usage:
            usage = response_metadata.get("usage_metadata", {})

        return {
            "input_tokens": usage.get("input_tokens"),
            "output_tokens": usage.get("output_tokens"),
            "total_tokens": usage.get("total_tokens"),
        }

    def _estimate_tokens(self, text):
        return max(1, int(len(text) / self.CHARS_PER_TOKEN)) if text else 0

    def _doc_id(self, doc):
        metadata = doc.metadata or {}
        raw_id = (
            metadata.get("_id")
            or metadata.get("id")
            or metadata.get("doc_id")
            or metadata.get("chunk_id")
        )
        return str(raw_id) if raw_id is not None else None

    def _calculate_retrieval_metrics(self, context, relevant_doc_ids, k=5):
        if not relevant_doc_ids:
            return {
                "recall_at_5": None,
                "precision_at_5": None,
                "mrr": None,
                "retrieved_doc_ids_at_5": [
                    self._doc_id(doc)
                    for doc in context[:k]
                ],
                "expected_relevant_doc_ids": None,
                "retrieval_eval_note": (
                    "Provide relevant_doc_ids in the request to calculate "
                    "Recall@5, Precision@5, and MRR."
                )
            }

        relevant_ids = {str(doc_id) for doc_id in relevant_doc_ids}
        retrieved_ids = [
            self._doc_id(doc)
            for doc in context[:k]
        ]
        retrieved_ids = [doc_id for doc_id in retrieved_ids if doc_id]

        hits = [
            doc_id for doc_id in retrieved_ids
            if doc_id in relevant_ids
        ]

        first_hit_rank = None
        for index, doc_id in enumerate(retrieved_ids, start=1):
            if doc_id in relevant_ids:
                first_hit_rank = index
                break

        return {
            "recall_at_5": round(len(set(hits)) / len(relevant_ids), 4)
            if relevant_ids else 0,
            "precision_at_5": round(len(hits) / k, 4),
            "mrr": round(1 / first_hit_rank, 4) if first_hit_rank else 0,
            "retrieved_doc_ids_at_5": retrieved_ids,
            "expected_relevant_doc_ids": list(relevant_ids),
            "retrieval_eval_note": None
        }

    def _content_words(self, text):
        return {
            word
            for word in self.CONTENT_WORD_RE.findall((text or "").lower())
            if len(word) > 2 and word not in self.STOP_WORDS
        }

    def _calculate_faithfulness_score(self, response, context_text):
        if not response:
            return 1.0

        if "could not find that information" in response.lower():
            return 1.0

        answer_words = self._content_words(response)
        if not answer_words:
            return 1.0

        context_words = self._content_words(context_text)
        if not context_words:
            return 0.0

        supported_words = answer_words.intersection(context_words)
        return round(len(supported_words) / len(answer_words), 4)

    def _calculate_cost_per_query(self, token_usage, prompt, response):
        input_tokens = token_usage["input_tokens"] or self._estimate_tokens(prompt)
        output_tokens = token_usage["output_tokens"] or self._estimate_tokens(response)

        input_cost_per_1m = os.getenv("MODEL_INPUT_COST_PER_1M_TOKEN")
        output_cost_per_1m = os.getenv("MODEL_OUTPUT_COST_PER_1M_TOKEN")

        if input_cost_per_1m is None or output_cost_per_1m is None:
            return None, (
                "Set MODEL_INPUT_COST_PER_1M_TOKEN and "
                "MODEL_OUTPUT_COST_PER_1M_TOKEN to calculate real cost."
            )

        try:
            input_cost = float(input_cost_per_1m)
            output_cost = float(output_cost_per_1m)
        except ValueError:
            return None, "Model cost environment variables must be numeric."

        cost = (
            (input_tokens / 1_000_000) * input_cost
            + (output_tokens / 1_000_000) * output_cost
        )

        return round(cost, 8), None

    def _percentage_reduction(self, baseline, current):
        if baseline is None or baseline <= 0:
            return None

        return round(((baseline - current) / baseline) * 100, 2)

    def _calculate_metrics(
        self,
        query,
        context,
        response,
        prompt,
        history_text,
        start_time,
        end_time,
        result,
        relevant_doc_ids=None,
        baseline_latency_sec=None,
        baseline_hallucination_rate=None,
        user_satisfaction_score=None
    ):

        context_text = "\n".join([
            doc.page_content for doc in context
        ])

        chunk_lengths = [
            len(doc.page_content) for doc in context
        ]

        sources = [
            doc.metadata.get("source")
            for doc in context
            if doc.metadata.get("source")
        ]

        token_usage = self._extract_token_usage(result)
        retrieval_metrics = self._calculate_retrieval_metrics(
            context=context,
            relevant_doc_ids=relevant_doc_ids,
            k=5
        )
        faithfulness_score = self._calculate_faithfulness_score(
            response=response,
            context_text=context_text
        )
        hallucination_rate = round(1 - faithfulness_score, 4)
        cost_per_query_usd, cost_note = self._calculate_cost_per_query(
            token_usage=token_usage,
            prompt=prompt,
            response=response
        )
        latency_sec = round(end_time - start_time, 3)

        metrics = {
            "latency_sec": latency_sec,
            "model": self.llm.model,
            "query_chars": len(query),
            "history_chars": len(history_text),
            "context_chars": len(context_text),
            "prompt_chars": len(prompt),
            "response_chars": len(response),
            "num_chunks": len(context),
            "unique_sources": len(set(sources)),
            "avg_chunk_chars": round(sum(chunk_lengths) / len(chunk_lengths), 2)
            if chunk_lengths else 0,
            "min_chunk_chars": min(chunk_lengths) if chunk_lengths else 0,
            "max_chunk_chars": max(chunk_lengths) if chunk_lengths else 0,
            "input_tokens": token_usage["input_tokens"],
            "output_tokens": token_usage["output_tokens"],
            "total_tokens": token_usage["total_tokens"],
            "estimated_input_tokens": self._estimate_tokens(prompt),
            "estimated_output_tokens": self._estimate_tokens(response),
            "recall_at_5": retrieval_metrics["recall_at_5"],
            "precision_at_5": retrieval_metrics["precision_at_5"],
            "mrr": retrieval_metrics["mrr"],
            "retrieved_doc_ids_at_5": retrieval_metrics["retrieved_doc_ids_at_5"],
            "expected_relevant_doc_ids": retrieval_metrics[
                "expected_relevant_doc_ids"
            ],
            "faithfulness_score": faithfulness_score,
            "hallucination_rate": hallucination_rate,
            "hallucination_reduction_percent": self._percentage_reduction(
                baseline_hallucination_rate,
                hallucination_rate
            ),
            "latency_reduction_percent": self._percentage_reduction(
                baseline_latency_sec,
                latency_sec
            ),
            "cost_per_query_usd": cost_per_query_usd,
            "user_satisfaction_percent": user_satisfaction_score,
            "metric_notes": {
                "retrieval": retrieval_metrics["retrieval_eval_note"],
                "cost": cost_note,
                "hallucination_reduction": None
                if baseline_hallucination_rate is not None
                else "Provide baseline_hallucination_rate to calculate reduction.",
                "latency_reduction": None
                if baseline_latency_sec is not None
                else "Provide baseline_latency_sec to calculate reduction.",
                "user_satisfaction": None
                if user_satisfaction_score is not None
                else "Collect user feedback to report satisfaction."
            }
        }

        return metrics

    def _build_rag_prompt(self, query, combined_context, history_text):
        return f"""
You are a precise and trustworthy conversational RAG assistant.

Your task is to answer the user's question ONLY using the provided context and conversation history.

Rules:
1. Use ONLY the information found in the Context and Conversation History.
2. Do NOT make up facts, assumptions, or external knowledge.
3. If the answer is not present in the context, clearly say:
   "I could not find that information in the provided context."
4. Keep the answer as short as possible while still fully answering the question.
5. For simple factual questions, answer with the exact name, value, phrase, or sentence supported by the context.
6. For direct lookup questions like "what is the name?", return only the answer value, not a full sentence.
7. Prefer wording that appears directly in the context. Avoid adding extra explanation unless the question asks for it.
8. If the answer needs a short sentence, include only claims that are directly supported by the context.
9. Prioritize the most relevant and recent information from the conversation history.
10. If multiple context chunks conflict, mention the conflict rather than guessing.
11. The answer must be safe for work and free of harmful, explicit, or unsafe content.
12. Do not mention that you are an AI model unless explicitly asked.
13. Do not repeat the entire context back to the user.

Conversation History:
{history_text}

Retrieved Context:
{combined_context}

User Question:
{query}

Final Answer:
""".strip()

    def _build_normal_prompt(self, query, history_text):
        return f"""
You are a helpful, trustworthy, and conversational assistant.

Your task is to respond naturally using the conversation history and the user's latest message.

Rules:
1. Be clear, concise, and conversational.
2. Use the conversation history to maintain continuity.
3. Do NOT mention retrieved context or missing context.
4. Do NOT produce harmful, explicit, or unsafe content.
5. Do not mention that you are an AI model unless explicitly asked.

Conversation History:
{history_text}

User Message:
{query}

Final Answer:
""".strip()

    def generate(
        self,
        query,
        context,
        history=None,
        mode="rag",
        return_metrics=False,
        relevant_doc_ids=None,
        baseline_latency_sec=None,
        baseline_hallucination_rate=None,
        user_satisfaction_score=None
    ):

        combined_context = "\n".join([
            doc.page_content for doc in context
        ])

        history_text = ""

        if history:
            history_text = "\n".join([
                f"{msg['role']}: {msg['content']}"
                for msg in history
            ])

        if mode.lower() == "rag":
            prompt = self._build_rag_prompt(
                query=query,
                combined_context=combined_context,
                history_text=history_text
            )
        else:
            prompt = self._build_normal_prompt(
                query=query,
                history_text=history_text
            )

        start_time = time.time()

        result = self.llm.invoke(prompt)
        answer = result.content

        end_time = time.time()

        metrics = self._calculate_metrics(
            query,
            context,
            answer,
            prompt,
            history_text,
            start_time,
            end_time,
            result,
            relevant_doc_ids=relevant_doc_ids,
            baseline_latency_sec=baseline_latency_sec,
            baseline_hallucination_rate=baseline_hallucination_rate,
            user_satisfaction_score=user_satisfaction_score
        )

        if return_metrics:
            return {
                "answer": answer,
                "metrics": metrics
            }

        return answer