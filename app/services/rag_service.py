import os
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

class RAGService:
    def __init__(self):
        self.persist_directory = "./chroma_db"
        self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        self.vectorstore = None
        self.initialize_knowledge_base()

    def initialize_knowledge_base(self):
        if not os.path.exists(self.persist_directory):
            try:
                print("📚 Initializing Knowledge Base...")
                loader = TextLoader("data/trusted_medical_guidelines.md")
                documents = loader.load()
                
                text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
                docs = text_splitter.split_documents(documents)
                
                self.vectorstore = Chroma.from_documents(
                    documents=docs, 
                    embedding=self.embeddings,
                    persist_directory=self.persist_directory
                )
                print("✅ Knowledge Base initialized.")
            except Exception as e:
                print(f"❌ Failed to initialize Knowledge Base: {e}")
        else:
            self.vectorstore = Chroma(
                persist_directory=self.persist_directory,
                embedding_function=self.embeddings
            )
            print("✅ Loaded existing Knowledge Base.")

    def get_relevant_context(self, query: str, k=3):
        if not self.vectorstore:
            return ""
        try:
            docs = self.vectorstore.similarity_search(query, k=k)
            return "\n".join([doc.page_content for doc in docs])
        except Exception as e:
            print(f"RAG search error: {e}")
            return ""

rag_service = RAGService()
