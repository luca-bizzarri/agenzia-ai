import streamlit as st
import pandas as pd
import io
import rag_engine as rag

st.set_page_config(page_title="Agenzia AI Hub", layout="wide", page_icon="🚀")

# --- STILE CSS PERSONALIZZATO PER RENDERLO PIÙ PROFESSIONALE ---
st.markdown("""
    <style>
    .main-header {font-size: 2.5rem; font-weight: bold; color: #1E88E5; margin-bottom: 1rem;}
    .sub-header {font-size: 1.2rem; color: #555; margin-bottom: 1.5rem;}
    .stTextArea textarea {font-size: 14px;}
    </style>
""", unsafe_allow_html=True)

# --- SIDEBAR: NAVIGAZIONE E CONTESTO ---
st.sidebar.title("🏢 Agenzia AI Hub")
st.sidebar.markdown("Il tuo assistente operativo multi-agente.")

client_id = st.sidebar.text_input("👤 ID Cliente (es. nike, mario_rossi)", value="cliente_test").lower().strip().replace(" ", "_")
task_type = st.sidebar.radio("🤖 Scegli l'Agente", [
    "📅 Piano Editoriale Completo", 
    "🔍 Analisi Competitor / Trend", 
    "🧠 Carica Documenti/Link Cliente"
])

st.sidebar.markdown("---")
st.sidebar.info(f"Memoria attiva per: **{client_id}**")

# --- MAIN AREA ---
st.markdown('<div class="main-header">Dashboard Operativa</div>', unsafe_allow_html=True)

# ==========================================
# AGENTE 1: CARICA DOCUMENTI / LINK
# ==========================================
if task_type == "🧠 Carica Documenti/Link Cliente":
    st.markdown('<div class="sub-header">Alimenta la memoria e le regole stilistiche del cliente</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    with col1:
        doc_text = st.text_area("Incolla qui testo da Brand Book, Link, Note call o vecchi copy di esempio:", height=300)
    with col2:
        doc_type = st.selectbox("Tipo di documento", ["brand_book", "vecchi_copy", "note_call", "link_referenza", "regole_negative"])
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
        mese = st.text_input("📅 Mese/Periodo", "Ottobre 2024")
        obiettivo = st.selectbox("🎯 Obiettivo Principale", ["Brand Awareness", "Lead Generation", "Lancio Prodotto", "Fidelizzazione", "Engagement"])
    with col2:
        tema = st.text_input("💡 Tema Centrale o Campagna", "Es. Lancio collezione autunnale")
        canali = st.multiselect("📱 Canali", ["LinkedIn", "Instagram", "Facebook", "TikTok", "Newsletter"], default=["LinkedIn", "Instagram"])

    istruzioni_extra = st.text_area("📝 Istruzioni specifiche o correzioni da applicare (Opzionale)", placeholder="Es. Il cliente odia la parola 'sinergia', usa un tono più diretto, evita emoji.")

    if st.button("🚀 Genera Bozza Piano Editoriale", type="primary"):
        with st.spinner("L'Agente Creativo sta lavorando... (Recupero contesto cliente + Generazione tabella)"):
            # 1. Recupera contesto (regole stilistiche, brand book, ecc.)
            context = rag.get_client_context(client_id, f"regole stilistiche, tono di voce, brand book, informazioni su {tema}")
            
            # 2. Prompt per il Piano Editoriale (forziamo l'output CSV per la tabella modificabile)
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

Genera 6 idee di post complete. Assicurati che il Copy rispetti le regole stilistiche del contesto cliente. Se ci sono virgole nel testo del copy, racchiudi il testo tra virgolette doppie per non rompere il CSV.
Rispondi SOLO con il CSV, includendo l'intestazione delle colonne come prima riga.
"""
            
            response = rag.llm.invoke(prompt_pe).content
            
            # 3. Pulizia e visualizzazione
            try:
                # Rimuove eventuali blocchi di codice markdown se l'AI li ha aggiunti
                clean_response = response.replace("```csv", "").replace("```", "").strip()
                
                df = pd.read_csv(io.StringIO(clean_response))
                
                # Salviamo l'originale nella sessione per il confronto futuro (Opzione B)
                st.session_state['original_pe'] = clean_response
                st.session_state['current_pe_df'] = df
                
                st.success("✅ Bozza generata! Puoi modificare le celle direttamente nella tabella qui sotto.")
                st.data_editor(df, num_rows="dynamic", key="editable_df", height=500, use_container_width=True)
                
            except Exception as e:
                st.error("⚠️ Errore nel formato della risposta dell'AI. Ecco l'output grezzo per debug:")
                st.code(response)
                st.session_state['original_pe'] = response

    # --- SEZIONE SALVA E INSEGNA (OPZIONE B) ---
    if 'current_pe_df' in st.session_state:
        st.markdown("---")
        st.markdown("### 🧠 Revisione e Apprendimento")
        st.write("Se hai modificato la tabella sopra (es. cambiato tono, accorciato frasi, tolto emoji), clicca qui sotto. L'AI analizzerà le tue correzioni e imparerà la regola per le prossime volte.")
        
        if st.button("💾 Salva e Insegna (Opzione B)", type="secondary"):
            with st.spinner("L'Agente Analista sta confrontando le versioni ed estraendo le regole..."):
                modified_df = st.session_state['editable_df']
                modified_csv = modified_df.to_csv(index=False)
                original_csv = st.session_state['original_pe']
                
                result = rag.save_and_teach(client_id, original_csv, modified_csv)
                st.success(result)
                st.info("La prossima volta che genererai un piano per questo cliente, queste regole verranno applicate automaticamente dal motore RAG.")

# ==========================================
# AGENTE 3: ANALISI COMPETITOR / TREND
# ==========================================
elif task_type == "🔍 Analisi Competitor / Trend":
    st.markdown('<div class="sub-header">Ricerva sul web trend attuali o analizza competitor specifici</div>', unsafe_allow_html=True)
    
    query_ricerca = st.text_input("🔍 Cosa vuoi cercare? (es. 'trend marketing B2B ottobre 2024' o 'ultime campagne [Nome Competitor]')")
    num_result = st.slider("Numero di fonti da analizzare", 3, 10, 5)
    
    if st.button("🌐 Avvia Ricerca Web", type="primary"):
        if query_ricerca:
            with st.spinner("L'Agente Ricercatore sta scansionando il web..."):
                # Usa la funzione web_search che abbiamo creato in rag_engine
                search_results = rag.web_search(query_ricerca, num_results=num_result)
                
                if "Errore" in search_results or "⚠️" in search_results:
                    st.warning(search_results)
                else:
                    st.markdown("### 📊 Risultati della Ricerca")
                    st.markdown(search_results)
                    
                    # Bonus: chiedi all'AI di sintetizzare i risultati per il cliente
                    with st.spinner("L'Agente Strategist sta sintetizzando gli insight per il tuo cliente..."):
                        context = rag.get_client_context(client_id, "tono di voce, obiettivi strategici")
                        prompt_sintesi = f"""Sei un Brand Strategist. Ecco i risultati di una ricerca web: 
{search_results}

Il nostro cliente è '{client_id}'. Il suo contesto strategico è:
{context}

Sintetizza questi risultati in 3 insight pratici e azionabili per il prossimo piano editoriale del cliente. Sii concreto.
"""
                        sintesi = rag.llm.invoke(prompt_sintesi).content
                        st.markdown("### 💡 Insight Strategici per il Cliente")
                        st.info(sintesi)
        else:
            st.warning("Inserisci una query di ricerca.")