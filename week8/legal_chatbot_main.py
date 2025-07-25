import os
import pickle
import streamlit as st 
from dotenv import load_dotenv
from llama_index.core import VectorStoreIndex, Settings, StorageContext, load_index_from_storage
from llama_index.core.storage.docstore import SimpleDocumentStore
from llama_index.core.storage.index_store import SimpleIndexStore
from llama_index.core.vector_stores import SimpleVectorStore
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.response_synthesizers import get_response_synthesizer, ResponseMode
from llama_index.core.prompts import PromptTemplate
from llama_index.embeddings.mistralai import MistralAIEmbedding
from llama_index.llms.mistralai import MistralAI
from document_processor import DocumentProcessor
from web_scraper import WebScraper
import nest_asyncio

# Apply nest_asyncio for Streamlit compatibility
nest_asyncio.apply()

# Load environment variables
load_dotenv()


class LegalChatbot:
    """Indian Legal System RAG Chatbot using LlamaIndex and Mistral - Optimized Version"""
    
    def __init__(self):
        self.mistral_api_key = st.secrets.get("MISTRAL_API_KEY") or os.getenv("MISTRAL_API_KEY")
        if not self.mistral_api_key:
            raise ValueError("MISTRAL_API_KEY not found in environment variables")
        
        # Storage paths for caching
        self.storage_dir = "./storage"
        self.index_cache_file = "./index_cache.pkl"
        
        # Initialize Mistral LLM and Embeddings with compatible versions
        try:
            self.llm = MistralAI(
                api_key=self.mistral_api_key,
                model="open-mistral-7b",
                max_tokens=1024,
                temperature=0.1
            )
            
            self.embed_model = MistralAIEmbedding(
                api_key=self.mistral_api_key,
                model_name="mistral-embed"
            )
            
        except Exception as e:
            print(f"Error with models, trying basic initialization: {e}")
            try:
                self.llm = MistralAI(api_key=self.mistral_api_key)
                self.embed_model = MistralAIEmbedding(api_key=self.mistral_api_key)
                print("✅ Using basic initialization")
            except Exception as final_error:
                raise ValueError(f"All initialization attempts failed. Please check your MISTRAL_API_KEY. Error: {final_error}")
        
        # Configure global settings
        Settings.llm = self.llm
        Settings.embed_model = self.embed_model
        Settings.chunk_size = 512  # Reduced for faster processing
        Settings.chunk_overlap = 50  # Reduced overlap
        
        self.index = None
        self.query_engine = None
        self.document_processor = DocumentProcessor()
        self.web_scraper = WebScraper()
        
        # Custom prompt template for legal queries with web context (Fixed formatting)
        self.legal_prompt_template = PromptTemplate(
            "You are an expert Indian legal assistant. Use both the provided context from Indian legal documents and recent web information to answer questions accurately and comprehensively.\n\n"
            "Context from Legal Documents:\n"
            "---------------------\n"
            "{context_str}\n"
            "---------------------\n\n"
            "Recent Web Information:\n"
            "---------------------\n"
            "{web_context}\n"
            "---------------------\n\n"
            "Instructions:\n"
            "1. Provide accurate legal information based on Indian law and recent developments\n"
            "2. Cite specific sections, articles, or acts when possible\n"
            "3. Include recent case law and judgments when relevant\n"
            "4. If information conflicts, prioritize statutory law but mention recent judicial interpretations\n"
            "5. Always remind users to consult with a qualified lawyer for legal advice\n"
            "6. Be precise and professional in your responses\n"
            "7. Clearly distinguish between established law and recent developments\n"
            "8. Format your response in plain text without markdown formatting\n\n"
            "Query: {query_str}\n"
            "Answer: "
        )
    
    def _documents_changed(self) -> bool:
        """Check if documents have been modified since last index build"""
        if not os.path.exists(self.index_cache_file):
            return True
        
        cache_time = os.path.getmtime(self.index_cache_file)
        
        # Check if any document is newer than cache
        documents_dir = "documents"
        if not os.path.exists(documents_dir):
            return True
        
        for filename in os.listdir(documents_dir):
            file_path = os.path.join(documents_dir, filename)
            if os.path.isfile(file_path) and os.path.getmtime(file_path) > cache_time:
                return True
        
        return False
    
    def build_index(self, force_rebuild: bool = False):
        """Build the vector index from processed documents with caching"""
        
        # Try to load existing index if documents haven't changed
        if not force_rebuild and not self._documents_changed():
            if self.load_cached_index():
                print("✅ Loaded cached index - startup accelerated!")
                return self.index
        
        print("📄 Processing documents...")
        documents = self.document_processor.process_all_documents()
        
        if not documents:
            raise ValueError("No documents found to process. Please add legal documents to the 'documents' folder.")
        
        print(f"🔍 Building vector index for {len(documents)} documents...")
        
        # Create storage context
        storage_context = StorageContext.from_defaults(
            docstore=SimpleDocumentStore(),
            vector_store=SimpleVectorStore(),
            index_store=SimpleIndexStore(),
        )
        
        # Build index with progress bar
        self.index = VectorStoreIndex.from_documents(
            documents,
            storage_context=storage_context,
            show_progress=True
        )
        
        # Cache the index
        self.save_index_cache()
        print("✅ Index built and cached successfully!")
        return self.index
    
    def save_index_cache(self):
        """Save index to cache for faster loading"""
        try:
            # Save index to storage directory
            if not os.path.exists(self.storage_dir):
                os.makedirs(self.storage_dir)
            
            self.index.storage_context.persist(self.storage_dir)
            
            # Create cache timestamp file
            with open(self.index_cache_file, 'w') as f:
                f.write("cached")
            
            print("💾 Index cached successfully")
        except Exception as e:
            print(f"⚠️ Warning: Could not cache index: {e}")
    
    def load_cached_index(self) -> bool:
        """Load index from cache"""
        try:
            if os.path.exists(self.storage_dir):
                storage_context = StorageContext.from_defaults(persist_dir=self.storage_dir)
                self.index = load_index_from_storage(storage_context)
                return True
        except Exception as e:
            print(f"⚠️ Could not load cached index: {e}")
        
        return False
    
    def setup_query_engine(self, similarity_top_k: int = 3):  # Reduced from 5 to 3
        """Setup the query engine with custom prompt"""
        if not self.index:
            raise ValueError("Index not built. Call build_index() first.")
        
        # Configure retriever
        retriever = VectorIndexRetriever(
            index=self.index,
            similarity_top_k=similarity_top_k,
        )
        
        # Configure response synthesizer with custom prompt
        response_synthesizer = get_response_synthesizer(
            text_qa_template=self.legal_prompt_template,
            response_mode=ResponseMode.COMPACT
        )
        
        # Create query engine
        self.query_engine = RetrieverQueryEngine(
            retriever=retriever,
            response_synthesizer=response_synthesizer,
        )
        
        return self.query_engine
    
    def should_search_web(self, question: str) -> bool:
        """Determine if web search is needed for the query"""
        web_search_keywords = [
            'recent', 'latest', 'new', '2024', '2023', 'current', 'today',
            'recent case', 'recent judgment', 'latest ruling', 'new law',
            'current status', 'updated', 'now', 'present'
        ]
        
        question_lower = question.lower()
        return any(keyword in question_lower for keyword in web_search_keywords)
    
    def get_web_context(self, question: str) -> str:
        """Get relevant web context for the query with plain text formatting"""
        try:
            search_results = self.web_scraper.comprehensive_legal_search(question)
            
            if not search_results['results']:
                return "No recent web information found for this query."
            
            web_context = "Recent Legal Information from Web Sources:\n\n"
            
            for i, result in enumerate(search_results['results'][:2], 1):  # Reduced to 2 results
                web_context += f"{i}. {result['title']} (Source: {result['source']})\n"
                web_context += f"   {result['content'][:400]}{'...' if len(result['content']) > 400 else ''}\n\n"
            
            return web_context
            
        except Exception as e:
            return f"Error retrieving web information: {str(e)}"
    
    def query(self, question: str) -> str:
        """Enhanced query method with web search integration and improved formatting"""
        if not self.query_engine:
            raise ValueError("Query engine not setup. Call setup_query_engine() first.")
        
        try:
            # Get context from document index (reduced similarity search)
            retriever = VectorIndexRetriever(index=self.index, similarity_top_k=3)
            nodes = retriever.retrieve(question)
            doc_context = "\n".join([node.node.text for node in nodes])
            
            # Check if web search is needed
            web_context = ""
            if self.should_search_web(question):
                print("🔍 Searching web for recent information...")
                web_context = self.get_web_context(question)
            else:
                web_context = "No web search performed - using statutory documents only."
            
            # Create enhanced prompt
            enhanced_prompt = self.legal_prompt_template.format(
                context_str=doc_context,
                web_context=web_context,
                query_str=question
            )
            
            # Query the LLM directly with enhanced context
            response = self.llm.complete(enhanced_prompt)
            
            # Clean up response formatting
            response_text = str(response)
            # Remove markdown formatting
            response_text = response_text.replace('**', '')
            response_text = response_text.replace('*', '')
            response_text = response_text.replace('###', '')
            response_text = response_text.replace('##', '')
            response_text = response_text.replace('#', '')
            
            return response_text
            
        except Exception as e:
            return f"Error processing query: {str(e)}"
    
    def initialize(self, force_rebuild: bool = False):
        """Initialize the complete chatbot system with faster startup"""
        print("🚀 Initializing Legal Chatbot...")
        self.build_index(force_rebuild=force_rebuild)
        self.setup_query_engine()
        print("✅ Legal Chatbot initialized successfully!")
    
    def rebuild_index(self):
        """Force rebuild the index (useful when documents are updated)"""
        print("🔄 Rebuilding index...")
        self.initialize(force_rebuild=True)
    
    def get_document_info(self):
        """Get information about loaded documents"""
        if not self.index:
            return "Index not built yet."
        
        doc_info = []
        for doc_id in self.index.docstore.docs:
            doc = self.index.docstore.get_document(doc_id)
            doc_info.append({
                "filename": doc.metadata.get("filename", "Unknown"),
                "document_type": doc.metadata.get("document_type", "Unknown"),
                "text_length": len(doc.text)
            })
        
        return doc_info