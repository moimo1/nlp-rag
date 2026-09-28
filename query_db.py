import chromadb
import sys

def query_database(query_text, db_dir):
    client = chromadb.PersistentClient(path=db_dir)
    collection = client.get_collection(name="brochures_collection")
    
    results = collection.query(query_texts=[query_text], n_results=3)
    
    if not results['documents'] or not results['documents'][0]:
        print("No results found.")
        return
        
    for i, (doc, meta, dist) in enumerate(zip(results['documents'][0], results['metadatas'][0], results['distances'][0])):
        source = meta.get('source', 'Unknown')
        page = meta.get('page', 'Unknown')
        
        print(f"\nResult {i+1} [Source: {source}, Page: {page}, Distance: {dist:.4f}]")
        print("-" * 40)
        snippet = doc[:300].replace("\n", " ")
        print(snippet + "..." if len(doc) > 300 else snippet)
        print("-" * 40)

if __name__ == "__main__":
    db_dir = r"C:\Users\ASUS TUF F15\Documents\NLP\VectorDB"
    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "What is the School History of SAMCIS?"
    query_database(query, db_dir)
