import json
import re
import html
import streamlit as st
from openai import OpenAI


# ============================================================
# 아인슈타인 - AI 추리 게임
# 파일 위치: pages/chat.py
# ============================================================


# ------------------------------------------------------------
# 1. 페이지 설정
# ------------------------------------------------------------

st.set_page_config(
    page_title="아인슈타인",
    page_icon="🧠",
    layout="centered"
)


# ------------------------------------------------------------
# 2. 기본 성격
# ------------------------------------------------------------

DEFAULT_PERSONALITY = (
    "너는 중고등학생에게 설명하는 친절한 정보 선생님이야. "
    "어려운 말은 쉬운 말로 바꿔 주고, "
    "반드시 순수 한국어로만 답해."
)


# ------------------------------------------------------------
# 3. 말투 설정
# ------------------------------------------------------------

TONE_INSTRUCTIONS = {
    "친절한 선생님": (
        "친절하고 차분하게 말해. "
        "학생이 이해하기 쉽도록 설명해."
    ),
    "시크한 전문가": (
        "군더더기 없이 핵심을 정확하게 말해. "
        "논리적이고 깔끔하게 설명해."
    ),
    "되물어보는 조교": (
        "학생이 스스로 생각할 수 있도록 질문 중심으로 진행해. "
        "정답을 너무 빨리 알려주지 말고 필요한 경우 힌트를 줘."
    )
}


# ------------------------------------------------------------
# 4. Gemini API 연결
# ------------------------------------------------------------

try:
    api_key = st.secrets["GEMINI_API_KEY"]

    client = OpenAI(
        api_key=api_key,
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
    )

except Exception:
    st.error(
        "AI 연결 설정을 불러오지 못했습니다. 관리자에게 확인해 주세요."
    )
    st.stop()


# ------------------------------------------------------------
# 5. 게임 상태 초기화
# ------------------------------------------------------------

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


# ============================================================
# 6. 아인슈타인 테마 CSS
# ============================================================

