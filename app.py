import streamlit as st
import pandas as pd
import io
import time
import rag_engine as rag

st.set_page_config(page_title="Agenzia AI Hub", layout="wide", page_icon="🚀")

# --- STILE CSS PERSONALIZZATO ---
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

# 1. Recupera lista clienti dal database (ora con la funzione blindata)
all_clients = rag.get_all_clients()

# 2. Menu a tendina per scegliere o creare
client_options = ["➕ CREA NUOVO CLIENTE..."] + all_clients
selected_option = st.sidebar.selectbox("👤 Seleziona Cliente", client_options, key="client_selector")

client_id = ""

# 3. Logica di creazione nuovo cliente
if selected_option == "➕ CREA NUOVO CLIENTE...":
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🆕 Nuovo Cliente")
    
    new_client_id = st.sidebar.text_input(
        "ID Cliente (es. nike, mario_rossi)", 
        key="new_client_input",
        help="Usa solo lettere minuscole, numeri e trattini bassi"
    ).lower().strip().replace(" ", "_")
    
    if st.sidebar.button("✅ CREA CLIENTE", type="primary", use_container_width=True):
        if not new_client_id:
            st.sidebar.error("⚠️ Inserisci un ID per il cliente")
        elif new_client_id in all_clients:
            st.sidebar.warning(f"Il cliente '{new_client_id}' esiste già. Selezionalo dal menu.")
        else:
            with st.sidebar.spinner(f"Creazione cliente '{new_client_id}' in corso..."):
                # Salviamo un documento "sistema" per registrare il cliente
                rag.add_document(new_client_id, f"Cliente {new_client_id} inizializzato nel sistema.", doc_type="sistema")
                
                st.sidebar.success(f"✅ Cliente '{new_client_id}' creato con successo!")
                st.sidebar.info("Aggiornamento della lista in corso...")
                
                # Piccola pausa per assicurare che Qdrant abbia indicizzato il dato
                time.sleep(1.5)
                st.rerun()

else:
    # Cliente esistente selezionato
    client_id = selected_option
    st.sidebar.markdown("---")
    st.sidebar.success(f"🟢 Cliente attivo: **{client_id}**")

# 4. Zona eliminazione sicura (visibile solo se un cliente è selezionato)
if client_id:
    st.sidebar.markdown("---")
    with st.sidebar.expander("⚠️ Elimina Cliente"):
        st.warning(f"Stai per eliminare **TUTTI** i dati di '{client_id}'. Azione irreversibile.")
        confirm_text = st.text_input(
            f"Per confermare, scrivi esattamente: {client_id}", 
            key="delete_confirm"
        )
        
        if st.button(f"🗑️ ELIMINA '{client_id}'", type="secondary", use_container_width=True):
            if confirm_text.strip().lower() == client_id:
                with st.spinner("Eliminazione in corso..."):
                    success = rag.delete_client(client_id)
                    if success:
                        st.success(f"✅ Cliente '{client_id}' eliminato definitivamente.")
                        time.sleep(1.5)
                        st.rerun()
                    else:
                        st.error("❌ Errore durante l'eliminazione.")
            else:
                st.error("❌ Testo di conferma errato. Eliminazione bloccata per sicurezza.")

# 5. Blocco se nessun cliente è selezionato
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

# ==========================================
# AGENTE 1: CARICA DOCUMENTI / LINK
# ==========================================
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

