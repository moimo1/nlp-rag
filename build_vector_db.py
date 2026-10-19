import os
import csv
from pathlib import Path
import chromadb

PROGRAM_EXPANSIONS = {
    "BSAC": "Bachelor of Science in Accountancy (BSAC)",
    "BSMA": "Bachelor of Science in Management Accounting (BSMA)",
    "BSENTREP-BA": "BS in Entrepreneurship specializing in Business Analytics (BSENTREP-BA)",
    "BSBA FINMAN-BA": "BSBA major in Financial Management specializing in Business Analytics (BSBA FINMAN-BA)",
    "BSHM": "Bachelor of Science in Hospitality Management (BSHM)",
    "BSBA MKTGMGMT-BA": "BSBA major in Marketing Management specializing in Business Analytics (BSBA MKTGMGMT-BA)",
    "BSTM": "Bachelor of Science in Tourism Management (BSTM)",
    "BSCS": "Bachelor of Science in Computer Science (BSCS)",
    "BSIT": "Bachelor of Science in Information Technology (BSIT)",
    "APMED": "Accelerated Pathway for Medicine (APMed)",
    "MD": "Doctor of Medicine (MD)",
    "BS BIO - MB": "Bachelor of Science in Biology major in Microbiology (BSBIO-MB)",
    "BS MLS": "Bachelor of Science in Medical Laboratory Science (BSMLS)",
    "BS PHARM": "Bachelor of Science in Pharmacy (BS Pharm)",
    "BS RADTECH": "Bachelor of Science in Radiologic Technology (BS RADTECH)",
    "BSN": "Bachelor of Science in Nursing (BSN)",
    "BA COMM": "Bachelor of Arts in Communication (BA COMM)",
    "BAPHILO": "Bachelor of Arts in Philosophy (BA PHILO)",
    "BAPOLSCI": "Bachelor of Arts in Political Science (BA POLSCI)",
    "BS PSYCH": "Bachelor of Science in Psychology (BS PSYCH)",
    "BA SWK": "Bachelor of Science in Social Work (BA SWK)",
    "BSED": "Bachelor of Secondary Education (BSED)",
    "BSNED": "Bachelor of Special Needs Education (BSNED)",
    "BPED": "Bachelor of Physical Education (BPED)",
    "BEED": "Bachelor of Elementary Education (BEED)",
}

def build_vector_database(text_dir, db_dir):
    client = chromadb.PersistentClient(path=db_dir)
    
    # Reset collection to avoid mixing stale/uncleaned documents
    try:
        client.delete_collection(name="brochures_collection")
    except Exception:
        pass
    
    collection = client.create_collection(name="brochures_collection")
    
    documents = []
    metadatas = []
    ids = []
    doc_id = 1
    
    # 1. Ingest cleaned brochure page text
    for filename in sorted(os.listdir(text_dir)):
        if not filename.endswith(".txt"):
            continue
            
        file_path = os.path.join(text_dir, filename)
        school_code = filename.replace("_extracted.txt", "").upper()
        source_name = filename.replace("_extracted.txt", ".pdf")
        
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        pages = [p.strip() for p in content.split("--- Page ") if p.strip()]
        
        for page in pages:
            parts = page.split("---", 1)
            page_num = parts[0].strip() if len(parts) == 2 else "Unknown"
            page_text = parts[1].strip() if len(parts) == 2 else page
            
            if len(page_text) < 20:
                continue
            
            documents.append(page_text)
            metadatas.append({
                "source": source_name,
                "school": school_code,
                "page": page_num,
                "type": "brochure_page"
            })
            ids.append(f"doc_{doc_id}")
            doc_id += 1

    # 2. Ingest structured course fees from converted_tables.csv if present
    tables_csv = os.path.join(text_dir, "converted_tables.csv")
    if os.path.exists(tables_csv):
        with open(tables_csv, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                course = row.get("COURSE", "").strip()
                downpayment = row.get("REQUIRED DOWNPAYMENT PARTIAL", "").strip()
                full_payment = row.get("FULL", "").strip()
                school = row.get("SCHOOL", "").strip()
                course_full = PROGRAM_EXPANSIONS.get(course, course)
                
                table_text = (
                    f"Saint Louis University ({school}) School Fees and Tuition Schedule: "
                    f"For program '{course_full}', the required downpayment (partial payment) is {downpayment}, "
                    f"and the full payment is {full_payment}."
                )
                documents.append(table_text)
                metadatas.append({
                    "source": "converted_tables.csv",
                    "school": school,
                    "course": course,
                    "page": "Fee Table",
                    "type": "fee_entry"
                })
                ids.append(f"doc_{doc_id}")
                doc_id += 1

    # Batch add to ChromaDB
    batch_size = 100
    for i in range(0, len(documents), batch_size):
        collection.add(
            documents=documents[i:i+batch_size],
            metadatas=metadatas[i:i+batch_size],
            ids=ids[i:i+batch_size]
        )
    print(f"Built database at {db_dir} with {collection.count()} documents from {text_dir}.")

if __name__ == "__main__":
    BASE_DIR = Path(__file__).resolve().parent
    text_dir = str(BASE_DIR / "CleanedText")
    db_dir = str(BASE_DIR / "VectorDB")
    
    if os.path.exists(text_dir):
        build_vector_database(text_dir, db_dir)
