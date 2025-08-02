import streamlit as st
import requests
import json
import os
BACKEND_URL = os.environ.get("BACKEND_URL")

st.set_page_config(
    page_title="clauseWise - Clause Simplification",
    page_icon="🔍",
    layout="wide"
)

st.title("🔍 Clause Simplification")
st.markdown("Transform complex legal clauses into plain English for better understanding.")

# Sidebar for navigation
st.sidebar.title("Navigation")
if st.sidebar.button("← Back to Home"):
    st.switch_page("Home.py")

# Main content
col1, col2 = st.columns(2)

with col1:
    st.subheader("📝 Input Legal Text")
    
    # Text input options
    input_method = st.radio("Choose input method:", ["Type/Paste Text", "Upload Document"])
    
    if input_method == "Type/Paste Text":
        clause_text = st.text_area(
            "Enter legal clause or text:",
            height=300,
            placeholder="Paste your legal clause here...\n\nExample: 'The party of the first part shall indemnify and hold harmless the party of the second part from any and all claims, damages, or liabilities arising heretofore or hereinafter.'"
        )
    else:
        uploaded_file = st.file_uploader("Upload a legal document", type=['pdf', 'docx', 'txt'])
        clause_text = ""
        
        if uploaded_file is not None:
            # For now, we'll handle this in a basic way
            # In a full implementation, you'd extract text from the uploaded file
            st.info("📄 Document uploaded. Please use the 'Advanced Analysis' page for full document processing.")

with col2:
    st.subheader("✨ Simplified Version")
    
    if st.button("🚀 Simplify Text", type="primary", disabled=not clause_text):
        if clause_text:
            with st.spinner("Simplifying legal text..."):
                try:
                    # Call the backend API
                    response = requests.post(
                        "http://localhost:8000/simplify-clause/",
                        json={"text": clause_text}
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        
                        # Display simplified text
                        st.success("✅ Simplified successfully!")
                        
                        # Show comparison
                        st.markdown("### 📊 Before & After Comparison")
                        
                        # Original text
                        with st.expander("📜 Original Text", expanded=False):
                            st.write(result["original"])
                        
                        # Simplified text
                        st.markdown("### 🎯 Simplified Version")
                        st.info(result["simplified"])
                        
                        # Show extracted entities
                        if result["entities"]:
                            st.markdown("### 🏷️ Extracted Legal Entities")
                            
                            # Create tabs for different entity types
                            entity_tabs = st.tabs(["📅 Dates", "💰 Money", "⚖️ Legal Terms", "🏢 Organizations", "📋 Obligations"])
                            
                            with entity_tabs[0]:
                                if result["entities"]["dates"]:
                                    for date in result["entities"]["dates"]:
                                        st.write(f"• {date}")
                                else:
                                    st.write("No dates found")
                            
                            with entity_tabs[1]:
                                if result["entities"]["monetary_values"]:
                                    for money in result["entities"]["monetary_values"]:
                                        st.write(f"• {money}")
                                else:
                                    st.write("No monetary values found")
                            
                            with entity_tabs[2]:
                                if result["entities"]["legal_terms"]:
                                    for term in result["entities"]["legal_terms"]:
                                        st.write(f"• {term}")
                                else:
                                    st.write("No legal terms found")
                            
                            with entity_tabs[3]:
                                if result["entities"]["organizations"]:
                                    for org in result["entities"]["organizations"]:
                                        st.write(f"• {org}")
                                else:
                                    st.write("No organizations found")
                            
                            with entity_tabs[4]:
                                if result["entities"]["obligations"]:
                                    for obligation in result["entities"]["obligations"]:
                                        st.write(f"• {obligation}")
                                else:
                                    st.write("No obligations found")
                    
                    else:
                        st.error(f"❌ Error: {response.status_code} - {response.text}")
                        
                except requests.exceptions.ConnectionError:
                    st.error("❌ Cannot connect to the backend server. Please make sure it's running on http://localhost:8000")
                except Exception as e:
                    st.error(f"❌ An error occurred: {str(e)}")

# Tips section
st.markdown("---")
st.markdown("### 💡 Tips for Better Results")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    **📝 Input Quality**
    - Use complete sentences
    - Include full clause context
    - Avoid fragmented text
    """)

with col2:
    st.markdown("""
    **🎯 Best Use Cases**
    - Contract clauses
    - Legal definitions
    - Terms and conditions
    """)

with col3:
    st.markdown("""
    **⚡ Quick Actions**
    - Copy simplified text
    - Share with stakeholders
    - Use for explanations
    """)

# Sample clauses for testing
st.markdown("---")
st.markdown("### 📚 Sample Legal Clauses")

sample_clauses = [
    "The party of the first part shall indemnify and hold harmless the party of the second part from any and all claims, damages, or liabilities arising heretofore or hereinafter.",
    "Notwithstanding any provision herein to the contrary, the obligations set forth in this Section shall survive termination of this Agreement in perpetuity.",
    "In consideration of the mutual covenants and agreements contained herein, and for other good and valuable consideration, the receipt and sufficiency of which are hereby acknowledged, the parties agree as follows.",
    "Force majeure events shall include, but not be limited to, acts of God, war, terrorism, pandemic, governmental action, or any other event beyond the reasonable control of the affected party."
]

st.markdown("Click on any sample clause below to try the simplification:")

for i, sample in enumerate(sample_clauses):
    if st.button(f"📄 Sample {i+1}: {sample[:50]}...", key=f"sample_{i}"):
        st.session_state.sample_clause = sample
        st.rerun()

# Handle sample clause selection
if 'sample_clause' in st.session_state:
    st.text_area("Selected sample clause:", value=st.session_state.sample_clause, key="sample_display")
    if st.button("Use This Sample", type="secondary"):
        # This would update the main text area - in a real app you'd handle this differently
        st.info("Copy the text above and paste it into the main input area.")