# ==========================================
# AGENTE 2: PIANO EDITORIALE COMPLETO
# ==========================================
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
        with st.spinner("L'Agente Creativo sta lavorando... (Recupero contesto + Generazione)"):
            context = rag.get_client_context(client_id, f"regole stilistiche, tono di voce, brand book, informazioni su {tema}")
            
            prompt_pe = f"""Sei un Social Media Manager e Brand Strategist esperto. Genera un Piano Editoriale completo in formato CSV STRICT (senza codice markdown, senza spiegazioni, solo testo separato da virgole).
Le colonne DEVONO essere esattamente queste: Data, Canale, Formato, Tema/Angolo, Hook, Copy, CTA, Brief Visivo.

CONTESTO CLIENTE (Regole da rispettare tassativamente):
{context}

RICHIESTA:
- Mese: {mese}
- Obiettivo: {obiettivo}
- Tema: {tema}
- Canali: {', '.join(canali)}
- Note extra: {istruzioni_extra}

Genera 6 idee di post complete. Assicurati che il Copy rispetti le regole stilistiche del contesto cliente. Se ci sono virgole nel testo del copy, racchiudi il testo tra virgolette doppie.
Rispondi SOLO con il CSV, includendo l'intestazione delle colonne come prima riga.
"""
            response = rag.llm.invoke(prompt_pe).content
            
            try:
                clean_response = response.replace("```csv", "").replace("```", "").strip()
                df = pd.read_csv(io.StringIO(clean_response))
                
                st.session_state['original_pe'] = clean_response
                st.session_state['current_pe_df'] = df
                
                st.success("✅ Bozza generata! Puoi modificare le celle direttamente nella tabella qui sotto.")
                st.data_editor(df, num_rows="dynamic", key="editable_df", height=500, use_container_width=True)
                
            except Exception as e:
                st.error("⚠️ Errore nel formato CSV. Ecco l'output grezzo:")
                st.code(response)
                st.session_state['original_pe'] = response

    # Sezione Salva e Insegna
    if 'current_pe_df' in st.session_state:
        st.markdown("---")
        st.markdown("### 🧠 Revisione e Apprendimento (Opzione B)")
        st.write("Se hai modificato la tabella, clicca qui sotto. L'AI analizzerà le tue correzioni e imparerà la regola per le prossime volte.")
        
        if st.button("💾 Salva e Insegna", type="secondary"):
            with st.spinner("L'Agente Analista sta confrontando le versioni..."):
                modified_df = st.session_state['editable_df']
                modified_csv = modified_df.to_csv(index=False)
                original_csv = st.session_state['original_pe']
                
                result = rag.save_and_teach(client_id, original_csv, modified_csv)
                st.success(result)

# ==========================================
# AGENTE 3: ANALISI COMPETITOR / TREND
# ==========================================
elif task_type == "🔍 Analisi Competitor / Trend":
    st.markdown('<div class="sub-header">Ricerca sul web trend attuali o analizza competitor specifici</div>', unsafe_allow_html=True)
    
    query_ricerca = st.text_input("🔍 Cosa vuoi cercare? (es. 'trend marketing B2B novembre 2024')")
    num_result = st.slider("Numero di fonti da analizzare", 3, 10, 5)
    
    if st.button("🌐 Avvia Ricerca Web", type="primary"):
        if query_ricerca:
            with st.spinner("L'Agente Ricercatore sta scansionando il web..."):
                search_results = rag.web_search(query_ricerca, num_results=num_result)
                
                if "Errore" in search_results or "⚠️" in search_results:
                    st.warning(search_results)
                else:
                    st.markdown("### 📊 Risultati della Ricerca")
                    st.markdown(search_results)
                    
                    with st.spinner("Sintesi degli insight in corso..."):
                        context = rag.get_client_context(client_id, "tono di voce, obiettivi strategici")
                        prompt_sintesi = f"""Sei un Brand Strategist. Ecco i risultati di una ricerca web: 
{search_results}
Il nostro cliente è '{client_id}'. Contesto strategico: {context}
Sintetizza questi risultati in 3 insight pratici e azionabili per il prossimo piano editoriale. Sii concreto.
"""
                        sintesi = rag.llm.invoke(prompt_sintesi).content
                        st.markdown("### 💡 Insight Strategici per il Cliente")
                        st.info(sintesi)
        else:
            st.warning("Inserisci una query di ricerca.")