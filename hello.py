import streamlit as st
import pandas as pd
import os

# 현재 코드 파일이 있는 위치를 기준으로 엑셀 파일 경로를 잡습니다.
base_path = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(base_path, 'ALC 코드 및 BOM 리스트.xlsx')

st.title("🚗 서열코드 검색기")

# 1. 엑셀 파일 로드 (openpyxl 사용)
@st.cache_data
def load_data():
    file_path = 'ALC 코드 및 BOM 리스트.xlsx'
    # ALC 시트와 Sheet2 시트를 엑셀 파일에서 직접 읽어옵니다.
    alc_df = pd.read_excel(file_path, sheet_name='ALC', engine='openpyxl')
    bom_df = pd.read_excel(file_path, sheet_name='Sheet2', engine='openpyxl')
    return alc_df, bom_df

try:
    alc_df, bom_df = load_data()
except Exception as e:
    st.error(f"엑셀 파일 로드 실패: {e}. 파일 이름과 시트명을 확인하세요.")
    st.stop()

# 2. 사용자 입력
# 차종(ALC 시트 '차종' 컬럼) 드롭박스 구성
car_list = alc_df['차종'].unique().tolist()
prod_name = st.selectbox("제품명(차종)", car_list)
direction = st.selectbox("방향", ["LH", "RH"])
seq_code = st.text_input("서열코드 (4자리)", max_chars=4)
qty = st.number_input("수량", min_value=1, value=1)

if st.button("조회"):
    # 1. 입력된 길이만큼만 검색 패턴 생성
    length = len(seq_code)
    if length == 2:
        patterns = [seq_code]
    elif length == 3:
        patterns = [seq_code, seq_code[:2], seq_code[-2:]]
    else:
        patterns = [seq_code, seq_code[:3], seq_code[-3:], seq_code[:2], seq_code[-2:]]
    # 3. 데이터 매칭 (ALC 시트)
    # 입력한 차종 및 방향으로 필터링
    subset = alc_df[(alc_df['차종'] == prod_name) & 
                    (alc_df['사양명'].astype(str).str.contains(direction, na=False))]
    
    # 서열코드 패턴 검색 (앞2/3, 뒤2/3)
    patterns = [seq_code[:3], seq_code[-3:], seq_code[:2], seq_code[-2:]]
    match = None
    
    # 여러 컬럼(고객사품번, 미러텍품번 등) 중 패턴이 포함된 행을 찾음
   # 2. 검색 대상 컬럼 지정
    search_cols = ['고객사품번', '미러텍품번'] 
    
    for p in patterns:
        # 입력값 p의 앞뒤 공백 제거
        p_clean = str(p).strip()
        
        # 데이터프레임의 해당 컬럼들도 앞뒤 공백 제거 후 비교
        mask = subset[search_cols].apply(lambda col: col.astype(str).str.strip().str.contains(p_clean, na=False)).any(axis=1)
        found = subset[mask]
        
        if not found.empty:
            match = found.iloc[0]
            break
            
    if match is not None:
        alc_val = match['ALC']
        h_val = match['F/SUB_ROH1'] # H열 값
        st.success(f"매칭 성공! [ALC: {alc_val}] [F/SUB_ROH1: {h_val}]")
        
        # 4. BOM 전개 (Sheet2/BOM 시트의 '모품번'과 대조)
        bom_result = bom_df[bom_df['모품번'] == h_val]
        
        if not bom_result.empty:
            # 상세 데이터 출력
            result = bom_result[['자품목', '자품명', '소요량', '품목']].copy()
            result['총 필요량'] = result['소요량'] * qty
            st.dataframe(result)
        else:
            st.warning("BOM 시트에서 해당 자재를 찾을 수 없습니다.")
    else:
        st.error("조건에 맞는 제품을 찾을 수 없습니다.")
        # 조회가 안 될 때, 해당 차종/방향으로 필터링된 데이터라도 보여주기
        st.write("---")
        st.write("### 🔍 디버깅: 현재 필터링된 데이터 샘플")
        st.write(subset[['고객사품번', '미러텍품번', 'ALC', '사양명']].head(5))
