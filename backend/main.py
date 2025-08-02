import os
import io
import re
import docx
import pdfplumber
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone, ServerlessSpec
from typing import List, Dict, Any
import json
from datetime import datetime

# Load environment variables
load_dotenv()

# --- Configuration ---
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT")
HUGGING_FACE_HUB_TOKEN = os.getenv("HUGGING_FACE_HUB_TOKEN")
PINECONE_INDEX_NAME = "clausewise" 

app = FastAPI(title="clauseWise API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)

processed_documents = []

class QueryRequest(BaseModel):
    question: str

class SimplifyRequest(BaseModel):
    text: str

class NERRequest(BaseModel):
    text: str

class ClauseExtractionRequest(BaseModel):
    text: str

class DocumentAnalysisResponse(BaseModel):
    filename: str
    document_type: str
    confidence: float
    simplified_clauses: List[Dict[str, Any]]
    extracted_entities: Dict[str, List[str]]
    clauses: List[Dict[str, Any]]

# --- Load Models on Startup ---
@app.on_event("startup")
def load_models():
    global embedding_model, generator, index
    print("--- Loading models and connecting to DB... ---")
    
    embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
    
    try:
        # Use a simple text processing approach instead of heavy models
        print("Setting up simple text processing...")
        generator = None  # We'll use simple context matching instead
        print("Text processing setup complete")
    except Exception as e:
        print(f"Error in setup: {e}")
        generator = None
    
    # --- Connect to Pinecone (NEW SYNTAX) ---
    try:
        pc = Pinecone(api_key=PINECONE_API_KEY)
        
        # Try to list existing indexes first
        existing_indexes = pc.list_indexes()
        print(f"Existing indexes: {existing_indexes.names()}")
        
        if PINECONE_INDEX_NAME not in existing_indexes.names():
            # Try different region/cloud combinations
            try:
                print("Attempting to create index with GCP us-central1...")
                pc.create_index(
                    name=PINECONE_INDEX_NAME, 
                    dimension=384, 
                    metric='cosine',
                    spec=ServerlessSpec(cloud='gcp', region='us-central1')
                )
            except Exception as gcp_error:
                print(f"GCP failed: {gcp_error}")
                try:
                    print("Attempting to create index with AWS us-east-1...")
                    pc.create_index(
                        name=PINECONE_INDEX_NAME, 
                        dimension=384, 
                        metric='cosine',
                        spec=ServerlessSpec(cloud='aws', region='us-east-1')
                    )
                except Exception as aws_error:
                    print(f"AWS failed: {aws_error}")
                    raise Exception("Failed to create Pinecone index with any available region")
        
        index = pc.Index(PINECONE_INDEX_NAME) # Get index object from Pinecone instance
        print("Pinecone connection successful!")
        
    except Exception as pinecone_error:
        print(f"Pinecone connection failed: {pinecone_error}")
        print("Running without Pinecone - document search will be limited")
        index = None
    
    print("--- Startup complete. ---")

# --- Helper Functions ---
def parse_document(file: UploadFile):
    content = file.file.read()
    if file.filename.endswith(".pdf"):
        with pdfplumber.open(io.BytesIO(content)) as pdf:
            return "\n".join(page.extract_text() for page in pdf.pages if page.extract_text())
    elif file.filename.endswith(".docx"):
        doc = docx.Document(io.BytesIO(content))
        return "\n".join(para.text for para in doc.paragraphs)
    return content.decode("utf-8")

def split_text(text: str):
    return text.split('\n\n')

# --- Legal Analysis Functions ---

def simplify_clause(clause_text: str) -> str:
    """
    Simplify complex legal language into layman-friendly terms
    """
    # Legal to simple term mappings
    simplification_rules = {
        r'\bheretofore\b': 'before this',
        r'\bhereinafter\b': 'after this',
        r'\bwhereas\b': 'since',
        r'\btherefore\b': 'so',
        r'\bnotwithstanding\b': 'despite',
        r'\bforthwith\b': 'immediately',
        r'\bpursuant to\b': 'according to',
        r'\bin consideration of\b': 'in exchange for',
        r'\bshall\b': 'must',
        r'\bmay\b': 'can',
        r'\bindemnify\b': 'protect from losses',
        r'\bholdco\b': 'holding company',
        r'\bforce majeure\b': 'unforeseeable circumstances',
        r'\bquid pro quo\b': 'something for something',
        r'\bper annum\b': 'per year',
        r'\bper se\b': 'by itself',
        r'\bpro rata\b': 'proportionally',
        r'\bad hoc\b': 'for this specific purpose',
        r'\bbona fide\b': 'genuine',
        r'\bin perpetuity\b': 'forever',
        r'\bnull and void\b': 'invalid',
        r'\bparty of the first part\b': 'first party',
        r'\bparty of the second part\b': 'second party'
    }
    
    simplified = clause_text
    for legal_term, simple_term in simplification_rules.items():
        simplified = re.sub(legal_term, simple_term, simplified, flags=re.IGNORECASE)
    
    # Break down long sentences
    sentences = simplified.split('.')
    simplified_sentences = []
    
    for sentence in sentences:
        if len(sentence.strip()) > 100:  # If sentence is too long
            # Try to break at conjunctions
            parts = re.split(r',\s*(?:and|or|but|however|moreover|furthermore)\s+', sentence)
            simplified_sentences.extend([part.strip() for part in parts if part.strip()])
        else:
            if sentence.strip():
                simplified_sentences.append(sentence.strip())
    
    return '. '.join(simplified_sentences) + ('.' if not simplified.endswith('.') else '')

def extract_named_entities(text: str) -> Dict[str, List[str]]:
    """
    Extract legal entities using rule-based NER
    """
    entities = {
        'parties': [],
        'dates': [],
        'monetary_values': [],
        'obligations': [],
        'legal_terms': [],
        'locations': [],
        'organizations': []
    }
    
    # Extract dates
    date_patterns = [
        r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',
        r'\b\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{2,4}\b',
        r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{2,4}\b'
    ]
    for pattern in date_patterns:
        entities['dates'].extend(re.findall(pattern, text, re.IGNORECASE))
    
    # Extract monetary values
    money_patterns = [
        r'\$[\d,]+(?:\.\d{2})?',
        r'\b\d+\s*(?:dollars?|USD|cents?)\b',
        r'\b(?:USD|EUR|GBP|CAD)\s*[\d,]+(?:\.\d{2})?\b'
    ]
    for pattern in money_patterns:
        entities['monetary_values'].extend(re.findall(pattern, text, re.IGNORECASE))
    
    # Extract legal terms
    legal_terms = [
        'contract', 'agreement', 'clause', 'provision', 'warranty', 'indemnification',
        'liability', 'damages', 'breach', 'termination', 'confidentiality', 'non-disclosure',
        'intellectual property', 'copyright', 'trademark', 'patent', 'trade secret',
        'force majeure', 'arbitration', 'jurisdiction', 'governing law', 'amendment'
    ]
    for term in legal_terms:
        if re.search(r'\b' + re.escape(term) + r'\b', text, re.IGNORECASE):
            entities['legal_terms'].append(term)
    
    # Extract organizations (simple pattern)
    org_patterns = [
        r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:Inc|LLC|Corp|Corporation|Company|Ltd|Limited)\b',
        r'\b(?:Inc|LLC|Corp|Corporation|Company|Ltd|Limited)\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b'
    ]
    for pattern in org_patterns:
        entities['organizations'].extend(re.findall(pattern, text))
    
    # Extract obligations (modal verbs + actions)
    obligation_patterns = [
        r'\b(?:shall|must|will|agree to|undertake to|covenant to)\s+[^.]+',
        r'\b(?:responsible for|liable for|obligated to)\s+[^.]+',
        r'\bparty\s+(?:A|B|\w+)\s+(?:shall|must|will)\s+[^.]+'
    ]
    for pattern in obligation_patterns:
        entities['obligations'].extend(re.findall(pattern, text, re.IGNORECASE))
    
    return entities

