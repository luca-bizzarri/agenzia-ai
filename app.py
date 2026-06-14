import streamlit as st
import pandas as pd
import io
import time
import rag_engine as rag
import PyPDF2
import docx

st.set_page_config(page_title="Agenzia AI Hub", layout="wide", page_icon="🚀")

st.markdown("""
    <style>
    .main-header {font-size: 2.2rem; font-weight: bold; color: #1E88E5; margin-bottom: 0.5rem;}
    .sub-header {font-size: 1.1rem; color: #555; margin-bottom: 1.5rem;}
    .memory-item {background-color: #f0f2f6; padding: 10px; border-radius: 5px; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center;}
    .debug-box {background-color: #282c34; color: #abb2bf; padding: 15px; border-radius: 5px; font-family: monospace; font-size: 0.9rem; white-space: pre-wrap;}
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
    new_client_id = st.sidebar.text_input("ID Cliente (es. Nike, Mario_Rossi)", key="new_client_input").strip().replace(" ", "_")
    if st.sidebar.button("✅ CREA CLIENTE", type="primary", use_container_width=True):
        if not new_client_id:
            st.sidebar.error("⚠️ Inserisci un ID")
        elif new_client_id in all_clients:
            st.sidebar.warning(f"Il cliente '{new_client_id}' esiste già.")
        else:
            with st.sidebar.spinner(f"Creazione in corso..."):
                if rag.register_client(new_client_id):
                    rag.add_document(new_client_id, f"Cliente {new_client_id} inizializzato.", doc_type="sistema")
                    st.sidebar.success(f"✅ Cliente '{new_client_id}' creato!")
                    time.sleep(1)
                    st.rerun()
else:
    client_id = selected_option
    st.sidebar.markdown("---")
    st.sidebar.success(f"🟢 Cliente attivo: **{client_id}**")

if client_id:
    st.sidebar.markdown("---")
    with st.sidebar.expander("⚠️ Elimina Cliente"):
        st.warning(f"Stai per eliminare **TUTTI** i dati di '{client_id}'.")
        confirm_text = st.text_input(f"Per confermare, scrivi: {client_id}", key="delete_confirm")
        if st.button(f"🗑️ ELIMINA '{client_id}'", type="secondary", use_container_width=True):
            if confirm_text.strip() == client_id:
                with st.spinner("Eliminazione in corso..."):
                    success, message = rag.delete_client(client_id)
                    if success:
                        st.success(f"✅ Eliminato.")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(f"❌ Errore: {message}")
            else:
                st.error("❌ Testo non corrispondente.")

if not client_id:
    st.markdown('<div class="main-header">Benvenuto in Agenzia AI Hub</div>', unsafe_allow_html=True)
    st.info("👈 Seleziona o crea un cliente per iniziare.")
    st.stop()

# ==========================================
# MAIN AREA
# ==========================================
st.markdown(f'<div class="main-header">Dashboard: {client_id}</div>', unsafe_allow_html=True)
task_type = st.radio("🤖 Scegli l'Agente", ["🧠 Carica e Gestisci Memoria", "📅 Piano Editoriale Completo", "🔍 Analisi Competitor / Trend"], horizontal=True)
st.markdown("---")

# ==========================================
# AGENTE 1: CARICA E GESTISCI MEMORIA
# ==========================================
if task_type == "🧠 Carica e Gestisci Memoria":
    st.markdown('<div class="sub-header">Alimenta o modifica la memoria strategica del cliente</div>', unsafe_allow_html=True)
    
    # --- SEZIONE 1: VISUALIZZA MEMORIA ESISTENTE ---
    st.markdown("### 📂 Memoria Attuale")
    memory_summary = rag.get_memory_summary(client_id)
    
    reverse_mapping = {
        "brand_book": "📘 Brand Book / Linee Guida",
        "icp_personas": "👤 ICP / Personas & Pain/Gain",
        "gestione_obiezioni": "🛡️ Gestione Obiezioni",
        "esempi_copy": "✍️ Esempi di Copy Approvati",
        "istruzioni_creazione": "📝 Istruzioni Specifiche di Creazione",
        "note_call": "📞 Note da Call / Briefing",
        "regole_negative": "🚫 Regole Negative",
        "report_dati": "📊 Report / Dati Precedenti",
        "sistema": "⚙️ Sistema",
        "regola_stile": "🧠 Regole Apprese (Opzione B)",
        "avviso": "⚠️ Avviso DB",
        "errore": "❌ Errore DB"
    }
    
    # Gestione visualizzazione riepilogo
    has_data = False
    for key in memory_summary:
        if key not in ["avviso", "errore", "_totale_punti_db"]:
            has_data = True
            break

    if not has_data:
        st.info("La memoria di questo cliente è vuota. Carica il primo documento qui sotto!")
        if "avviso" in memory_summary:
            st.warning(memory_summary["avviso"])
        if "errore" in memory_summary:
            st.error(f"Dettaglio errore DB: {memory_summary['errore']}")
    else:
        total_db_points = memory_summary.get("_totale_punti_db", 0)
        st.success(f"✅ Database sincronizzato: {total_db_points} blocchi totali trovati per questo cliente.")
        
        st.write("Clicca su 🗑️ per eliminare una categoria specifica e ricaricarla aggiornata.")
        for doc_type, count in memory_summary.items():
            if doc_type in ["avviso", "errore", "_totale_punti_db"]:
                continue
                
            display_name = reverse_mapping.get(doc_type, f"📁 {doc_type}")
            col_chk1, col_chk2 = st.columns([3, 1])
            with col_chk1:
                st.markdown(f"<div class='memory-item'><b>{display_name}</b> <span style='color:#666'>({count} blocchi)</span></div>", unsafe_allow_html=True)
            with col_chk2:
                if st.button(f"🗑️ Elimina", key=f"del_{doc_type}", type="secondary", use_container_width=True):
                    with st.spinner(f"Eliminazione di {display_name} in corso..."):
                        success, msg = rag.delete_category(client_id, doc_type)
                        if success:
                            st.success(msg)
                            time.sleep(1.5)
                            st.rerun()
                        else:
                            st.error(msg)
        st.markdown("---")

    # --- SEZIONE 2: CARICAMENTO ---
    st.markdown("### ➕ Aggiungi Nuovo Contenuto")
    col1, col2 = st.columns([2, 1])
    with col1:
        uploaded_files = st.file_uploader("📎 Carica uno o più file (PDF, DOCX, TXT)", type=["pdf", "docx", "txt"], accept_multiple_files=True)
        manual_text = st.text_area("Oppure incolla qui del testo manuale:", height=150)
    
    with col2:
        st.markdown("**🏷️ Categoria:**")
        standard_categories = [
            "📘 Brand Book / Linee Guida",
            "👤 ICP / Personas & Pain/Gain",
            "🛡️ Gestione Obiezioni",
            "✍️ Esempi di Copy Approvati",
            "📝 Istruzioni Specifiche di Creazione",
            "📞 Note da Call / Briefing",
            "🚫 Regole Negative",
            "📊 Report / Dati Precedenti",
            "➕ Scrivi una categoria personalizzata..."
        ]
        selected_cat = st.selectbox("Scegli", standard_categories, key="cat_select")
        
        if "➕" in selected_cat:
            doc_type = st.text_input("Nome categoria (es. 'promo_natale')", key="custom_cat").strip().lower().replace(" ", "_")
        else:
            mapping = {
                "📘 Brand Book / Linee Guida": "brand_book",
                "👤 ICP / Personas & Pain/Gain": "icp_personas",
                "🛡️ Gestione Obiezioni": "gestione_obiezioni",
                "✍️ Esempi di Copy Approvati": "esempi_copy",
                "📝 Istruzioni Specifiche di Creazione": "istruzioni_creazione",
                "📞 Note da Call / Briefing": "note_call",
                "🚫 Regole Negative": "regole_negative",
                "📊 Report / Dati Precedenti": "report_dati"
            }
            doc_type = mapping.get(selected_cat, "generico")
            
        st.info(f"Salverai come: **`{doc_type}`**")

    if st.button("💾 Salva nella Memoria", type="primary"):
        final_text = ""
        files_processed = 0
        debug_info = []
        
        clean_cid = rag._clean_id(client_id)
        debug_info.append(f"🔑 ID Cliente per salvataggio: '{clean_cid}'")
        
        if uploaded_files:
            for uploaded_file in uploaded_files:
                try:
                    extracted = ""
                    uploaded_file.seek(0)
                    
                    if uploaded_file.type == "text/plain":
                        extracted = uploaded_file.read().decode("utf-8")
                    elif uploaded_file.type == "application/pdf":
                        reader = PyPDF2.PdfReader(uploaded_file)
                        extracted = "\n".join([page.extract_text() or "" for page in reader.pages])
                    elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                        doc = docx.Document(uploaded_file)
                        extracted = "\n".join([para.text for para in doc.paragraphs if para.text.strip()])
                    
                    char_count = len(extracted.strip())
                    snippet = extracted.strip()[:100].replace("\n", " ") + ("..." if char_count > 100 else "")
                    
                    debug_info.append(f"📄 **{uploaded_file.name}**")
                    debug_info.append(f"   ↳ Caratteri estratti: {char_count}")
                    debug_info.append(f"   ↳ Anteprima: '{snippet}'")
                    
                    if char_count > 0:
                        final_text += f"\n\n--- FILE: {uploaded_file.name} ---\n" + extracted
                        files_processed += 1
                except Exception as e:
                    debug_info.append(f"❌ **{uploaded_file.name}**: Errore ({str(e)})")
        
        if manual_text.strip():
            final_text += "\n\n--- TESTO MANUALE ---\n" + manual_text.strip()
            debug_info.append(f"📝 **Testo Manuale**: {len(manual_text.strip())} caratteri.")
            
        final_text = final_text.strip()
        
        st.markdown("### 🔍 Pannello di Debug")
        st.markdown(f'<div class="debug-box">' + "\n".join(debug_info) + f"\n\n✅ **TOTALE TESTO DA SALVARE:** {len(final_text)} caratteri.</div>", unsafe_allow_html=True)

        if final_text and len(final_text) >= 50:
            with st.spinner(f"Elaborazione e salvataggio in corso..."):
                result = rag.add_document(client_id, final_text, doc_type)
                st.success(result)
                
                # PAUSA DI INDICIZZAZIONE QDRANT (FONDAMENTALE)
                time.sleep(3) 
                
                new_summary = rag.get_memory_summary(client_id)
                total_points = new_summary.get("_totale_punti_db", 0)
                
                if total_points > 0:
                    st.success(f"✅ Verifica completata: Il database contiene ora {total_points} blocchi per questo cliente.")
                else:
                    st.warning("⚠️ Il database non riporta ancora i dati. Attendi 5 secondi e ricarica la pagina (F5).")
                
                time.sleep(1)
                st.rerun()
        elif final_text and len(final_text) < 50:
            st.error("⛔ BLOCCATO: Testo troppo breve (< 50 caratteri).")
        else:
            st.error("⛔ BLOCCATO: Nessun testo valido trovato. Controlla il Debug.")

# ==========================================
# AGENTE 2: PIANO EDITORIALE
# ==========================================
elif task_type == "📅 Piano Editoriale Completo":
    st.markdown('<div class="sub-header">Genera un piano editoriale completo rispettando il tono di voce</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        mese = st.text_input("📅 Mese/Periodo", "Dicembre 2024")
        obiettivo = st.selectbox("🎯 Obiettivo", ["Brand Awareness", "Lead Generation", "Lancio Prodotto", "Fidelizzazione", "Engagement"])
    with col2:
        tema = st.text_input("💡 Tema Centrale", "Es. Campagna Natalizia")
        canali = st.multiselect("📱 Canali", ["LinkedIn", "Instagram", "Facebook", "TikTok", "Newsletter"], default=["Instagram"])

    if st.button("🚀 Genera Bozza Piano Editoriale", type="primary"):
        with st.spinner("L'Agente Creativo sta lavorando..."):
            context = rag.get_client_context(client_id, "brand book, ICP, personas, pain, gain, obiezioni, istruzioni di creazione, tono di voce")
            
            prompt_pe = (
                f"Sei un Social Media Manager e Brand Strategist esperto. Genera un Piano Editoriale in formato CSV STRICT (solo testo separato da virgole, no markdown).\n"
                f"Colonne ESATTE: Data, Canale, Formato, Tema/Angolo, Hook, Copy, CTA, Brief Visivo.\n\n"
                f"CONTESTO CLIENTE (Rispetta tassativamente ICP, Pain/Gain, Obiezioni e Istruzioni di Creazione se presenti):\n{context}\n\n"
                f"RICHIESTA: Mese: {mese}, Obiettivo: {obiettivo}, Tema: {tema}, Canali: {', '.join(canali)}\n"
                f"Genera 6 idee. Se ci sono virgole nel Copy, racchiudilo tra virgolette doppie. Rispondi SOLO con il CSV, intestazione inclusa."
            )
            
            response = rag.llm.invoke(prompt_pe).content
            
            try:
                clean_response = response.replace("```csv", "").replace("```", "").strip()
                df = pd.read_csv(io.StringIO(clean_response))
                st.session_state['original_pe'] = clean_response
                st.session_state['current_pe_df'] = df
                st.success("✅ Bozza generata! Modifica le celle direttamente nella tabella.")
                st.data_editor(df, num_rows="dynamic", key="editable_df", height=500, use_container_width=True)
            except Exception as e:
                st.error("⚠️ Errore formato CSV. Output grezzo:")
                st.code(response)
                st.session_state['original_pe'] = response

    if 'current_pe_df' in st.session_state:
        st.markdown("---")
        st.markdown("### 🧠 Revisione e Apprendimento (Opzione B)")
        if st.button("💾 Salva e Insegna", type="secondary"):
            with st.spinner("L'Agente Analista sta confrontando le versioni..."):
                modified_csv = st.session_state['editable_df'].to_csv(index=False)
                result = rag.save_and_teach(client_id, st.session_state['original_pe'], modified_csv)
                st.success(result)

# ==========================================
# AGENTE 3: ANALISI COMPETITOR / TREND
# ==========================================
elif task_type == "🔍 Analisi Competitor / Trend":
    st.markdown('<div class="sub-header">Ricerca sul web trend o competitor</div>', unsafe_allow_html=True)
    query_ricerca = st.text_input("🔍 Cosa cercare? (es. 'trend marketing B2B dicembre 2024')")
    if st.button("🌐 Avvia Ricerca Web", type="primary"):
        if query_ricerca:
            with st.spinner("Ricerca in corso..."):
                search_results = rag.web_search(query_ricerca, num_results=5)
                if "Errore" in search_results or "⚠️" in search_results:
                    st.warning(search_results)
                else:
                    st.markdown("### 📊 Risultati")
                    st.markdown(search_results)
                    with st.spinner("Sintesi insight..."):
                        context = rag.get_client_context(client_id, "obiettivi strategici, ICP, pain gain")
                        prompt_sintesi = f"Sei un Brand Strategist. Ricerca:\n{search_results}\nCliente: '{client_id}'. Contesto: {context}\nSintetizza in 3 insight pratici per il prossimo piano editoriale, collegandoli ai Pain/Gain del cliente."
                        st.info(rag.llm.invoke(prompt_sintesi).content)