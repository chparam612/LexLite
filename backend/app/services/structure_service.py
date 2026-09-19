import re
from typing import List, Dict, Any, Optional

# Regular expressions for legal structural hierarchy
ARTICLE_REGEX = re.compile(
    r"^(?:ARTICLE|Article)\s+([0-9IVXLCDM]+)[\s:.\-]*(.*)$",
    re.IGNORECASE
)

CHAPTER_REGEX = re.compile(
    r"^(?:CHAPTER|Chapter)\s+([0-9IVXLCDM]+)[\s:.\-]*(.*)$",
    re.IGNORECASE
)

SECTION_REGEX = re.compile(
    r"^(?:(?:SECTION|Section|§)\s+)?([0-9]{1,3}(?:\.[0-9]{1,3})+|[0-9]{1,3})[\s:.\-]+([^\n]+)$",
    re.IGNORECASE
)

SCHEDULE_REGEX = re.compile(
    r"^(?:SCHEDULE|ANNEXURE|EXHIBIT|APPENDIX)\s+([0-9A-Z]+)[\s:.\-]*(.*)$",
    re.IGNORECASE
)

DEFINITION_REGEX = re.compile(
    r'["“\']([^"”\']+)["”\']\s+(?:means|shall mean|has the meaning|refers to)\s+([^.]+\.)',
    re.IGNORECASE
)


class ParsedSection:
    def __init__(
        self,
        section_number: str,
        heading: str,
        section_type: str,
        page_start: int,
        page_end: int,
        full_text: str,
        parent_index: Optional[int] = None
    ):
        self.section_number = section_number
        self.heading = heading
        self.section_type = section_type
        self.page_start = page_start
        self.page_end = page_end
        self.full_text = full_text
        self.parent_index = parent_index
        self.subsections: List['ParsedSection'] = []


class StructureService:
    @staticmethod
    def detect_document_title(first_page_text: str, fallback_title: str = "Legal Document") -> str:
        """Extract title from the beginning of the first page or fallback."""
        lines = [line.strip() for line in first_page_text.split("\n") if line.strip()]
        for line in lines[:5]:
            if len(line) > 3 and not line.lower().startswith("page ") and len(line) < 120:
                if line.isupper() or "agreement" in line.lower() or "contract" in line.lower() or "policy" in line.lower():
                    return line
        return fallback_title

    @staticmethod
    def parse_legal_structure(pages: List[Dict[str, Any]]) -> List[ParsedSection]:
        """
        Parse hierarchical legal sections across document pages.
        Detects Articles, Chapters, Sections, Definitions, Schedules, and nested clauses.
        Processes line-by-line to preserve structure across varying line-break conventions.
        """
        parsed_sections: List[ParsedSection] = []
        current_article: Optional[ParsedSection] = None
        current_section: Optional[ParsedSection] = None

        for p in pages:
            page_num = p["page_number"]
            raw_text = p["extracted_text"]
            lines = [line.strip() for line in raw_text.split("\n") if line.strip()]

            for line in lines:
                # 1. Schedules / Annexures
                sched_match = SCHEDULE_REGEX.match(line)
                if sched_match:
                    sched_num = sched_match.group(1).strip()
                    sched_heading = sched_match.group(2).strip() or f"Schedule {sched_num}"
                    sec = ParsedSection(
                        section_number=sched_num,
                        heading=sched_heading,
                        section_type="schedule",
                        page_start=page_num,
                        page_end=page_num,
                        full_text=line
                    )
                    parsed_sections.append(sec)
                    current_section = sec
                    current_article = None
                    continue

                # 2. Articles
                art_match = ARTICLE_REGEX.match(line)
                if art_match:
                    art_num = art_match.group(1).strip()
                    art_heading = art_match.group(2).strip() or f"Article {art_num}"
                    sec = ParsedSection(
                        section_number=art_num,
                        heading=art_heading,
                        section_type="article",
                        page_start=page_num,
                        page_end=page_num,
                        full_text=line
                    )
                    parsed_sections.append(sec)
                    current_article = sec
                    current_section = sec
                    continue

                # 3. Numbered Sections
                sec_match = SECTION_REGEX.match(line)
                if sec_match:
                    sec_num = sec_match.group(1).strip()
                    sec_heading = sec_match.group(2).strip()
                    parent_idx = parsed_sections.index(current_article) if current_article in parsed_sections else None
                    sec = ParsedSection(
                        section_number=sec_num,
                        heading=sec_heading,
                        section_type="section",
                        page_start=page_num,
                        page_end=page_num,
                        full_text=line,
                        parent_index=parent_idx
                    )
                    parsed_sections.append(sec)
                    if current_article:
                        current_article.subsections.append(sec)
                    current_section = sec
                    continue

                # 4. Definitions
                def_match = DEFINITION_REGEX.search(line)
                if def_match and len(line) < 400:
                    def_term = def_match.group(1).strip()
                    sec = ParsedSection(
                        section_number="",
                        heading=f'Definition: "{def_term}"',
                        section_type="definition",
                        page_start=page_num,
                        page_end=page_num,
                        full_text=line
                    )
                    parsed_sections.append(sec)
                    current_section = sec
                    continue

                # Normal body line: append to current section
                if current_section:
                    current_section.full_text += "\n" + line
                    current_section.page_end = max(current_section.page_end, page_num)
                else:
                    # Initial preamble / title section
                    sec = ParsedSection(
                        section_number="0",
                        heading="Preamble and Recitals",
                        section_type="preamble",
                        page_start=page_num,
                        page_end=page_num,
                        full_text=line
                    )
                    parsed_sections.append(sec)
                    current_section = sec

        return parsed_sections
