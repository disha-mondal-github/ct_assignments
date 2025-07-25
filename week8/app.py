import streamlit as st
import os
from legal_chatbot_main import LegalChatbot
import time

# Configure Streamlit page
st.set_page_config(
    page_title="Indian Legal System Chatbot",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling (Fixed markdown rendering)
st.markdown("""
<style>
    .main-header {
        text-align: center;
        color: #1f4e79;
        margin-bottom: 2rem;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
        line-height: 1.6;
    }
    .user-message {
        background-color: #e3f2fd;
        border-left: 4px solid #2196f3;
    }
    .bot-message {
        background-color: #f5f5f5;
        border-left: 4px solid #4caf50;
        white-space: pre-wrap;
    }
    .disclaimer {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 1rem 0;
    }
    .stProgress .st-bo {
        background-color: #1f4e79;
    }
</style>
""", unsafe_allow_html=True)

def initialize_chatbot():
    """Initialize the chatbot with better progress feedback"""
    if 'chatbot' not in st.session_state:
        
        # Show different messages based on cache status
        cache_exists = os.path.exists("./index_cache.pkl") and os.path.exists("./storage")
        
        if cache_exists:
            progress_text = "Loading cached index... This should be quick! ⚡"
        else:
            progress_text = "Building index for the first time... This may take 2-3 minutes ⏳"
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            with st.spinner(progress_text):
                status_text.text("🔧 Initializing Mistral AI...")
                progress_bar.progress(20)
                
                chatbot = LegalChatbot()
                
                status_text.text("📚 Processing legal documents...")
                progress_bar.progress(60)
                
                chatbot.initialize()
                
                status_text.text("✅ Setting up query engine...")
                progress_bar.progress(100)
                
                st.session_state.chatbot = chatbot
                
                # Clear progress indicators
                progress_bar.empty()
                status_text.empty()
                
                if cache_exists:
                    st.success("✅ Legal Chatbot loaded from cache in seconds!")
                else:
                    st.success("✅ Legal Chatbot initialized successfully! Future startups will be much faster.")
                
                return True
                
        except Exception as e:
            progress_bar.empty()
            status_text.empty()
            st.error(f"❌ Error initializing chatbot: {str(e)}")
            
            # Offer to rebuild if there's a cache issue
            if "cache" in str(e).lower():
                if st.button("🔄 Try rebuilding index"):
                    try:
                        chatbot = LegalChatbot()
                        chatbot.rebuild_index()
                        st.session_state.chatbot = chatbot
                        st.success("✅ Index rebuilt successfully!")
                        return True
                    except Exception as rebuild_error:
                        st.error(f"❌ Rebuild failed: {str(rebuild_error)}")
            
            return False
    return True

def main():
    # Main header
    st.markdown("<h1 class='main-header'>⚖️ Indian Legal System Chatbot</h1>", unsafe_allow_html=True)
    
    # Sidebar for information
    with st.sidebar:
        st.header("📚 About")
        st.write("""
        This AI legal assistant provides:
        - **Statutory Information**: Constitution, IPC, CrPC, CPC, etc.
        - **Recent Case Law**: Latest judgments and rulings
        - **Real-time Updates**: Current legal developments
        - **Comprehensive Analysis**: Combined statutory and case law insights
        """)
        
        st.header("🚀 Performance Features")
        st.info("""
        - **Smart Caching**: Index cached for instant startup
        - **Optimized Search**: Faster document retrieval
        - **Web Integration**: Auto-detects when recent info needed
        - **Clean Formatting**: Readable responses
        """)
        
        # Cache management
        st.header("🔧 Cache Management")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔄 Rebuild Index"):
                if 'chatbot' in st.session_state:
                    with st.spinner("Rebuilding index..."):
                        st.session_state.chatbot.rebuild_index()
                    st.success("✅ Index rebuilt!")
                else:
                    st.warning("Initialize chatbot first")
        
        with col2:
            cache_size = "Unknown"
            try:
                if os.path.exists("./storage"):
                    import shutil
                    cache_size = f"{shutil.disk_usage('./storage')[1] / (1024*1024):.1f} MB"
            except:
                pass
            st.metric("Cache Size", cache_size)
        
        st.header("🔍 Search Capabilities")
        st.write("""
        - **Document Search**: Instant access to legal provisions
        - **Web Search**: Recent cases and judgments
        - **Smart Detection**: Automatically searches web for recent queries
        - **Trusted Sources**: IndianKanoon, Supreme Court, legal news
        """)
        
        st.header("⚠️ Disclaimer")
        st.warning("""
        This chatbot provides general legal information and recent case updates. 
        Web-scraped information is from trusted legal sources but should be 
        independently verified. Always consult with a qualified lawyer for 
        specific legal advice.
        """)
    
    # Check if documents folder exists
    if not os.path.exists("documents"):
        st.error("📁 Documents folder not found! Please create a 'documents' folder and add your legal documents (PDF, DOCX, or TXT format).")
        st.info("Recommended documents: Indian Constitution, IPC, CrPC, CPC, Indian Evidence Act, Contract Act, etc.")
        return
    
    # Check if documents folder is empty
    if not os.listdir("documents"):
        st.warning("📁 Documents folder is empty! Please add legal documents to get started.")
        st.info("Supported formats: PDF, DOCX, TXT")
        return
    
    # Initialize chatbot
    if not initialize_chatbot():
        return
    
    # Display document information
    if st.sidebar.button("📄 Show Loaded Documents"):
        if 'chatbot' in st.session_state:
            doc_info = st.session_state.chatbot.get_document_info()
            st.sidebar.write("**Loaded Documents:**")
            for doc in doc_info:
                st.sidebar.write(f"- {doc['filename']} ({doc['text_length']} chars)")
    
    # Initialize chat history
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    # Display chat history with improved formatting
    for message in st.session_state.chat_history:
        if message['role'] == 'user':
            st.markdown(f"""
            <div class="chat-message user-message">
                <strong>You:</strong> {message['content']}
            </div>
            """, unsafe_allow_html=True)
        else:
            # Clean message content for display
            clean_content = message['content'].replace('\n', '<br>')
            st.markdown(f"""
            <div class="chat-message bot-message">
                <strong>Legal Assistant:</strong><br>{clean_content}
            </div>
            """, unsafe_allow_html=True)
    
    # Sample questions
    st.subheader("💡 Sample Questions")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("What is Article 21 of Indian Constitution?"):
            st.session_state.current_question = "What is Article 21 of Indian Constitution?"
    
    with col2:
        if st.button("Recent Supreme Court judgments on bail"):
            st.session_state.current_question = "Recent Supreme Court judgments on bail"
    
    with col3:
        if st.button("Latest cases on Article 370"):
            st.session_state.current_question = "Latest cases on Article 370"
    
    # Additional row for recent queries
    col4, col5, col6 = st.columns(3)
    
    with col4:
        if st.button("Current GST law updates"):
            st.session_state.current_question = "Current GST law updates"
    
    with col5:
        if st.button("2024 criminal law amendments"):
            st.session_state.current_question = "2024 criminal law amendments"
    
    with col6:
        if st.button("Recent divorce law changes"):
            st.session_state.current_question = "Recent divorce law changes"
    
    # Chat input
    user_question = st.chat_input("Ask your legal question here...")
    
    # Handle sample question button clicks
    if 'current_question' in st.session_state:
        user_question = st.session_state.current_question
        del st.session_state.current_question
    
    if user_question:
        # Add user message to chat history
        st.session_state.chat_history.append({
            'role': 'user',
            'content': user_question
        })
        
        # Display user message immediately
        st.markdown(f"""
        <div class="chat-message user-message">
            <strong>You:</strong> {user_question}
        </div>
        """, unsafe_allow_html=True)
        
        # Generate response with better progress indication
        response_placeholder = st.empty()
        
        with st.spinner("🔍 Analyzing legal documents and searching for information..."):
            try:
                start_time = time.time()
                response = st.session_state.chatbot.query(user_question)
                end_time = time.time()
                
                # Add bot response to chat history
                st.session_state.chat_history.append({
                    'role': 'assistant',
                    'content': response
                })
                
                # Display bot response with timing
                processing_time = f"⏱️ Response generated in {end_time - start_time:.1f} seconds"
                
                clean_response = response.replace('\n', '<br>')
                response_placeholder.markdown(f"""
                <div class="chat-message bot-message">
                    <strong>Legal Assistant:</strong><br>{clean_response}
                    <br><br><small style="color: #666;">{processing_time}</small>
                </div>
                """, unsafe_allow_html=True)
                
            except Exception as e:
                error_message = f"Sorry, I encountered an error: {str(e)}"
                st.error(error_message)
                st.session_state.chat_history.append({
                    'role': 'assistant',
                    'content': error_message
                })
        
        # Rerun to update the display
        st.rerun()
    
    # Clear chat button
    if st.sidebar.button("🗑️ Clear Chat History"):
        st.session_state.chat_history = []
        st.rerun()
    
    # Legal disclaimer at the bottom
    st.markdown("""
    <div class="disclaimer">
        <strong>⚠️ Legal Disclaimer:</strong> This chatbot provides general information about Indian law 
        and recent legal developments for educational purposes only. Web-scraped information is sourced 
        from trusted legal websites but should be independently verified. This is not a substitute for 
        professional legal advice. Always consult with a qualified lawyer for legal matters specific to your situation.
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()