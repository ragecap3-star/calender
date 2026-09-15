import calendar
from datetime import datetime
import holidays
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

# 페이지 설정
st.set_page_config(
    page_title="병원 진료일 & 공지사항", page_icon="🏥", layout="centered"
)

# --- 1. 구글 스프레드시트 데이터 불러오기 (공개 CSV 링크 활용) ---
@st.cache_data(ttl=60)  # 60초마다 캐시 갱신 (시트 수정사항 반영)
def load_data():
  # ⚠️ 아래 링크를 본인의 구글 시트 '웹에 게시된 CSV 링크'로 각각 변경하세요!
  notice_csv_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vReihb92LxghRUxSMJinTTUXuPgrEz4MHly0_8IL-T_t_RNsEM7UPgtMAp_UZ7qwXolr1M8V0F7qN_-/pub?gid=0&single=true&output=csv"
  holiday_csv_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vReihb92LxghRUxSMJinTTUXuPgrEz4MHly0_8IL-T_t_RNsEM7UPgtMAp_UZ7qwXolr1M8V0F7qN_-/pub?gid=1822084661&single=true&output=csv"

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

# 사이드바 공지 상시 노출
with st.sidebar:
  st.header("📢 병원 소식")
  st.subheader(notice_title)
  st.write(notice_content)


# --- 3. 월간 달력 네비게이션 (전달 / 다음달 이동) ---
st.title("📅 E건강치과의원 월간 진료일 안내")

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
# 1) 구글 시트 등록 휴진일 리스트화
holiday_dates = []
if not holiday_df.empty and "Date" in holiday_df.columns:
  holiday_dates = holiday_df["Date"].astype(str).tolist()

# 2) 대한민국 공휴일 자동 생성 (현재 조회 중인 연도 기준)
kr_holidays = holidays.KR(years=st.session_state.current_year)

# 3) [예외 처리] 목요일이나 일요일이지만 '강제로 정상 진료'를 해야 하는 날짜가 있다면 여기에 추가 (YYYY-MM-DD)
force_work_dates = ["2026-10-05", "2026-12-10"]

# 달력 시작을 일요일(SUNDAY)로 설정
calendar.setfirstweekday(calendar.SUNDAY)
cal = calendar.monthcalendar(
    st.session_state.current_year, st.session_state.current_month
)
weekdays_name = ["일", "월", "화", "수", "목", "금", "토"]

# HTML/CSS 스타일 및 테이블 헤더 생성
calendar_html = """
<style>
.cal-table { width: 100%; border-collapse: collapse; text-align: center; font-family: sans-serif; table-layout: fixed; }
.cal-th { background-color: #f8f9fa; padding: 10px; border: 1px solid #e9ecef; font-weight: bold; color: #333; }
.cal-td { height: 85px; vertical-align: top; border: 1px solid #e9ecef; padding: 6px; }
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

# 날짜 데이터 채우기
for week in cal:
  calendar_html += "<tr>"
  for i, day in enumerate(week):
    if day == 0:
      calendar_html += (
          '<td class="cal-td" style="background-color: #fdfdfd;"></td>'
      )
    else:
      current_date = datetime(
          st.session_state.current_year, st.session_state.current_month, day
      )
      current_date_str = current_date.strftime("%Y-%m-%d")

      is_sheet_holiday = current_date_str in holiday_dates
      is_kr_holiday = current_date in kr_holidays
      is_force_work = current_date_str in force_work_dates  # 강제 진료일 체크
      is_sunday = i == 0  # 일요일
      is_thursday = i == 4  # 💡 목요일 체크 추가

      # 💡 상태 판별 로직 (강제 진료일 ➔ 구글시트/공휴일 ➔ 일요일/목요일 정기휴일 순서)
      if is_force_work:
        cell_class = "work-bg"
        badge = '<span class="badge-work">진료일</span>'
      elif is_sheet_holiday or is_kr_holiday:
        cell_class = "holiday-bg"
        badge = '<span class="badge-off">휴진일</span>'
      elif is_sunday or is_thursday:  # 💡 일요일과 목요일 모두 정기 휴일로 지정
        cell_class = "weekend-bg"
        badge = '<span class="badge-off">정기휴진</span>'
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

components.html(calendar_html, height=600, scrolling=False)
