import streamlit as st
import requests
import time

BACKEND_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="Upload Documents", page_icon="📄", layout="wide")

st.title("📄 Upload Legal Documents")
st.markdown("Upload your legal documents for AI-powered analysis. Supported formats: PDF, DOCX, and TXT.")

# Processing options
col1, col2 = st.columns(2)

with col1:
    st.subheader("📤 Document Upload")
    
    uploaded_files = st.file_uploader(
        "Drop your legal documents here",
        type=["pdf", "docx", "txt"],
        accept_multiple_files=True,
        help="Upload PDF, DOCX, or TXT files for processing"
    )
    
    # Processing mode selection
    processing_mode = st.radio(
        "Choose processing mode:",
        ["Basic Upload", "Full Analysis"],
        help="Basic Upload: Quick indexing for Q&A. Full Analysis: Comprehensive document analysis with clause extraction."
    )

with col2:
    st.subheader("⚙️ Processing Options")
    
    if processing_mode == "Full Analysis":
        st.info("🧠 **Full Analysis includes:**")
        st.markdown("""
        - Document type classification
        - Clause extraction and categorization
        - Named entity recognition
        - Clause simplification
        - Risk assessment
        """)
    else:
        st.info("⚡ **Basic Upload includes:**")
        st.markdown("""
        - Text extraction and indexing
        - Semantic search preparation
        - Quick Q&A readiness
        """)

# Process button
if uploaded_files:
    if st.button("🚀 Process Documents", use_container_width=True, type="primary"):
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        results = []
        
        for i, file in enumerate(uploaded_files):
            status_text.text(f"Processing {file.name}...")
            progress_bar.progress((i) / len(uploaded_files))
            
            files = {'file': (file.name, file.getvalue(), file.type)}
            
            try:
                if processing_mode == "Full Analysis":
                    # Use the comprehensive analysis endpoint
                    response = requests.post(f"{BACKEND_URL}/analyze-document/", files=files)
                else:
                    # Use the basic upload endpoint
                    response = requests.post(f"{BACKEND_URL}/upload/", files=files)
                
                if response.status_code == 200:
                    result = response.json()
                    results.append({
                        "filename": file.name,
                        "status": "success",
                        "data": result
                    })
                    st.toast(f"✅ Successfully processed {file.name}", icon="🎉")
                else:
                    results.append({
                        "filename": file.name,
                        "status": "error",
                        "error": response.text
                    })
                    st.toast(f"❌ Failed to process {file.name}", icon="⚠️")
                    
            except requests.exceptions.RequestException as e:
                results.append({
                    "filename": file.name,
                    "status": "error",
                    "error": str(e)
                })
                st.toast(f"❌ Connection error for {file.name}", icon="⚠️")
        
        progress_bar.progress(1.0)
        status_text.text("Processing complete!")
        
        # Display results
        st.markdown("---")
        st.subheader("📊 Processing Results")
        
        for result in results:
            if result["status"] == "success":
                with st.expander(f"✅ {result['filename']} - Processed Successfully", expanded=False):
                    if processing_mode == "Full Analysis":
                        data = result["data"]
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Document Type", data.get("document_type", "Unknown").replace('_', ' ').title())
                        with col2:
                            confidence = data.get("confidence", 0)
                            st.metric("Confidence", f"{confidence:.1%}")
                        with col3:
                            clauses_count = len(data.get("clauses", []))
                            st.metric("Clauses Found", clauses_count)
                        
                        # Quick summary
                        st.markdown("**📋 Quick Summary:**")
                        entities = data.get("extracted_entities", {})
                        total_entities = sum(len(v) for v in entities.values())
                        st.write(f"• Total entities extracted: {total_entities}")
                        st.write(f"• Legal terms found: {len(entities.get('legal_terms', []))}")
                        st.write(f"• Organizations mentioned: {len(entities.get('organizations', []))}")
                        
                        if st.button(f"View Full Analysis for {result['filename']}", key=f"analysis_{result['filename']}"):
                            st.info("📄 Full analysis available in the 'Advanced Analysis' page")
                    
                    else:
                        st.write(f"Status: {result['data'].get('status', 'Unknown')}")
                        st.success("Document ready for Q&A queries!")
            
            else:
                with st.expander(f"❌ {result['filename']} - Processing Failed", expanded=False):
                    st.error(f"Error: {result['error']}")

# Navigation and tips
st.markdown("---")

