import os
import pytesseract
from pdf2image import convert_from_path
from pathlib import Path

TESSERACT_CMD = "C:/Program Files/Tesseract-OCR/tesseract.exe"
POPPLER_PATH = "C:/Users/ASUS TUF F15/Documents/Release-26.09.0-0/poppler-26.09.0/Library/bin"

if TESSERACT_CMD:
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD

def extract_text_from_pdf(pdf_path, output_dir):
    print(f"Processing: {pdf_path}")
    try:
        images = convert_from_path(pdf_path, poppler_path=POPPLER_PATH) if POPPLER_PATH else convert_from_path(pdf_path)
    except Exception as e:
        print(f"Error converting {pdf_path}: {e}")
        return ""

    full_text = []
    for page_num, img in enumerate(images, start=1):
        print(f"  OCR on page {page_num}...")
        text = pytesseract.image_to_string(img, config=r'--psm 6')
        full_text.append(f"--- Page {page_num} ---\n{text}\n")
    
    final_text = "\n".join(full_text)
    
    os.makedirs(output_dir, exist_ok=True)
    out_file = os.path.join(output_dir, f"{Path(pdf_path).stem}_extracted.txt")
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(final_text)
        
    return final_text

if __name__ == "__main__":
    pdf_dir = r"C:\Users\ASUS TUF F15\Documents\NLP\NLP"
    output_dir = r"C:\Users\ASUS TUF F15\Documents\NLP\ExtractedText"
    
    if os.path.exists(pdf_dir):
        for filename in os.listdir(pdf_dir):
            if filename.lower().endswith(".pdf"):
                extract_text_from_pdf(os.path.join(pdf_dir, filename), output_dir)
