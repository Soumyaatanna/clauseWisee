import streamlit as st
import requests
import json

st.set_page_config(
    page_title="clauseWise - Advanced Analysis",
    page_icon="🧠",
    layout="wide"
)

st.title("🧠 Advanced Legal Document Analysis")
st.markdown("Comprehensive analysis including document classification, clause extraction, and entity recognition.")

# Sidebar for navigation
st.sidebar.title("Navigation")
if st.sidebar.button("← Back to Home"):
    st.switch_page("Home.py")

# Main content
st.subheader("📤 Upload Document for Analysis")

uploaded_file = st.file_uploader(
    "Choose a legal document",
    type=['pdf', 'docx', 'txt'],
    help="Upload PDF, DOCX, or TXT files for comprehensive analysis"
)

if uploaded_file is not None:
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.info(f"📄 **File:** {uploaded_file.name}")
        st.info(f"📊 **Size:** {uploaded_file.size} bytes")
        
        if st.button("🚀 Analyze Document", type="primary"):
            with st.spinner("Analyzing document... This may take a moment."):
                try:
                    # Call the comprehensive analysis endpoint
                    files = {"file": uploaded_file.getvalue()}
                    response = requests.post(
                        "http://localhost:8000/analyze-document/",
                        files={"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        st.session_state.analysis_result = result
                        st.success("✅ Analysis completed!")
                        st.rerun()
                    
                    else:
                        st.error(f"❌ Error: {response.status_code} - {response.text}")
                        
                except requests.exceptions.ConnectionError:
                    st.error("❌ Cannot connect to the backend server. Please make sure it's running on http://localhost:8000")
                except Exception as e:
                    st.error(f"❌ An error occurred: {str(e)}")

# Display analysis results if available
if 'analysis_result' in st.session_state:
    result = st.session_state.analysis_result
    
    st.markdown("---")
    st.header("📊 Analysis Results")
    
    # Document Classification
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("📋 Document Type", result["document_type"].replace('_', ' ').title())
    
    with col2:
        confidence_pct = f"{result['confidence']:.1%}"
        st.metric("🎯 Confidence", confidence_pct)
    
    with col3:
        st.metric("📄 Total Clauses", len(result["clauses"]))
    
    # Tabs for different analysis views
    tab1, tab2, tab3, tab4 = st.tabs(["🏷️ Entities", "📋 Clauses", "✨ Simplified", "📊 Summary"])
    
    with tab1:
        st.subheader("🏷️ Extracted Entities")
        
        entities = result["extracted_entities"]
        
        # Create columns for different entity types
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**📅 Dates**")
            if entities["dates"]:
                for date in entities["dates"]:
                    st.write(f"• {date}")
            else:
                st.write("None found")
            
            st.markdown("**💰 Monetary Values**")
            if entities["monetary_values"]:
                for money in entities["monetary_values"]:
                    st.write(f"• {money}")
            else:
                st.write("None found")
        
        with col2:
            st.markdown("**⚖️ Legal Terms**")
            if entities["legal_terms"]:
                for term in entities["legal_terms"]:
                    st.write(f"• {term}")
            else:
                st.write("None found")
            
            st.markdown("**🏢 Organizations**")
            if entities["organizations"]:
                for org in entities["organizations"]:
                    st.write(f"• {org}")
            else:
                st.write("None found")
        
        with col3:
            st.markdown("**📋 Key Obligations**")
            if entities["obligations"]:
                for obligation in entities["obligations"][:5]:  # Show first 5
                    st.write(f"• {obligation[:100]}...")
            else:
                st.write("None found")
    
    with tab2:
        st.subheader("📋 Extracted Clauses")
        
        # Filter clauses by type
        clause_types = list(set(clause["type"] for clause in result["clauses"]))
        selected_type = st.selectbox("Filter by clause type:", ["All"] + clause_types)
        
        filtered_clauses = result["clauses"]
        if selected_type != "All":
            filtered_clauses = [c for c in result["clauses"] if c["type"] == selected_type]
        
        for i, clause in enumerate(filtered_clauses):
            with st.expander(f"📄 Clause {clause['id']} - {clause['type'].replace('_', ' ').title()}", expanded=False):
                st.markdown("**Original Text:**")
                st.write(clause["text"])
                
                if clause["entities"]:
                    st.markdown("**Entities in this clause:**")
                    # Show entities for this specific clause
                    for entity_type, entity_list in clause["entities"].items():
                        if entity_list:
                            st.write(f"• **{entity_type.replace('_', ' ').title()}:** {', '.join(entity_list)}")
    
    with tab3:
        st.subheader("✨ Simplified Clauses")
        
        for simplified_clause in result["simplified_clauses"]:
            with st.expander(f"📝 {simplified_clause['type'].replace('_', ' ').title()} Clause", expanded=False):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**📜 Original:**")
                    st.write(simplified_clause["original"])
                
                with col2:
                    st.markdown("**✨ Simplified:**")
                    st.info(simplified_clause["simplified"])
    
    with tab4:
        st.subheader("📊 Document Summary")
        
        # Clause type distribution
        clause_types_count = {}
        for clause in result["clauses"]:
            clause_type = clause["type"]
            clause_types_count[clause_type] = clause_types_count.get(clause_type, 0) + 1
        
        st.markdown("**📋 Clause Distribution:**")
        for clause_type, count in clause_types_count.items():
            st.write(f"• **{clause_type.replace('_', ' ').title()}:** {count} clause(s)")
        
        # Entity summary
        st.markdown("**🏷️ Entity Summary:**")
        total_entities = sum(len(entities) for entities in result["extracted_entities"].values())
        st.write(f"• **Total entities found:** {total_entities}")
        
        for entity_type, entity_list in result["extracted_entities"].items():
            if entity_list:
                st.write(f"• **{entity_type.replace('_', ' ').title()}:** {len(entity_list)}")
        
        # Document insights
        st.markdown("**💡 Key Insights:**")
        doc_type = result["document_type"]
        confidence = result["confidence"]
        
        if confidence > 0.7:
            st.success(f"✅ High confidence document classification as {doc_type.replace('_', ' ')}.")
        elif confidence > 0.4:
            st.warning(f"⚠️ Medium confidence document classification as {doc_type.replace('_', ' ')}.")
        else:
            st.info(f"ℹ️ Low confidence classification. Document may be mixed-type or unusual.")
        
        # Recommendations based on document type
        st.markdown("**📝 Recommended Review Points:**")
        recommendations = {
            'nda': [
                "Review confidentiality scope and duration",
                "Check permitted disclosures and exceptions",
                "Verify return/destruction of confidential information clauses"
            ],
            'employment_contract': [
                "Review compensation and benefits details",
                "Check termination clauses and notice periods",
                "Verify non-compete and intellectual property assignments"
            ],
            'service_agreement': [
                "Review scope of work and deliverables",
                "Check payment terms and schedule",
                "Verify liability limitations and indemnification"
            ],
            'lease_agreement': [
                "Review rent amount and escalation clauses",
                "Check maintenance and repair responsibilities",
                "Verify termination and renewal options"
            ]
        }
        
        doc_recommendations = recommendations.get(doc_type, [
            "Review all key terms and conditions",
            "Check liability and indemnification clauses",
            "Verify governing law and dispute resolution"
        ])
        
        for rec in doc_recommendations:
            st.write(f"• {rec}")

# Additional tools section
st.markdown("---")
st.header("🛠️ Additional Tools")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    **🔍 Clause Extraction**
    
    Extract and categorize individual clauses from any legal text.
    """)
    
    if st.button("Extract Clauses", use_container_width=True):
        st.info("Use the text input below to extract clauses from specific text.")

with col2:
    st.markdown("""
    **🏷️ Entity Recognition**
    
    Identify legal entities, dates, amounts, and key terms.
    """)
    
    if st.button("Extract Entities", use_container_width=True):
        st.info("Upload a document above or use the Simplify page for entity extraction.")

with col3:
    st.markdown("""
    **📊 Document Classification**
    
    Automatically classify document types with confidence scores.
    """)
    
    if st.button("Classify Document", use_container_width=True):
        st.info("Upload a document above for automatic classification.")

# Quick text analysis
st.markdown("---")
st.subheader("⚡ Quick Text Analysis")

quick_text = st.text_area(
    "Paste legal text for quick entity extraction:",
    height=150,
    placeholder="Paste any legal text here for quick entity analysis..."
)

if st.button("🚀 Analyze Text", disabled=not quick_text) and quick_text:
    with st.spinner("Analyzing text..."):
        try:
            response = requests.post(
                "http://localhost:8000/extract-entities/",
                json={"text": quick_text}
            )
            
            if response.status_code == 200:
                result = response.json()
                
                st.success("✅ Analysis completed!")
                
                # Display entities
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**📅 Dates:**")
                    for date in result["entities"]["dates"]:
                        st.write(f"• {date}")
                    
                    st.markdown("**💰 Monetary Values:**")
                    for money in result["entities"]["monetary_values"]:
                        st.write(f"• {money}")
                
                with col2:
                    st.markdown("**⚖️ Legal Terms:**")
                    for term in result["entities"]["legal_terms"]:
                        st.write(f"• {term}")
                    
                    st.markdown("**🏢 Organizations:**")
                    for org in result["entities"]["organizations"]:
                        st.write(f"• {org}")
            
            else:
                st.error(f"❌ Error: {response.status_code}")
                
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
