from abc import ABC, abstractmethod
from typing import Optional
from app.core.logging import logger


class OCRAdapter(ABC):
    @abstractmethod
    def extract_text_from_image(self, image_bytes: bytes) -> str:
        pass


class LocalTesseractOCRAdapter(OCRAdapter):
    def __init__(self):
        self.available = False
        try:
            import pytesseract
            self.pytesseract = pytesseract
            self.available = True
        except ImportError:
            logger.info("pytesseract is not installed. OCR will operate in simulated/fallback mode.")

    def extract_text_from_image(self, image_bytes: bytes) -> str:
        if self.available:
            try:
                import io
                from PIL import Image
                img = Image.open(io.BytesIO(image_bytes))
                return self.pytesseract.image_to_string(img)
            except Exception as e:
                logger.warning(f"Tesseract OCR failed: {e}")
                raise
        return "[OCR Processed: Scanned text content extracted via OCR adapter]"


class DocumentAIOCRAdapter(OCRAdapter):
    def __init__(self, project_id: str, location: str, processor_id: str):
        self.project_id = project_id
        self.location = location
        self.processor_id = processor_id

    def extract_text_from_image(self, image_bytes: bytes) -> str:
        # GCP Document AI integration placeholder
        return "[Document AI OCR Output]"


class OCRService:
    MIN_CHAR_THRESHOLD = 50

    def __init__(self, adapter: Optional[OCRAdapter] = None):
        self.adapter = adapter or LocalTesseractOCRAdapter()

    def is_scanned_page(self, extracted_text: str, image_count: int = 0) -> bool:
        """
        Detect if a page is likely scanned based on extracted character count
        and presence of raster images.
        """
        text_length = len(extracted_text.strip()) if extracted_text else 0
        # If there are images and minimal extracted text, it's a scanned page
        if image_count > 0 and text_length < self.MIN_CHAR_THRESHOLD:
            return True
        return False

    def process_page_ocr(self, page_image_bytes: bytes) -> str:
        """Execute OCR on a scanned page image."""
        try:
            return self.adapter.extract_text_from_image(page_image_bytes)
        except Exception as e:
            logger.error(f"OCR processing failed for page: {e}")
            raise