st.markdown(
    """
    <style>

    /* 전체 배경 */
    .stApp {
        background:
            radial-gradient(
                circle at 50% 10%,
                rgba(255, 211, 128, 0.13),
                transparent 30%
            ),
            linear-gradient(
                135deg,
                #17120e 0%,
                #2b2118 50%,
                #100d0a 100%
            );
        color: #f5ead7;
    }

    /* 중앙 콘텐츠 크기 */
    .block-container {
        max-width: 900px;
        padding-top: 1.5rem;
        padding-bottom: 3rem;
    }

    /* 사이드바 */
    section[data-testid="stSidebar"] {
        background:
            linear-gradient(
                180deg,
                #17120e,
                #251c15
            );
        border-right: 1px solid rgba(230, 190, 110, 0.2);
    }

    /* 메인 제목 */
    .einstein-title {
        text-align: center;
        color: #e8c77e;
        font-family: Georgia, serif;
        font-size: 4rem;
        font-weight: bold;
        letter-spacing: 0.08em;
        margin-bottom: 0;
        text-shadow: 0 3px 15px rgba(0, 0, 0, 0.5);
    }

    .einstein-subtitle {
        text-align: center;
        color: #bba98f;
        font-family: Georgia, serif;
        margin-bottom: 22px;
    }

    /* 연구실 */
    .lab {
        position: relative;
        height: 330px;
        overflow: hidden;
        border-radius: 24px;
        border: 1px solid rgba(232, 199, 126, 0.28);
        background:
            linear-gradient(
                rgba(25, 19, 14, 0.18),
                rgba(10, 8, 6, 0.65)
            ),
            repeating-linear-gradient(
                90deg,
                rgba(255,255,255,0.025) 0px,
                rgba(255,255,255,0.025) 2px,
                transparent 2px,
                transparent 70px
            ),
            linear-gradient(
                #3a2d23,
                #17120e
            );
        box-shadow:
            0 20px 50px rgba(0, 0, 0, 0.5);
        margin-bottom: 20px;
    }

    /* 창문 */
    .window {
        position: absolute;
        left: 25px;
        top: 25px;
        width: 180px;
        height: 125px;
        border: 8px solid #533b28;
        background:
            linear-gradient(
                135deg,
                #3d4d55,
                #9aa6a7,
                #34434b
            );
        box-shadow:
            inset 0 0 30px rgba(0,0,0,0.5);
    }

    .window:before {
        content: "";
        position: absolute;
        left: 50%;
        top: 0;
        bottom: 0;
        width: 5px;
        background: #533b28;
        transform: translateX(-50%);
    }

    .window:after {
        content: "";
        position: absolute;
        top: 50%;
        left: 0;
        right: 0;
        height: 5px;
        background: #533b28;
        transform: translateY(-50%);
    }

    /* 칠판 */
    .blackboard {
        position: absolute;
        left: 230px;
        top: 25px;
        width: 310px;
        height: 145px;
        background:
            linear-gradient(
                135deg,
                #17251d,
                #26372b
            );
        border: 9px solid #513b27;
        border-radius: 6px;
        box-shadow:
            0 10px 20px rgba(0,0,0,0.4);
        padding: 15px;
        box-sizing: border-box;
    }

    .formula {
        color: #d8dfcb;
        font-family: Georgia, serif;
        font-size: 18px;
        line-height: 1.8;
        transform: rotate(-1deg);
    }

    /* 책상 */
    .desk {
        position: absolute;
        bottom: 0;
        left: 0;
        right: 0;
        height: 65px;
        background:
            linear-gradient(
                #714c2c,
                #3b2517
            );
        border-top: 9px solid #94663c;
    }

    /* 아인슈타인 캐릭터 */
    .einstein {
        position: absolute;
        right: 35px;
        bottom: 38px;
        width: 245px;
        height: 270px;
        filter:
            drop-shadow(
                0 15px 12px rgba(0,0,0,0.5)
            );
    }

    /* 머리카락 */
    .hair {
        position: absolute;
        left: 48px;
        top: 5px;
        width: 150px;
        height: 75px;
        background: #eee9dc;
        border-radius: 55% 45% 40% 50%;
        box-shadow:
            -25px 17px 0 #eee9dc,
            22px 10px 0 #eee9dc,
            2px -12px 0 #eee9dc;
        z-index: 3;
    }

    /* 얼굴 */
    .face {
        position: absolute;
        left: 65px;
        top: 43px;
        width: 120px;
        height: 145px;
        background: #d8a97c;
        border: 3px solid #80583d;
        border-radius: 48% 48% 45% 45%;
        z-index: 2;
    }

    /* 귀 */
    .ear {
        position: absolute;
        top: 100px;
        width: 25px;
        height: 45px;
        background: #d8a97c;
        border: 3px solid #80583d;
        border-radius: 50%;
        z-index: 1;
    }

    .ear.left {
        left: 52px;
    }

    .ear.right {
        left: 172px;
    }

    /* 눈 */
    .eye {
        position: absolute;
        top: 91px;
        width: 12px;
        height: 7px;
        background: #2c211b;
        border-radius: 50%;
        z-index: 4;
    }

    .eye.left {
        left: 98px;
    }

    .eye.right {
        left: 143px;
    }

    /* 안경 */
    .glasses {
        position: absolute;
        top: 82px;
        left: 91px;
        width: 75px;
        height: 32px;
        z-index: 5;
    }

    .glasses:before,
    .glasses:after {
        content: "";
        position: absolute;
        width: 31px;
        height: 25px;
        border: 3px solid #30251d;
        border-radius: 50%;
    }

    .glasses:before {
        left: 0;
    }

    .glasses:after {
        right: 0;
    }

    /* 콧수염 */
    .mustache {
        position: absolute;
        left: 92px;
        top: 120px;
        width: 68px;
        height: 30px;
        background: #eee9dc;
        border-radius: 50%;
        z-index: 5;
    }

    /* 몸 */
    .body {
        position: absolute;
        left: 48px;
        top: 175px;
        width: 165px;
        height: 125px;
        background:
            linear-gradient(
                90deg,
                #292929,
                #555555,
                #292929
            );
        border-radius: 55px 55px 10px 10px;
        z-index: 1;
    }

    /* 손 */
    .hand {
        position: absolute;
        left: 10px;
        top: 185px;
        width: 82px;
        height: 23px;
        background: #d8a97c;
        border-radius: 20px;
        transform: rotate(-12deg);
        z-index: 4;
    }

    /* 생각 중 표시 */
    .thought {
        position: absolute;
        right: 210px;
        top: 20px;
        background: #f2eadc;
        color: #2b2119;
        padding: 13px 18px;
        border-radius: 20px;
        font-family: Georgia, serif;
        font-size: 16px;
        box-shadow: 0 8px 20px rgba(0,0,0,0.35);
    }

    .thought:after {
        content: "";
        position: absolute;
        right: -8px;
        bottom: 10px;
        width: 18px;
        height: 18px;
        background: #f2eadc;
        transform: rotate(45deg);
    }

    /* 질문 카드 */
    .question-card {
        background:
            linear-gradient(
                145deg,
                rgba(61, 47, 34, 0.97),
                rgba(29, 23, 18, 0.97)
            );
        border: 1px solid rgba(232, 199, 126, 0.25);
        border-radius: 22px;
        padding: 28px;
        text-align: center;
        box-shadow:
            0 15px 40px rgba(0,0,0,0.4);
        margin-bottom: 18px;
    }

    .question-label {
        color: #caa85f;
        font-size: 13px;
        letter-spacing: 0.16em;
        margin-bottom: 10px;
    }

    .question-text {
        color: #fff4df;
        font-family: Georgia, serif;
        font-size: 25px;
        font-weight: bold;
        line-height: 1.5;
    }

    /* 추측 결과 */
    .guess-card {
        background:
            linear-gradient(
                145deg,
                rgba(77, 58, 35, 0.98),
                rgba(35, 27, 20, 0.98)
            );
        border: 1px solid rgba(232, 199, 126, 0.4);
        border-radius: 22px;
        padding: 30px;
        text-align: center;
        margin-bottom: 20px;
        box-shadow:
            0 15px 45px rgba(0,0,0,0.45);
    }

    .guess-small {
        color: #d1b36d;
        font-size: 14px;
        letter-spacing: 0.15em;
    }

    .guess-answer {
        color: #fff0c9;
        font-family: Georgia, serif;
        font-size: 32px;
        font-weight: bold;
        margin-top: 12px;
    }

    /* 버튼 */
    .stButton > button {
        min-height: 48px !important;
        border-radius: 14px !important;
        border: 1px solid rgba(232, 199, 126, 0.28) !important;
        background:
            linear-gradient(
                145deg,
                #493625,
                #2d2219
            ) !important;
        color: #f8ead2 !important;
        font-weight: 600 !important;
    }

    .stButton > button:hover {
        border-color: #d9b86c !important;
        background:
            linear-gradient(
                145deg,
                #5c432b,
                #3b2b1e
            ) !important;
    }

    /* 모바일 */
    @media (max-width: 700px) {

        .einstein-title {
            font-size: 3rem;
        }

        .lab {
            height: 300px;
        }

        .window {
            width: 120px;
            height: 90px;
        }

        .blackboard {
            left: 160px;
            width: 180px;
            height: 110px;
        }

        .formula {
            font-size: 12px;
        }

        .einstein {
            right: -20px;
            transform: scale(0.78);
            transform-origin: bottom right;
        }

        .thought {
            right: 120px;
            font-size: 12px;
        }

        .question-text {
            font-size: 20px;
        }
    }

    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# 7. 아인슈타인 제목
# ============================================================

st.markdown(
    """
    <div class="einstein-title">아인슈타인</div>
    <div class="einstein-subtitle">
        EINSTEIN · 논리로 답을 찾아내다
    </div>
    """,
    unsafe_allow_html=True
)


# ============================================================
# 8. 아인슈타인 연구실
# ============================================================

st.markdown(
    """
    <div class="lab">

        <div class="window"></div>

        <div class="blackboard">
            <div class="formula">
                E = mc²<br>
                상대성 이론<br>
                F = ma<br>
                ? → ? → ?
            </div>
        </div>

        <div class="thought">
            흠... 그렇다면?
        </div>

        <div class="einstein">

            <div class="hair"></div>

            <div class="ear left"></div>
            <div class="ear right"></div>

            <div class="face"></div>

            <div class="eye left"></div>
            <div class="eye right"></div>

            <div class="glasses"></div>

            <div class="mustache"></div>

            <div class="body"></div>

            <div class="hand"></div>

        </div>

        <div class="desk"></div>

    </div>
    """,
    unsafe_allow_html=True
)


# ============================================================
# 9. 사이드바
# ============================================================

with st.sidebar:

    st.header("🧠 아인슈타인 설정")

    st.subheader("말투 고르기")

    selected_tone = st.selectbox(
        "말투",
        [
            "친절한 선생님",
            "시크한 전문가",
            "되물어보는 조교"
        ],
        label_visibility="collapsed"
    )

    st.subheader("성격 문장")

    personality = st.text_area(
        "아인슈타인의 성격",
        value=DEFAULT_PERSONALITY,
        height=150,
        help="이 내용은 AI에게만 전달됩니다."
    )

    st.divider()

    if st.button(
        "🔄 새로운 추리 시작",
        use_container_width=True
    ):

        st.session_state.game_started = False
        st.session_state.game_finished = False
        st.session_state.game_topic = ""
        st.session_state.question_number = 0
        st.session_state.game_history = []
        st.session_state.current_question = ""
        st.session_state.current_guess = ""

        st.rerun()

    if st.button(
        "🗑️ 대화 지우기",
        use_container_width=True
    ):

        st.session_state.game_history = []
        st.session_state.question_number = 0

        st.rerun()


# ============================================================
# 10. 게임 시작 화면
# ============================================================

if not st.session_state.game_started:

    st.markdown(
        """
        <div class="question-card">

            <div class="question-label">
                EINSTEIN'S THINKING ROOM
            </div>

            <div class="question-text">
                머릿속으로 하나를 정해 보세요.
            </div>

            <div style="color:#bca98e; margin-top:12px;">
                아인슈타인이 질문을 통해 정답을 추리합니다.
            </div>

        </div>
        """,
        unsafe_allow_html=True
    )

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

    if st.button(
        "🧠 아인슈타인에게 추리 맡기기",
        type="primary",
        use_container_width=True
    ):

        st.session_state.game_started = True
        st.session_state.game_finished = False
        st.session_state.game_topic = topic
        st.session_state.question_number = 0
        st.session_state.game_history = []
        st.session_state.current_guess = ""

        with st.spinner(
            "아인슈타인이 첫 번째 질문을 생각하고 있습니다..."
        ):

            try:

                prompt = f"""
너는 아인슈타인처럼 논리적으로 생각하는 추리 게임 AI다.

사용자가 '{topic}' 중 하나를 머릿속으로 정했다.

아직 아무 정보도 없다.

후보를 크게 나눌 수 있는 첫 번째 질문을 만들어라.

규칙:
- 예/아니오/잘 모르겠어요로 대답할 수 있어야 한다.
- 질문 하나만 출력한다.
- 설명하지 않는다.
- 반드시 한국어로 출력한다.
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
                            "content": prompt
                        }
                    ]
                )

                question = (
                    response.choices[0]
                    .message.content
                    .strip()
                )

                question = question.strip('"').strip("'")

                st.session_state.current_question = question
                st.session_state.question_number = 1

                st.rerun()

            except Exception:

                st.warning(
                    "아인슈타인이 질문을 준비하는 중 문제가 생겼어요. 다시 시도해 주세요."
                )

    st.stop()


