# ============================================================
# 아키네이터 스타일 AI 추리 게임
# 파일 위치: pages/chat.py
#
# 중요:
# 기존 main.py는 전혀 수정하지 않습니다.
# 이 파일만 pages/chat.py로 저장하면 됩니다.
# ============================================================

import json
import re

import streamlit as st
from openai import OpenAI


# ============================================================
# 1. 페이지 설정
# ============================================================

st.set_page_config(
    page_title="AI 추리 게임",
    page_icon="🔮",
    layout="centered"
)


# ============================================================
# 2. 기본 성격
# ============================================================

DEFAULT_PERSONALITY = (
    "너는 중고등학생에게 설명하는 친절한 정보 선생님이야. "
    "어려운 말은 쉬운 말로 바꿔 주고, "
    "반드시 순수 한국어로만 답해."
)


# ============================================================
# 3. 말투별 설정
# ============================================================

TONE_INSTRUCTIONS = {

    "친절한 선생님": (
        "친절하고 차분하게 말해. "
        "학생이 부담을 느끼지 않도록 쉽게 설명해."
    ),

    "시크한 전문가": (
        "군더더기 없이 핵심적으로 말해. "
        "논리적이고 깔끔한 표현을 사용해."
    ),

    "되물어보는 조교": (
        "학생이 스스로 생각할 수 있도록 질문 중심으로 진행해. "
        "정답을 너무 빨리 알려주지 말고 필요한 경우 힌트를 줘."
    )
}


# ============================================================
# 4. Gemini API 연결
# ============================================================

try:

    # Streamlit Secrets에서 API 키를 가져옵니다.
    api_key = st.secrets["GEMINI_API_KEY"]

    # Gemini의 OpenAI 호환 주소를 사용합니다.
    client = OpenAI(
        api_key=api_key,
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
    )

except Exception:

    st.error(
        "AI 연결 설정을 불러오지 못했습니다. 관리자에게 확인해 주세요."
    )

    st.stop()


# ============================================================
# 5. 세션 상태 초기화
#
# Streamlit은 버튼을 누를 때마다 코드를 다시 실행합니다.
# 그래서 게임의 진행 상황을 session_state에 저장합니다.
# ============================================================

if "game_started" not in st.session_state:
    st.session_state.game_started = False

if "game_finished" not in st.session_state:
    st.session_state.game_finished = False

if "game_topic" not in st.session_state:
    st.session_state.game_topic = ""

if "question_number" not in st.session_state:
    st.session_state.question_number = 0

if "game_history" not in st.session_state:
    st.session_state.game_history = []

if "current_question" not in st.session_state:
    st.session_state.current_question = ""

if "current_guess" not in st.session_state:
    st.session_state.current_guess = ""

if "last_ai_message" not in st.session_state:
    st.session_state.last_ai_message = ""


# ============================================================
# 6. 사이드바
# ============================================================

with st.sidebar:

    st.header("⚙️ 게임 설정")

    # --------------------------------------------------------
    # 말투 선택
    # --------------------------------------------------------

    st.subheader("말투 고르기")

    selected_tone = st.selectbox(
        "AI의 말투",
        [
            "친절한 선생님",
            "시크한 전문가",
            "되물어보는 조교"
        ],
        label_visibility="collapsed"
    )


    # --------------------------------------------------------
    # AI 성격 직접 수정
    # --------------------------------------------------------

    st.subheader("AI 성격")

    personality = st.text_area(
        "AI의 성격 문장",
        value=DEFAULT_PERSONALITY,
        height=150,
        help="AI에게만 전달되는 설정입니다."
    )


    st.divider()


    # --------------------------------------------------------
    # 새 게임 버튼
    # --------------------------------------------------------

    if st.button(
        "🔄 새 게임",
        use_container_width=True
    ):

        st.session_state.game_started = False
        st.session_state.game_finished = False
        st.session_state.game_topic = ""
        st.session_state.question_number = 0
        st.session_state.game_history = []
        st.session_state.current_question = ""
        st.session_state.current_guess = ""
        st.session_state.last_ai_message = ""

        st.rerun()


    # --------------------------------------------------------
    # 대화 기록 삭제
    # --------------------------------------------------------

    if st.button(
        "🗑️ 대화 지우기",
        use_container_width=True
    ):

        st.session_state.game_history = []
        st.session_state.question_number = 0
        st.session_state.last_ai_message = ""

        st.rerun()


# ============================================================
# 7. 제목
# ============================================================

st.title("🔮 AI 추리 게임")

st.caption(
    "머릿속으로 하나를 정해 보세요. "
    "AI가 질문을 통해 정답을 추리합니다."
)


# ============================================================
# 8. 게임 시작 화면
# ============================================================

