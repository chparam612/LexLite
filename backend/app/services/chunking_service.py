from typing import List, Dict, Any, Optional
from app.utils.file_utils import compute_sha256
from app.services.structure_service import ParsedSection

# Simple token estimator: ~4 characters per token
CHAR_PER_TOKEN = 4
TARGET_MIN_TOKENS = 300
TARGET_MAX_TOKENS = 700
OVERLAP_TOKENS = 60


class LegalChunk:
    def __init__(
        self,
        chunk_index: int,
        heading_path: str,
        section_number: str,
        content: str,
        contextual_content: str,
        page_start: int,
        page_end: int,
        token_count: int,
        checksum: str,
        metadata: Optional[Dict[str, Any]] = None,
        section_id: Optional[str] = None
    ):
        self.chunk_index = chunk_index
        self.heading_path = heading_path
        self.section_number = section_number
        self.content = content
        self.contextual_content = contextual_content
        self.page_start = page_start
        self.page_end = page_end
        self.token_count = token_count
        self.checksum = checksum
        self.metadata = metadata or {}
        self.section_id = section_id


class ChunkingService:
    @staticmethod
    def estimate_tokens(text: str) -> int:
        """Estimate token count based on word and character counts."""
        if not text:
            return 0
        words = len(text.split())
        return max(words, len(text) // CHAR_PER_TOKEN)

    @staticmethod
    def create_contextual_text(
        document_title: str,
        jurisdiction: Optional[str],
        section_heading: str,
        clause_number: str,
        original_text: str
    ) -> str:
        """
        Generate contextual embedding text enriched with document metadata
        while keeping original text strictly segregated for citation verification.
        """
        jur_text = jurisdiction or "General / Unspecified"
        return (
            f"Document: {document_title}\n"
            f"Jurisdiction: {jur_text}\n"
            f"Section: {section_heading}\n"
            f"Clause: {clause_number}\n\n"
            f"Content:\n{original_text}"
        )

    @classmethod
    def chunk_legal_sections(
        cls,
        document_title: str,
        jurisdiction: Optional[str],
        sections: List[ParsedSection]
    ) -> List[LegalChunk]:
        """
        Produce legal-aware hierarchical chunks from parsed legal sections.
        Preserves complete clauses, attaches modifying exceptions to clauses,
        and constructs contextual representations for dense retrieval.
        """
        chunks: List[LegalChunk] = []
        chunk_counter = 0

        target_max_chars = TARGET_MAX_TOKENS * CHAR_PER_TOKEN
        overlap_chars = OVERLAP_TOKENS * CHAR_PER_TOKEN

        for sec in sections:
            sec_text = sec.full_text.strip()
            if not sec_text:
                continue

            heading_path = f"{document_title} > {sec.heading}"
            if sec.section_number:
                heading_path = f"{document_title} > Section {sec.section_number}: {sec.heading}"

            # If section fits within target max size, keep as a single unified clause chunk
            sec_len = len(sec_text)
            if sec_len <= target_max_chars:
                token_cnt = cls.estimate_tokens(sec_text)
                checksum = compute_sha256(sec_text.encode("utf-8"))
                contextual = cls.create_contextual_text(
                    document_title=document_title,
                    jurisdiction=jurisdiction,
                    section_heading=sec.heading,
                    clause_number=sec.section_number,
                    original_text=sec_text
                )
                chunks.append(
                    LegalChunk(
                        chunk_index=chunk_counter,
                        heading_path=heading_path,
                        section_number=sec.section_number,
                        content=sec_text,
                        contextual_content=contextual,
                        page_start=sec.page_start,
                        page_end=sec.page_end,
                        token_count=token_cnt,
                        checksum=checksum,
                        metadata={
                            "section_type": sec.section_type,
                            "heading": sec.heading
                        }
                    )
                )
                chunk_counter += 1
            else:
                # Long clause/section: split by paragraphs/sentences without separating exceptions
                paragraphs = [p.strip() for p in sec_text.split("\n\n") if p.strip()]
                current_chunk_text = ""
                chunk_page_start = sec.page_start
                chunk_page_end = sec.page_end

                for para in paragraphs:
                    if len(current_chunk_text) + len(para) <= target_max_chars:
                        if current_chunk_text:
                            current_chunk_text += "\n\n" + para
                        else:
                            current_chunk_text = para
                    else:
                        if current_chunk_text:
                            token_cnt = cls.estimate_tokens(current_chunk_text)
                            checksum = compute_sha256(current_chunk_text.encode("utf-8"))
                            contextual = cls.create_contextual_text(
                                document_title=document_title,
                                jurisdiction=jurisdiction,
                                section_heading=sec.heading,
                                clause_number=sec.section_number,
                                original_text=current_chunk_text
                            )
                            chunks.append(
                                LegalChunk(
                                    chunk_index=chunk_counter,
                                    heading_path=heading_path,
                                    section_number=sec.section_number,
                                    content=current_chunk_text,
                                    contextual_content=contextual,
                                    page_start=chunk_page_start,
                                    page_end=chunk_page_end,
                                    token_count=token_cnt,
                                    checksum=checksum,
                                    metadata={"section_type": sec.section_type, "heading": sec.heading}
                                )
                            )
                            chunk_counter += 1

                            # Overlap
                            current_chunk_text = current_chunk_text[-overlap_chars:] + "\n\n" + para
                        else:
                            current_chunk_text = para

                if current_chunk_text and current_chunk_text.strip():
                    token_cnt = cls.estimate_tokens(current_chunk_text)
                    checksum = compute_sha256(current_chunk_text.encode("utf-8"))
                    contextual = cls.create_contextual_text(
                        document_title=document_title,
                        jurisdiction=jurisdiction,
                        section_heading=sec.heading,
                        clause_number=sec.section_number,
                        original_text=current_chunk_text
                    )
                    chunks.append(
                        LegalChunk(
                            chunk_index=chunk_counter,
                            heading_path=heading_path,
                            section_number=sec.section_number,
                            content=current_chunk_text,
                            contextual_content=contextual,
                            page_start=chunk_page_start,
                            page_end=chunk_page_end,
                            token_count=token_cnt,
                            checksum=checksum,
                            metadata={"section_type": sec.section_type, "heading": sec.heading}
                        )
                    )
                    chunk_counter += 1

        return chunks
