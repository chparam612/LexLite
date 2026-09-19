from typing import List
from dataclasses import dataclass
from sqlalchemy.orm import Session

from app.services.retrieval_service import RetrievalService
from app.services.generation_service import GenerationService
from app.services.verification_service import VerificationService


@dataclass
class EvaluationSample:
    query: str
    expected_answer_keywords: List[str]
    expected_chunk_ids: List[str]


@dataclass
class EvaluationMetrics:
    total_samples: int
    faithfulness_score: float  # Supported claims / total claims
    answer_relevance_score: float  # Keyword hit ratio in answer
    context_precision: float  # Expected chunks found in top-k
    context_recall: float  # Proportion of expected chunks retrieved
    average_latency_ms: float


class RAGEvaluator:
    def __init__(
        self,
        retrieval_service: RetrievalService = None,
        generation_service: GenerationService = None,
        verification_service: VerificationService = None
    ):
        self.retrieval_service = retrieval_service or RetrievalService()
        self.generation_service = generation_service or GenerationService()
        self.verification_service = verification_service or VerificationService()

    def evaluate_benchmark(
        self,
        db: Session,
        user_id: str,
        samples: List[EvaluationSample],
        top_k: int = 5
    ) -> EvaluationMetrics:
        """
        Run automated RAG evaluation measuring Faithfulness, Answer Relevance,
        Context Precision, and Context Recall across a test benchmark.
        """
        if not samples:
            return EvaluationMetrics(0, 1.0, 1.0, 1.0, 1.0, 0.0)

        total_claims = 0
        supported_claims = 0
        relevance_scores = []
        precision_scores = []
        recall_scores = []
        latencies = []

        import time

        for sample in samples:
            t0 = time.time()
            hits = self.retrieval_service.hybrid_search(
                db=db,
                user_id=user_id,
                query=sample.query,
                top_k=top_k
            )
            latencies.append((time.time() - t0) * 1000)

            # 1. Context Precision & Recall
            retrieved_chunk_ids = [h.chunk_id for h in hits]
            if sample.expected_chunk_ids:
                matches = set(retrieved_chunk_ids).intersection(set(sample.expected_chunk_ids))
                recall = len(matches) / len(sample.expected_chunk_ids)
                precision = len(matches) / len(retrieved_chunk_ids) if retrieved_chunk_ids else 0.0
                recall_scores.append(recall)
                precision_scores.append(precision)
            else:
                recall_scores.append(1.0)
                precision_scores.append(1.0)

            # 2. Grounded Answer Synthesis
            resp = self.generation_service.generate_grounded_answer(
                query=sample.query,
                hits=hits
            )

            # 3. Answer Relevance (keyword coverage)
            if sample.expected_answer_keywords:
                matched_kw = sum(
                    1 for kw in sample.expected_answer_keywords
                    if kw.lower() in resp.answer.lower()
                )
                relevance = matched_kw / len(sample.expected_answer_keywords)
                relevance_scores.append(relevance)
            else:
                relevance_scores.append(1.0)

            # 4. Faithfulness (verification of claims)
            for claim in resp.claims:
                total_claims += 1
                # Find cited hit
                cited_hit = next((h for h in hits if h.chunk_id == claim.chunk_id), None)
                if cited_hit:
                    is_found, _ = self.verification_service.verify_quote_in_chunk(
                        claim.quote,
                        cited_hit.content
                    )
                    if is_found:
                        supported_claims += 1

        avg_faithfulness = (
            supported_claims / total_claims if total_claims > 0 else 1.0
        )
        avg_relevance = sum(relevance_scores) / len(relevance_scores)
        avg_precision = sum(precision_scores) / len(precision_scores)
        avg_recall = sum(recall_scores) / len(recall_scores)
        avg_latency = sum(latencies) / len(latencies)

        return EvaluationMetrics(
            total_samples=len(samples),
            faithfulness_score=round(avg_faithfulness, 4),
            answer_relevance_score=round(avg_relevance, 4),
            context_precision=round(avg_precision, 4),
            context_recall=round(avg_recall, 4),
            average_latency_ms=round(avg_latency, 2)
        )

    def generate_markdown_report(self, metrics: EvaluationMetrics) -> str:
        """Generate a formatted markdown evaluation scorecard."""
        return (
            f"# RAG Benchmark Evaluation Scorecard\n\n"
            f"- **Evaluated Samples**: {metrics.total_samples}\n"
            f"- **Faithfulness (Grounding)**: {metrics.faithfulness_score * 100:.1f}% "
            f"({'PASS' if metrics.faithfulness_score >= 0.90 else 'NEEDS IMPROVEMENT'})\n"
            f"- **Answer Relevance**: {metrics.answer_relevance_score * 100:.1f}% "
            f"({'PASS' if metrics.answer_relevance_score >= 0.80 else 'NEEDS IMPROVEMENT'})\n"
            f"- **Context Recall**: {metrics.context_recall * 100:.1f}%\n"
            f"- **Context Precision**: {metrics.context_precision * 100:.1f}%\n"
            f"- **Average Retrieval Latency**: {metrics.average_latency_ms:.2f} ms\n"
        )