if not st.session_state.game_started:

    st.info(
        "사람, 캐릭터, 동물, 물건, 장소 등 무엇이든 하나를 머릿속으로 정하세요."
    )

    st.markdown("### 🎯 게임 방법")

    st.write(
        "1. 머릿속으로 하나를 정합니다."
    )

    st.write(
        "2. AI가 질문을 합니다."
    )

    st.write(
        "3. 예 / 아니오 / 잘 모르겠어요 중 하나를 선택합니다."
    )

    st.write(
        "4. AI가 답변을 바탕으로 범위를 좁혀 갑니다."
    )

    st.write(
        "5. 충분히 좁혀지면 AI가 정답을 추측합니다."
    )

    st.divider()


    # --------------------------------------------------------
    # 무엇을 생각했는지 종류를 선택
    #
    # 정답 자체는 입력하지 않습니다.
    # --------------------------------------------------------

    topic = st.selectbox(
        "무엇을 생각했나요?",
        [
            "사람",
            "가상의 인물",
            "동물",
            "물건",
            "장소",
            "음식",
            "영화·드라마 속 대상",
            "게임 속 대상",
            "기타"
        ]
    )


    # --------------------------------------------------------
    # 게임 시작
    # --------------------------------------------------------

    if st.button(
        "🎮 게임 시작하기",
        type="primary",
        use_container_width=True
    ):

        st.session_state.game_started = True
        st.session_state.game_finished = False
        st.session_state.game_topic = topic
        st.session_state.question_number = 0
        st.session_state.game_history = []
        st.session_state.current_guess = ""
        st.session_state.last_ai_message = ""

        # 첫 질문을 만들기 위해 AI를 호출합니다.
        with st.spinner("첫 번째 질문을 생각하고 있어요..."):

            try:

                first_question_prompt = f"""
너는 아키네이터처럼 대상을 추리하는 AI야.

사용자가 머릿속으로 하나의 대상을 정했다.
대상의 종류는 '{topic}'이다.

아직 아무 정보도 얻지 못했다.

처음에는 후보를 크게 나눌 수 있는 좋은 질문 하나를 만들어라.

규칙:
- 반드시 예/아니오/모르겠어요로 대답할 수 있는 질문이어야 한다.
- 질문 하나만 출력한다.
- 설명하지 않는다.
- 순수 한국어로 출력한다.
"""

                response = client.chat.completions.create(
                    model="gemini-3.5-flash-lite",
                    messages=[
                        {
                            "role": "system",
                            "content": personality
                        },
                        {
                            "role": "user",
                            "content": first_question_prompt
                        }
                    ]
                )

                question = response.choices[0].message.content.strip()

                # 혹시 따옴표가 붙으면 제거합니다.
                question = question.strip('"').strip("'")

                st.session_state.current_question = question
                st.session_state.question_number = 1

                st.rerun()

            except Exception:

                st.error(
                    "질문을 만드는 중 문제가 생겼어요. 잠시 후 다시 시도해 주세요."
                )

    st.stop()


# ============================================================
# 9. 게임 진행 화면
# ============================================================

st.markdown(
    f"### 🎯 {st.session_state.game_topic} 추리 중"
)

st.caption(
    f"질문 {st.session_state.question_number}"
)


# ============================================================
# 10. 지금까지의 질문과 답변 표시
# ============================================================

if st.session_state.game_history:

    with st.expander(
        "📋 지금까지의 질문과 답변 보기",
        expanded=False
    ):

        for i, item in enumerate(
            st.session_state.game_history,
            start=1
        ):

            st.write(
                f"**{i}. {item['question']}**"
            )

            st.write(
                f"→ {item['answer']}"
            )

            st.divider()


# ============================================================
# 11. 게임이 끝났으면 추측 결과 표시
# ============================================================

if st.session_state.game_finished:

    st.success(
        "추리가 끝났어요!"
    )

    if st.session_state.current_guess:

        st.markdown(
            f"## 🔮 제 추측은 **{st.session_state.current_guess}**!"
        )

    st.write(
        "정답이 맞았나요?"
    )

    col1, col2 = st.columns(2)

    with col1:

        if st.button(
            "🎉 맞아요!",
            use_container_width=True
        ):

            st.balloons()

            st.success(
                "정답을 맞혔어요! 🎉"
            )

    with col2:

        if st.button(
            "❌ 아니에요",
            use_container_width=True
        ):

            # 다시 질문하도록 게임을 계속합니다.
            st.session_state.game_finished = False
            st.session_state.current_guess = ""

            st.session_state.question_number += 1

            # 틀린 추측도 기록에 넣습니다.
            st.session_state.game_history.append(
                {
                    "question": "AI의 추측",
                    "answer": f"{st.session_state.current_guess} → 틀림"
                }
            )

            st.rerun()

    st.stop()


# ============================================================
# 12. 현재 질문 표시
# ============================================================

st.markdown("### ❓ 질문")

st.markdown(
    f"## {st.session_state.current_question}"
)


