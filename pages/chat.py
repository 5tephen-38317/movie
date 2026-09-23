# ============================================================
# AI 채팅 페이지
# 파일 위치: pages/chat.py
#
# 이 파일은 기존 main.py와 완전히 별개의 페이지입니다.
# Streamlit에서는 pages 폴더 안의 파일이 자동으로 별도 페이지가 됩니다.
# ============================================================

import streamlit as st
from openai import OpenAI


# ------------------------------------------------------------
# 1. 페이지 기본 설정
# ------------------------------------------------------------

st.set_page_config(
    page_title="AI 정보 선생님",
    page_icon="🤖",
    layout="centered"
)


# ------------------------------------------------------------
# 2. 화면 제목
# ------------------------------------------------------------

st.title("🤖 AI 정보 선생님")
st.caption("궁금한 것을 질문해 보세요.")


# ------------------------------------------------------------
# 3. Gemini API 연결
#
# API 키는 코드에 직접 적지 않습니다.
# Streamlit의 Secrets에 저장한 GEMINI_API_KEY를 사용합니다.
# ------------------------------------------------------------

try:
    api_key = st.secrets["GEMINI_API_KEY"]

    client = OpenAI(
        api_key=api_key,
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
    )

except Exception:
    # API 키가 없거나 Secrets를 불러오지 못했을 때
    st.error("AI 연결 설정을 불러오지 못했습니다. 관리자에게 확인해 주세요.")
    st.stop()


# ------------------------------------------------------------
# 4. 대화 기록 저장
#
# st.session_state를 사용하면 페이지가 다시 실행되어도
# 현재 대화 내용을 계속 기억할 수 있습니다.
# ------------------------------------------------------------

if "messages" not in st.session_state:
    st.session_state.messages = []


# ------------------------------------------------------------
# 5. 지금까지의 대화 내용을 화면에 표시
# ------------------------------------------------------------

for message in st.session_state.messages:

    # 사용자와 AI의 말풍선을 서로 다르게 표시합니다.
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# ------------------------------------------------------------
# 6. 채팅 입력창
# ------------------------------------------------------------

user_input = st.chat_input("메시지를 입력하세요.")


# 사용자가 메시지를 입력했을 때만 아래 내용을 실행합니다.
if user_input:

    # --------------------------------------------------------
    # 6-1. 사용자의 메시지를 대화 기록에 저장
    # --------------------------------------------------------

    st.session_state.messages.append(
        {
            "role": "user",
            "content": user_input
        }
    )

    # 사용자의 말풍선을 바로 화면에 표시합니다.
    with st.chat_message("user"):
        st.markdown(user_input)


    # --------------------------------------------------------
    # 6-2. AI의 말풍선 생성
    # --------------------------------------------------------

    with st.chat_message("assistant"):

        # AI의 답변이 실시간으로 하나씩 나타날 공간입니다.
        answer_box = st.empty()

        # AI에게 전달할 기본 성격입니다.
        #
        # 이 문장은 화면에 표시되지 않고
        # AI에게만 전달됩니다.
        system_message = {
            "role": "system",
            "content": (
                "너는 중고등학생에게 설명하는 친절한 정보 선생님이야. "
                "어려운 말은 쉬운 말로 바꿔 주고, "
                "반드시 순수 한국어로만 답해."
            )
        }

        # 시스템 성격 + 지금까지의 대화 내용을 합칩니다.
        # 이렇게 하기 때문에 AI가 이전 대화의 흐름을 이어갈 수 있습니다.
        messages_to_send = [
            system_message
        ] + st.session_state.messages


        # ----------------------------------------------------
        # 6-3. Gemini에게 요청하고 답변을 실시간으로 받기
        # ----------------------------------------------------

        try:
            stream = client.chat.completions.create(
                model="gemini-3.5-flash-lite",
                messages=messages_to_send,
                stream=True
            )

            # 지금까지 받은 답변을 저장할 변수
            full_answer = ""

            # Gemini가 보내주는 내용을 하나씩 받습니다.
            for chunk in stream:

                # 이번에 새로 들어온 글자를 가져옵니다.
                if chunk.choices and chunk.choices[0].delta.content:
                    new_text = chunk.choices[0].delta.content

                    # 기존 답변 뒤에 새 글자를 붙입니다.
                    full_answer += new_text

                    # 지금까지 만들어진 답변을 화면에 표시합니다.
                    answer_box.markdown(full_answer + "▌")

            # 마지막에는 커서를 제거하고 완성된 답변만 표시합니다.
            answer_box.markdown(full_answer)


            # ------------------------------------------------
            # 6-4. AI의 답변도 대화 기록에 저장
            #
            # 다음 질문을 할 때 이 내용까지 Gemini에게
            # 함께 전달되므로 대화를 이어갈 수 있습니다.
            # ------------------------------------------------

            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": full_answer
                }
            )


        except Exception:
            # 오류가 발생했을 때 복잡한 오류 화면 대신
            # 한국어 안내 문구 한 줄만 보여줍니다.
            answer_box.markdown(
                "잠시 문제가 생겼어요. 잠시 후 다시 시도해 주세요."
            )
