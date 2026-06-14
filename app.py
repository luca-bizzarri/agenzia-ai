import streamlit as st
import pandas as pd
import io
import time
import rag_engine as rag

st.set_page_config(page_title="Agenzia AI Hub", layout="wide", page_icon="🚀")

st.markdown("""
    <style>
    .main-header {font-size: 2.2rem; font-weight: bold; color: #1E88E5; margin-bottom: 0.5rem;}
    .sub-header {font-size: 1.1rem; color: #555; margin-bottom: 1.5rem;}
    </style>
""", unsafe_allow_html=True)

# ==========================================
# SIDEBAR: GESTIONE CLIENTI
# ==========================================
st.sidebar.title("🏢 Agenzia AI Hub")

all_clients = rag.get_all_clients()
client_options = ["➕ CREA NUOVO CLIENTE..."] + all_clients
selected_option = st.sidebar.selectbox("👤 Seleziona Cliente", client_options, key="client_selector")

client_id = ""

if selected_option == "➕ CREA NUOVO CLIENTE...":
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🆕 Nuovo Cliente")
    
    new_client_id = st.sidebar.text_input(
        "ID Cliente (es. Nike, Mario_Rossi, ACME_Corp)", 
        key="new_client_input",
        help="Le maiuscole verranno mantenute. Usa '_' al posto degli spazi."
    ).strip().replace(" ", "_")
    
    if st.sidebar.button("✅ CREA CLIENTE", type="primary", use_container_width=True):
        if not new_client_id:
            st.sidebar.error("⚠️ Inserisci un ID per il cliente")
        elif new_client_id in all_clients:
            st.sidebar.warning(f"Il cliente '{new_client_id}' esiste già.")
        else:
            with st.sidebar.spinner(f"Creazione cliente '{new_client_id}' in corso..."):
                success_registry = rag.register_client(new_client_id)
                rag.add_document(new_client_id, f"Cliente {new_client_id} inizializzato nel sistema.", doc_type="sistema")
                
                if success_registry:
                    st.sidebar.success(f"✅ Cliente '{new_client_id}' creato!")
                    st.sidebar.info("Aggiornamento menu...")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.sidebar.error("❌ Errore nella creazione del cliente.")
else:
    client_id = selected_option
    st.sidebar.markdown("---")
    st.sidebar.success(f"🟢 Cliente attivo: **{client_id}**")

if client_id:
    st.sidebar.markdown("---")
    with st.sidebar.expander("⚠️ Elimina Cliente"):
        st.warning(f"Stai per eliminare **TUTTI** i dati di '{client_id}'. Azione irreversibile.")
        confirm_text = st.text_input(
            f"Per confermare, scrivi esattamente: {client_id}", 
            key="delete_confirm"
        )
        
        if st.button(f"🗑️ ELIMINA '{client_id}'", type="secondary", use_container_width=True):
            if confirm_text.strip() == client_id:
                with st.spinner("Eliminazione in corso..."):
                    success, message = rag.delete_client(client_id)
                    if success:
                        st.success(f"✅ Cliente '{client_id}' eliminato definitivamente.")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(f"❌ Errore Qdrant: {message}")
            else:
                st.error("❌ Testo non corrispondente. Eliminazione bloccata.")

if not client_id:
    st.markdown('<div class="main-header">Benvenuto in Agenzia AI Hub</div>', unsafe_allow_html=True)
    st.info("👈 Seleziona un cliente dal menu a sinistra o creane uno nuovo per iniziare.")
    st.stop()

# ==========================================
# MAIN AREA
# ==========================================
st.markdown(f'<div class="main-header">Dashboard: {client_id}</div>', unsafe_allow_html=True)

task_type = st.radio("🤖 Scegli l'Agente", [
    "📅 Piano Editoriale Completo", 
    "🔍 Analisi Competitor / Trend", 
    "🧠 Carica Documenti/Link Cliente"
], horizontal=True)

st.markdown("---")

if task_type == "🧠 Carica Documenti/Link Cliente":
    st.markdown('<div class="sub-header">Alimenta la memoria e le regole stilistiche del cliente</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    with col1:
        doc_text = st.text_area("Incolla qui testo da Brand Book, Link, Note call o vecchi copy di esempio:", height=300, key="doc_text_area")
    with col2:
        doc_type = st.selectbox("Tipo di documento", ["brand_book", "vecchi_copy", "note_call", "link_referenza", "regole_negative", "sistema"])
        st.info("💡 Consiglio: Incolla 2-3 esempi di copy che il cliente ama. L'AI imparerà lo stile.")
    
    if st.button("💾 Salva nella Memoria", type="primary"):
        if doc_text.strip():
            with st.spinner("Elaborazione e salvataggio in corso..."):
                result = rag.add_document(client_id, doc_text, doc_type)
                st.success(result)
        else:
            st.warning("Inserisci del testo prima di salvare.")

elif task_type == "📅 Piano Editoriale Completo":
    st.markdown('<div class="sub-header">Genera un piano editoriale completo rispettando il tono di voce del cliente</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        mese = st.text_input("📅 Mese/Periodo", "Novembre 2024")
        obiettivo = st.selectbox("🎯 Obiettivo Principale", ["Brand Awareness", "Lead Generation", "Lancio Prodotto", "Fidelizzazione", "Engagement"])
    with col2:
        tema = st.text_input("💡 Tema Centrale o Campagna", "Es. Lancio collezione invernale")
        canali = st.multiselect("📱 Canali", ["LinkedIn", "Instagram", "Facebook", "TikTok", "Newsletter"], default=["LinkedIn", "Instagram"])

    istruzioni_extra = st.text_area("📝 Istruzioni specifiche (Opzionale)", placeholder="Es. Il cliente odia la parola 'sinergia', usa un tono più diretto.")

    if st.button("🚀 Genera Bozza Piano Editoriale", type="primary"):
        with st.spinner("L'Agente Creativo sta lavorando..."):
            context = rag.get_client_context(client_id, f"regole stilistiche, tono di voce, brand book, informazioni su {tema}")
            
            prompt_pe = f"""Sei un Social Media Manager e Brand Strategist esperto. Genera un Piano Editoriale completo in formato CSV STRICT (senza codice markdown, senza spiegazioni, solo testo separato da virgole).
Le colonne DEVONO essere esattamente queste: Data, Canale, Formato, Tema/Angolo, Hook, Copy, CTA, Brief Visivo.

CONTESTO CLIENTE (Regole da rispettare tassativamente):
{context}

RICHIESTA:
- Mese: {mese}
- Obiettivo: {obiettivo}
- Tema: {tema}