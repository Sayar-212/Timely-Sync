import os
import json
from core.constraint_schema import Timetable
from utils.pdf_utils import timetable_to_pdf
from utils.logging_utils import get_logger
from config.settings import settings

logger = get_logger("FormatterAgent")

class FormatterAgent:
    def export(self, tt: Timetable, base_filename: str = "timetable") -> dict:
        os.makedirs(settings.OUTPUT_DIR, exist_ok=True)
        json_path = os.path.join(settings.OUTPUT_DIR, f"{base_filename}.json")
        pdf_path = os.path.join(settings.OUTPUT_DIR, f"{base_filename}.pdf")

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(tt.model_dump(), f, indent=2)

        timetable_to_pdf(tt, pdf_path, title=settings.PDF_TITLE)
        logger.info(f"Exported JSON -> {json_path}")
        logger.info(f"Exported PDF  -> {pdf_path}")
        return {"json": json_path, "pdf": pdf_path}
