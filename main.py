import streamlit as st
import pandas as pd
import requests

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo


# ============================================================
# 1. 기본 화면 설정
# ============================================================

st.set_page_config(
    page_title="어제의 박스오피스",
    page_icon="🎬",
    layout="wide"
)

st.title("🎬 어제의 박스오피스")
st.caption("영화진흥위원회(KOBIS) 일일 박스오피스 기준")


# ============================================================
# 2. 한국 시간 기준으로 '어제' 계산
# ============================================================

korea_now = datetime.now(
    ZoneInfo("Asia/Seoul")
)

yesterday = (
    korea_now.date()
    - timedelta(days=1)
)

target_date = yesterday.strftime("%Y%m%d")

display_date = yesterday.strftime(
    "%Y년 %m월 %d일"
)


# ============================================================
# 3. KOBIS 인증키 가져오기
# ============================================================

try:

    kobis_key = st.secrets["KOBIS_KEY"]

except Exception:

    st.error(
        "⚠️ KOBIS 인증키를 찾을 수 없습니다."
    )

    st.info(
        """
        Streamlit Cloud의

        Settings → Secrets

        에 다음과 같이 입력했는지 확인하세요.

        KOBIS_KEY = "본인의_실제_인증키"

        확인할 사항:
        • 이름이 정확히 KOBIS_KEY인지 확인
        • 인증키를 큰따옴표 안에 넣었는지 확인
        • Secrets 저장 후 앱을 다시 실행했는지 확인
        """
    )

    st.stop()


# ============================================================
# 4. KOBIS API 주소
# ============================================================

DAILY_BOXOFFICE_URL = (
    "https://www.kobis.or.kr/"
    "kobisopenapi/webservice/rest/boxoffice/"
    "searchDailyBoxOfficeList.json"
)

MOVIE_INFO_URL = (
    "https://www.kobis.or.kr/"
    "kobisopenapi/webservice/rest/movie/"
    "searchMovieInfo.json"
)


# ============================================================
# 5. KOBIS API 요청 함수
# ============================================================

def request_kobis(url, params):
    """
    KOBIS API에 요청을 보내고 JSON 데이터를 반환합니다.
    """

    try:

        response = requests.get(
            url,
            params=params,
            timeout=10
        )

        response.raise_for_status()

        data = response.json()

    except requests.exceptions.Timeout:

        return None, (
            "KOBIS API 요청 시간이 초과되었습니다."
        )

    except requests.exceptions.RequestException:

        return None, (
            "KOBIS API에 연결하지 못했습니다."
        )

    except ValueError:

        return None, (
            "KOBIS에서 올바른 JSON 데이터를 "
            "받지 못했습니다."
        )


    # KOBIS는 인증키가 잘못되어도
    # HTTP 상태코드가 200일 수 있습니다.
    # 따라서 faultInfo를 직접 확인합니다.

    if "faultInfo" in data:

        fault = data["faultInfo"]

        error_code = fault.get(
            "errorCode",
            "알 수 없음"
        )

        error_message = fault.get(
            "message",
            "알 수 없는 오류"
        )

        return None, (
            f"오류 코드: {error_code}\n"
            f"오류 내용: {error_message}"
        )


    return data, None


# ============================================================
# 6. 어제의 박스오피스 요청
# ============================================================

params = {
    "key": kobis_key,
    "targetDt": target_date
}

data, error = request_kobis(
    DAILY_BOXOFFICE_URL,
    params
)


if error:

    st.error(
        "⚠️ KOBIS API 요청에 실패했습니다."
    )

    st.info(
        f"""
        {error}

        다음 사항을 확인해 보세요.

        • KOBIS 인증키가 정확한지 확인
        • Streamlit Secrets의 이름이 KOBIS_KEY인지 확인
        • KOBIS API 서버 상태 확인
        • 잠시 후 다시 실행
        """
    )

    st.stop()


# ============================================================
# 7. 박스오피스 결과 확인
# ============================================================

