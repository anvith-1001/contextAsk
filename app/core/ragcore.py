class RAGCore:

    def __init__(self, retriever, generator, chat_message_core):
        self.retriever = retriever
        self.generator = generator
        self.chat_message_core = chat_message_core

    def run(
        self,
        query,
        user_id,
        chat_id,
        mode="normal",
        relevant_doc_ids=None,
        baseline_latency_sec=None,
        baseline_hallucination_rate=None,
        user_satisfaction_score=None
    ):

        self.chat_message_core.save_message(
            chat_id=chat_id,
            user_id=user_id,
            role="user",
            content=query
        )

        history = self.chat_message_core.get_messages(
            chat_id=chat_id,
            user_id=user_id,
            limit=10
        )

        context = []

        if mode.lower() == "rag":
            context = self.retriever.retrieve(
                query=query,
                user_id=user_id,
                chat_id=chat_id,
                k=5
            )

        answer = self.generator.generate(
            query=query,
            context=context,
            history=history,
            mode=mode,
            return_metrics=True,
            relevant_doc_ids=relevant_doc_ids,
            baseline_latency_sec=baseline_latency_sec,
            baseline_hallucination_rate=baseline_hallucination_rate,
            user_satisfaction_score=user_satisfaction_score
        )

        self.chat_message_core.save_message(
            chat_id=chat_id,
            user_id=user_id,
            role="assistant",
            content=answer["answer"]
        )

        return {
            "answer": answer,
            "sources": [doc.metadata for doc in context] if context else []
        }