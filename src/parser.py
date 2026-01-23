import os
import re
import docx2txt
from pdfminer.high_level import extract_text


def extract_text_from_pdf(file_path):
    """
    Extract text from PDF resume
    """
    try:
        text = extract_text(file_path)
        return text
    except Exception as e:
        print("Error reading PDF:", e)
        return ""


def extract_text_from_docx(file_path):
    """
    Extract text from DOCX resume
    """
    try:
        text = docx2txt.process(file_path)
        return text
    except Exception as e:
        print("Error reading DOCX:", e)
        return ""


def clean_text(text):
    """
    Clean unwanted characters from text
    """
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^a-zA-Z0-9., ]', '', text)
    return text.lower()


def parse_resume(file_path):
    """
    Main function to parse resume
    """
    if file_path.endswith(".pdf"):
        raw_text = extract_text_from_pdf(file_path)
    elif file_path.endswith(".docx"):
        raw_text = extract_text_from_docx(file_path)
    else:
        return {}

    cleaned_text = clean_text(raw_text)

    return {
        "file_name": os.path.basename(file_path),
        "raw_text": cleaned_text
    }
