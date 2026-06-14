import os
import requests
import streamlit as st
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.prompts import PromptTemplate
from langchain_qdrant import Qdrant
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, Filter, FieldCondition, MatchValue, PointStruct, PayloadSchemaType
from langchain_text_splitters import RecursiveCharacterTextSplitter
import uuid

def get_key(key_name):
    return os.getenv(key_name) or st.secrets.get(key_name, "")

API_KEY = get_key("OPENAI_API_KEY")
API_BASE = get_key("OPENAI_API_BASE") or "https://openrouter.ai/api/v1"
MODEL_NAME = get_key("MODEL_NAME") or "qwen/qwen-2.5-72b-instruct"
QDRANT_URL = get_key("QDRANT_URL")
QDRANT_API_KEY = get_key("QDRANT_API_KEY")
SERPER_API_KEY = get_key("SERPER_API_KEY")

client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)

embeddings = OpenAIEmbeddings(
    model="openai/text-embedding-3-small",
    openai_api_key=API_KEY,
    openai_api_base=API_BASE
)

collection_knowledge = "agenzia_knowledge"
collection_registry = "client_registry"

try:
    info = client.get_collection(collection_name=collection_knowledge)
    vector_size = 1536
    if hasattr(info.config.params, 'vectors'):
        if isinstance(info.config.params.vectors, dict):
            first_key = list(info.config.params.vectors.keys())[0]
            vector_size = info.config.params.vectors[first_key].size
        else:
            vector_size = info.config.params.vectors.size
    if vector_size != 1536:
        client.delete_collection(collection_name=collection_knowledge)
        client.create_collection(collection_name=collection_knowledge, vectors_config=VectorParams(size=1536, distance=Distance.COSINE))
except Exception:
    client.create_collection(collection_name=collection_knowledge, vectors_config=VectorParams(size=1536, distance=Distance.COSINE))

try:
    client.create_collection(collection_name=collection_registry, vectors_config=VectorParams(size=4, distance=Distance.COSINE))
except Exception:
    pass

try:
    client.create_payload_index(collection_name=collection_knowledge, field_name="client_id", field_schema=PayloadSchemaType.KEYWORD)
except Exception:
    pass
try:
    client.create_payload_index(collection_name=collection_registry, field_name="client_id", field_schema=PayloadSchemaType.KEYWORD)
except Exception:
    pass

vectorstore = Qdrant(client=client, collection_name=collection_knowledge, embeddings=embeddings)
llm = ChatOpenAI(model=MODEL_NAME, api_key=API_KEY, base_url=API_BASE, temperature=0.2)

def _clean_id(client_id: str) -> str:
    return str(client_id).strip().replace(" ", "_")

def get_all_clients():
    try:
        records, _ = client.scroll(collection_name=collection_registry, limit=1000, with_payload=True, with_vectors=False)
        clients = [record.payload.get("client_id") for record in records if record.payload and record.payload.get("client_id")]
        return sorted(list(set(clients)))
    except Exception:
        return []

def register_client(client_id: str):
    client_id_clean = _clean_id(client_id)
    point = PointStruct(id=str(uuid.uuid5(uuid.NAMESPACE_DNS, client_id_clean)), vector=[0.1, 0.1, 0.1, 0.1], payload={"client_id": client_id_clean})
    try:
        client.upsert(collection_name=collection_registry, points=[point])
        return True
    except Exception:
        return False

def add_document(client_id: str, text: str, doc_type: str = "generico"):
    client_id_clean = _clean_id(client_id)
    if not text or len(text.strip()) < 50:
        return "⚠️ Il testo è troppo breve o vuoto per essere salvato."
    
    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
    chunks = splitter.split_text(text)
    metadatas = [{"client_id": client_id_clean, "type": doc_type} for _ in chunks]
    vectorstore.add_texts(texts=chunks, metadatas=metadatas)
    return f"✅ Salvati {len(chunks)} blocchi per '{client_id_clean}' (Categoria: {doc_type})."