# ============================================================
# 11. 현재 질문 화면
# ============================================================

safe_question = html.escape(
    st.session_state.current_question
)

st.markdown(
    f"""
    <div class="question-card">

        <div class="question-label">
            QUESTION {st.session_state.question_number}
        </div>

        <div class="question-text">
            {safe_question}
        </div>

        <div style="color:#bca98e; margin-top:12px;">
            아인슈타인이 논리적으로 범위를 좁히고 있습니다.
        </div>

    </div>
    """,
    unsafe_allow_html=True
)


# ============================================================
# 12. 지금까지의 추리 과정
# ============================================================

if st.session_state.game_history:

    with st.expander(
        "📜 지금까지의 추리 과정"
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


# ============================================================
# 13. AI가 정답을 추측한 경우
# ============================================================

if st.session_state.game_finished:

    safe_guess = html.escape(
        st.session_state.current_guess
    )

    st.markdown(
        f"""
        <div class="guess-card">

            <div class="guess-small">
                EINSTEIN HAS A THEORY
            </div>

            <div class="guess-answer">
                제 추측은<br>
                「{safe_guess}」입니다.
            </div>

        </div>
        """,
        unsafe_allow_html=True
    )

    st.write(
        "아인슈타인의 추측이 맞나요?"
    )

    col1, col2 = st.columns(2)

    with col1:

        if st.button(
            "🎉 맞아요!",
            use_container_width=True
        ):

            st.balloons()

            st.success(
                "아인슈타인이 정답을 찾아냈습니다! 🎉"
            )

    with col2:

        if st.button(
            "❌ 아니에요",
            use_container_width=True
        ):

            st.session_state.game_finished = False
            st.session_state.current_guess = ""

            st.session_state.question_number += 1

            st.rerun()

    st.stop()


# ============================================================
# 14. 답변 버튼
# ============================================================

st.markdown(
    """
    <div style="
        text-align:center;
        color:#bca98e;
        margin-bottom:10px;
    ">
        아인슈타인의 질문에 답해주세요.
    </div>
    """,
    unsafe_allow_html=True
)


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
# 15. 답변 처리
# ============================================================

if answer:

    current_question = st.session_state.current_question

    st.session_state.game_history.append(
        {
            "question": current_question,
            "answer": answer
        }
    )


    # --------------------------------------------------------
    # 지금까지의 기록을 AI가 읽을 수 있도록 정리
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
    # AI에게 다음 행동 요청
    # --------------------------------------------------------

    prompt = f"""
너는 아인슈타인처럼 논리적으로 사고하는 추리 게임 AI다.

사용자는 '{st.session_state.game_topic}' 중 하나를
머릿속으로 정했다.

지금까지의 추리 기록:

{history_text}

다음 행동을 결정하라.

규칙:

1. 후보를 최대한 효율적으로 줄여라.
2. 이미 물어본 질문과 거의 같은 질문은 하지 마라.
3. '잘 모르겠어요'는 확정 정보로 취급하지 마라.
4. 충분한 정보가 모이면 정답을 추측하라.
5. 아직 정보가 부족하면 새로운 질문을 하나만 하라.
6. 질문은 예/아니오/잘 모르겠어요로 답할 수 있어야 한다.
7. 추측할 때는 가장 가능성이 높은 대상 하나만 말한다.
8. 반드시 한국어로 답한다.

반드시 아래 JSON 형식으로만 답하라.

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
    # Gemini 호출
    # --------------------------------------------------------

    with st.spinner(
        "🧠 아인슈타인이 생각하고 있습니다..."
    ):

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
                        "content": prompt
                    }
                ]
            )


            result_text = (
                response.choices[0]
                .message.content
                .strip()
            )


            # ------------------------------------------------
            # AI가 JSON을 코드블록으로 감쌀 경우 제거
            # ------------------------------------------------

            result_text = re.sub(
                r"```json\s*",
                "",
                result_text,
                flags=re.IGNORECASE
            )

            result_text = re.sub(
                r"```\s*$",
                "",
                result_text
            ).strip()


            # ------------------------------------------------
            # JSON 해석
            # ------------------------------------------------

            result = json.loads(result_text)

            action = result.get(
                "action",
                ""
            )

            content = result.get(
                "content",
                ""
            ).strip()


            # ------------------------------------------------
            # 다음 질문
            # ------------------------------------------------

            if action == "QUESTION":

                if not content:
                    raise ValueError(
                        "질문이 없습니다."
                    )

                st.session_state.current_question = content

                st.session_state.question_number += 1

                st.rerun()


            # ------------------------------------------------
            # 정답 추측
            # ------------------------------------------------

            elif action == "GUESS":

                if not content:
                    raise ValueError(
                        "추측 결과가 없습니다."
                    )

                st.session_state.current_guess = content

                st.session_state.game_finished = True

                st.rerun()


            # ------------------------------------------------
            # 잘못된 응답
            # ------------------------------------------------

            else:

                raise ValueError(
                    "AI 응답 형식이 올바르지 않습니다."
                )


        except Exception:

            st.warning(
                "아인슈타인이 생각하는 중 문제가 생겼어요. 다시 한 번 선택해 주세요."
            )
