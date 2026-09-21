import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo


# --------------------------------------------------
# 1. 기본 화면 설정
# --------------------------------------------------

st.set_page_config(
    page_title="어제의 박스오피스",
    page_icon="🎬",
    layout="wide"
)

st.title("🎬 어제의 박스오피스")
st.caption("영화진흥위원회(KOBIS) 일일 박스오피스 기준")


# --------------------------------------------------
# 2. 한국 시간 기준으로 '어제' 계산하기
# --------------------------------------------------
# Streamlit Cloud 서버의 시간이 한국 시간이 아닐 수 있으므로
# 반드시 Asia/Seoul 시간대를 사용합니다.

korea_time = datetime.now(ZoneInfo("Asia/Seoul"))
yesterday = korea_time.date() - timedelta(days=1)

# KOBIS API가 요구하는 날짜 형식: YYYYMMDD
target_date = yesterday.strftime("%Y%m%d")

# 화면에 보여줄 날짜
display_date = yesterday.strftime("%Y년 %m월 %d일")


# --------------------------------------------------
# 3. KOBIS 인증키 가져오기
# --------------------------------------------------
# 실제 인증키는 코드에 적지 않고
# Streamlit Cloud의 Secrets에 KOBIS_KEY라는 이름으로 저장합니다.

try:
    kobis_key = st.secrets["KOBIS_KEY"]
except Exception:
    st.error("⚠️ KOBIS 인증키를 찾을 수 없습니다.")
    st.info(
        "Streamlit Cloud의 앱 설정에서 Secrets를 열고 "
        "다음과 같이 입력했는지 확인하세요:\n\n"
        "KOBIS_KEY = \"발급받은 인증키\""
    )
    st.stop()


# --------------------------------------------------
# 4. KOBIS API 요청
# --------------------------------------------------

API_URL = (
    "https://www.kobis.or.kr/"
    "kobisopenapi/webservice/rest/boxoffice/"
    "searchDailyBoxOfficeList.json"
)

params = {
    "key": kobis_key,
    "targetDt": target_date
}


try:
    response = requests.get(
        API_URL,
        params=params,
        timeout=10
    )

    # HTTP 자체가 실패한 경우
    response.raise_for_status()

    data = response.json()

except requests.exceptions.Timeout:
    st.error("⚠️ KOBIS API 요청 시간이 초과되었습니다.")
    st.info(
        "인터넷 연결이나 KOBIS 서버 상태를 확인한 뒤 "
        "잠시 후 다시 실행해 보세요."
    )
    st.stop()

except requests.exceptions.RequestException as e:
    st.error("⚠️ KOBIS API에 연결하지 못했습니다.")
    st.info(
        "인터넷 연결, KOBIS API 주소, KOBIS 서버 상태를 확인해 보세요."
    )
    st.stop()

except ValueError:
    st.error("⚠️ KOBIS에서 올바른 JSON 데이터를 받지 못했습니다.")
    st.info(
        "KOBIS API 서버의 응답 상태를 확인한 뒤 잠시 후 다시 시도해 보세요."
    )
    st.stop()


# --------------------------------------------------
# 5. KOBIS 인증 오류 확인
# --------------------------------------------------
# KOBIS는 인증키가 잘못되어도 HTTP 상태코드가 200일 수 있습니다.
# 따라서 faultInfo가 있는지를 반드시 확인해야 합니다.

if "faultInfo" in data:
    fault_info = data["faultInfo"]

    fault_code = fault_info.get("errorCode", "알 수 없음")
    fault_message = fault_info.get("message", "알 수 없는 오류")

    st.error("⚠️ KOBIS API에서 오류를 반환했습니다.")

    st.info(
        f"오류 코드: {fault_code}\n\n"
        f"오류 내용: {fault_message}\n\n"
        "KOBIS 인증키가 정확한지 확인하고, "
        "Streamlit Cloud의 Secrets에 KOBIS_KEY가 올바르게 등록되어 있는지 확인하세요."
    )

    st.stop()


# --------------------------------------------------
# 6. 박스오피스 데이터 확인
# --------------------------------------------------

try:
    boxoffice_result = data["boxOfficeResult"]
    movie_list = boxoffice_result["dailyBoxOfficeList"]

