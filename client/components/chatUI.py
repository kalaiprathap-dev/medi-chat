import streamlit as st
from utils.api import ask_question


def _show_sources(sources):
    if sources:
        with st.expander(f"📚 Sources ({len(sources)})"):
            for src in sources:
                st.markdown(f"- `{src}`")


def render_chat():
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # render existing chat history
    for msg in st.session_state.messages:
        avatar = "🧑" if msg["role"] == "user" else "🩺"
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["content"])
            if msg["role"] == "assistant":
                _show_sources(msg.get("sources", []))

    # input and response
    user_input = st.chat_input("Ask a question about your documents...")
    if not user_input:
        return

    with st.chat_message("user", avatar="🧑"):
        st.markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.chat_message("assistant", avatar="🩺"):
        with st.spinner("Thinking... the first request can take about a minute."):
            try:
                response = ask_question(user_input)
            except Exception as e:
                st.error(f"Could not reach the server. Try again in a minute. ({e})")
                return

        if response.status_code == 200:
            data = response.json()
            answer = data["response"]
            sources = sorted({s for s in data.get("sources", []) if s})
            st.markdown(answer)
            _show_sources(sources)
            st.session_state.messages.append(
                {"role": "assistant", "content": answer, "sources": sources}
            )
        else:
            st.error(f"Error: {response.text}")



'''import streamlit as st
from utils.api import ask_question


def render_chat():
    st.subheader("💬 Chat with your assistant")

    if "messages" not in st.session_state:
        st.session_state.messages=[]

    # render existing chat history
    for msg in st.session_state.messages:
        st.chat_message(msg["role"]).markdown(msg["content"])

    # input and response
    user_input=st.chat_input("Type your question....")
    if user_input:
        st.chat_message("user").markdown(user_input)
        st.session_state.messages.append({"role":"user","content":user_input})

        response=ask_question(user_input)
        if response.status_code==200:
            data=response.json()
            answer=data["response"]
            sources=data.get("sources",[])
            st.chat_message("assistant").markdown(answer)
            # if sources:
            #     st.markdown("📄 **Sources: **")
            #     for src in sources:
            #         st.markdown(f"- `{src}`")
            st.session_state.messages.append({"role":"assistant","content":answer})
        else:
            st.error(f"Error: {response.text}")'''