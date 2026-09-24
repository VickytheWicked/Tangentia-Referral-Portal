import io
import os
import re
import shutil
import zipfile
import tempfile
import subprocess
import logging
import xml.etree.ElementTree as ET
from typing import Optional

logger = logging.getLogger("cv_intelligence")


class TextExtractionError(Exception):
    """Raised when text cannot be extracted from a CV file."""
    pass


def ocr_extract_pdf(file_bytes: bytes) -> str:
    """
    Perform optical character recognition (OCR) on PDF bytes using pdftoppm and tesseract.
    Converts pages to high-resolution PNGs and runs tesseract engine.
    """
    pdftoppm_bin = shutil.which("pdftoppm")
    tesseract_bin = shutil.which("tesseract")

    if not pdftoppm_bin or not tesseract_bin:
        logger.warning("pdftoppm or tesseract binary not found in system PATH. Cannot perform OCR fallback.")
        return ""

    pages_text = []
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            pdf_path = os.path.join(tmpdir, "input.pdf")
            with open(pdf_path, "wb") as f:
                f.write(file_bytes)

            # Rasterize PDF pages to PNG at 150 DPI
            prefix = os.path.join(tmpdir, "page")
            render_cmd = [pdftoppm_bin, "-png", "-r", "150", pdf_path, prefix]
            subprocess.run(render_cmd, capture_output=True, check=True, timeout=30)

            png_files = sorted([os.path.join(tmpdir, f) for f in os.listdir(tmpdir) if f.endswith(".png")])
            for png in png_files:
                ocr_cmd = [tesseract_bin, png, "stdout", "-l", "eng", "--oem", "1"]
                proc = subprocess.run(ocr_cmd, capture_output=True, text=True, check=True, timeout=20)
                if proc.stdout.strip():
                    pages_text.append(proc.stdout.strip())

        return "\n\n".join(pages_text).strip()
    except Exception as e:
        logger.warning(f"OCR extraction on PDF failed: {e}")
        return ""


def ocr_extract_image(file_bytes: bytes, ext: str = ".png") -> str:
    """
    Perform OCR directly on image files (.png, .jpg, .jpeg, .webp, .tiff).
    """
    tesseract_bin = shutil.which("tesseract")
    if not tesseract_bin:
        logger.warning("tesseract binary not found. Cannot perform OCR on image.")
        return ""

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            img_path = os.path.join(tmpdir, f"input{ext}")
            with open(img_path, "wb") as f:
                f.write(file_bytes)

            ocr_cmd = [tesseract_bin, img_path, "stdout", "-l", "eng", "--oem", "1"]
            proc = subprocess.run(ocr_cmd, capture_output=True, text=True, check=True, timeout=20)
            return proc.stdout.strip()
    except Exception as e:
        logger.warning(f"Image OCR failed: {e}")
        return ""


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """
    Extract readable text from PDF bytes using pypdf with automated OCR fallback
    for scanned pages, image-only resumes, or multi-column layout issues.
    """
    pypdf_text = ""
    try:
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(file_bytes))
        pages_text = []
        for page in reader.pages:
            t = page.extract_text()
            if t:
                pages_text.append(t)
        pypdf_text = "\n\n".join(pages_text).strip()
    except Exception as e:
        logger.debug(f"pypdf digital extraction encountered error: {e}")

    word_count = len(pypdf_text.split()) if pypdf_text else 0

    # If digital extraction succeeded with sufficient density, return it
    if word_count >= 60:
        return pypdf_text

    # Fallback to OCR if pypdf was empty or yielded low text count
    logger.info(f"Digital PDF extraction yielded {word_count} words. Initiating OCR fallback pipeline...")
    ocr_text = ocr_extract_pdf(file_bytes)
    if ocr_text and len(ocr_text.split()) > word_count:
        return ocr_text

    if pypdf_text:
        return pypdf_text

    raise TextExtractionError("PDF file contains no extractable text (even after OCR fallback).")