if "boxOfficeResult" not in data:

    st.error(
        "⚠️ KOBIS 응답에서 박스오피스 정보를 "
        "찾을 수 없습니다."
    )

    st.info(
        "KOBIS API 응답을 확인한 뒤 다시 실행해 보세요."
    )

    st.stop()


movie_list = data[
    "boxOfficeResult"
].get(
    "dailyBoxOfficeList",
    []
)


if not movie_list:

    st.warning(
        f"📭 {display_date}의 박스오피스 "
        "영화 목록이 없습니다."
    )

    st.info(
        """
        다음 사항을 확인해 보세요.

        • 해당 날짜의 박스오피스가 집계되었는지 확인
        • KOBIS API 서버 상태 확인
        • 인증키가 정상적으로 등록되어 있는지 확인
        • 잠시 후 다시 실행
        """
    )

    st.stop()


# ============================================================
# 8. DataFrame 생성
# ============================================================

df = pd.DataFrame(movie_list)


# 숫자 데이터 변환

for column in [
    "rank",
    "audiCnt",
    "audiAcc",
    "scrnCnt"
]:

    if column in df.columns:

        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        ).fillna(0).astype(int)


# ============================================================
# 9. 영화 상세정보 가져오기
# ============================================================

@st.cache_data(ttl=3600)
def get_movie_info(movie_code):

    params = {
        "key": kobis_key,
        "movieCd": movie_code
    }

    data, error = request_kobis(
        MOVIE_INFO_URL,
        params
    )

    if error:
        return {}

    try:

        return data[
            "movieInfoResult"
        ][
            "movieInfo"
        ]

    except (KeyError, TypeError):

        return {}


# ============================================================
# 10. 영화 상세정보 수집
# ============================================================

with st.spinner(
    "🎬 영화 정보를 불러오는 중..."
):

    movie_details = {}

    for _, row in df.iterrows():

        movie_code = row.get(
            "movieCd"
        )

        if movie_code:

            movie_details[
                movie_code
            ] = get_movie_info(
                movie_code
            )


# ============================================================
# 11. 상세정보 정리 함수
# ============================================================

def get_genres(info):

    genres = info.get(
        "genres",
        []
    )

    return [
        genre.get(
            "genreNm",
            ""
        )
        for genre in genres
        if genre.get("genreNm")
    ]


def get_directors(info):

    directors = info.get(
        "directors",
        []
    )

    return [
        director.get(
            "peopleNm",
            ""
        )
        for director in directors
        if director.get("peopleNm")
    ]


def get_actors(info):

    actors = info.get(
        "actors",
        []
    )

    return [
        actor.get(
            "peopleNm",
            ""
        )
        for actor in actors[:10]
        if actor.get("peopleNm")
    ]


# ============================================================
# 12. 상세정보를 DataFrame에 추가
# ============================================================

df["genres"] = ""
df["directors"] = ""
df["actors"] = ""


for index, row in df.iterrows():

    movie_code = row.get(
        "movieCd"
    )

    info = movie_details.get(
        movie_code,
        {}
    )

    df.at[
        index,
        "genres"
    ] = ", ".join(
        get_genres(info)
    )

    df.at[
        index,
        "directors"
    ] = ", ".join(
        get_directors(info)
    )

    df.at[
        index,
        "actors"
    ] = ", ".join(
        get_actors(info)
    )


# ============================================================
# 13. 날짜 표시
# ============================================================

st.subheader(
    f"📅 {display_date} 박스오피스"
)

st.caption(
    "한국 시간 기준으로 자동 계산한 전날의 박스오피스입니다."
)


# ============================================================
# 14. 1위 영화
# ============================================================

first_movie = df.iloc[0]

first_movie_name = first_movie[
    "movieNm"
]

first_audience = int(
    first_movie["audiCnt"]
)

first_total_audience = int(
    first_movie["audiAcc"]
)

first_screen_count = int(
    first_movie["scrnCnt"]
)


st.markdown(
    "## 🏆 일일 박스오피스 1위"
)

st.markdown(
    f"# 🥇 {first_movie_name}"
)