# ==========================================
# FUNZIONE AGGIORNATA CON "RAW COUNT" (VERITÀ ASSOLUTA)
# ==========================================
def get_memory_summary(client_id: str):
    client_id_clean = _clean_id(client_id)
    try:
        # 1. Chiediamo a Qdrant QUANTI elementi ci sono in totale per questo cliente (bypassa cache UI)
        count_result = client.count(
            collection_name=collection_knowledge,
            count_filter=Filter(must=[FieldCondition(key="client_id", match=MatchValue(value=client_id_clean))]),
            exact=True
        )
        total_points = count_result.count
        
        if total_points == 0:
            return {"avviso": f"Nessun dato trovato nel DB per '{client_id_clean}'."}

        # 2. Se ci sono dati, leggiamo le categorie
        records, _ = client.scroll(
            collection_name=collection_knowledge,
            limit=total_points + 100, # Prendiamo tutto senza limiti
            with_payload=True,
            with_vectors=False,
            scroll_filter=Filter(must=[FieldCondition(key="client_id", match=MatchValue(value=client_id_clean))])
        )
        
        summary = {"_totale_punti_db": total_points}
        for record in records:
            doc_type = record.payload.get("type", "generico")
            summary[doc_type] = summary.get(doc_type, 0) + 1
        
        return summary
    except Exception as e:
        return {"errore": str(e)}
# ==========================================

def delete_category(client_id: str, doc_type: str):
    client_id_clean = _clean_id(client_id)
    try:
        client.delete(
            collection_name=collection_knowledge,
            points_selector=Filter(
                must=[
                    FieldCondition(key="client_id", match=MatchValue(value=client_id_clean)),
                    FieldCondition(key="type", match=MatchValue(value=doc_type))
                ]
            )
        )
        return True, f"✅ Categoria '{doc_type}' eliminata con successo."
    except Exception as e:
        return False, f"❌ Errore: {str(e)}"

def get_client_context(client_id: str, query: str, k: int = 8):
    client_id_clean = _clean_id(client_id)
    docs = vectorstore.similarity_search(query, k=k, filter=Filter(must=[FieldCondition(key="client_id", match=MatchValue(value=client_id_clean))]))
    if not docs:
        return "Nessuna informazione trovata."
    return "\n\n---\n\n".join([f"[{doc.metadata.get('type', 'generico')}] {doc.page_content}" for doc in docs])

def web_search(query: str, num_results: int = 3):
    if not SERPER_API_KEY:
        return "⚠️ Chiave SERPER_API_KEY non trovata."
    try:
        response = requests.post("https://google.serper.dev/search", json={"q": query, "num": num_results}, headers={"X-API-KEY": SERPER_API_KEY, "Content-Type": "application/json"})
        if response.status_code == 200:
            return "\n".join([f"- {r.get('title')}: {r.get('snippet')}" for r in response.json().get("organic", [])])
        return f"Errore Serper: {response.status_code}"
    except Exception as e:
        return f"Errore: {str(e)}"

def save_and_teach(client_id: str, original_text: str, modified_text: str):
    prompt = PromptTemplate.from_template("Sei un Brand Strategist. AI ha scritto:\n'{original}'\nUmano ha corretto in:\n'{modified}'\nEstrai 1-2 regole stilistiche concrete. Rispondi SOLO con le regole.")
    rule = (prompt | llm).invoke({"original": original_text, "modified": modified_text}).content.strip()
    add_document(client_id, rule, doc_type="regola_stile")
    return f"🧠 Regola appresa per '{client_id}':\n{rule}"

def delete_client(client_id: str):
    client_id_clean = _clean_id(client_id)
    try:
        client.delete(collection_name=collection_knowledge, points_selector=Filter(must=[FieldCondition(key="client_id", match=MatchValue(value=client_id_clean))]))
        client.delete(collection_name=collection_registry, points_selector=Filter(must=[FieldCondition(key="client_id", match=MatchValue(value=client_id_clean))]))
        return True, "Eliminato"
    except Exception as e:
        return False, str(e)