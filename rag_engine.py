import os
import requests
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_qdrant import Qdrant
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, Filter, FieldCondition, MatchValue
from langchain_huggingface import HuggingFaceEmbeddings
from dotenv import load_dotenv

# Se vuoi provare l'opzione gratis, decommenta la riga sotto e installa: pip install duckduckgo-search
# from langchain_community.tools import DuckDuckGoSearchRun

load_dotenv()

# 1. Connessione a Qdrant Cloud
client = QdrantClient(
    url=os.getenv("QDRANT_URL"),
    api_key=os.getenv("QDRANT_API_KEY"),
)

# 2. Embeddings gratuiti e locali
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")

# 3. Inizializza collezione
collection_name = "agenzia_knowledge"
try:
    client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=384, distance=Distance.COSINE),
    )
except Exception:
    pass

vectorstore = Qdrant(client=client, collection_name=collection_name, embeddings=embeddings)

# 4. Modello LLM (Qwen)
llm = ChatOpenAI(
    model=os.getenv("MODEL_NAME", "qwen/qwen-2.5-72b-instruct"),
    openai_api_key=os.getenv("OPENAI_API_KEY"),
    openai_api_base=os.getenv("OPENAI_API_BASE"),
    temperature=0.2
)

def add_document(client_id: str, text: str, doc_type: str = "generico"):
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
    chunks = splitter.split_text(text)
    metadatas = [{"client_id": client_id, "type": doc_type} for _ in chunks]
    vectorstore.add_texts(texts=chunks, metadatas=metadatas)
    return f"✅ Salvati {len(chunks)} blocchi di memoria per '{client_id}'."

def get_client_context(client_id: str, query: str, k: int = 5):
    docs = vectorstore.similarity_search(
        query, 
        k=k, 
        filter=Filter(must=[FieldCondition(key="client_id", match=MatchValue(value=client_id))])
    )
    if not docs:
        return "Nessuna informazione specifica trovata per questo cliente."
    return "\n\n---\n\n".join([doc.page_content for doc in docs])

def web_search(query: str, num_results: int = 3):
    """Cerca sul web usando Serper.dev (o DuckDuckGo se preferisci il gratis)"""
    
    # --- METODO SERPER (Consigliato per Agenzie) ---
    api_key = os.getenv("SERPER_API_KEY")
    if api_key:
        url = "https://google.serper.dev/search"
        payload = {"q": query, "num": num_results}
        headers = {"X-API-KEY": api_key, "Content-Type": "application/json"}
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            results = response.json().get("organic", [])
            return "\n".join([f"- {r.get('title')}: {r.get('snippet')}" for r in results])
        return "Errore nella ricerca Serper."

    # --- METODO DUCKDUCKGO (Gratis, fallback) ---
    # else:
    #     search = DuckDuckGoSearchRun(num_results=num_results)
    #     return search.run(query)

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
    return f"🧠 Regola appresa e salvata nel profilo di '{client_id}':\n\n{rule_extracted}"