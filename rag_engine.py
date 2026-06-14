import os
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_qdrant import Qdrant
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, Filter, FieldCondition, MatchValue
from langchain_community.embeddings import HuggingFaceEmbeddings
from dotenv import load_dotenv

load_dotenv()

# 1. Connessione a Qdrant Cloud
client = QdrantClient(
    url=os.getenv("QDRANT_URL"),
    api_key=os.getenv("QDRANT_API_KEY"),
)

# 2. Embeddings gratuiti e locali (non consumano API, ottimi per l'italiano)
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")

# 3. Inizializza o crea la collezione nel cloud
collection_name = "agenzia_knowledge"
# Tentativo di creare la collezione se non esiste (ignora errore se esiste già)
try:
    client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=384, distance=Distance.COSINE), # 384 è la dimensione del modello MiniLM
    )
except Exception:
    pass # La collezione esiste già

vectorstore = Qdrant(
    client=client,
    collection_name=collection_name,
    embeddings=embeddings,
)

# 4. Modello LLM (Qwen)
llm = ChatOpenAI(
    model=os.getenv("MODEL_NAME", "qwen/qwen-2.5-72b-instruct"),
    openai_api_key=os.getenv("OPENAI_API_KEY"),
    openai_api_base=os.getenv("OPENAI_API_BASE"),
    temperature=0.2
)

def add_document(client_id: str, text: str, doc_type: str = "generico"):
    """Salva un testo nel database cloud associandolo al cliente."""
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    
    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
    chunks = splitter.split_text(text)
    
    metadatas = [{"client_id": client_id, "type": doc_type} for _ in chunks]
    vectorstore.add_texts(texts=chunks, metadatas=metadatas)
    return f"✅ Salvati {len(chunks)} blocchi di memoria per '{client_id}'."

def get_client_context(client_id: str, query: str, k: int = 5):
    """Recupera le informazioni e le regole specifiche del cliente."""
    docs = vectorstore.similarity_search(
        query, 
        k=k, 
        filter=Filter(must=[FieldCondition(key="client_id", match=MatchValue(value=client_id))])
    )
    if not docs:
        return "Nessuna informazione specifica trovata per questo cliente."
    
    return "\n\n---\n\n".join([doc.page_content for doc in docs])

def save_and_teach(client_id: str, original_text: str, modified_text: str):
    """Analizza la correzione, estrae la regola e la salva come 'regola_stile'."""
    prompt = PromptTemplate.from_template(
        "Sei un Brand Strategist esperto. Il sistema AI ha generato questo testo/struttura:\n'{original}'\n"
        "L'editor umano lo ha corretto/modificato in questo modo:\n'{modified}'\n"
        "Analizza le differenze e estrai 1 o 2 regole stilistiche o strutturali pratiche e concrete che spiegano questa correzione. "
        "Esempio: 'Usa sempre elenchi puntati per i benefici', 'Non usare emoji', 'Mantieni il tono formale dando del Lei'. "
        "Rispondi SOLO con le regole estratte, senza premesse, senza virgolette e senza saluti."
    )
    
    chain = prompt | llm
    rule_extracted = chain.invoke({"original": original_text, "modified": modified_text}).content.strip()
    
    # Salva la regola estratta nel DB
    add_document(client_id, rule_extracted, doc_type="regola_stile")
    return f"🧠 Regola appresa e salvata nel profilo di '{client_id}':\n\n{rule_extracted}"