def extract_clauses(text: str) -> List[Dict[str, Any]]:
    """
    Extract and categorize individual clauses from legal documents
    """
    clauses = []
    
    # Split text into potential clauses
    clause_patterns = [
        r'\n\s*\d+\.\s*[A-Z][^.]*\.(?:[^.]*\.)*',  # Numbered clauses
        r'\n\s*\([a-z]\)\s*[A-Z][^.]*\.(?:[^.]*\.)*',  # Lettered sub-clauses
        r'\n\s*[IVX]+\.\s*[A-Z][^.]*\.(?:[^.]*\.)*',  # Roman numeral clauses
        r'WHEREAS[^;]*;',  # Whereas clauses
        r'NOW, THEREFORE[^.]*\.',  # Therefore clauses
    ]
    
    clause_types = {
        'definitions': ['definition', 'means', 'shall mean', 'defined as'],
        'payment': ['payment', 'fee', 'compensation', 'salary', 'remuneration', 'cost'],
        'termination': ['terminate', 'termination', 'end', 'expiry', 'expire'],
        'confidentiality': ['confidential', 'non-disclosure', 'proprietary', 'secret'],
        'liability': ['liability', 'liable', 'damages', 'loss', 'harm', 'responsible'],
        'warranty': ['warranty', 'warrant', 'guarantee', 'represent', 'representation'],
        'intellectual_property': ['intellectual property', 'copyright', 'trademark', 'patent'],
        'governing_law': ['governing law', 'jurisdiction', 'court', 'applicable law'],
        'force_majeure': ['force majeure', 'act of god', 'unforeseeable', 'beyond control'],
        'amendment': ['amendment', 'modify', 'change', 'alter', 'update']
    }
    
    # Simple clause extraction based on paragraphs
    paragraphs = text.split('\n\n')
    
    for i, paragraph in enumerate(paragraphs):
        if len(paragraph.strip()) > 50:  # Ignore very short paragraphs
            clause_type = 'general'
            
            # Categorize clause
            for category, keywords in clause_types.items():
                if any(keyword.lower() in paragraph.lower() for keyword in keywords):
                    clause_type = category
                    break
            
            clauses.append({
                'id': i + 1,
                'text': paragraph.strip(),
                'type': clause_type,
                'simplified': simplify_clause(paragraph.strip()),
                'entities': extract_named_entities(paragraph.strip())
            })
    
    return clauses

