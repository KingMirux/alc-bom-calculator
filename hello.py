import streamlit as st
import pandas as pd

st.set_page_config(page_title="ALC/BOM 자재 조회", page_icon="🔧", layout="wide")

DATA_PATH = "data.xlsx"


@st.cache_data
def load_data():
    alc = pd.read_excel(DATA_PATH, sheet_name="ALC")
    bom = pd.read_excel(DATA_PATH, sheet_name="BOM")

    # 공백/결측 정리
    alc["차종"] = alc["차종"].astype(str).str.strip()
    alc["ALC"] = alc["ALC"].astype(str).str.strip()
    alc = alc[alc["ALC"] != "nan"]

    bom["모품번"] = bom["모품번"].astype(str).str.strip()
    return alc, bom


alc_df, bom_df = load_data()

st.title("🔧 ALC/BOM 자재 조회")
st.caption("차종과 서열코드(ALC)를 선택하면 해당 사양에 들어가는 단품 자재품번/자재명을 조회합니다.")

col1, col2 = st.columns(2)

with col1:
    car_types = sorted(alc_df["차종"].unique())
    selected_car = st.selectbox("차종 선택", car_types)

with col2:
    alc_codes = sorted(alc_df.loc[alc_df["차종"] == selected_car, "ALC"].unique())
    selected_alc = st.selectbox("서열코드(ALC) 선택", alc_codes)

matched = alc_df[(alc_df["차종"] == selected_car) & (alc_df["ALC"] == selected_alc)]

if matched.empty:
    st.warning("일치하는 사양이 없습니다.")
else:
    # LH/RH 등 동일 서열코드에 여러 사양이 걸리는 경우 선택하게 함
    if len(matched) > 1:
        spec_options = matched["사양명"].tolist()
        selected_spec = st.radio("사양 선택", spec_options, horizontal=True)
        row = matched[matched["사양명"] == selected_spec].iloc[0]
    else:
        row = matched.iloc[0]

    st.divider()
    st.subheader(f"📋 사양 정보 — {row['사양명']}")

    info_cols = st.columns(4)
    info_cols[0].metric("고객사품번", row["고객사품번"])
    info_cols[1].metric("미러텍품번", row["미러텍품번"])
    info_cols[2].metric("F/SUB HALB", row["F/SUB_HALB"])
    info_cols[3].metric("F/SUB ROH1", row["F/SUB_ROH1"])

    st.subheader("🧩 하위 단품 자재 목록 (BOM)")

    parent_code = str(row["F/SUB_ROH1"]).strip()
    bom_matched = bom_df[bom_df["모품번"] == parent_code]

    if bom_matched.empty:
        st.info(f"BOM에서 모품번 '{parent_code}'에 해당하는 하위 자재를 찾지 못했습니다.")
    else:
        display_cols = ["자품목", "자품명", "유형", "소요량", "품목", "비고"]
        display_cols = [c for c in display_cols if c in bom_matched.columns]
        st.dataframe(
            bom_matched[display_cols].rename(
                columns={"자품목": "자재품번", "자품명": "자재명"}
            ),
            use_container_width=True,
            hide_index=True,
        )

st.divider()
with st.expander("전체 ALC 데이터 검색 (자유 검색)"):
    keyword = st.text_input("검색어 입력 (품번, 품명, 사양명 등)")
    if keyword:
        mask = alc_df.apply(lambda r: r.astype(str).str.contains(keyword, case=False, na=False).any(), axis=1)
        st.dataframe(alc_df[mask], use_container_width=True, hide_index=True)