st.write("")


# ============================================================
# 13. 답변 버튼
# ============================================================

col1, col2, col3 = st.columns(3)


answer = None


with col1:

    if st.button(
        "⭕ 예",
        use_container_width=True
    ):

        answer = "예"


with col2:

    if st.button(
        "❌ 아니오",
        use_container_width=True
    ):

        answer = "아니오"


with col3:

    if st.button(
        "🤔 잘 모르겠어요",
        use_container_width=True
    ):

        answer = "잘 모르겠어요"


# ============================================================
# 14. 사용자가 답변을 선택했을 때
# ============================================================

if answer:

    # --------------------------------------------------------
    # 현재 질문과 답변을 기록합니다.
    # --------------------------------------------------------

    current_question = st.session_state.current_question

    st.session_state.game_history.append(
        {
            "question": current_question,
            "answer": answer
        }
    )


    # --------------------------------------------------------
    # 지금까지의 기록을 AI가 읽을 수 있는 형태로 만듭니다.
    # --------------------------------------------------------

    history_text = ""

    for i, item in enumerate(
        st.session_state.game_history,
        start=1
    ):

        history_text += (
            f"{i}. 질문: {item['question']}\n"
            f"   답변: {item['answer']}\n"
        )


    # --------------------------------------------------------
    # AI에게 다음 행동을 결정하게 합니다.
    #
    # AI는
    # QUESTION = 다음 질문
    # GUESS = 정답 추측
    # 중 하나를 반환합니다.
    # --------------------------------------------------------

    decision_prompt = f"""
너는 아키네이터 스타일의 추리 게임 AI다.

사용자는 '{st.session_state.game_topic}' 중 하나를
머릿속으로 정했다.

지금까지의 질문과 답변:

{history_text}

이 정보를 바탕으로 가장 효율적으로 대상을 좁혀라.

중요한 규칙:

1. 질문 하나로 후보를 최대한 많이 구분할 수 있도록 한다.
2. 이미 물어본 내용과 거의 같은 질문을 반복하지 않는다.
3. 답변이 '잘 모르겠어요'인 것은 확정된 정보로 취급하지 않는다.
4. 충분한 정보가 모였다고 판단되면 추측한다.
5. 아직 정보가 부족하면 다음 질문을 한다.
6. 질문은 반드시 예/아니오/잘 모르겠어요로 대답할 수 있어야 한다.
7. 질문은 하나만 한다.
8. 정답을 추측할 때는 가장 가능성이 높은 대상 하나만 제시한다.

반드시 아래 JSON 형식으로만 답해라.

다음 질문을 할 경우:

{{
  "action": "QUESTION",
  "content": "질문 내용"
}}

정답을 추측할 경우:

{{
  "action": "GUESS",
  "content": "추측한 대상"
}}
"""


    # --------------------------------------------------------
    # AI 호출
    # --------------------------------------------------------

    with st.spinner("답변을 분석하고 있어요..."):

        try:

            response = client.chat.completions.create(
                model="gemini-3.5-flash-lite",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            personality
                            + "\n\n"
                            + TONE_INSTRUCTIONS[selected_tone]
                        )
                    },
                    {
                        "role": "user",
                        "content": decision_prompt
                    }
                ]
            )


            raw_result = response.choices[0].message.content.strip()


            # ------------------------------------------------
            # AI가 ```json ... ``` 형태로 답할 수도 있기 때문에
            # 코드 블록 표시를 제거합니다.
            # ------------------------------------------------

            raw_result = re.sub(
                r"```json\s*",
                "",
                raw_result,
                flags=re.IGNORECASE
            )

            raw_result = re.sub(
                r"```\s*$",
                "",
                raw_result
            ).strip()


            # ------------------------------------------------
            # JSON 변환
            # ------------------------------------------------

            result = json.loads(raw_result)


            action = result.get("action", "")
            content = result.get("content", "")


            # ------------------------------------------------
            # 다음 질문
            # ------------------------------------------------

            if action == "QUESTION":

                if not content:

                    raise ValueError("질문 내용이 없습니다.")

                st.session_state.current_question = content.strip()

                st.session_state.question_number += 1

                st.rerun()


            # ------------------------------------------------
            # 정답 추측
            # ------------------------------------------------

            elif action == "GUESS":

                if not content:

                    raise ValueError("추측 내용이 없습니다.")

                st.session_state.current_guess = content.strip()

                st.session_state.game_finished = True

                st.rerun()


            # ------------------------------------------------
            # 예상하지 못한 결과
            # ------------------------------------------------

            else:

                raise ValueError("AI 응답 형식이 올바르지 않습니다.")


        # ----------------------------------------------------
        # 오류 처리
        # ----------------------------------------------------

        except Exception:

            st.warning(
                "답변을 분석하는 중 문제가 생겼어요. 다시 한 번 선택해 주세요."
            )