def extract_text_from_docx(file_bytes: bytes) -> str:
    """
    Extract readable text from DOCX bytes using python-docx with deep extraction
    (paragraphs, tables, headers, footers, and text box content) and stdlib XML fallback.
    """
    # 1. Try python-docx
    try:
        import docx
        doc = docx.Document(io.BytesIO(file_bytes))
        chunks = []

        # Headers & Footers
        for section in doc.sections:
            for p in section.header.paragraphs:
                if p.text.strip():
                    chunks.append(p.text.strip())
            for p in section.footer.paragraphs:
                if p.text.strip():
                    chunks.append(p.text.strip())

        # Main paragraphs
        for p in doc.paragraphs:
            if p.text.strip():
                chunks.append(p.text.strip())

        # Tables
        for table in doc.tables:
            for row in table.rows:
                row_text = " | ".join(cell.text.strip() for cell in row.cells if cell.text.strip())
                if row_text:
                    chunks.append(row_text)

        # Shapes and Textboxes (w:txbxContent)
        try:
            ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
            text_boxes = doc.element.xpath("//w:txbxContent//w:t")
            tb_texts = [t.text.strip() for t in text_boxes if t.text and t.text.strip()]
            if tb_texts:
                chunks.append(" ".join(tb_texts))
        except Exception:
            pass

        text = "\n".join(chunks).strip()
        if text:
            return text
    except Exception as e:
        logger.debug(f"python-docx extraction failed, trying zipfile fallback: {e}")

    # 2. Fallback: stdlib zipfile XML extraction
    try:
        with zipfile.ZipFile(io.BytesIO(file_bytes)) as z:
            xml_files = [f for f in z.namelist() if f.startswith("word/") and f.endswith(".xml")]
            if "word/document.xml" not in z.namelist():
                raise TextExtractionError("Invalid DOCX format: word/document.xml not found.")

            all_text_nodes = []
            namespaces = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
            for xml_file in xml_files:
                try:
                    xml_content = z.read(xml_file)
                    tree = ET.fromstring(xml_content)
                    nodes = tree.findall(".//w:t", namespaces)
                    if not nodes:
                        nodes = tree.findall(".//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t")
                    all_text_nodes.extend([t.text for t in nodes if t.text])
                except Exception:
                    continue

            extracted = " ".join(all_text_nodes)
            if extracted.strip():
                return extracted.strip()
    except Exception as e:
        logger.warning(f"DOCX XML extraction failed: {e}")
        raise TextExtractionError(f"Could not extract text from DOCX: {str(e)}")

    raise TextExtractionError("DOCX file contains no extractable text.")


def clean_extracted_text(text: str) -> str:
    """
    Normalize whitespace, strip control characters, replace private-use Unicode icons,
    and clean extracted text.
    """
    if not text:
        return ""
    # Strip null bytes and non-printable control characters (except newline, tab)
    cleaned = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", text)
    # Strip Private Use Area (PUA) Unicode characters often used for icons in PDFs (e.g. \uf698, \uf095)
    cleaned = re.sub(r"[\ue000-\uf8ff]", " ", cleaned)
    # Normalize excessive spaces and tabs
    cleaned = re.sub(r"[ \t]+", " ", cleaned)
    # Normalize excessive newlines
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def extract_cv_text(file_bytes: bytes, filename: str, content_type: Optional[str] = None) -> str:
    """
    Extract clean text from PDF, DOCX, or image binary files.
    Dispatches based on file extension, mime type, or magic bytes.
    """
    if not file_bytes:
        raise TextExtractionError("CV file is empty (0 bytes).")

    lower_name = (filename or "").lower()
    ct = (content_type or "").lower()

    if lower_name.endswith(".pdf") or "pdf" in ct:
        raw_text = extract_text_from_pdf(file_bytes)
    elif lower_name.endswith(".docx") or "officedocument" in ct:
        raw_text = extract_text_from_docx(file_bytes)
    elif lower_name.endswith(".doc"):
        raise TextExtractionError("Legacy .doc format is not supported for AI parsing. Please provide a .docx or .pdf file.")
    else:
        # Magic bytes inspection
        if file_bytes.startswith(b"%PDF"):
            raw_text = extract_text_from_pdf(file_bytes)
        elif file_bytes.startswith(b"PK"):
            raw_text = extract_text_from_docx(file_bytes)
        else:
            raise TextExtractionError(f"Unsupported file format for CV extraction: '{filename}'. Supported: PDF, DOCX.")

    return clean_extracted_text(raw_text)
