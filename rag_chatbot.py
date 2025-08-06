import streamlit as st
import json
import os
import hashlib
from typing import List, Dict
from langchain.vectorstores import FAISS
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.chains import ConversationalRetrievalChain
from langchain.prompts.prompt import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.docstore.document import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.memory import ConversationSummaryBufferMemory


@st.cache_resource
def get_embeddings():
    return HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={'device': 'cpu'},
        encode_kwargs={'normalize_embeddings': True}
    )

@st.cache_resource
def get_llm():
    return ChatGoogleGenerativeAI(
        model="gemini-2.5-pro",
        temperature=0.3,
        max_tokens=2048
    )

def create_document_hash(notes_list: List[Dict]) -> str:
    content = ""
    for note in notes_list:
        filepath = note.get('filepath', '')
        if filepath and os.path.exists(filepath):
            content += f"{filepath}_{os.path.getmtime(filepath)}"
    return hashlib.md5(content.encode()).hexdigest()


def load_documents_optimized(notes_list: List[Dict]) -> List[Document]:
    docs = []
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1200,
        chunk_overlap=300,
        separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""],
        length_function=len
    )

    for note in notes_list:
        filepath = note.get('filepath')
        if not filepath or not os.path.exists(filepath):
            continue

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            sections = []

            if data.get("video_title"):
                sections.append(f"Video Başlığı: {data['video_title']}")

            if data.get("analysis_result"):
                sections.append(f"İçerik Analizi:\n{data['analysis_result']}")

            if data.get("user_notes"):
                sections.append(f"Kullanıcı Notları:\n{data['user_notes']}")

            raw_text = "\n\n".join(sections)

            metadata = {
                "source": data.get("source_url", "bilinmiyor"),
                "title": data.get("video_title", data.get("title", "Bilinmeyen")),
                "file_path": filepath,
                "doc_type": "video_analysis"
            }

            if raw_text.strip():
                chunks = splitter.split_text(raw_text)
                for i, chunk in enumerate(chunks):
                    chunk_metadata = metadata.copy()
                    chunk_metadata["chunk_id"] = i
                    docs.append(Document(page_content=chunk, metadata=chunk_metadata))

        except Exception as e:
            st.warning(f"Doküman okuma hatası ({filepath}): {str(e)}")
            continue

    return docs


@st.cache_resource
def build_vectorstore(_docs: List[Document], _embeddings):
    if not _docs:
        return None
    return FAISS.from_documents(_docs, _embeddings)


def get_optimized_prompt():
    return PromptTemplate(
        input_variables=["context", "question", "chat_history"],
        template="""Sen uzman bir video analizi asistanısın. Kullanıcının dokümanlarından bilgi alarak sorularını yanıtlıyorsun.

    KAYNAK BELGELER:
    {context}
    
    GEÇMİŞ SOHBET:
    {chat_history}
    
    KULLANICI SORUSU:
    {question}
    
    YANIT KURALLARI:
    1. SADECE ve SADECE verilen kaynak belgelerindeki bilgileri kullan
    2. Bilgiyi direkt olarak belgelerden al, kendi yorumunu katma
    3. Emin olmadığın veya belgede olmayan bilgiler için "Bu bilgi dokümanlarımda mevcut değil" de
    4. Cevaplarını detaylı ver - belgede varsa tüm ilgili bilgiyi aktar
    5. Önceki sohbet geçmişini dikkate al ama yine sadece belgelerden bilgi ver
    6. Çok net ve kesin cevaplar ver, belirsizlik ifadeleri kullanma
    
    YANIT FORMAT:
    [Detaylı cevap buraya]
    
    """
    )


def create_rag_chain_optimized(vectorstore, llm):
    if not vectorstore:
        return None

    memory = ConversationSummaryBufferMemory(
        llm=llm,
        memory_key="chat_history",
        return_messages=True,
        output_key="answer",
        max_token_limit=800
    )

    retriever = vectorstore.as_retriever(
        search_type="mmr",
        search_kwargs={
            "k": 6,
            "lambda_mult": 0.8,
            "fetch_k": 20
        }
    )

    qa_chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=retriever,
        memory=memory,
        return_source_documents=True,
        combine_docs_chain_kwargs={"prompt": get_optimized_prompt()},
        output_key="answer",
        verbose=False
    )

    return qa_chain

def render_chatbot_page(get_saved_notes_list_func, model=None):
    st.header("🚀🤖 AI Asistan")

    notes_list = get_saved_notes_list_func()

    if not notes_list:
        st.warning("⚠️ Henüz analiz dokümanınız yok.")
        st.info("💡 Önce video analizi yaparak doküman oluşturun.")
        return

    current_hash = create_document_hash(notes_list)

    embeddings = get_embeddings()
    llm = get_llm()

    if ("doc_hash" not in st.session_state or
            st.session_state.doc_hash != current_hash or
            "vectorstore" not in st.session_state):

        if "vectorstore" not in st.session_state:
            progress_placeholder = st.empty()
            with progress_placeholder:
                st.info("📊 Sistem ilk kez hazırlanıyor, lütfen bekleyin...")

        docs = load_documents_optimized(notes_list)
        st.session_state.vectorstore = build_vectorstore(docs, embeddings)
        st.session_state.doc_hash = current_hash

        st.session_state.qa_chain = create_rag_chain_optimized(
            st.session_state.vectorstore, llm
        )

        if "vectorstore" in st.session_state:
            if 'progress_placeholder' in locals():
                progress_placeholder.empty()

    if "qa_chain" not in st.session_state:
        st.session_state.qa_chain = create_rag_chain_optimized(
            st.session_state.vectorstore, llm
        )

    if "messages" not in st.session_state:
        st.session_state.messages = []
        welcome_msg = """👋 Merhaba! Ben fikir galaksisinin chatbotuyum. Sizi gördüğüme memnun oldum 😊
        Dokümanlarınız hakkında herhangi bir sorunuz var mı?"""

        st.session_state.messages.append({
            "role": "assistant",
            "content": welcome_msg
        })

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("💬 Dokümanlarınız hakkında soru sorun..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.rerun()

    if (st.session_state.messages and
            st.session_state.messages[-1]["role"] == "user"):

        last_msg = st.session_state.messages[-1]

        with st.chat_message("assistant"):
            with st.spinner("🔍 Dokümanlarınızı analiz ediyorum..."):
                try:
                    result = st.session_state.qa_chain({"question": last_msg["content"]})
                    response = result["answer"]
                    sources = result.get("source_documents", [])

                    st.markdown(response)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": response
                    })

                    st.rerun()

                except Exception as e:
                    error_msg = f"❌ Üzgünüm, yanıt oluştururken bir hata oluştu: {str(e)}"
                    st.error(error_msg)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": error_msg
                    })
                    st.rerun()

    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("🗑️ Sohbet Geçmişini Temizle", use_container_width=True):
            st.session_state.messages = []
            if "qa_chain" in st.session_state:
                st.session_state.qa_chain.memory.clear()
            st.rerun()