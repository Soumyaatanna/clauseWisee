import streamlit as st

st.set_page_config(
    page_title="clauseWise - Dashboard",
    page_icon="⚖️",
    layout="wide"
)

st.title("Welcome to clauseWise ⚖️")
st.markdown("AI-powered legal document analysis that transforms complex legal language into plain English. Upload, analyze, and query your documents with ease.")

# Backend status check
try:
    import requests
    response = requests.get("http://localhost:8000/health", timeout=2)
    if response.status_code == 200:
        st.success("🟢 Backend is running and ready!")
    else:
        st.warning("🟡 Backend is starting up...")
except:
    st.error("🔴 Backend is not running. Please start the backend server first.")
    with st.expander("🛠️ How to start the backend"):
        st.code("cd backend\npython -m uvicorn main:app --reload", language="bash")
        st.markdown("Run this command in your terminal to start the backend server.")

st.markdown("---")

col1, col2, col3, col4 = st.columns(4)

with col1:
    with st.container(border=True):
        st.header("📄 Upload & Analyze")
        st.write("Upload legal documents for comprehensive AI analysis including clause extraction and entity recognition.")
        if st.button("Upload New Document", use_container_width=True, type="primary"):
            st.switch_page("pages/1_Upload.py")

with col2:
    with st.container(border=True):
        st.header("🔍 Simplify Legal Text")
        st.write("Transform complex legal clauses into plain English for better understanding.")
        if st.button("Simplify Clauses", use_container_width=True):
            st.switch_page("pages/3_Simplify.py")

with col3:
    with st.container(border=True):
        st.header("❓ Ask Questions")
        st.write("Query your documents using natural language and get contextual answers.")
        if st.button("Start Q&A Session", use_container_width=True):
             st.switch_page("pages/2_Q&A.py")

with col4:
    with st.container(border=True):
        st.header("🧠 Advanced Analysis")
        st.write("Extract entities, classify documents, and break down clauses for detailed review.")
        if st.button("Advanced Tools", use_container_width=True):
            st.switch_page("pages/4_Analysis.py")

st.markdown("---")

# Feature highlights
st.header("🚀 Features")
col1, col2 = st.columns(2)

with col1:
    st.subheader("📋 Document Analysis")
    st.markdown("""
    - **Document Type Classification**: Automatically identify NDAs, contracts, leases, etc.
    - **Clause Extraction**: Break down documents into individual, categorized clauses
    - **Entity Recognition**: Extract parties, dates, monetary values, and legal terms
    - **Smart Categorization**: Organize clauses by type (payment, liability, termination, etc.)
    """)

with col2:
    st.subheader("💡 Intelligent Processing")
    st.markdown("""
    - **Clause Simplification**: Convert complex legal language to plain English
    - **Contextual Q&A**: Ask questions and get relevant answers from your documents
    - **Risk Assessment**: Identify key obligations and potential issues
    - **Export & Review**: Generate summaries and analysis reports
    """)

st.markdown("---")
st.header("📊 Recent Documents")

