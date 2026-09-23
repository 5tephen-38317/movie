import json
import re
import streamlit as st
import streamlit.components.v1 as components
from openai import OpenAI


# ============================================================
# 기본 설정
# ============================================================

st.set_page_config(
    page_title="아인슈타인",
    page_icon="🧠",
    layout="wide"
)


# ============================================================
# AI 기본 성격
# ============================================================

DEFAULT_PERSONALITY = (
    "너는 중고등학생에게 설명하는 친절한 정보 선생님이야. "
    "어려운 말은 쉬운 말로 바꿔 주고, "
    "반드시 순수 한국어로만 답해."
)


# ============================================================
# 말투
# ============================================================

TONE_INSTRUCTIONS = {
    "친절한 선생님": (
        "친절하고 차분하게 설명한다. "
        "학생이 이해하기 쉬운 표현을 사용한다."
    ),

    "시크한 전문가": (
        "간결하고 논리적으로 말한다. "
        "불필요한 설명은 줄이고 핵심을 정확하게 전달한다."
    ),

    "되물어보는 조교": (
        "학생이 스스로 생각하도록 유도한다. "
        "정답을 바로 말하지 않는다. "
        "필요하면 힌트를 하나만 주고 학생에게 다시 질문한다. "
        "학생이 자신의 답을 말하면 그 답을 확인해 준다."
    )
}


# ============================================================
# Gemini API 연결
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
# 세션 상태
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
# 전체 배경 CSS
# ============================================================

