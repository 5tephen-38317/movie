````python
# ============================================================
# 아인슈타인 - AI 추리 게임
# 파일 위치: pages/chat.py
#
# 기존 main.py는 수정하지 않습니다.
# ============================================================

import json
import re
import streamlit as st
from openai import OpenAI


# ============================================================
# 1. 페이지 기본 설정
# ============================================================

st.set_page_config(
    page_title="아인슈타인",
    page_icon="🧠",
    layout="centered"
)


# ============================================================
# 2. AI 기본 성격
# ============================================================

DEFAULT_PERSONALITY = (
    "너는 중고등학생에게 설명하는 친절한 정보 선생님이야. "
    "어려운 말은 쉬운 말로 바꿔 주고, "
    "반드시 순수 한국어로만 답해."
)


# ============================================================
# 3. 말투 설정
# ============================================================

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


# ============================================================
# 4. Gemini API 연결
# ============================================================

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


# ============================================================
# 5. 세션 상태
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


# ============================================================
# 6. 아인슈타인 테마 디자인
#
# 외부 이미지 파일 없이 CSS와 SVG를 이용합니다.
# ============================================================

st.markdown(
    """
    <style>

    /* -------------------------------------------------------
       전체 배경
       ------------------------------------------------------- */

    .stApp {
        background:
            radial-gradient(
                circle at 50% 20%,
                rgba(255, 224, 151, 0.15),
                transparent 35%
            ),
            linear-gradient(
                135deg,
                #191512 0%,
                #2a211a 45%,
                #120f0d 100%
            );

        color: #f4ead8;
    }


    /* -------------------------------------------------------
       Streamlit 기본 여백
       ------------------------------------------------------- */

    .block-container {
        max-width: 900px;
        padding-top: 2rem;
        padding-bottom: 4rem;
    }


    /* -------------------------------------------------------
       사이드바
       ------------------------------------------------------- */

    section[data-testid="stSidebar"] {
        background:
            linear-gradient(
                180deg,
                #17130f,
                #251d16
            );

        border-right: 1px solid rgba(255, 216, 150, 0.18);
    }


    /* -------------------------------------------------------
       제목
       ------------------------------------------------------- */

    .einstein-title {
        text-align: center;
        font-family: Georgia, serif;
        font-size: 4.5rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        color: #f4d28a;
        text-shadow:
            0 0 12px rgba(244, 210, 138, 0.25);
        margin-bottom: 0;
    }


    .einstein-subtitle {
        text-align: center;
        color: #c8b79d;
        font-family: Georgia, serif;
        font-size: 1rem;
        margin-bottom: 1.5rem;
    }


    /* -------------------------------------------------------
       연구실 카드
       ------------------------------------------------------- */

    .lab-scene {
        position: relative;
        overflow: hidden;
        min-height: 310px;

        border-radius: 24px;

        border: 1px solid rgba(240, 210, 150, 0.22);

        background:
            linear-gradient(
                rgba(30, 23, 17, 0.38),
                rgba(15, 12, 10, 0.72)
            ),
            radial-gradient(
                circle at 20% 30%,
                rgba(255, 215, 130, 0.14),
                transparent 25%
            );

        box-shadow:
            0 20px 60px rgba(0, 0, 0, 0.45);

        margin-bottom: 1.5rem;
    }


    /* -------------------------------------------------------
       연구실 벽
       ------------------------------------------------------- */

    .wall {
        position: absolute;
        inset: 0;

        background-image:
            linear-gradient(
                rgba(255,255,255,0.025) 1px,
                transparent 1px
            ),
            linear-gradient(
                90deg,
                rgba(255,255,255,0.025) 1px,
                transparent 1px
            );

        background-size: 34px 34px;

        opacity: 0.55;
    }


    /* -------------------------------------------------------
       칠판
       ------------------------------------------------------- */

    .blackboard {
        position: absolute;
        left: 25px;
        top: 25px;

        width: 45%;
        height: 170px;

        border-radius: 8px;

        background:
            linear-gradient(
                135deg,
                #18241e,
                #25352b
            );

        border: 8px solid #513b27;

        box-shadow:
            0 8px 20px rgba(0,0,0,0.4);

        padding: 18px;

        color: #d9e0c9;

        font-family: Georgia, serif;
    }


    .formula {
        font-size: 1.15rem;
        line-height: 2;
        opacity: 0.85;
        transform: rotate(-1deg);
    }


    /* -------------------------------------------------------
       책상
       ------------------------------------------------------- */

    .desk {
        position: absolute;
        left: 0;
        right: 0;
        bottom: 0;

        height: 55px;

        background:
            linear-gradient(
                #6a4a2d,
                #382518
            );

        border-top: 8px solid #8a6039;

        box-shadow:
            0 -8px 20px rgba(0,0,0,0.3);
    }


    /* -------------------------------------------------------
       아인슈타인 일러스트
       ------------------------------------------------------- */

    .einstein {
        position: absolute;

        right: 8%;
        bottom: 35px;

        width: 260px;
        height: 250px;

        filter:
            drop-shadow(
                0 15px 15px rgba(0,0,0,0.45)
            );
    }


    /* 머리 */

    .head {
        position: absolute;

        left: 75px;
        top: 35px;

        width: 120px;
        height: 145px;

        background: #d6a878;

        border-radius:
            48% 48% 45% 45%;

        border: 3px solid #8e6345;
    }


    /* 머리카락 */

    .hair {
        position: absolute;

        left: 55px;
        top: 10px;

        width: 165px;
        height: 70px;

        background: #eee9dc;

        border-radius:
            50% 50% 35% 45%;

        transform: rotate(-5deg);

        box-shadow:
            -20px 15px 0 #eee9dc,
            20px 10px 0 #eee9dc,
            0 -15px 0 #eee9dc;
    }


    /* 눈 */

    .eye {
        position: absolute;

        top: 88px;

        width: 12px;
        height: 8px;

        background: #34251d;

        border-radius: 50%;
    }

    .eye.left {
        left: 102px;
    }

    .eye.right {
        left: 150px;
    }


    /* 콧수염 */

    .mustache {
        position: absolute;

        left: 102px;
        top: 118px;

        width: 65px;
        height: 28px;

        background: #eee9dc;

        border-radius:
            50% 50% 60% 60%;

        transform: rotate(-2deg);
    }


    /* 몸 */

    .body {
        position: absolute;

        left: 65px;
        top: 160px;

        width: 145px;
        height: 130px;

        background:
            linear-gradient(
                90deg,
                #383838,
                #555,
                #292929
            );

        border-radius:
            45px 45px 10px 10px;
    }


    /* 손가락 */

    .hand {
        position: absolute;

        left: 15px;
        top: 170px;

        width: 75px;
        height: 20px;

        background: #d6a878;

        border-radius: 15px;

        transform:
            rotate(-12deg);
    }


    /* -------------------------------------------------------
       질문 카드
       ------------------------------------------------------- */

    .question-card {
        background:
            linear-gradient(
                145deg,
                rgba(54, 43, 32, 0.96),
                rgba(31, 25, 20, 0.96)
            );

        border: 1px solid rgba(242, 210, 145, 0.25);

        border-radius: 22px;

        padding: 30px;

        text-align: center;

        box-shadow:
            0 15px 40px rgba(0,0,0,0.35);

        margin-bottom: 1.2rem;
    }


    .question-label {
        color: #c8a96b;
        font-size: 0.9rem;
        letter-spacing: 0.12em;
        margin-bottom: 10px;
    }


    .question-text {
        color: #fff5e5;
        font-family: Georgia, serif;
        font-size: 1.65rem;
        font-weight: 600;
        line-height: 1.5;
    }


    /* -------------------------------------------------------
       안내 문구
       ------------------------------------------------------- */

    .thinking {
        text-align: center;
        color: #bca98e;
        font-size: 0.9rem;
        margin-top: 10px;
    }


    /* -------------------------------------------------------
       Streamlit 버튼 스타일
       ------------------------------------------------------- */

    .stButton > button {
        border-radius: 14px !important;

        border: 1px solid rgba(242, 210, 145, 0.25) !important;

        background:
            linear-gradient(
                145deg,
                #443526,
                #2d241c
            ) !important;

        color: #f5e7ce !important;

        min-height: 48px;

        transition: 0.2s ease;
    }


    .stButton > button:hover {
        border-color: #d9b86c !important;

        background:
            linear-gradient(
                145deg,
                #59432d,
                #3b2d21
            ) !important;

        transform: translateY(-1px);
    }


    /* -------------------------------------------------------
       성공 메시지
       ------------------------------------------------------- */

    .guess-card {
        text-align: center;

        padding: 30px;

        border-radius: 22px;

        background:
            linear-gradient(
                145deg,
                rgba(78, 59, 34, 0.95),
                rgba(37, 29, 22, 0.95)
            );

        border:
            1px solid rgba(242, 210, 145, 0.35);

        margin-bottom: 20px;
    }


    .guess-title {
        color: #d8b96d;
        font-size: 0.95rem;
        letter-spacing: 0.12em;
    }


    .guess-answer {
        color: #fff0ca;
        font-family: Georgia, serif;
        font-size: 2rem;
        font-weight: 700;

        margin-top: 10px;
    }


    /* -------------------------------------------------------
       모바일 대응
       ------------------------------------------------------- */

    @media (max-width: 700px) {

        .einstein-title {
            font-size: 3rem;
        }

        .blackboard {
            width: 55%;
            height: 130px;
        }

        .formula {
            font-size: 0.8rem;
        }

        .einstein {
            right: -25px;
            transform: scale(0.8);
            transform-origin: bottom right;
        }

        .question-text {
            font-size: 1.25rem;
        }

        .lab-scene {
            min-height: 280px;
        }
    }

    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# 7. 아인슈타인 연구실 화면
# ============================================================

st.markdown(
    """
    <div class="einstein-title">아인슈타인</div>

    <div class="einstein-subtitle">
        EINSTEIN · 생각으로 답을 찾아내다
    </div>

    <div class="lab-scene">

        <div class="wall"></div>

        <!-- 연구실 칠판 -->
        <div class="blackboard">
            <div class="formula">
                E = mc²<br>
                상대성 이론<br>
                ∫ f(x) dx<br>
                ? → ? → ?
            </div>
        </div>

        <!-- 책상 -->
        <div class="desk"></div>

        <!-- 아인슈타인 -->
        <div class="einstein">

            <div class="hair"></div>

            <div class="head"></div>

            <div class="eye left"></div>
            <div class="eye right"></div>

            <div class="mustache"></div>

            <div class="body"></div>

            <div class="hand"></div>

        </div>

    </div>
    """,
    unsafe_allow_html=True
)


# ============================================================
# 8. 사이드바
# ============================================================

with st.sidebar:

    st.header("⚙️ 연구실 설정")

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

    st.subheader("아인슈타인의 성격")

    personality = st.text_area(
        "성격 문장",
        value=DEFAULT_PERSONALITY,
        height=150,
        help="아인슈타인에게만 전달되는 설정입니다."
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

        st.rerun()


# ============================================================
# 9. 게임 시작 화면
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

            <div class="thinking">
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

        with st.spinner("아인슈타인이 첫 번째 질문을 생각하고 있습니다..."):

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
- 한국어로만 출력한다.
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
                    .strip('"')
                    .strip("'")
                )

                st.session_state.current_question = question
                st.session_state.question_number = 1

                st.rerun()

            except Exception:

                st.warning(
                    "아인슈타인이 질문을 준비하는 중 문제가 생겼어요. 다시 시도해 주세요."
                )

    st.stop()


# ============================================================
# 10. 추리 진행 화면
# ============================================================

st.markdown(
    f"""
    <div class="question-card">

        <div class="question-label">
            QUESTION {st.session_state.question_number}
        </div>

        <div class="question-text">
            {st.session_state.current_question}
        </div>

        <div class="thinking">
            아인슈타인이 논리적으로 범위를 좁히고 있습니다.
        </div>

    </div>
    """,
    unsafe_allow_html=True
)


# ============================================================
# 11. 지금까지의 기록
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
# 12. 정답 추측 화면
# ============================================================

if st.session_state.game_finished:

    st.markdown(
        f"""
        <div class="guess-card">

            <div class="guess-title">
                EINSTEIN HAS A THEORY
            </div>

            <div class="guess-answer">
                제 추측은<br>
                「{st.session_state.current_guess}」입니다.
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
                "아인슈타인이 정답을 찾아냈습니다!"
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
# 13. 답변 버튼
# ============================================================

st.markdown(
    "<div style='text-align:center;color:#bca98e;margin-bottom:10px;'>"
    "아인슈타인의 질문에 답해주세요."
    "</div>",
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
# 14. 답변 처리
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
    # 지금까지의 질문과 답변을 문자열로 만듭니다.
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
    # Gemini에게 다음 질문 또는 추측을 요청합니다.
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
8. 한국어로만 답한다.

반드시 JSON만 출력하라.

질문을 계속할 경우:

{{
  "action": "QUESTION",
  "content": "질문 내용"
}}

추측할 경우:

{{
  "action": "GUESS",
  "content": "추측한 대상"
}}
"""


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
                ],
                stream=False
            )


            result_text = (
                response.choices[0]
                .message.content
                .strip()
            )


            # ------------------------------------------------
            # JSON 코드블록 제거
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


            result = json.loads(result_text)


            action = result.get(
                "action",
                ""
            )

            content = result.get(
                "content",
                ""
            )


            # ------------------------------------------------
            # 다음 질문
            # ------------------------------------------------

            if action == "QUESTION":

                if not content:
                    raise ValueError()

                st.session_state.current_question = (
                    content.strip()
                )

                st.session_state.question_number += 1

                st.rerun()


            # ------------------------------------------------
            # 정답 추측
            # ------------------------------------------------

            elif action == "GUESS":

                if not content:
                    raise ValueError()

                st.session_state.current_guess = (
                    content.strip()
                )

                st.session_state.game_finished = True

                st.rerun()


            else:

                raise ValueError()


        except Exception:

            st.warning(
                "아인슈타인이 생각하는 중 문제가 생겼어요. 다시 한 번 선택해 주세요."
            )
````
