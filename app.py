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
    .channel-box {background-color: #f0f2f6; padding: 10px; border-radius: 5px; margin-bottom: 5px;}
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

# ==========================================
# AGENTE 1: GESTIONE MEMORIA (identico)
# ==========================================
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
        st.info("La memoria di questo cliente è vuota.")
        if "errore" in memory_summary:
            st.error(f"Dettaglio errore DB: {memory_summary['errore']}")
    else:
        st.success(f"✅ Memoria caricata correttamente.")
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
                            if st.button("🗑️", key=f"del_file_{doc_type}_{f}", help=f"Elimina {f}"):
                                with st.spinner(f"Eliminazione di '{f}'..."):
                                    success, msg = rag.delete_specific_file(client_id, doc_type, f)
                                    if success:
                                        st.success(msg)
                                        time.sleep(1)
                                        st.rerun()
                                    else:
                                        st.error(msg)
                st.markdown("---")
                if st.button(f"🗑️ ELIMINA TUTTA LA CATEGORIA", key=f"del_cat_{doc_type}", type="secondary"):
                    with st.spinner(f"Eliminazione di {display_name}..."):
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
        uploaded_files = st.file_uploader("📎 Carica file (PDF, DOCX, TXT, CSV)", type=["pdf", "docx", "txt", "csv"], accept_multiple_files=True)
        manual_text = st.text_area("Oppure incolla testo manuale:", height=150)
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
            doc_type = st.text_input("Nome categoria", key="custom_cat").strip().lower().replace(" ", "_")
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
        if uploaded_files:
            for uploaded_file in uploaded_files:
                try:
                    extracted = ""
                    uploaded_file.seek(0)
                    if uploaded_file.type in ["text/plain", "text/csv"]:
                        extracted = uploaded_file.read().decode("utf-8")
                    elif uploaded_file.type == "application/pdf":
                        reader = PyPDF2.PdfReader(uploaded_file)
                        extracted = "\n".join([page.extract_text() or "" for page in reader.pages])
                    elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                        doc = docx.Document(uploaded_file)
                        extracted = "\n".join([para.text for para in doc.paragraphs if para.text.strip()])
                    if len(extracted.strip()) > 0:
                        rag.add_document(client_id, extracted, doc_type, source_file=uploaded_file.name)
                        debug_info.append(f"✅ {uploaded_file.name}: {len(extracted)} caratteri")
                        files_processed += 1
                except Exception as e:
                    debug_info.append(f"❌ {uploaded_file.name}: {str(e)}")
        if manual_text.strip():
            rag.add_document(client_id, manual_text.strip(), doc_type, source_file="testo_manuale")
            debug_info.append(f"✅ Testo manuale: {len(manual_text.strip())} caratteri")
        
        if debug_info:
            st.markdown(f'<div class="debug-box">' + "\n".join(debug_info) + "</div>", unsafe_allow_html=True)
        if files_processed > 0 or manual_text.strip():
            st.success("✅ Salvataggio completato!")
            time.sleep(1.5)
            st.rerun()

# ==========================================
# AGENTE 2: PED COMPOSITORE FLESSIBILE (NUOVO!)
# ==========================================
elif task_type == "📅 Piano Editoriale Completo":
    st.markdown('<div class="sub-header">Componi il tuo piano editoriale su misura: decidi tu canali, quantità e formati</div>', unsafe_allow_html=True)
    
    # --- SEZIONE 1: INFO GENERALI ---
    st.markdown("### 📋 1. Informazioni Generali")
    col1, col2, col3 = st.columns(3)
    with col1:
        mese = st.text_input("📅 Periodo", "Gennaio 2025")
    with col2:
        obiettivo = st.selectbox("🎯 Obiettivo", ["Brand Awareness", "Lead Generation", "Lancio Prodotto", "Fidelizzazione", "Engagement", "Educazione Mercato"])
    with col3:
        durata = st.selectbox("⏱️ Durata Piano", ["1 settimana", "2 settimane", "1 mese", "3 mesi (trimestrale)"])
    
    tema = st.text_input("💡 Tema Centrale / Campagna", "Es. Posizionamento come esperti del settore")
    istruzioni_extra = st.text_area("📝 Note / Vincoli specifici (opzionale)", placeholder="Es. Evitare la parola X, enfatizzare Y, promuovere evento Z il giorno W...")
    
    st.markdown("---")
    
    # --- SEZIONE 2: CANALI SOCIAL ---
    st.markdown("### 📱 2. Contenuti Social (scegli quantità per canale)")
    st.caption("Usa gli slider per decidere quanti contenuti generare per ogni canale. Imposta a 0 per escluderlo.")
    
    canali_config = {}
    canali_disponibili = {
        "LinkedIn": ("💼 Post LinkedIn (testo lungo + carosello)", "Post testuali professionali, caroselli educativi, storytelling B2B"),
        "Instagram_Feed": ("📸 Post Instagram Feed (foto/carosello)", "Visual curati, caroselli educativi, citazioni, foto prodotto"),
        "Instagram_Reels": ("🎬 Instagram Reels", "Video brevi 15-60s, trend, tutorial, dietro le quinte"),
        "Instagram_Stories": ("📲 Instagram Stories", "Contenuti effimeri, sondaggi, Q&A, countdown"),
        "Facebook": ("👥 Post Facebook", "Contenuti community, link, album foto, eventi"),
        "TikTok": ("🎵 TikTok", "Video brevi virali, trend, educational veloce"),
        "Twitter_X": ("🐦 Post Twitter/X", "Thread, tweet brevi, opinioni, news")
    }
    
    cols = st.columns(2)
    for idx, (canale, (label, descrizione)) in enumerate(canali_disponibili.items()):
        with cols[idx % 2]:
            st.markdown(f'<div class="channel-box">', unsafe_allow_html=True)
            quant = st.slider(f"**{label}**", 0, 20, 0, help=descrizione, key=f"slider_{canale}")
            if quant > 0:
                st.caption(f"→ {quant} contenuti • {descrizione}")
                canali_config[canale] = quant
            st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # --- SEZIONE 3: CONTENUTI LONG-FORM ---
    st.markdown("### 🎙️ 3. Contenuti Long-Form / Speciali (opzionale)")
    st.caption("Aggiungi contenuti più strutturati al tuo piano.")
    
    longform_config = {}
    longform_disponibili = {
        "Blog_Article": ("📝 Articoli Blog", "Articoli SEO 800-1500 parole per il sito"),
        "Podcast_Episode": ("🎙️ Episodi Podcast", "Audio 20-45 min, monologhi o interviste"),
        "Newsletter": ("📧 Newsletter", "Email settimanali/mensili alla lista iscritti"),
        "Video_YouTube": ("📺 Video YouTube", "Video lunghi 8-20 min, tutorial, approfondimenti"),
        "Lead_Magnet": ("🎁 Lead Magnet", "PDF, checklist, ebook, template gratuiti")
    }
    
    cols_lf = st.columns(2)
    for idx, (tipo, (label, descrizione)) in enumerate(longform_disponibili.items()):
        with cols_lf[idx % 2]:
            quant = st.slider(f"**{label}**", 0, 10, 0, help=descrizione, key=f"slider_lf_{tipo}")
            if quant > 0:
                st.caption(f"→ {quant} contenuti • {descrizione}")
                longform_config[tipo] = quant
    
    st.markdown("---")
    
    # --- RIEPILOGO E GENERAZIONE ---
    totale_contenuti = sum(canali_config.values()) + sum(longform_config.values())
    
    if totale_contenuti == 0:
        st.warning("⚠️ **Configura almeno un contenuto** (social o long-form) per generare il piano.")
    else:
        st.success(f"🎯 **Piano configurato: {totale_contenuti} contenuti totali**")
        
        # Riepilogo visivo
        riepilogo_cols = st.columns(2)
        with riepilogo_cols[0]:
            if canali_config:
                st.markdown("**📱 Social:**")
                for k, v in canali_config.items():
                    st.markdown(f"- {k}: **{v}**")
        with riepilogo_cols[1]:
            if longform_config:
                st.markdown("**🎙️ Long-form:**")
                for k, v in longform_config.items():
                    st.markdown(f"- {k}: **{v}**")
        
        if st.button(f"🚀 GENERA PIANO ({totale_contenuti} contenuti)", type="primary", use_container_width=True):
            with st.spinner("L'Agente Creativo sta componendo il piano su misura..."):
                context = rag.get_client_context(client_id, "brand book, ICP, personas, pain, gain, obiezioni, istruzioni di creazione, tono di voce, link riferimento")
                
                # Costruzione dinamica del prompt
                canali_str = "\n".join([f"- {k}: {v} contenuti" for k, v in canali_config.items()])
                longform_str = "\n".join([f"- {k}: {v} contenuti" for k, v in longform_config.items()]) if longform_config else "Nessuno"
                
                prompt_pe = (
                    f"Sei un Social Media Manager e Content Strategist esperto. Genera un Piano Editoriale COMPLETO in formato CSV STRICT.\n\n"
                    f"## CONTESTO CLIENTE (tassativo):\n{context}\n\n"
                    f"## CONFIGURAZIONE RICHIESTA:\n"
                    f"- Periodo: {mese}\n"
                    f"- Durata: {durata}\n"
                    f"- Obiettivo: {obiettivo}\n"
                    f"- Tema centrale: {tema}\n"
                    f"- Note extra: {istruzioni_extra}\n\n"
                    f"## CANALI SOCIAL RICHIESTI:\n{canali_str if canali_str else 'Nessuno'}\n\n"
                    f"## CONTENUTI LONG-FORM RICHIESTI:\n{longform_str}\n\n"
                    f"## COLONNE CSV OBBLIGATORIE (esattamente queste, in questo ordine):\n"
                    f"Tipo,Data,Titolo/Tema,Hook,Copy/Script,CTA,Brief_Visivo_Produktivo,Hashtag_SEO,Note_Aggiuntive\n\n"
                    f"## ISTRUZIONI DI COMPILAZIONE:\n"
                    f"- **Tipo**: usa esattamente uno di questi valori: 'Post LinkedIn', 'Post IG Feed', 'Reel IG', 'Story IG', 'Post FB', 'TikTok', 'Tweet', 'Blog Article', 'Podcast Episode', 'Newsletter', 'Video YouTube', 'Lead Magnet'\n"
                    f"- **Data**: suggerisci una data coerente con il periodo e la frequenza\n"
                    f"- **Titolo/Tema**: l'argomento principale del contenuto\n"
                    f"- **Hook**: la frase di apertura (per social e video; per blog/podcast metti il sottotitolo)\n"
                    f"- **Copy/Script**: il testo completo del post, oppure lo script/struttura per blog, podcast, video, newsletter\n"
                    f"- **CTA**: call-to-action specifica\n"
                    f"- **Brief_Visivo_Produktivo**: descrizione dell'immagine/video da produrre, o struttura tecnica per podcast/blog\n"
                    f"- **Hashtag_SEO**: hashtag per social, o parole chiave SEO per blog/newsletter\n"
                    f"- **Note_Aggiuntive**: suggerimenti strategici, formati, best practice\n\n"
                    f"Genera ESATTAMENTE il numero di contenuti richiesti per ogni canale/tipologia. "
                    f"Rispetta il tono di voce, l'ICP e le regole del cliente. "
                    f"Se ci sono virgole nel Copy/Script, racchiudilo tra virgolette doppie. "
                    f"Rispondi SOLO con il CSV, intestazione inclusa, senza markdown."
                )
                
                response = rag.llm.invoke(prompt_pe).content
                
                try:
                    clean_response = response.replace("```csv", "").replace("```", "").strip()
                    df = pd.read_csv(io.StringIO(clean_response))
                    st.session_state['original_pe'] = clean_response
                    st.session_state['current_pe_df'] = df
                    
                    # Statistiche
                    st.success(f"✅ Piano generato con {len(df)} contenuti!")
                    
                    type_counts = df['Tipo'].value_counts().to_dict() if 'Tipo' in df.columns else {}
                    stat_cols = st.columns(4)
                    for idx, (tipo, count) in enumerate(type_counts.items()):
                        with stat_cols[idx % 4]:
                            st.metric(tipo, count)
                    
                    st.data_editor(df, num_rows="dynamic", key="editable_df", height=600, use_container_width=True)
                    
                    # Download CSV
                    csv_export = df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="📥 Scarica Piano Editoriale (CSV)",
                        data=csv_export,
                        file_name=f"PED_{client_id}_{mese.replace(' ', '_')}.csv",
                        mime="text/csv"
                    )
                    
                except Exception as e:
                    st.error("⚠️ Errore formato CSV. Output grezzo:")
                    st.code(response)
                    st.session_state['original_pe'] = response

    # --- SEZIONE APPRENDIMENTO ---
    if 'current_pe_df' in st.session_state:
        st.markdown("---")
        st.markdown("### 🧠 Revisione e Apprendimento (Opzione B)")
        st.write("Se hai modificato la tabella, l'AI analizzerà le tue correzioni e imparerà la regola per le prossime volte.")
        if st.button("💾 Salva e Insegna", type="secondary"):
            with st.spinner("L'Agente Analista sta confrontando le versioni..."):
                modified_csv = st.session_state['editable_df'].to_csv(index=False)
                result = rag.save_and_teach(client_id, st.session_state['original_pe'], modified_csv)
                st.success(result)

# ==========================================
# AGENTE 3: ANALISI COMPETITOR (identico)
# ==========================================
elif task_type == "🔍 Analisi Competitor / Trend":
    st.markdown('<div class="sub-header">Ricerca sul web trend o competitor</div>', unsafe_allow_html=True)
    query_ricerca = st.text_input("🔍 Cosa cercare?")
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
                        prompt_sintesi = f"Sei un Brand Strategist. Ricerca:\n{search_results}\nCliente: '{client_id}'. Contesto: {context}\nSintetizza in 3 insight pratici per il prossimo piano editoriale."
                        st.info(rag.llm.invoke(prompt_sintesi).content)