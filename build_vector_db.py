import os
import chromadb

def build_vector_database(text_dir, db_dir):
    client = chromadb.PersistentClient(path=db_dir)
    collection = client.get_or_create_collection(name="brochures_collection")
    
    documents = []
    metadatas = []
    ids = []
    doc_id = 1
    
    for filename in os.listdir(text_dir):
        if not filename.endswith(".txt"):
            continue
            
        file_path = os.path.join(text_dir, filename)
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
            metadatas.append({"source": source_name, "page": page_num})
            ids.append(f"doc_{doc_id}")
            doc_id += 1

    batch_size = 100
    for i in range(0, len(documents), batch_size):
        collection.add(
            documents=documents[i:i+batch_size],
            metadatas=metadatas[i:i+batch_size],
            ids=ids[i:i+batch_size]
        )
    print(f"Built database at {db_dir} with {collection.count()} documents.")

if __name__ == "__main__":
    text_dir = r"C:\Users\ASUS TUF F15\Documents\NLP\ExtractedText"
    db_dir = r"C:\Users\ASUS TUF F15\Documents\NLP\VectorDB"
    
    if os.path.exists(text_dir):
        build_vector_database(text_dir, db_dir)