st.markdown(
    """
    <style>

    .stApp {
        background:
            radial-gradient(
                circle at 50% 10%,
                rgba(196, 151, 76, 0.13),
                transparent 35%
            ),
            linear-gradient(
                135deg,
                #0b0a09,
                #211812 45%,
                #0c0b0a
            );
    }

    .block-container {
        padding-top: 1rem;
        padding-bottom: 3rem;
        max-width: 1100px;
    }

    section[data-testid="stSidebar"] {
        background:
            linear-gradient(
                180deg,
                #110e0c,
                #1d1510
            );
    }

    /* 제목 */
    .title {
        text-align: center;
        color: #e5c17b;
        font-family: Georgia, serif;
        font-size: 4rem;
        font-weight: 700;
        letter-spacing: 8px;
        margin-bottom: 0;
        text-shadow: 0 4px 20px rgba(0,0,0,0.6);
    }

    .subtitle {
        text-align: center;
        color: #9d8a70;
        font-family: Georgia, serif;
        letter-spacing: 3px;
        margin-bottom: 25px;
    }

    /* 질문 카드 */
    .question-box {
        background:
            linear-gradient(
                145deg,
                rgba(47, 36, 27, 0.97),
                rgba(22, 18, 15, 0.98)
            );

        border: 1px solid rgba(229, 193, 123, 0.28);
        border-radius: 20px;

        padding: 30px;

        margin-top: 20px;

        text-align: center;

        box-shadow:
            0 15px 40px rgba(0,0,0,0.35);
    }

    .question-number {
        color: #c8a15d;
        font-size: 13px;
        letter-spacing: 4px;
        margin-bottom: 12px;
    }

    .question-text {
        color: #fff2d7;
        font-size: 26px;
        font-weight: 600;
        line-height: 1.5;
    }

    /* 추측 */
    .guess-box {
        background:
            linear-gradient(
                145deg,
                rgba(71, 53, 31, 0.98),
                rgba(29, 22, 17, 0.98)
            );

        border: 1px solid rgba(229, 193, 123, 0.4);

        border-radius: 20px;

        padding: 35px;

        text-align: center;

        box-shadow:
            0 20px 50px rgba(0,0,0,0.4);
    }

    .guess-small {
        color: #cba75f;
        letter-spacing: 4px;
        font-size: 13px;
    }

    .guess-name {
        color: #fff0c9;
        font-family: Georgia, serif;
        font-size: 34px;
        font-weight: bold;
        margin-top: 15px;
    }

    /* 버튼 */
    .stButton > button {
        min-height: 50px;
        border-radius: 13px;

        background:
            linear-gradient(
                145deg,
                #493625,
                #2b2119
            );

        color: #f7ead2;

        border: 1px solid rgba(229,193,123,0.3);

        font-weight: 600;
    }

    .stButton > button:hover {
        border-color: #e1bd72;
        background:
            linear-gradient(
                145deg,
                #60472d,
                #3b2b20
            );
    }

    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# 제목
# ============================================================

st.markdown(
    """
    <div class="title">아인슈타인</div>
    <div class="subtitle">
        THE MIND THAT FINDS THE ANSWER
    </div>
    """,
    unsafe_allow_html=True
)


# ============================================================
# 실제 아인슈타인 사진
#
# Wikimedia Commons의 공개 도메인 사진
# ============================================================

EINSTEIN_IMAGE = (
    "https://upload.wikimedia.org/"
    "wikipedia/commons/"
    "thumb/0/09/Einstein.jpg/"
    "600px-Einstein.jpg"
)


# ============================================================
# 연구실 화면
#
# HTML을 st.components.v1.html로 렌더링해서
# 코드가 화면에 그대로 출력되는 문제를 방지합니다.
# ============================================================

lab_html = f"""
<!DOCTYPE html>

<html>
<head>

<meta charset="UTF-8">

<style>

* {{
    box-sizing: border-box;
}}

body {{
    margin: 0;
    background: transparent;
    font-family: Georgia, serif;
}}

.scene {{
    position: relative;

    width: 100%;
    height: 430px;

    overflow: hidden;

    border-radius: 24px;

    background:
        linear-gradient(
            rgba(15, 11, 8, 0.25),
            rgba(9, 7, 5, 0.75)
        ),
        radial-gradient(
            circle at 50% 20%,
            rgba(213, 166, 83, 0.18),
            transparent 35%
        ),
        linear-gradient(
            135deg,
            #3b2c20,
            #17110d
        );

    border: 1px solid rgba(229,193,123,0.28);

    box-shadow:
        0 25px 70px rgba(0,0,0,0.55);
}}


/* -------------------------------------------------
   나무 벽
------------------------------------------------- */

.wall-lines {{
    position: absolute;
    inset: 0;

    background:
        repeating-linear-gradient(
            90deg,
            rgba(255,255,255,0.025) 0px,
            rgba(255,255,255,0.025) 2px,
            transparent 2px,
            transparent 90px
        );
}}


/* -------------------------------------------------
   조명
------------------------------------------------- */

.lamp {{
    position: absolute;

    top: -30px;
    left: 50%;

    transform: translateX(-50%);

    width: 220px;
    height: 180px;

    background:
        radial-gradient(
            ellipse,
            rgba(255,204,110,0.28),
            transparent 65%
        );

    filter: blur(8px);
}}


/* -------------------------------------------------
   칠판
------------------------------------------------- */

.board {{
    position: absolute;

    left: 35px;
    top: 40px;

    width: 45%;
    height: 190px;

    padding: 25px;

    border-radius: 8px;

    background:
        linear-gradient(
            135deg,
            #17241c,
            #26382b
        );

    border: 10px solid #60452d;

    box-shadow:
        0 15px 25px rgba(0,0,0,0.45);
}}

.formula {{
    color: rgba(231,235,216,0.86);

    font-size: 22px;

    line-height: 1.8;

    transform: rotate(-1deg);
}}

.small-formula {{
    font-size: 15px;
    opacity: 0.7;
}}


/* -------------------------------------------------
   책상
------------------------------------------------- */

.desk {{
    position: absolute;

    left: 0;
    right: 0;

    bottom: 0;

    height: 75px;

    background:
        linear-gradient(
            #7a5430,
            #3c2618
        );

    border-top: 8px solid #9a6b3e;

    box-shadow:
        0 -10px 25px rgba(0,0,0,0.45);
}}


/* -------------------------------------------------
   책
------------------------------------------------- */

.book {{
    position: absolute;

    right: 50px;
    bottom: 76px;

    width: 115px;
    height: 30px;

    background: #c9a968;

    border-radius: 3px;

    transform: rotate(-5deg);

    box-shadow:
        0 5px 8px rgba(0,0,0,0.4);
}}


/* -------------------------------------------------
   아인슈타인 사진
------------------------------------------------- */

.einstein-photo {{
    position: absolute;

    right: 55px;
    bottom: 55px;

    height: 350px;
    width: 265px;

    object-fit: cover;
    object-position: center top;

    border-radius: 8px;

    filter:
        grayscale(100%)
        sepia(20%)
        contrast(1.08)
        brightness(0.82);

    box-shadow:
        0 20px 35px rgba(0,0,0,0.6);

    border: 8px solid #e1d3b5;
}}


/* -------------------------------------------------
   말풍선
------------------------------------------------- */

.thought {{
    position: absolute;

    right: 290px;
    top: 35px;

    background: #f5eee2;

    color: #29211a;

    padding: 15px 22px;

    border-radius: 22px;

    font-size: 17px;

    box-shadow:
        0 8px 20px rgba(0,0,0,0.35);
}}

.thought:after {{
    content: "";

    position: absolute;

    right: -10px;
    bottom: 10px;

    width: 20px;
    height: 20px;

    background: #f5eee2;

    transform: rotate(45deg);
}}


/* -------------------------------------------------
   작은 장식
------------------------------------------------- */

.clock {{
    position: absolute;

    right: 350px;
    top: 125px;

    width: 60px;
    height: 60px;

    border-radius: 50%;

    background: #e6d8bc;

    border: 6px solid #63472e;

    box-shadow:
        0 5px 15px rgba(0,0,0,0.35);
}}

.clock:before {{
    content: "";

    position: absolute;

    left: 50%;
    top: 50%;

    width: 20px;
    height: 3px;

    background: #38291e;

    transform-origin: left center;
    transform: rotate(-45deg);
}}

.clock:after {{
    content: "";

    position: absolute;

    left: 50%;
    top: 50%;

    width: 16px;
    height: 3px;

    background: #38291e;

    transform-origin: left center;
    transform: rotate(55deg);
}}


@media(max-width:700px) {{

    .scene {{
        height: 360px;
    }}

    .board {{
        left: 15px;
        width: 52%;
        height: 145px;
    }}

    .formula {{
        font-size: 15px;
    }}

    .einstein-photo {{
        right: 10px;
        height: 285px;
        width: 215px;
    }}

    .thought {{
        right: 170px;
        font-size: 12px;
    }}

}}

</style>

</head>


<body>

<div class="scene">

    <div class="wall-lines"></div>

    <div class="lamp"></div>

    <div class="board">

        <div class="formula">

            E = mc²<br>

            F = ma<br>

            상대성 이론<br>

            <span class="small-formula">
                생각 → 질문 → 추론 → 정답
            </span>

        </div>

    </div>


    <div class="clock"></div>


    <div class="thought">
        흠... 이제 거의 다 왔군.
    </div>


    <img
        class="einstein-photo"
        src="{EINSTEIN_IMAGE}"
        alt="Albert Einstein"
    >


    <div class="book"></div>


    <div class="desk"></div>

</div>

</body>

</html>
"""


components.html(
    lab_html,
    height=450,
    scrolling=False
)


# ============================================================
# 사이드바
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
        height=150
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
# 게임 시작 화면
# ============================================================

if not st.session_state.game_started:

    st.markdown(
        """
        <div class="question-box">

            <div class="question-number">
                EINSTEIN'S THINKING ROOM
            </div>

            <div class="question-text">
                머릿속으로 하나를 정해 보세요.
            </div>

            <div style="color:#a9967c; margin-top:12px;">
                아인슈타인이 질문을 하나씩 던지며 정답을 찾아냅니다.
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
        "🧠 추리 시작",
        type="primary",
        use_container_width=True
    ):

        st.session_state.game_started = True
        st.session_state.game_finished = False
        st.session_state.game_topic = topic
        st.session_state.question_number = 1
        st.session_state.game_history = []
        st.session_state.current_guess = ""

        with st.spinner(
            "아인슈타인이 첫 번째 질문을 생각하고 있습니다..."
        ):

            try:

                prompt = f"""
사용자가 '{topic}' 중 하나를 머릿속으로 정했다.

아직 아무 정보도 없다.

정답 후보를 크게 나눌 수 있는
첫 번째 질문 하나를 만들어라.

질문은 예, 아니오, 잘 모르겠어요로
대답할 수 있어야 한다.

질문 하나만 출력한다.

한국어로만 출력한다.
"""

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

                question = (
                    response.choices[0]
                    .message.content
                    .strip()
                )

                st.session_state.current_question = question

                st.rerun()

            except Exception:

                st.warning(
                    "아인슈타인이 질문을 준비하지 못했어요. 다시 시도해 주세요."
                )

    st.stop()


