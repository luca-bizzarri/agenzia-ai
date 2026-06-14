import os
import requests
import streamlit as st
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.prompts import PromptTemplate
from langchain_qdrant import Qdrant
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, Filter, FieldCondition, MatchValue, PointStruct
from langchain_text_splitters import RecursiveCharacterTextSplitter
import uuid

# --- FUNZIONE MAGICA PER LE CHIAVI ---
def get_key(key_name):
    return os.getenv(key_name) or st.secrets.get(key_name, "")

API_KEY = get_key("OPENAI_API_KEY")
API_BASE = get_key("OPENAI_API_BASE") or "https://openrouter.ai/api/v1"
MODEL_NAME = get_key("MODEL_NAME") or "qwen/qwen-2.5-72b-instruct"
QDRANT_URL = get_key("QDRANT_URL")
QDRANT_API_KEY = get_key("QDRANT_API_KEY")
SERPER_API_KEY = get_key("SERPER_API_KEY")

# 1. Connessione a Qdrant Cloud
client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)

# 2. Embeddings VIA API
embeddings = OpenAIEmbeddings(
    model="nomic-ai/nomic-embed-text-v1.5",
    openai_api_key=API_KEY,
    openai_api_base=API_BASE,
    dimensions=768 
)

# 3. DUE COLLEZIONI SEPARATE
collection_knowledge = "agenzia_knowledge"
collection_registry = "client_registry"

try:
    client.create_collection(
        collection_name=collection_knowledge,
        vectors_config=VectorParams(size=768, distance=Distance.COSINE),
    )
except Exception:
    pass

try:
    client.create_collection(
        collection_name=collection_registry,
        vectors_config=VectorParams(size=4, distance=Distance.COSINE),
    )
except Exception:
    pass

vectorstore = Qdrant(
    client=client,
    collection_name=collection_knowledge,
    embeddings=embeddings,
)

# 4. Modello LLM
llm = ChatOpenAI(
    model=MODEL_NAME,
    api_key=API_KEY,
    base_url=API_BASE,
    temperature=0.2
)

# ==========================================
# GESTIONE REGISTRO CLIENTI
# ==========================================
def _clean_id(client_id: str) -> str:
    return str(client_id).strip().replace(" ", "_")

def get_all_clients():
    try:
        records, _ = client.scroll(
            collection_name=collection_registry,
            limit=1000,
            with_payload=True,
            with_vectors=False
        )
        clients = []
        for record in records:
            if record.payload and record.payload.get("client_id"):
                clients.append(record.payload.get("client_id"))
        return sorted(clients)
    except Exception as e:
        return []

def register_client(client_id: str):
    client_id_clean = _clean_id(client_id)
    point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, client_id_clean))
    
    point = PointStruct(
        id=point_id,
        vector=[0.1, 0.1, 0.1, 0.1],
        payload={"client_id": client_id_clean}
    )
    
    try:
        client.upsert(collection_name=collection_registry, points=[point])
        return True
    except Exception:
        return False

# ==========================================
# GESTIONE CONTENUTI
# ==========================================
def add_document(client_id: str, text: str, doc_type: str = "generico"):
    client_id_clean = _clean_id(client_id)
    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
    chunks = splitter.split_text(text)
    metadatas = [{"client_id": client_id_clean, "type": doc_type} for _ in chunks]
    vectorstore.add_texts(texts=chunks, metadatas=metadatas)
    return f"✅ Salvati {len(chunks)} blocchi di memoria per '{client_id_clean}'."

def get_client_context(client_id: str, query: str, k: int = 5):
    client_id_clean = _clean_id(client_id)
    docs = vectorstore.similarity_search(
        query, 
        k=k, 
        filter=Filter(must=[FieldCondition(key="client_id", match=MatchValue(value=client_id_clean))])
    )
    if not docs:
        return "Nessuna informazione specifica trovata per questo cliente nel database."
    return "\n\n---\n\n".join([doc.page_content for doc in docs])

def web_search(query: str, num_results: int = 3):
    if not SERPER_API_KEY:
        return "⚠️ Chiave SERPER_API_KEY non trovata."
    
    url = "https://google.serper.dev/search"
    payload = {"q": query, "num": num_results}
    headers = {"X-API-KEY": SERPER_API_KEY, "Content-Type": "application/json"}
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            results = response.json().get("organic", [])
            return "\n".join([f"- {r.get('title')}: {r.get('snippet')}" for r in results])
        return f"Errore Serper: {response.status_code}"
    except Exception as e:
        return f"Errore di connessione: {str(e)}"

def save_and_teach(client_id: str, original_text: str, modified_text: str):
    prompt = PromptTemplate.from_template(
        "Sei un Brand Strategist esperto. Il sistema AI ha generato questo testo/struttura:\n'{original}'\n"
        "L'editor umano lo ha corretto/modificato in questo modo:\n'{modified}'\n"
        "Analizza le differenze e estrai 1 o 2 regole stilistiche o strutturali pratiche e concrete che spiegano questa correzione. "
        "Rispondi SOLO con le regole estratte, senza premesse, senza virgolette e senza saluti."
    )
    chain = prompt | llm
    rule_extracted = chain.invoke({"original": original_text, "modified": modified_text}).content.strip()
    add_document(client_id, rule_extracted, doc_type="regola_stile")
    return f"🧠 Regola appresa e salvata per '{client_id}':\n\n{rule_extracted}"

def delete_client(client_id: str):
    """ELIMINA COMPLETAMENTE un cliente. Restituisce (True/False, Messaggio di errore o successo)"""
    client_id_clean = _clean_id(client_id)
    try:
        # 1. Elimina dalla knowledge base
        client.delete(
            collection_name=collection_knowledge,
            points_selector=Filter(must=[FieldCondition(key="client_id", match=MatchValue(value=client_id_clean))])
        )
        # 2. Elimina dal registro
        client.delete(
            collection_name=collection_registry,
            points_selector=Filter(must=[FieldCondition(key="client_id", match=MatchValue(value=client_id_clean))])
        )
        return True, "Eliminato con successo"
    except Exception as e:
        # QUI CATTURIAMO L'ERRORE REALE E LO RESTITUIAMO ALL'APP
        return False, str(e)