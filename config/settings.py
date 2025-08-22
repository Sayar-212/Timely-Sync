import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class Settings:
    GEMINI_API_KEY: Optional[str]
    MODEL_NAME: str
    LOG_LEVEL: str
    MAX_RETRIES: int
    CSP_MAX_TIME_SECONDS: int
    OUTPUT_DIR: str
    PDF_TITLE: str
    DAYS: list
    SLOTS_PER_DAY: int
    CLASS_NAME: str

def load_settings() -> Settings:
    return Settings(
        GEMINI_API_KEY="AIzaSyC8VjRZv0it8uOMclq9GjfVVpgCh7299uE",
        MODEL_NAME=os.getenv("GEMINI_MODEL_NAME", "models/gemini-1.5-flash"),
        LOG_LEVEL=os.getenv("LOG_LEVEL", "INFO"),
        MAX_RETRIES=int(os.getenv("MAX_RETRIES", "2")),
        CSP_MAX_TIME_SECONDS=int(os.getenv("CSP_MAX_TIME_SECONDS", "5")),
        OUTPUT_DIR=os.getenv("OUTPUT_DIR", "outputs"),
        PDF_TITLE=os.getenv("PDF_TITLE", "Automated Timetable"),
        DAYS=os.getenv("DAYS", "Mon,Tue,Wed").split(","),
        SLOTS_PER_DAY=int(os.getenv("SLOTS_PER_DAY", "3")),
        CLASS_NAME=os.getenv("CLASS_NAME", "Class A"),
    )

settings = load_settings()
