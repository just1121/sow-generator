import os
from langchain_community.document_loaders import DirectoryLoader, PyPDFLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up the embeddings
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# Set the path to your document folder
doc_folder = "/Users/katecunningham/myproject_env/documents"

# Set the path to your existing vectorstore
vectorstore_path = "/Users/katecunningham/myproject_env/vectorstore.faiss"

# Function to recursively find PDF files
def find_pdf_files(directory):
    pdf_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.pdf'):
                pdf_files.append(os.path.join(root, file))
    return pdf_files

# Function to run a query on the vectorstore
def run_query(vectorstore, query, k=3):
    results = vectorstore.similarity_search(query, k=k)
    print(f"\nQuery: {query}")
    for i, result in enumerate(results, 1):
        print(f"\nResult {i}:")
        print(f"Content: {result.page_content[:200]}...")  # Print first 200 characters
        print(f"Source: {result.metadata.get('source', 'Unknown')}")

# Main function to update vectorstore and run queries
def main():
    # Check if the documents folder exists
    if not os.path.exists(doc_folder):
        print(f"Error: The document folder {doc_folder} does not exist.")
        return

    # Find PDF files recursively
    pdf_files = find_pdf_files(doc_folder)

    if not pdf_files:
        print(f"No PDF files found in {doc_folder} or its subdirectories. Please add some documents and try again.")
        return

    print(f"Found {len(pdf_files)} PDF files.")

    # Initialize the document loader for PDF files
    loader = DirectoryLoader(doc_folder, glob="**/*.pdf", loader_cls=PyPDFLoader, recursive=True)
    documents = loader.load()

    # Initialize the text splitter
    text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
    texts = text_splitter.split_documents(documents)

    # Load the existing vectorstore or create a new one
    if os.path.exists(vectorstore_path):
        print(f"Attempting to load vectorstore from: {vectorstore_path}")
        try:
            vectorstore = FAISS.load_local(vectorstore_path, embeddings, allow_dangerous_deserialization=True)
            print("Vectorstore loaded successfully")
            
            # Add new documents to the existing vectorstore
            print("Updating vectorstore with new documents...")
            print(f"Number of new documents to add: {len(texts)}")
            if texts:
                sample_embedding = embeddings.embed_query(texts[0].page_content)
                print(f"Dimensionality of new embeddings: {len(sample_embedding)}")
                print(f"Dimensionality of existing index: {vectorstore.index.d}")
            
            texts = [doc for doc in texts if doc.page_content.strip()]
            if texts:
                vectorstore.add_documents(texts)
            else:
                print("No new documents to add.")
        except Exception as e:
            print(f"Error loading existing vectorstore: {e}")
            print("Creating new vectorstore...")
            vectorstore = FAISS.from_documents(texts, embeddings)
    else:
        print("Creating new vectorstore...")
        vectorstore = FAISS.from_documents(texts, embeddings)

    # Save the updated vectorstore
    vectorstore.save_local(vectorstore_path)

    print(f"Number of documents processed: {len(texts)}")
    print(f"Total vectors in the store: {vectorstore.index.ntotal}")

    print("Vectorstore updated successfully!")

    # Run custom queries
    while True:
        query = input("\nEnter a query (or 'quit' to exit): ")
        if query.lower() == 'quit':
            break
        run_query(vectorstore, query)

if __name__ == "__main__":
    main()