from typing import List, Dict, Any
import fitz  # PyMuPDF
from app.services.ocr_service import OCRService
from app.core.exceptions import LegalAIException
from app.core.logging import logger


class ExtractionService:
    def __init__(self, ocr_service: OCRService = None):
        self.ocr_service = ocr_service or OCRService()

    def extract_pages(self, pdf_bytes: bytes) -> List[Dict[str, Any]]:
        """
        Extract text from a PDF document page by page.
        Identifies scanned pages and runs OCR where required.
        Preserves Unicode, multilingual text, and page metadata.
        """
        try:
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        except Exception as e:
            raise LegalAIException(
                message=f"Failed to open PDF document for extraction: {str(e)}",
                code="PDF_EXTRACTION_ERROR",
                status_code=400
            )

        extracted_pages: List[Dict[str, Any]] = []

        try:
            for page_index in range(len(doc)):
                page_num = page_index + 1
                page = doc[page_index]

                # Extract unicode text
                text = page.get_text("text") or ""

                # Extract images list
                image_list = page.get_images(full=True)
                image_count = len(image_list)

                ocr_used = False
                # Check if page is scanned or below threshold
                if self.ocr_service.is_scanned_page(text, image_count):
                    logger.info(f"Page {page_num} flagged as scanned/image-heavy. Triggering OCR adapter...")
                    try:
                        # Render page to pixmap for OCR
                        pix = page.get_pixmap(dpi=150)
                        image_bytes = pix.tobytes("png")
                        ocr_text = self.ocr_service.process_page_ocr(image_bytes)
                        if ocr_text and ocr_text.strip():
                            text = ocr_text
                            ocr_used = True
                    except Exception as ocr_err:
                        logger.warning(f"OCR failed on page {page_num}: {ocr_err}")
                        # Keep original text even if empty or partial

                # Page dimensions & metadata
                rect = page.rect
                page_metadata = {
                    "width": rect.width,
                    "height": rect.height,
                    "image_count": image_count,
                    "char_count": len(text),
                    "rotation": page.rotation
                }

                extracted_pages.append({
                    "page_number": page_num,
                    "extracted_text": text,
                    "ocr_used": ocr_used,
                    "metadata": page_metadata
                })

        finally:
            doc.close()

        return extracted_pages