col1, col2, col3 = st.columns(3)


with col1:

    st.metric(
        "어제 관객수",
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
        f"{first_screen_count:,}개"
    )


# ============================================================
# 15. 관객수 상위 5편 그래프
# ============================================================

st.markdown(
    "## 📊 관객수 상위 5편"
)

top5 = (
    df.sort_values(
        by="audiCnt",
        ascending=False
    )
    .head(5)
    .copy()
)

chart_data = top5[
    [
        "movieNm",
        "audiCnt"
    ]
].set_index(
    "movieNm"
)


st.bar_chart(
    chart_data,
    y="audiCnt",
    horizontal=True
)


# ============================================================
# 16. 내 취향으로 영화 찾기
# ============================================================

st.divider()

st.markdown(
    "## 🍿 내 취향으로 영화 찾기"
)

st.write(
    "원하는 장르를 여러 개 선택하면 "
    "**선택한 모든 장르를 포함하는 영화만** 추천합니다."
)


# ============================================================
# 17. 장르 목록 만들기
# ============================================================

all_genres = []


for genres in df["genres"]:

    if genres:

        for genre in genres.split(","):

            genre = genre.strip()

            if (
                genre
                and genre not in all_genres
            ):

                all_genres.append(
                    genre
                )


# KOBIS 데이터에 없는 장르가 있더라도
# 선택창에 표시할 수 있도록 기본 장르 추가

default_genres = [
    "액션",
    "코미디",
    "드라마",
    "로맨스",
    "스릴러",
    "공포",
    "SF",
    "판타지",
    "애니메이션",
    "범죄",
    "미스터리"
]


for genre in default_genres:

    if genre not in all_genres:

        all_genres.append(
            genre
        )


# ============================================================
# 18. 장르 선택
# ============================================================

selected_genres = st.multiselect(
    "🎭 좋아하는 장르를 선택하세요",
    options=all_genres
)

st.caption(
    "여러 장르를 선택하면 "
    "선택한 장르를 모두 포함하는 영화만 추천합니다. "
    "(AND 조건)"
)


# ============================================================
# 19. 자유 취향 입력
# ============================================================

preference = st.text_input(
    "💭 좋아하는 영화의 특징을 입력하세요",
    placeholder=(
        "예: 긴장감 있는 영화, "
        "반전이 있는 영화"
    )
)


# ============================================================
# 20. 추천 버튼
# ============================================================

recommend_button = st.button(
    "🎬 내 취향에 맞는 영화 찾기",
    use_container_width=True
)


# ============================================================
# 21. 영화 추천
# ============================================================

