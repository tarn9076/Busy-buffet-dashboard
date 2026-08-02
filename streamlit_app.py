"""
================================================================================
streamlit_app.py  |  SMOKE TEST  |  Busy Buffet - ATMIND Data Test 2026
================================================================================
ไฟล์นี้ไม่ใช่ dashboard จริง เป็นแค่ไฟล์ทดสอบว่า deploy ได้จริงไหม
เทส 4 อย่าง: streamlit รันได้ / อ่าน csv ได้ / plotly วาดกราฟได้ / ภาษาไทยขึ้น

[บทเรียนสำคัญ - แก้จาก error รอบแรก]
ห้ามใช้ภาษาไทยเป็น "ชื่อคอลัมน์" หรือ "ชื่อตัวแปร" ใน Python เด็ดขาด
เพราะ Python จะ normalize สระอำ (ำ) แตกเป็น นิคหิต+สระอา (ํา) อัตโนมัติ
ทำให้ชื่อคอลัมน์ที่ได้ ไม่ตรงกับ string ที่เราพิมพ์ ทั้งที่ตาเห็นเหมือนกัน
--> ชื่อคอลัมน์ใช้อังกฤษล้วน / ภาษาไทยใช้เฉพาะข้อความที่แสดงผล (labels, title)
================================================================================
"""

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Smoke Test - Busy Buffet", layout="wide")

st.title("✅ Smoke Test — Busy Buffet Dashboard")
st.caption("ถ้าเห็นครบทั้ง 4 ข้อข้างล่าง แปลว่า deploy สำเร็จ พร้อมทำของจริง")

# --- เทส 1 ---
st.success("**เทส 1 ผ่าน** — Streamlit รันได้")

# --- เทส 2 ---
st.success("**เทส 2 ผ่าน** — ภาษาไทยอ่านออก: ศุกร์ เสาร์ อาทิตย์ อังคาร พุธ")


# --- เทส 3: อ่านไฟล์ ---
# cache ไว้ ไม่ต้องอ่านไฟล์ใหม่ทุกครั้งที่ผู้ใช้กดอะไร
@st.cache_data
def load_data():
    return pd.read_csv("clean_groups.csv")


try:
    df = load_data()
    st.success(f"**เทส 3 ผ่าน** — อ่าน clean_groups.csv ได้ {len(df)} แถว {len(df.columns)} คอลัมน์")
except Exception as e:
    st.error(f"**เทส 3 ไม่ผ่าน** — อ่านไฟล์ไม่ได้: {e}")
    st.stop()

# --- เทส 4: วาดกราฟ ---
# เรียงวันตามปฏิทิน ไม่ให้เรียงตามตัวอักษรไทยเอง
ORDER = ["ศุกร์ 13/3", "เสาร์ 14/3", "อาทิตย์ 15/3", "อังคาร 17/3", "พุธ 18/3"]

# ชื่อคอลัมน์เป็นอังกฤษ "n_groups" (ไม่ใช้ไทย ดูเหตุผลหัวไฟล์)
summary = (df.groupby("day_label")
             .agg(n_groups=("service_no", "size"))
             .reindex(ORDER)
             .reset_index())

fig = px.bar(
    summary,
    x="day_label",
    y="n_groups",
    text="n_groups",
    title="จำนวนกลุ่มลูกค้าต่อวัน (13–18 มี.ค. 2026)",
    # labels = แปลงชื่อคอลัมน์อังกฤษ -> ข้อความไทยตอนแสดงผล (ปลอดภัย)
    labels={"day_label": "", "n_groups": "จำนวนกลุ่ม"},
)
fig.update_traces(textposition="outside")

st.success("**เทส 4 ผ่าน** — plotly วาดกราฟได้")
st.plotly_chart(fig, use_container_width=True)

st.divider()
st.subheader("ตัวอย่างข้อมูล 10 แถวแรก")
st.dataframe(df.head(10), use_container_width=True)