# ============================================================
# 현재 질문
#
# HTML을 사용하지 않고 Streamlit로 직접 출력합니다.
# ============================================================

st.markdown(
    f"""
    <div class="question-box">

        <div class="question-number">
            QUESTION {st.session_state.question_number}
        </div>

        <div class="question-text">
            {st.session_state.current_question}
        </div>

        <div style="color:#a9967c; margin-top:12px;">
            아인슈타인이 범위를 좁히고 있습니다.
        </div>

    </div>
    """,
    unsafe_allow_html=True
)


# ============================================================
# 추리 기록
# ============================================================

if st.session_state.game_history:

    with st.expander("📜 지금까지의 추리 과정"):

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
# 정답 추측
# ============================================================

if st.session_state.game_finished:

    st.markdown(
        f"""
        <div class="guess-box">

            <div class="guess-small">
                EINSTEIN HAS A THEORY
            </div>

            <div class="guess-name">
                「{st.session_state.current_guess}」
            </div>

        </div>
        """,
        unsafe_allow_html=True
    )

    st.write("아인슈타인의 추측이 맞나요?")

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
# 답변 버튼
# ============================================================

st.markdown(
    """
    <div style="
        text-align:center;
        color:#a9967c;
        margin:18px 0 10px 0;
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
# 답변 처리
# ============================================================

if answer:

    st.session_state.game_history.append(
        {
            "question": st.session_state.current_question,
            "answer": answer
        }
    )


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
    # 다음 질문 또는 정답 추측
    # --------------------------------------------------------

    prompt = f"""
너는 아인슈타인처럼 논리적으로 사고하는 추리 게임 AI다.

사용자는 '{st.session_state.game_topic}' 중 하나를
머릿속으로 정했다.

지금까지의 기록:

{history_text}

다음 행동을 결정하라.

규칙:

1. 지금까지의 답변을 반드시 모두 고려한다.
2. 이미 물어본 질문은 반복하지 않는다.
3. 후보를 효율적으로 좁힌다.
4. 충분한 정보가 있으면 정답을 추측한다.
5. 정보가 부족하면 새로운 질문을 하나 한다.
6. 질문은 예/아니오/잘 모르겠어요로 답할 수 있어야 한다.
7. 정답을 추측할 때는 하나만 선택한다.
8. 반드시 한국어로 출력한다.

JSON 형식으로만 답한다.

질문:

{{
    "action": "QUESTION",
    "content": "질문 내용"
}}

정답 추측:

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
                ]
            )


            result_text = (
                response.choices[0]
                .message.content
                .strip()
            )


            # AI가 JSON을 코드블록으로 보내는 경우 제거
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
            ).strip()


            # ------------------------------------------------
            # 다음 질문
            # ------------------------------------------------

            if action == "QUESTION":

                st.session_state.current_question = content

                st.session_state.question_number += 1

                st.rerun()


            # ------------------------------------------------
            # 정답
            # ------------------------------------------------

            elif action == "GUESS":

                st.session_state.current_guess = content

                st.session_state.game_finished = True

                st.rerun()


            else:

                raise ValueError()


        except Exception:

            st.warning(
                "아인슈타인이 생각하는 중 문제가 생겼어요. 다시 한 번 선택해 주세요."
            )