if recommend_button:

    # 아무것도 선택하지 않은 경우

    if (
        not selected_genres
        and not preference.strip()
    ):

        st.warning(
            "장르를 하나 이상 선택하거나 "
            "영화의 특징을 입력해주세요."
        )

    else:

        result_df = df.copy()

        result_df[
            "recommend_score"
        ] = 0.0


        # ====================================================
        # ⭐ 핵심: 선택한 장르를 '모두' 만족해야 함
        # ====================================================

        if selected_genres:

            genre_match = result_df[
                "genres"
            ].apply(
                lambda movie_genres: all(
                    selected_genre in movie_genres
                    for selected_genre
                    in selected_genres
                )
            )


            # 선택한 장르를 모두 포함하는 영화만
            # 추천 대상에 남깁니다.

            result_df = result_df[
                genre_match
            ].copy()


            # 선택한 장르를 모두 만족한 영화이므로
            # 장르 조건을 만족했다는 점수를 부여합니다.

            result_df[
                "recommend_score"
            ] += 10


        # ====================================================
        # 자유 입력 키워드 반영
        # ====================================================

        keywords = (
            preference
            .lower()
            .split()
        )


        for index, row in result_df.iterrows():

            searchable_text = " ".join(
                [
                    str(row["movieNm"]),
                    str(row["genres"]),
                    str(row["directors"]),
                    str(row["actors"])
                ]
            ).lower()


            for keyword in keywords:

                if (
                    len(keyword) >= 2
                    and keyword
                    in searchable_text
                ):

                    result_df.at[
                        index,
                        "recommend_score"
                    ] += 3


        # ====================================================
        # 관객수를 약간 반영
        # ====================================================

        if not result_df.empty:

            max_audience = (
                result_df["audiCnt"].max()
            )

            if max_audience > 0:

                result_df[
                    "audience_score"
                ] = (
                    result_df["audiCnt"]
                    / max_audience
                    * 2
                )

                result_df[
                    "recommend_score"
                ] += result_df[
                    "audience_score"
                ]


        # ====================================================
        # 추천 영화 정렬
        # ====================================================

        result_df = result_df.sort_values(
            by=[
                "recommend_score",
                "audiCnt"
            ],
            ascending=False
        )


        # ====================================================
        # 조건을 만족하는 영화가 없는 경우
        # ====================================================

        if result_df.empty:

            if selected_genres:

                selected_text = (
                    " + ".join(
                        selected_genres
                    )
                )

                st.warning(
                    f"현재 박스오피스에는 "
                    f"'{selected_text}' "
                    "장르를 모두 포함하는 영화가 없습니다."
                )

                st.info(
                    "선택한 장르 중 일부를 해제하면 "
                    "더 많은 영화를 찾을 수 있습니다."
                )

            else:

                st.warning(
                    "입력한 취향에 맞는 영화가 없습니다."
                )


        # ====================================================
        # 추천 결과 표시
        # ====================================================

        else:

            st.markdown(
                "### 🍿 추천 영화"
            )


            # 최대 3편 표시

            recommendations = (
                result_df.head(3)
            )


            for i, (_, movie) in enumerate(
                recommendations.iterrows()
            ):

                recommendation_number = (
                    i + 1
                )

                movie_name = movie[
                    "movieNm"
                ]

                genres = movie[
                    "genres"
                ]

                audience = int(
                    movie["audiCnt"]
                )

                screens = int(
                    movie["scrnCnt"]
                )

                directors = movie[
                    "directors"
                ]


                st.markdown(
                    f"### "
                    f"{recommendation_number}. "
                    f"🎬 {movie_name}"
                )


                col1, col2, col3 = (
                    st.columns(3)
                )


                with col1:

                    st.write(
                        f"**장르**\n\n"
                        f"{genres if genres else '정보 없음'}"
                    )


                with col2:

                    st.write(
                        f"**어제 관객수**\n\n"
                        f"{audience:,}명"
                    )


                with col3:

                    st.write(
                        f"**스크린수**\n\n"
                        f"{screens:,}개"
                    )


                if directors:

                    st.caption(
                        f"감독: {directors}"
                    )


                st.divider()


# ============================================================
# 22. 전체 박스오피스 표
# ============================================================

st.markdown(
    "## 🎬 전체 박스오피스"
)


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


table_df.columns = [
    "순위",
    "영화명",
    "개봉일",
    "관객수",
    "누적관객",
    "스크린수"
]


# ============================================================
# 23. 개봉일 형식 변경
# ============================================================

def format_open_date(value):

    value = str(value)

    if (
        len(value) == 8
        and value.isdigit()
    ):

        return (
            f"{value[:4]}-"
            f"{value[4:6]}-"
            f"{value[6:]}"
        )

    return value


table_df[
    "개봉일"
] = table_df[
    "개봉일"
].apply(
    format_open_date
)


# ============================================================
# 24. 숫자에 천 단위 콤마
# ============================================================

for column in [
    "관객수",
    "누적관객",
    "스크린수"
]:

    table_df[
        column
    ] = table_df[
        column
    ].apply(
        lambda x: f"{int(x):,}"
    )


# ============================================================
# 25. 표 출력
# ============================================================

st.dataframe(
    table_df,
    use_container_width=True,
    hide_index=True
)


# ============================================================
# 26. 출처
# ============================================================

st.divider()

st.caption(
    "데이터 출처: 영화진흥위원회(KOBIS) Open API"
)
