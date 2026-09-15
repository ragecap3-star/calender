import calendar
from datetime import datetime
import pandas as pd
import streamlit as st

# 페이지 설정
st.set_page_config(
    page_title="병원 진료일 & 공지사항", page_icon="🏥", layout="centered"
)

# --- 1. 구글 스프레드시트 데이터 불러오기 (공개 CSV 링크 활용) ---
@st.cache_data(ttl=60)  # 60초마다 캐시 갱신 (시트 수정사항 반영)
def load_data():
  # ⚠️ 아래 링크를 본인의 구글 시트 '웹에 게시된 CSV 링크'로 각각 변경하세요!
  notice_csv_url = "YOUR_NOTICE_CSV_LINK"
  holiday_csv_url = "YOUR_HOLIDAY_CSV_LINK"

  try:
    notice_df = pd.read_csv(notice_csv_url)
    holiday_df = pd.read_csv(holiday_csv_url)
  except:
    # 링크가 아직 연결되지 않았을 때 기본값
    notice_df = pd.DataFrame(
        {
            "Key": ["title", "content"],
            "Value": [
                "링크 연결 대기중",
                "구글 시트 CSV 링크를 app.py에 입력해주세요.",
            ],
        }
    )
    holiday_df = pd.DataFrame(columns=["Date", "Reason"])

  return notice_df, holiday_df


notice_df, holiday_df = load_data()

# 공지사항 데이터를 딕셔너리로 변환
notice_dict = dict(zip(notice_df.iloc[:, 0], notice_df.iloc[:, 1]))
notice_title = notice_dict.get("title", "공지사항")
notice_content = notice_dict.get("content", "등록된 내용이 없습니다.")


# --- 2. 팝업 공지사항 구현 ---
@st.dialog("📢 병원 소식 & 공지사항")
def notice_popup():
  st.markdown(f"### **{notice_title}**")
  st.write(notice_content)
  if st.button("확인 (닫기)", use_container_width=True):
    st.rerun()


# 세션을 이용해 첫 접속 시 팝업 띄우기
if "popup_shown" not in st.session_state:
  st.session_state.popup_shown = True
  notice_popup()

# 사이드바에도 공지 상시 노출
with st.sidebar:
  st.header("📢 병원 소식")
  st.subheader(notice_title)
  st.write(notice_content)
  st.divider()
  st.info("💡 구글 스프레드시트만 수정하면 웹사이트 내용이 바로 바뀝니다!")


# --- 3. 월간 달력 네비게이션 (전달 / 다음달 이동) ---
st.title("📅 월간 진료일 안내")

if "current_year" not in st.session_state:
  st.session_state.current_year = datetime.now().year
if "current_month" not in st.session_state:
  st.session_state.current_month = datetime.now().month

col1, col2, col3 = st.columns([1, 2, 1])
with col1:
  if st.button("◀ 이전 달", use_container_width=True):
    if st.session_state.current_month == 1:
      st.session_state.current_month = 12
      st.session_state.current_year -= 1
    else:
      st.session_state.current_month -= 1
    st.rerun()

with col2:
  st.markdown(
      f"<h3 style='text-align: center; margin: 0;'>{st.session_state.current_year}년"
      f" {st.session_state.current_month}월</h3>",
      unsafe_allow_html=True,
  )

with col3:
  if st.button("다음 달 ▶", use_container_width=True):
    if st.session_state.current_month == 12:
      st.session_state.current_month = 1
      st.session_state.current_year += 1
    else:
      st.session_state.current_month += 1
    st.rerun()

st.write("")

# --- 4. 달력 렌더링 및 진료일/휴진일 판별 ---
# 휴진일 데이터 리스트화 (YYYY-MM-DD)
holiday_dates = []
if not holiday_df.empty and "Date" in holiday_df.columns:
  holiday_dates = holiday_df["Date"].astype(str).tolist()

cal = calendar.monthcalendar(
    st.session_state.current_year, st.session_state.current_month
)
weekdays_name = ["월", "화", "수", "목", "금", "토", "일"]

# HTML/CSS로 깔끔한 달력 표 만들기
calendar_html = """
<style>
.cal-table { width: 100%; border-collapse: collapse; text-align: center; font-family: sans-serif; }
.cal-th { background-color: #f8f9fa; padding: 12px; border: 1px solid #e9ecef; font-weight: bold; color: #333; }
.cal-td { height: 85px; vertical-align: top; border: 1px solid #e9ecef; padding: 6px; width: 14.28%; }
.day-num { font-weight: bold; font-size: 15px; margin-bottom: 6px; color: #212529; }
.holiday-bg { background-color: #fff5f5; }
.weekend-bg { background-color: #f8f9fa; }
.work-bg { background-color: #ffffff; }
.badge-off { background-color: #ff6b6b; color: white; font-size: 10px; padding: 2px 6px; border-radius: 4px; display: inline-block; font-weight: 500; }
.badge-work { background-color: #339af0; color: white; font-size: 10px; padding: 2px 6px; border-radius: 4px; display: inline-block; font-weight: 500; }
</style>
<table class="cal-table">
    <tr>
"""

for name in weekdays_name:
  calendar_html += f'<th class="cal-th">{name}</th>'
calendar_html += "</tr>"

for week in cal:
  calendar_html += "<tr>"
  for i, day in enumerate(week):
    if day == 0:
      calendar_html += (
          '<td class="cal-td" style="background-color: #fdfdfd;"></td>'
      )
    else:
      current_date_str = f"{st.session_state.current_year}-{st.session_state.current_month:02d}-{day:02d}"

      is_holiday = current_date_str in holiday_dates
      is_weekend = i >= 5  # 토(5), 일(6) 주말 진료 여부에 따라 조정 가능

      # 상태 판별 및 디자인 적용 (진료일 / 휴진일)
      if is_holiday:
        cell_class = "holiday-bg"
        badge = '<span class="badge-off">휴진일</span>'
      elif is_weekend:
        cell_class = "weekend-bg"
        badge = '<span class="badge-off">주말휴진</span>'
      else:
        cell_class = "work-bg"
        badge = '<span class="badge-work">진료일</span>'

      calendar_html += f"""
                <td class="cal-td {cell_class}">
                    <div class="day-num">{day}</div>
                    {badge}
                </td>
                """
  calendar_html += "</tr>"

calendar_html += "</table>"

st.markdown(calendar_html, unsafe_allow_html=True)