def classify_document_type(text: str) -> tuple:
    """
    Classify the type of legal document using keyword analysis
    """
    document_types = {
        'nda': ['non-disclosure', 'confidentiality', 'proprietary information', 'trade secret'],
        'employment_contract': ['employment', 'employee', 'employer', 'salary', 'job title', 'work duties'],
        'service_agreement': ['service', 'services', 'provider', 'client', 'deliverables', 'scope of work'],
        'lease_agreement': ['lease', 'rent', 'tenant', 'landlord', 'premises', 'property'],
        'purchase_agreement': ['purchase', 'sale', 'buyer', 'seller', 'goods', 'merchandise'],
        'license_agreement': ['license', 'licensor', 'licensee', 'intellectual property', 'usage rights'],
        'partnership_agreement': ['partnership', 'partner', 'joint venture', 'profit sharing'],
        'loan_agreement': ['loan', 'borrower', 'lender', 'interest', 'repayment', 'principal'],
        'merger_agreement': ['merger', 'acquisition', 'consolidation', 'shareholders'],
        'settlement_agreement': ['settlement', 'dispute', 'resolution', 'claims', 'release']
    }
    
    text_lower = text.lower()
    scores = {}
    
    for doc_type, keywords in document_types.items():
        score = sum(1 for keyword in keywords if keyword in text_lower)
        scores[doc_type] = score / len(keywords)  # Normalize by number of keywords
    
    # Get the type with highest score
    best_type = max(scores, key=scores.get)
    confidence = scores[best_type]
    
    # If confidence is too low, classify as 'other'
    if confidence < 0.1:
        return 'other', 0.0
    
    return best_type, confidence

