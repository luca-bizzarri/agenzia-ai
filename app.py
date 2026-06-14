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
    .debug-box {background-color: #282c34; color: #abb2bf; padding: 15px; border-radius: 5px; font-family: monospace; font-size: 0.85rem; white-space: pre-wrap;}
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
        "errore": "❌ Errore DB"
    }
    
    has_data = False
    for key in memory_summary:
        if key not in ["errore", "_DEBUG_SONDA", "_DEBUG_ID_CERCATO"]:
            has_data = True
            break

    if not has_data:
        st.info("La memoria di questo cliente è vuota. Carica il primo documento qui sotto!")
        if "errore" in memory_summary:
            st.error(f"Dettaglio errore DB: {memory_summary['errore']}")
            
        # MOSTRA LA SONDA DI DEBUG SE ATTIVA
        if "_DEBUG_SONDA" in memory_summary:
            st.warning("⚠️ Il filtro non ha trovato dati, ma ecco cosa c'è REALMENTE negli ultimi 5 record del database:")
            st.markdown(f'<div class="debug-box">{memory_summary["_DEBUG_SONDA"]}\n\n{memory_summary["_DEBUG_ID_CERCATO"]}</div>', unsafe_allow_html=True)
    else:
        st.success(f"✅ Memoria caricata correttamente.")
        st.write("Clicca su 🗑️ per eliminare una categoria specifica e ricaricarla aggiornata.")
        for doc_type, count in memory_summary.items():
            if doc_type in ["errore", "_DEBUG_SONDA", "_DEBUG_ID_CERCATO"]:
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
                        doc = docx.Document(