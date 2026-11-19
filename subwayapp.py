import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
import dotenv 


# 환경변수(API 키) 로드
dotenv.load_dotenv()
#인증키 = os.getenv('seoulkey')
인증키 = st.secrets["seoulkey"]


st.set_page_config(layout="wide")
# 1. 마크다운을 사용한 가로 가운데 정렬 제목 설정
st.markdown("<h1 style='text-align: center;'>서울 지하철 승하차 인원 분석</h1>", unsafe_allow_html=True)
st.markdown("---")

# 2. 날짜 입력 (달력 형식)
selected_date = st.date_input("조회할 일자를 선택하세요")
use_ymd = selected_date.strftime("%Y%m%d")

# '조회하기' 버튼 생성
if st.button("조회하기"):
    if not 인증키:
        st.error("API 인증키가 설정되지 않았습니다. .env 파일을 확인해 주세요.")
    else:
        url = f'http://openapi.seoul.go.kr:8088/{인증키}/json/CardSubwayStatsNew/1/1000/{use_ymd}'
        
        with st.spinner('데이터를 불러오는 중입니다...'):
            try:
                response = requests.get(url)
                data = response.json()
                
                if 'CardSubwayStatsNew' in data and 'row' in data['CardSubwayStatsNew']:
                    rows = data['CardSubwayStatsNew']['row']
                    
                    if len(rows) > 0:
                        df = pd.DataFrame(rows)
                        
                        st.subheader("📋 데이터 기본 정보")
                        st.write(f"**총 수집된 역/노선 수:** {len(df)} 개")
                        
                        # 데이터 전처리
                        df['GTON_TNOPE'] = pd.to_numeric(df['GTON_TNOPE'])
                        df['GTOFF_TNOPE'] = pd.to_numeric(df['GTOFF_TNOPE'])
                        df['총승객수'] = df['GTON_TNOPE'] + df['GTOFF_TNOPE']
                        
                        max_pax = df['총승객수'].max()
                        min_pax = df['총승객수'].min()
                        mean_pax = df['총승객수'].mean()
                        
                        st.subheader("📈 총승객수 통계 요약")
                        # 컬럼을 나누어 통계량 표시 (Streamlit Metric 위젯 활용)
                        col1, col2, col3 = st.columns(3)
                        col1.metric("최대 총승객수", f"{int(max_pax):,} 명")
                        col2.metric("최소 총승객수", f"{int(min_pax):,} 명")
                        col3.metric("평균 총승객수", f"{int(mean_pax):,} 명")
                        
                        st.subheader("🏆 역명별 총승객수 상위 3개 역")
                        top3 = df.groupby('SBWY_STNS_NM')['총승객수'].sum().sort_values(ascending=False).head(3)
                        for i, (station, pax) in enumerate(top3.items(), 1):
                            st.write(f"**{i}위.** {station} : {int(pax):,}명")
                            
                        st.subheader("📊 승하차 인원 상위 10개 항목 차트")
                        
                        # 한글 폰트 설정
                        plt.rcParams['font.family'] = 'NanumGothic'
                        plt.rcParams['axes.unicode_minus'] = False
                        
                        # 차트용 데이터 가공
                        top10 = df.groupby(['SBWY_STNS_NM', 'SBWY_ROUT_LN_NM'])[['총승객수', 'GTON_TNOPE', 'GTOFF_TNOPE']].sum().reset_index()
                        top10 = top10.sort_values(by='총승객수', ascending=False).head(10)
                        top10['x_label'] = top10['SBWY_STNS_NM'] + "(" + top10['SBWY_ROUT_LN_NM'] + ")"
                        
                        # 차트 그리기
                        fig, ax1 = plt.subplots(figsize=(12, 6))
                        
                        ax1.bar(top10['x_label'], top10['총승객수'], width=0.8, color='skyblue', label='총승객수')
                        ax1.tick_params(axis='x', rotation=45)
                        ax1.set_xlabel('')
                        ax1.set_ylabel('총승객수')
                        
                        ax2 = ax1.twinx()
                        ax2.plot(top10['x_label'], top10['GTON_TNOPE'], color='red', marker='o', label='승차총승객수')
                        ax2.plot(top10['x_label'], top10['GTOFF_TNOPE'], color='blue', marker='s', label='하차총승객수')
                        ax2.set_xlabel('')
                        ax2.set_ylabel('승하차 승객수')
                        
                        max_line_val = max(top10['GTON_TNOPE'].max(), top10['GTOFF_TNOPE'].max())
                        ax2.set_ylim(0, max_line_val * 1.5)
                        
                        lines_1, labels_1 = ax1.get_legend_handles_labels()
                        lines_2, labels_2 = ax2.get_legend_handles_labels()
                        ax2.legend(lines_1 + lines_2, labels_1 + labels_2, loc='upper right')
                        
                        y, m, d = use_ymd[:4], use_ymd[4:6], use_ymd[6:]
                        plt.title(f'[{y}년 {m}월 {d}일] 지하철 역명(호선명) 기준 승하차 인원 상위 10개 항목')
                        
                        ax1.grid(axis='y', linestyle='-', alpha=0.5)
                        plt.tight_layout()
                        
                        # 생성된 차트를 Streamlit 화면에 출력
                        st.pyplot(fig)
                        
                    else:
                        st.warning("해당 날짜에 가져올 자료가 없습니다. 다른 날짜를 선택해주세요.")
                else:
                    st.warning("데이터를 불러오지 못했습니다. 서울시 공공데이터포털 서버 상태나 날짜를 확인해주세요.")
            except Exception as e:
                st.error(f"데이터를 가져오는 중 오류가 발생했습니다: {e}")