# --- API Endpoints ---
@app.post("/upload/")
async def upload_document_endpoint(file: UploadFile = File(...)):
    try:
        if index is None:
            # Store document info without vector indexing
            text = parse_document(file)
            if file.filename not in [doc['name'] for doc in processed_documents]:
                processed_documents.append({
                    "name": file.filename, 
                    "status": "Processed (Local storage - Pinecone unavailable)",
                    "content": text[:1000] + "..." if len(text) > 1000 else text  # Store first 1000 chars
                })
            return {"filename": file.filename, "status": "Stored locally - Pinecone unavailable"}
        
        text = parse_document(file)
        chunks = split_text(text)
        embeddings = embedding_model.encode(chunks).tolist()
        
        vectors = [{"id": f"{file.filename}-{i}", "values": emb, "metadata": {"text": chunk, "filename": file.filename}} for i, (chunk, emb) in enumerate(zip(chunks, embeddings))]
        index.upsert(vectors=vectors)

        if file.filename not in [doc['name'] for doc in processed_documents]:
            processed_documents.append({"name": file.filename, "status": "Processed"})

        return {"filename": file.filename, "status": "Successfully indexed."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/query/")
async def query_endpoint(request: QueryRequest):
    try:
        if index is None:
            # Simple text search in stored documents
            matching_docs = []
            query_lower = request.question.lower()
            
            for doc in processed_documents:
                if 'content' in doc:
                    content_lower = doc['content'].lower()
                    if any(word in content_lower for word in query_lower.split()):
                        matching_docs.append(doc)
            
            if matching_docs:
                answer = "Based on your uploaded documents (Pinecone unavailable, using simple text matching):\n\n"
                for i, doc in enumerate(matching_docs[:2], 1):
                    answer += f"{i}. From {doc['name']}: {doc['content'][:200]}...\n\n"
                answer += f"This information relates to your question: '{request.question}'"
            else:
                answer = "No relevant documents found using simple text matching. Note: Pinecone vector search is currently unavailable."
            
            return {"question": request.question, "answer": answer}
        
        question_embedding = embedding_model.encode([request.question])[0].tolist()
        query_results = index.query(vector=question_embedding, top_k=4, include_metadata=True)
        context = "\n---\n".join([match['metadata']['text'] for match in query_results['matches']])
        
        prompt = f"Based on the following document context, answer the question.\n\nContext:\n{context}\n\nQuestion: {request.question}\n\nAnswer:"
        
        # Use context-based answering without heavy language models
        relevant_chunks = [match['metadata']['text'] for match in query_results['matches']]
        
        # Create a comprehensive answer from the most relevant chunks
        if relevant_chunks:
            answer = "Based on your legal documents, here's the relevant information:\n\n"
            for i, chunk in enumerate(relevant_chunks[:2], 1):  # Use top 2 most relevant chunks
                answer += f"{i}. {chunk.strip()}\n\n"
            
            # Add a summary line
            answer += f"This information was found in response to your question: '{request.question}'"
        else:
            answer = "I couldn't find relevant information in your documents for this question. Please try rephrasing or ensure the document contains information about this topic."
        
        return {"question": request.question, "answer": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/documents/")
async def list_documents_endpoint():
    return {"documents": processed_documents}

# --- Advanced Legal Analysis Endpoints ---

@app.post("/analyze-document/")
async def analyze_document_endpoint(file: UploadFile = File(...)):
    """
    Comprehensive document analysis including type classification, clause extraction, 
    entity recognition, and clause simplification
    """
    try:
        text = parse_document(file)
        
        # Document type classification
        doc_type, confidence = classify_document_type(text)
        
        # Extract clauses
        extracted_clauses = extract_clauses(text)
        
        # Extract entities from the entire document
        all_entities = extract_named_entities(text)
        
        # Simplify all clauses
        simplified_clauses = []
        for clause in extracted_clauses:
            simplified_clauses.append({
                'original': clause['text'],
                'simplified': clause['simplified'],
                'type': clause['type'],
                'entities': clause['entities']
            })
        
        # Store the analysis
        if file.filename not in [doc['name'] for doc in processed_documents]:
            processed_documents.append({
                "name": file.filename, 
                "status": "Analyzed",
                "document_type": doc_type,
                "confidence": confidence,
                "clauses_count": len(extracted_clauses),
                "entities_count": sum(len(v) for v in all_entities.values())
            })
        
        response = DocumentAnalysisResponse(
            filename=file.filename,
            document_type=doc_type,
            confidence=confidence,
            simplified_clauses=simplified_clauses,
            extracted_entities=all_entities,
            clauses=extracted_clauses
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/simplify-clause/")
async def simplify_clause_endpoint(request: SimplifyRequest):
    """
    Simplify a specific clause into layman-friendly language
    """
    try:
        simplified = simplify_clause(request.text)
        return {
            "original": request.text,
            "simplified": simplified,
            "entities": extract_named_entities(request.text)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/extract-entities/")
async def extract_entities_endpoint(request: NERRequest):
    """
    Extract named entities from legal text
    """
    try:
        entities = extract_named_entities(request.text)
        return {
            "text": request.text,
            "entities": entities,
            "total_entities": sum(len(v) for v in entities.values())
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/extract-clauses/")
async def extract_clauses_endpoint(request: ClauseExtractionRequest):
    """
    Extract and categorize clauses from legal text
    """
    try:
        clauses = extract_clauses(request.text)
        
        # Categorize clauses by type
        clause_categories = {}
        for clause in clauses:
            category = clause['type']
            if category not in clause_categories:
                clause_categories[category] = []
            clause_categories[category].append(clause)
        
        return {
            "text": request.text,
            "clauses": clauses,
            "total_clauses": len(clauses),
            "categories": clause_categories,
            "category_counts": {k: len(v) for k, v in clause_categories.items()}
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/classify-document/")
async def classify_document_endpoint(file: UploadFile = File(...)):
    """
    Classify the type of legal document
    """
    try:
        text = parse_document(file)
        doc_type, confidence = classify_document_type(text)
        
        return {
            "filename": file.filename,
            "document_type": doc_type,
            "confidence": confidence,
            "classification_details": {
                "certainty": "high" if confidence > 0.5 else "medium" if confidence > 0.2 else "low",
                "suggested_actions": get_document_suggestions(doc_type)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def get_document_suggestions(doc_type: str) -> List[str]:
    """
    Get suggested review points based on document type
    """
    suggestions = {
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
        ],
        'other': [
            "Review all key terms and conditions",
            "Check liability and indemnification clauses",
            "Verify governing law and dispute resolution"
        ]
    }
    
    return suggestions.get(doc_type, suggestions['other'])