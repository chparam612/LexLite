import re
from typing import List, Tuple
from dataclasses import dataclass
from sqlalchemy.orm import Session

from app.models.chunk import DocumentChunk
from app.models.citation import Citation, AnswerClaim, ClaimEvidence
from app.services.generation_service import GroundedResponse
from app.core.logging import logger


@dataclass
class ClaimVerificationResult:
    claim_id: str
    quote: str
    chunk_id: str
    quote_found_in_chunk: bool
    entailment_score: float
    support_status: str  # "supported", "unverified", "refuted"


def normalize_text(text: str) -> str:
    """Normalize text by collapsing whitespace and standardizing quotes/punctuation."""
    if not text:
        return ""
    # Replace curly quotes and apostrophes
    t = text.replace("“", '"').replace("”", '"').replace("‘", "'").replace("’", "'")
    # Collapse multiple whitespace/newlines to single space
    t = re.sub(r"\s+", " ", t)
    return t.strip().lower()


class VerificationService:
    @classmethod
    def verify_exact_quote(cls, quote: str, chunk_content: str) -> bool:
        """Helper checking if quote is verified in chunk content."""
        found, _ = cls.verify_quote_in_chunk(quote, chunk_content)
        return found

    @staticmethod
    def verify_quote_in_chunk(quote: str, chunk_content: str) -> Tuple[bool, float]:
        """
        Verify if the cited quote exists in the chunk content.
        Returns (is_found, match_ratio).
        """
        if not quote or not chunk_content:
            return False, 0.0

        norm_quote = normalize_text(quote)
        norm_chunk = normalize_text(chunk_content)

        # 1. Exact or punctuation-stripped substring check
        clean_quote = re.sub(r"[^\w\s]", "", norm_quote)
        clean_chunk = re.sub(r"[^\w\s]", "", norm_chunk)

        if norm_quote in norm_chunk or clean_quote in clean_chunk:
            return True, 1.0

        # 2. Token containment check (tolerant of slight excerpt trimming)
        quote_words = clean_quote.split()
        if not quote_words:
            return False, 0.0

        chunk_words = set(clean_chunk.split())
        matched_words = sum(1 for w in quote_words if w in chunk_words)
        ratio = matched_words / len(quote_words)

        if ratio >= 0.85 and len(quote_words) >= 4:
            return True, round(ratio, 2)

        return False, round(ratio, 2)

    @staticmethod
    def verify_claim_entailment(claim_text: str, quote: str) -> float:
        """
        Verify whether the quote actually supports the claim text.
        Computes root-level and lexical overlap between claim assertion and evidentiary quote.
        """
        if not claim_text or not quote:
            return 0.0

        norm_claim = normalize_text(claim_text)
        norm_quote = normalize_text(quote)

        # Extract words >= 3 chars without punctuation
        claim_words = re.findall(r"\b\w{3,}\b", norm_claim)
        quote_words = set(re.findall(r"\b\w{3,}\b", norm_quote))

        if not claim_words:
            return 1.0

        # Extract roots (first 4 chars) to handle inflection (e.g. govern / governed / governing)
        quote_roots = set(w[:4] for w in quote_words)
        matched = 0
        for w in claim_words:
            if w in quote_words or w[:4] in quote_roots:
                matched += 1

        score = matched / len(claim_words)
        return min(1.0, round(score, 2))

    def verify_claims_and_citations(
        self,
        db: Session,
        grounded_resp: GroundedResponse,
        created_claims: List[AnswerClaim],
        created_evidence: List[ClaimEvidence],
        created_citations: List[Citation]
    ) -> float:
        """
        Verify all claims and citations against referenced document chunks.
        Updates support_status and entailment_score in the database.
        Returns overall grounding score (0.0 to 1.0).
        """
        if not grounded_resp.claims:
            return 1.0  # Refusal / insufficient evidence answers have no hallucinated claims

        supported_count = 0
        total_claims = len(grounded_resp.claims)

        for idx, claim_data in enumerate(grounded_resp.claims):
            chunk = db.query(DocumentChunk).filter_by(id=claim_data.chunk_id).first()
            if not chunk:
                logger.warning(f"Verification failure: Chunk {claim_data.chunk_id} not found.")
                if idx < len(created_claims):
                    created_claims[idx].support_status = "unverified"
                if idx < len(created_evidence):
                    created_evidence[idx].entailment_score = 0.0
                continue

            # 1. Verify quote exists in chunk
            quote_found, quote_match = self.verify_quote_in_chunk(claim_data.quote, chunk.content)

            # 2. Verify claim entailment
            entailment = self.verify_claim_entailment(claim_data.claim_text, claim_data.quote)

            # 3. Determine status
            if quote_found and entailment >= 0.4:
                status = "supported"
                supported_count += 1
                final_score = max(quote_match, entailment)
            else:
                status = "unverified"
                final_score = 0.0
                logger.warning(
                    f"Claim unverified: quote_found={quote_found}, entailment={entailment}. "
                    f"Quote: '{claim_data.quote[:50]}...'"
                )

            # Update DB records
            if idx < len(created_claims):
                created_claims[idx].support_status = status
            if idx < len(created_evidence):
                created_evidence[idx].entailment_score = final_score

        db.commit()

        grounding_score = supported_count / total_claims if total_claims > 0 else 1.0
        logger.info(
            f"Citation verification complete. Grounding Score: {grounding_score:.2f} ({supported_count}/{total_claims})"
        )
        return grounding_score
