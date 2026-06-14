import streamlit as st
import pandas as pd
import rag_engine as rag

st.set_page_config(page_title="Agenzia AI Hub", layout="wide")

# --- SIDEBAR ---
st.sidebar.title("🏢 Agenzia AI Hub")
client_id = st.sidebar.text_input("ID Cliente (es. nike, mario_rossi)", value="cliente_test").lower().replace(" ", "_")
task_type = st.sidebar.selectbox("Scegli l'Agente", ["📅 Piano Editoriale Completo", "🧠 Carica Documenti/Link Cliente"])

st.sidebar.markdown("---")
st.sidebar.info(f"Memoria attiva per: **{client_id}**")

# --- MAIN AREA ---
st.title("Dashboard Operativa")

if task_type == "🧠 Carica Documenti/Link Cliente":
    st.subheader("Alimenta la memoria del cliente")
    doc_text = st.text_area("Incolla qui testo da Brand Book, Link, Note call o vecchi copy di esempio:")
    doc_type = st.selectbox("Tipo di documento", ["brand_book", "vecchi_copy", "note_call", "link_referenza"])
    
    if st.button("💾 Salva nella Memoria"):
        if doc_text:
            with st.spinner("Elaborazione e salvataggio in corso..."):
                result = rag.add_document(client_id, doc_text, doc_type)
                st.success(result)
        else:
            st.warning("Inserisci del testo prima di salvare.")

elif task_type == "📅 Piano Editoriale Completo":
    st.subheader("Generatore Piano Editoriale")
    
    col1, col2 = st.columns(2)
    with col1:
        mese = st.text_input("Mese/Periodo", "Ottobre 2024")
        obiettivo = st.selectbox("Obiettivo Principale", ["Brand Awareness", "Lead Generation", "Lancio Prodotto", "Fidelizzazione"])
    with col2:
        tema = st.text_input("Tema Centrale o Campagna", "Es. Lancio collezione autunnale")
        canali = st.multiselect("Canali", ["LinkedIn", "Instagram", "Facebook", "Newsletter"], default=["LinkedIn", "Instagram"])

    istruzioni_extra = st.text_area("Istruzioni specifiche o correzioni da applicare (Opzionale)", placeholder="Es. Il cliente odia la parola 'sinergia', usa un tono più diretto.")

    if st.button("🚀 Genera Bozza Piano Editoriale", type="primary"):
        with st.spinner("L'Agente Creativo sta lavorando... (Recupero contesto cliente + Generazione)"):
            # 1. Recupera contesto
            context = rag.get_client_context(client_id, f"regole stilistiche, tono di voce, informazioni su {tema}")
            
            # 2. Prompt per il Piano Editoriale
            prompt_pe = f"""Sei un Social Media Manager esperto. Genera un Piano Editoriale completo in formato CSV (senza codice markdown, solo testo separato da virgole) con le colonne: Data, Canale, Formato, Tema/Angolo, Hook, Copy, CTA, Brief Visivo.
            
            CONTESTO CLIENTE (Regole da rispettare tassativamente):
            {context}
            
            RICHIESTA:
            - Mese: {mese}
            - Obiettivo: {obiettivo}
            - Tema: {tema}
            - Canali: {', '.join(canali)}
            - Note extra: {istruzioni_extra}
            
            Genera 6 idee di post. Assicurati che il Copy rispetti le regole stilistiche del contesto cliente.
            Rispondi SOLO con il CSV, includendo l'intestazione delle colonne.
            """
            
            response = rag.llm.invoke(prompt_pe).content
            
            # 3. Pulizia e visualizzazione
            try:
                # Tentativo di convertire la risposta in DataFrame
                import io
                df = pd.read_csv(io.StringIO(response))
                
                # Salviamo l'originale nella sessione per il confronto futuro
                st.session_state['original_pe'] = response
                st.session_state['current_pe_df'] = df
                
                st.success("Bozza generata! Puoi modificare le celle direttamente nella tabella qui sotto.")
                st.data_editor(df, num_rows="dynamic", key="editable_df", height=400)
                
            except Exception as e:
                st.error("Errore nel formato della risposta dell'AI. Ecco l'output grezzo:")
                st.code(response)
                st.session_state['original_pe'] = response

    # --- SEZIONE SALVA E INSEGNA ---
    if 'current_pe_df' in st.session_state:
        st.markdown("---")
        st.subheader("Revisione e Apprendimento")
        st.write("Se hai modificato la tabella sopra, clicca qui sotto per insegnare all'AI le tue correzioni.")
        
        if st.button("💾 Salva e Insegna (Opzione B)", type="secondary"):
            with st.spinner("L'Agente Analista sta confrontando le versioni..."):
                modified_df = st.session_state['editable_df']
                modified_csv = modified_df.to_csv(index=False)
                original_csv = st.session_state['original_pe']
                
                result = rag.save_and_teach(client_id, original_csv, modified_csv)
                st.success(result)
                st.info("La prossima volta che genererai un piano per questo cliente, queste regole verranno applicate automaticamente.")