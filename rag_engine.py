import os
import requests
import streamlit as st
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_qdrant import Qdrant
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, Filter, FieldCondition, MatchValue
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

# --- FUNZIONE MAGICA PER LE CHIAVI ---
# Controlla prima il file .env (locale), poi i Segreti di Streamlit (Cloud)
def get_key(key_name):
    return os.getenv(key_name) or st.secrets.get(key_name, "")

# Recupero sicuro di tutte le chiavi
API_KEY = get_key("OPENAI_API_KEY")
API_BASE = get_key("OPENAI_API_BASE") or "https://openrouter.ai/api/v1"
MODEL_NAME = get_key("MODEL_NAME") or "qwen/qwen-2.5-72b-instruct"
QDRANT_URL = get_key("QDRANT_URL")
QDRANT_API_KEY = get_key("QDRANT_API_KEY")
SERPER_API_KEY = get_key("SERPER_API_KEY")

# 1. Connessione a Qdrant Cloud
client = QdrantClient(
    url=QDRANT_URL,
    api_key=QDRANT_API_KEY,
)

# 2. Embeddings gratuiti e locali (ottimi per l'italiano, non consumano API)
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")

# 3. Inizializza o recupera la collezione nel cloud
collection_name = "agenzia_knowledge"
try:
    client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=384, distance=Distance.COSINE), # 384 è la dimensione del modello MiniLM
    )
except Exception:
    pass # La collezione esiste già, ignoriamo l'errore

vectorstore = Qdrant(
    client=client,
    collection_name=collection_name,
    embeddings=embeddings,
)

# 4. Modello LLM (Qwen via OpenRouter/Groq)
llm = ChatOpenAI(
    model=MODEL_NAME,
    api_key=API_KEY,       # Passata esplicitamente per evitare errori su Streamlit Cloud
    base_url=API_BASE,     # Passata esplicitamente
    temperature=0.2        # Temperatura bassa per risposte coerenti e strutturate
)

def add_document(client_id: str, text: str, doc_type: str = "generico"):
    """Spezzetta e salva un testo (da Brand Book, Link, Note) nel database del cliente."""
    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
    chunks = splitter.split_text(text)
    
    metadatas = [{"client_id": client_id, "type": doc_type} for _ in chunks]
    vectorstore.add_texts(texts=chunks, metadatas=metadatas)
    
    return f"✅ Salvati {len(chunks)} blocchi di memoria per '{client_id}'."

def get_client_context(client_id: str, query: str, k: int = 5):
    """Recupera le informazioni e le regole stilistiche più rilevanti per un cliente specifico."""
    docs = vectorstore.similarity_search(
        query, 
        k=k, 
        filter=Filter(must=[FieldCondition(key="client_id", match=MatchValue(value=client_id))])
    )
    if not docs:
        return "Nessuna informazione specifica trovata per questo cliente nel database."
    
    # Unisce tutti i pezzi di testo trovati in un unico contesto leggibile
    return "\n\n---\n\n".join([doc.page_content for doc in docs])

def web_search(query: str, num_results: int = 3):
    """Cerca sul web usando Serper.dev per ottenere informazioni aggiornate (trend, competitor, ecc.)"""
    if not SERPER_API_KEY:
        return "⚠️ Chiave SERPER_API_KEY non trovata. Configura la ricerca web nelle impostazioni."
    
    url = "https://google.serper.dev/search"
    payload = {"q": query, "num": num_results}
    headers = {"X-API-KEY": SERPER_API_KEY, "Content-Type": "application/json"}
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            results = response.json().get("organic", [])
            return "\n".join([f"- {r.get('title')}: {r.get('snippet')}" for r in results])
        return f"Errore nella ricerca Serper: {response.status_code}"
    except Exception as e:
        return f"Errore di connessione nella ricerca web: {str(e)}"

def save_and_teach(client_id: str, original_text: str, modified_text: str):
    """Analizza la correzione umana, estrae la regola stilistica e la salva nel DB come 'regola_stile'."""
    prompt = PromptTemplate.from_template(
        "Sei un Brand Strategist esperto. Il sistema AI ha generato questo testo/struttura:\n'{original}'\n"
        "L'editor umano lo ha corretto/modificato in questo modo:\n'{modified}'\n"
        "Analizza le differenze e estrai 1 o 2 regole stilistiche o strutturali pratiche e concrete che spiegano questa correzione. "
        "Esempio: 'Usa sempre elenchi puntati per i benefici', 'Non usare emoji', 'Mantieni il tono formale dando del Lei'. "
        "Rispondi SOLO con le regole estratte, senza premesse, senza virgolette e senza saluti."
    )
    
    chain = prompt | llm
    rule_extracted = chain.invoke({"original": original_text, "modified": modified_text}).content.strip()
    
    # Salva la regola estratta nel database vettoriale
    add_document(client_id, rule_extracted, doc_type="regola_stile")
    
    return f"🧠 Regola appresa e salvata nel profilo di '{client_id}':\n\n{rule_extracted}"