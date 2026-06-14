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
    .debug-box {background-color: #282c34; color: #abb2bf; padding: 15px; border-radius: 5px; font-family: monospace; font-size: 0.85rem; white-space: pre-wrap;}
    </style>
""", unsafe_allow_html=True)

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
                    rag.add_document(new_client_id, f"Cliente {new_client_id} inizializzato.", doc_type="sistema", source_file="sistema")
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

st.markdown(f'<div class="main-header">Dashboard: {client_id}</div>', unsafe_allow_html=True)
task_type = st.radio("🤖 Scegli l'Agente", ["🧠 Carica e Gestisci Memoria", "📅 Piano Editoriale Completo", "🔍 Analisi Competitor / Trend"], horizontal=True)
st.markdown("---")

if task_type == "🧠 Carica e Gestisci Memoria":
    st.markdown('<div class="sub-header">Alimenta o modifica la memoria strategica del cliente</div>', unsafe_allow_html=True)
    
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
        "link_riferimento": "🔗 Link Asset, Competitor e Fonti",
        "sistema": "⚙️ Sistema",
        "regola_stile": "🧠 Regole Apprese (Opzione B)",
        "errore": "❌ Errore DB"
    }
    
    has_data = False
    for key in memory_summary:
        if key != "errore":
            has_data = True
            break

    if not has_data:
        st.info("La memoria di questo cliente è vuota. Carica il primo documento qui sotto!")
        if "errore" in memory_summary:
            st.error(f"Dettaglio errore DB: {memory_summary['errore']}")
    else:
        st.success(f"✅ Memoria caricata correttamente.")
        st.write("Clicca sulle categorie per espanderle, vedere i singoli file ed eliminarli se necessario.")
        
        for doc_type, data in memory_summary.items():
            if doc_type == "errore":
                continue
                
            display_name = reverse_mapping.get(doc_type, f"📁 {doc_type}")
            count = data.get("count", 0)
            files = data.get("files", [])
            
            with st.expander(f"**{display_name}** ({count} blocchi totali)"):
                if files:
                    st.markdown("📎 **File / Fonti presenti:**")
                    for f in files:
                        col_f1, col_f2 = st.columns([4, 1])
                        with col_f1:
                            st.markdown(f"- 📄 `{f}`")
                        with col_f2:
                            if st.button("🗑️ Elimina", key=f"del_file_{doc_type}_{f}", help=f"Elimina {f}"):
                                with st.spinner(f"Eliminazione di '{f}' in corso..."):
                                    success, msg = rag.delete_specific_file(client_id, doc_type, f)
                                    if success:
                                        st.success(msg)
                                        time.sleep(1)
                                        st.rerun()
                                    else:
                                        st.error(msg)
                else:
                    st.markdown("📝 *Nessun file specifico tracciato.*")
                
                st.markdown("---")
                if st.button(f"🗑️ ELIMINA TUTTA LA CATEGORIA '{display_name}'", key=f"del_cat_{doc_type}", type="secondary"):
                    with st.spinner(f"Eliminazione di {display_name} in corso..."):
                        success, msg = rag.delete_category(client_id, doc_type)
                        if success:
                            st.success(msg)
                            time.sleep(1.5)
                            st.rerun()
                        else:
                            st.error(msg)
        st.markdown("---")

    st.markdown("### ➕ Aggiungi Nuovo Contenuto")
    col1, col2 = st.columns([2, 1])
    with col1:
        # AGGIUNTO SUPPORTO CSV PER LISTE DI LINK
        uploaded_files = st.file_uploader("📎 Carica file (PDF, DOCX, TXT, CSV)", type=["pdf", "docx", "txt", "csv"], accept_multiple_files=True)
        
        # Placeholder dinamico in base alla categoria
        placeholder_text = "Oppure incolla qui del testo manuale:"
        if "link_riferimento" in locals() and doc_type == "link_riferimento":
            placeholder_text = "Incolla qui la lista di link (uno per riga). Es:\nhttps://sitocliente.it\nhttps://competitor1.com\n..."
            
        manual_text = st.text_area(placeholder_text, height=150)
    
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
            "🔗 Link Asset, Competitor e Fonti",
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
                "📊 Report / Dati Precedenti": "report_dati",
                "🔗 Link Asset, Competitor e Fonti": "link_riferimento"
            }
            doc_type = mapping.get(selected_cat, "generico")
            
        st.info(f"Salverai come: **`{doc_type}`**")

    if st.button("💾 Salva nella Memoria", type="primary"):
        files_processed = 0
        debug_info = []
        clean_cid = rag._clean_id(client_id)
        debug_info.append(f"🔑 ID Cliente: '{clean_cid}'")
        
        if uploaded_files:
            for uploaded_file in uploaded_files:
                try:
                    extracted = ""
                    uploaded_file.seek(0)
                    
                    if uploaded_file.type in ["text/plain", "text/csv"]:
                        # Tratta sia TXT che CSV come testo semplice (perfetto per liste di link)
                        extracted = uploaded_file.read().decode("utf-8")
                    elif uploaded_file.type == "application/pdf":
                        reader = PyPDF2.PdfReader(uploaded_file)
                        extracted = "\n".join([page.extract_text() or "" for page in reader.pages])
                    elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                        doc = docx.Document(uploaded_file)
                        paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]
                        extracted = "\n".join(paragraphs)
                    
                    char_count = len(extracted.strip())
                    debug_info.append(f"📄 **{uploaded_file.name}**: {char_count} caratteri.")
                    
                    if char_count > 0:
                        res = rag.add_document(client_id, extracted, doc_type, source_file=uploaded_file.name)
                        debug_info.append(f"   ↳ {res}")
                        files_processed += 1
                except Exception as e:
                    debug_info.append(f"❌ **{uploaded_file.name}**: Errore ({str(e)})")
        
        if manual_text.strip():
            res = rag.add_document(client_id, manual_text.strip(), doc_type, source_file="testo_manuale")
            debug_info.append(f"📝 **Testo Manuale**: {res}")
            
        st.markdown("### 🔍 Riepilogo Operazione")
        st.markdown(f'<div class="debug-box">' + "\n".join(debug_info) + "</div>", unsafe_allow_html=True)

        if files_processed > 0 or manual_text.strip():
            st.success("✅ Salvataggio completato con successo!")
            time.sleep(1.5)
            st.rerun()
        else:
            st.warning("⚠️ Nessun testo valido o file caricato.")

elif task_type == "📅 Piano Editoriale Completo":
    st.markdown('<div class="sub-header">Genera un piano editoriale completo rispettando il tono di voce</div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        mese = st.text_input("📅 Mese/Periodo", "Gennaio 2025")
        obiettivo = st.selectbox("🎯 Obiettivo", ["Brand Awareness", "Lead Generation", "Lancio Prodotto", "Fidelizzazione", "Engagement"])
    with col2:
        tema = st.text_input("💡 Tema Centrale", "Es. Presentazione nuovo approccio")
        canali = st.multiselect("📱 Canali", ["LinkedIn", "Instagram", "Facebook", "TikTok", "Newsletter"], default=["LinkedIn", "Instagram"])

    if st.button("🚀 Genera Bozza Piano Editoriale", type="primary"):
        with st.spinner("L'Agente Creativo sta lavorando..."):
            context = rag.get_client_context(client_id, "brand book, ICP, personas, pain, gain, obiezioni, istruzioni di creazione, link di riferimento, tono di voce")
            prompt_pe = (
                f"Sei un Social Media Manager e Brand Strategist esperto. Genera un Piano Editoriale in formato CSV STRICT (solo testo separato da virgole, no markdown).\n"
                f"Colonne ESATTE: Data, Canale, Formato, Tema/Angolo, Hook, Copy, CTA, Brief Visivo.\n\n"
                f"CONTESTO CLIENTE (Rispetta tassativamente ICP, Pain/Gain, Obiezioni, Link di riferimento e Istruzioni di Creazione se presenti):\n{context}\n\n"
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

elif task_type == "🔍 Analisi Competitor / Trend":
    st.markdown('<div class="sub-header">Ricerca sul web trend o competitor</div>', unsafe_allow_html=True)
    query_ricerca = st.text_input("🔍 Cosa cercare? (es. 'trend marketing B2B gennaio 2025')")
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
                        context = rag.get_client_context(client_id, "obiettivi strategici, ICP, pain gain, link competitor")
                        prompt_sintesi = f"Sei un Brand Strategist. Ricerca:\n{search_results}\nCliente: '{client_id}'. Contesto: {context}\nSintetizza in 3 insight pratici per il prossimo piano editoriale, collegandoli ai Pain/Gain del cliente."
                        st.info(rag.llm.invoke(prompt_sintesi).content)