col1, col2 = st.columns(2)

with col1:
    st.subheader("🧭 Next Steps")
    st.markdown("""
    After uploading your documents:
    
    - **Ask Questions**: Use the Q&A page to query your documents
    - **Simplify Text**: Get plain English versions of complex clauses
    - **Advanced Analysis**: View detailed breakdowns and insights
    """)
    
    if st.button("➡️ Go to Q&A", use_container_width=True):
        st.switch_page("pages/2_Q&A.py")

with col2:
    st.subheader("💡 Tips for Better Results")
    st.markdown("""
    **Document Quality:**
    - Use clear, readable documents
    - Ensure text is not image-based
    - Complete documents work better than fragments
    
    **Processing Mode:**
    - Use **Basic Upload** for quick Q&A setup
    - Use **Full Analysis** for comprehensive review
    """)

# Document status and recent documents
try:
    response = requests.get(f"{BACKEND_URL}/documents/")
    if response.status_code == 200:
        docs_data = response.json()
        if docs_data.get("documents"):
            st.markdown("---")
            st.subheader("📚 Recently Uploaded Documents")
            
            # Summary stats
            total_docs = len(docs_data["documents"])
            analyzed_docs = len([doc for doc in docs_data["documents"] if 'document_type' in doc])
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Documents", total_docs)
            with col2:
                st.metric("Fully Analyzed", analyzed_docs)
            with col3:
                st.metric("Available for Q&A", total_docs)
            
            # Document cards
            for i, doc in enumerate(docs_data["documents"]):
                with st.container(border=True):
                    col1, col2, col3 = st.columns([3, 2, 1])
                    
                    with col1:
                        st.markdown(f"**📄 {doc['name']}**")
                        st.write(f"Status: {doc['status']}")
                        
                        # Show document type if available
                        if 'document_type' in doc:
                            doc_type = doc['document_type'].replace('_', ' ').title()
                            confidence = doc.get('confidence', 0)
                            
                            if confidence > 0.7:
                                st.success(f"🎯 {doc_type} (High confidence: {confidence:.1%})")
                            elif confidence > 0.4:
                                st.warning(f"🎯 {doc_type} (Medium confidence: {confidence:.1%})")
                            else:
                                st.info(f"🎯 {doc_type} (Low confidence: {confidence:.1%})")
                    
                    with col2:
                        if 'clauses_count' in doc and 'entities_count' in doc:
                            st.write(f"**📋 Clauses:** {doc['clauses_count']}")
                            st.write(f"**🏷️ Entities:** {doc['entities_count']}")
                        else:
                            st.write("**📊 Analysis:** Basic indexing")
                            st.write("**🔍 Features:** Q&A ready")
                    
                    with col3:
                        # Action buttons
                        if st.button("🔍 Analyze", key=f"analyze_btn_{i}", help="Go to Advanced Analysis"):
                            st.switch_page("pages/4_Analysis.py")
                        
                        if st.button("❓ Q&A", key=f"qa_btn_{i}", help="Ask questions about this document"):
                            st.switch_page("pages/2_Q&A.py")
        else:
            st.markdown("---")
            st.info("📝 **No documents uploaded yet.** Upload your first legal document above to get started!")
    else:
        st.warning("⚠️ Cannot retrieve document list. Please check if the backend is running.")

except requests.exceptions.ConnectionError:
    st.error("❌ **Backend Connection Error**: Cannot connect to the analysis server. Please ensure the backend is running on http://127.0.0.1:8000")
except Exception as e:
    st.warning(f"⚠️ **Error retrieving documents**: {str(e)}")

# Quick actions section
st.markdown("---")
st.subheader("⚡ Quick Actions")

action_col1, action_col2, action_col3, action_col4 = st.columns(4)

with action_col1:
    if st.button("🔍 Simplify Text", use_container_width=True, help="Transform complex legal clauses into plain English"):
        st.switch_page("pages/3_Simplify.py")

with action_col2:
    if st.button("🧠 Advanced Analysis", use_container_width=True, help="Comprehensive document analysis"):
        st.switch_page("pages/4_Analysis.py")

with action_col3:
    if st.button("❓ Ask Questions", use_container_width=True, help="Query your documents using natural language"):
        st.switch_page("pages/2_Q&A.py")

with action_col4:
    if st.button("🏠 Home", use_container_width=True, help="Return to the main dashboard"):
        st.switch_page("Home.py")