except (KeyError, TypeError):
    st.error("⚠️ KOBIS 응답에서 영화 목록을 찾을 수 없습니다.")
    st.info(
        "KOBIS API 응답 구조가 정상인지 확인하거나 "
        "잠시 후 다시 실행해 보세요."
    )
    st.stop()


# --------------------------------------------------
# 7. 영화 목록이 비어 있는 경우
# --------------------------------------------------

if not movie_list:
    st.warning("📭 해당 날짜의 박스오피스 영화 목록이 없습니다.")

    st.info(
        f"조회 날짜: {display_date}\n\n"
        "다음 사항을 확인해 보세요.\n\n"
        "• KOBIS에서 해당 날짜의 박스오피스가 집계되었는지 확인\n"
        "• KOBIS API가 정상적으로 응답했는지 확인\n"
        "• 인증키가 정상적으로 등록되어 있는지 확인\n"
        "• 잠시 후 다시 실행"
    )

    st.stop()


# --------------------------------------------------
# 8. 데이터프레임 만들기
# --------------------------------------------------

df = pd.DataFrame(movie_list)


# --------------------------------------------------
# 9. 숫자 데이터를 숫자로 변환
# --------------------------------------------------
# KOBIS API에서는 숫자도 문자열로 전달되므로
# 그래프나 숫자 표시를 위해 정수로 변환합니다.

number_columns = [
    "rank",
    "audiCnt",
    "audiAcc",
    "scrnCnt",
    "showCnt"
]

for column in number_columns:
    if column in df.columns:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        ).fillna(0).astype(int)


# --------------------------------------------------
# 10. 제목과 조회 날짜
# --------------------------------------------------

st.subheader(f"📅 {display_date} 박스오피스")

st.caption(
    "한국 시간 기준으로 자동 계산된 전날의 일일 박스오피스입니다."
)


# --------------------------------------------------
# 11. 1위 영화 확인
# --------------------------------------------------

first_movie = df.iloc[0]

first_movie_name = first_movie["movieNm"]
first_audience = int(first_movie["audiCnt"])
first_total_audience = int(first_movie["audiAcc"])


# --------------------------------------------------
# 12. 1위 영화 지표 카드
# --------------------------------------------------

st.markdown("## 🏆 1위 영화")

st.markdown(
    f"### 🥇 {first_movie_name}"
)

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "일일 관객수",
        f"{first_audience:,}명"
    )

with col2:
    st.metric(
        "누적 관객수",
        f"{first_total_audience:,}명"
    )

with col3:
    st.metric(
        "스크린수",
        f"{int(first_movie['scrnCnt']):,}개"
    )


# --------------------------------------------------
# 13. 관객수 상위 5편 막대그래프
# --------------------------------------------------

st.markdown("## 📊 관객수 상위 5편")

top5 = df.head(5).copy()

# 그래프에서 영화명을 인덱스로 사용
chart_data = top5[
    ["movieNm", "audiCnt"]
].set_index("movieNm")

st.bar_chart(
    chart_data,
    y="audiCnt",
    horizontal=True
)


# --------------------------------------------------
# 14. 전체 영화 목록 표
# --------------------------------------------------

st.markdown("## 🎬 전체 박스오피스")

table_df = df[
    [
        "rank",
        "movieNm",
        "openDt",
        "audiCnt",
        "audiAcc",
        "scrnCnt"
    ]
].copy()


# 표에 표시할 한글 이름으로 변경
table_df.columns = [
    "순위",
    "영화명",
    "개봉일",
    "관객수",
    "누적관객",
    "스크린수"
]


# 개봉일을 보기 좋은 형태로 변경
def format_open_date(value):
    value = str(value)

    if len(value) == 8 and value.isdigit():
        return (
            f"{value[:4]}-{value[4:6]}-{value[6:]}"
        )

    return value


table_df["개봉일"] = table_df["개봉일"].apply(
    format_open_date
)


# 숫자를 천 단위 콤마로 표시
for column in [
    "관객수",
    "누적관객",
    "스크린수"
]:
    table_df[column] = table_df[column].map(
        lambda x: f"{int(x):,}"
    )


st.dataframe(
    table_df,
    use_container_width=True,
    hide_index=True
)


# --------------------------------------------------
# 15. 데이터 출처
# --------------------------------------------------

st.caption(
    "데이터 출처: 영화진흥위원회(KOBIS) 일일 박스오피스 Open API"
)