# Try to fetch recent documents from backend
try:
    import requests
    response = requests.get("http://localhost:8000/documents/")
    if response.status_code == 200:
        docs_data = response.json()
        documents = docs_data.get("documents", [])
        
        if documents:
            # Show summary metrics
            col1, col2, col3, col4 = st.columns(4)
            
            total_docs = len(documents)
            analyzed_docs = len([doc for doc in documents if 'document_type' in doc])
            unique_types = len(set(doc.get('document_type', 'unknown') for doc in documents))
            total_clauses = sum(doc.get('clauses_count', 0) for doc in documents)
            
            with col1:
                st.metric("📄 Total Documents", total_docs)
            with col2:
                st.metric("🧠 Fully Analyzed", analyzed_docs)
            with col3:
                st.metric("📋 Document Types", unique_types)
            with col4:
                st.metric("📝 Total Clauses", total_clauses)
            
            st.markdown("### 📋 Document List")
            
            # Show recent documents (limit to 5 most recent)
            recent_docs = documents[-5:] if len(documents) > 5 else documents
            
            for i, doc in enumerate(reversed(recent_docs)):  # Show most recent first
                with st.container(border=True):
                    col1, col2, col3 = st.columns([4, 2, 2])
                    
                    with col1:
                        st.markdown(f"**📄 {doc['name']}**")
                        
                        # Show document type and confidence if available
                        if 'document_type' in doc:
                            doc_type = doc['document_type'].replace('_', ' ').title()
                            confidence = doc.get('confidence', 0)
                            
                            if confidence > 0.7:
                                st.success(f"🎯 {doc_type} ({confidence:.0%} confidence)")
                            elif confidence > 0.4:
                                st.warning(f"🎯 {doc_type} ({confidence:.0%} confidence)")
                            else:
                                st.info(f"🎯 {doc_type} ({confidence:.0%} confidence)")
                        else:
                            st.info("📊 Basic upload - Ready for Q&A")
                    
                    with col2:
                        # Show analysis details
                        if 'clauses_count' in doc:
                            st.write(f"📋 **{doc['clauses_count']}** clauses")
                        if 'entities_count' in doc:
                            st.write(f"🏷️ **{doc['entities_count']}** entities")
                        
                        st.write(f"Status: {doc['status']}")
                    
                    with col3:
                        # Quick action buttons
                        if st.button("🔍 Analyze", key=f"home_analyze_{i}", use_container_width=True):
                            st.switch_page("pages/4_Analysis.py")
                        if st.button("❓ Ask Q&A", key=f"home_qa_{i}", use_container_width=True):
                            st.switch_page("pages/2_Q&A.py")
            
            # Show "View All" button if there are more documents
            if len(documents) > 5:
                st.info(f"📚 Showing 5 most recent documents. Total: {len(documents)} documents.")
                if st.button("📋 View All Documents", use_container_width=True):
                    st.switch_page("pages/1_Upload.py")
        else:
            # No documents uploaded yet
            st.info("📝 **No documents uploaded yet.** Get started by uploading your first legal document!")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📤 Upload Document", use_container_width=True, type="primary"):
                    st.switch_page("pages/1_Upload.py")
            with col2:
                if st.button("📚 Sample Documents", use_container_width=True):
                    st.info("💡 Try uploading a legal document like an NDA, contract, or agreement to see the analysis in action!")
    
    else:
        st.warning("⚠️ Cannot retrieve document list. Backend may be starting up...")
        
except ImportError:
    st.info("📝 The document list will appear here after you upload files and start the backend.")
except:
    st.info("📝 The document list will appear here after you upload files.")

# Tips section
st.markdown("---")
st.markdown("### 💡 Getting Started Tips")

tip_col1, tip_col2 = st.columns(2)

with tip_col1:
    st.markdown("""
    **🚀 Quick Start:**
    1. Upload a legal document (PDF, DOCX, or TXT)
    2. Choose "Full Analysis" for comprehensive insights
    3. Explore simplified clauses and extracted entities
    4. Ask questions about your documents
    """)

with tip_col2:
    st.markdown("""
    **📋 Best Practices:**
    - Use clear, complete legal documents
    - Try different document types (NDAs, contracts, etc.)
    - Use the Q&A feature for specific questions
    - Review simplified clauses for better understanding
    """)

# Footer with feature highlights
st.markdown("---")
st.markdown("### 🎯 Feature Highlights")

feature_col1, feature_col2, feature_col3 = st.columns(3)

with feature_col1:
    st.markdown("""
    **🔍 Document Analysis**
    - Automatic type classification
    - Clause extraction & categorization
    - Named entity recognition
    - Risk assessment
    """)

with feature_col2:
    st.markdown("""
    **✨ Text Simplification**
    - Plain English translations
    - Complex clause breakdown
    - Legal term explanations
    - Context preservation
    """)

with feature_col3:
    st.markdown("""
    **❓ Smart Q&A**
    - Natural language queries
    - Context-aware responses
    - Multi-document search
    - Semantic understanding
    """)