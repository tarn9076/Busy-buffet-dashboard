"""
================================================================================
streamlit_app.py  |  SMOKE TEST  |  Busy Buffet - ATMIND Data Test 2026
================================================================================
ไฟล์นี้ไม่ใช่ dashboard จริง เป็นแค่ไฟล์ทดสอบว่า deploy ได้จริงไหม
เทส 4 อย่างพร้อมกัน:
    1. Streamlit ขึ้นเป็น public URL ได้
    2. pandas อ่านไฟล์ CSV ได้ (path ถูก)
    3. plotly วาดกราฟได้
    4. ภาษาไทยแสดงผลถูกต้อง ไม่เป็นสี่เหลี่ยม
ถ้าหน้านี้ขึ้นครบทุกส่วน = พร้อมทำ dashboard จริง
================================================================================
"""

import pandas as pd
import plotly.express as px
import streamlit as st

# ตั้งค่าหน้าเว็บ - ต้องเป็นคำสั่งแรกสุดของ streamlit เสมอ
st.set_page_config(page_title="Smoke Test - Busy Buffet", layout="wide")

st.title("✅ Smoke Test — Busy Buffet Dashboard")
st.caption("ถ้าเห็นครบทั้ง 4 ข้อข้างล่าง แปลว่า deploy สำเร็จ พร้อมทำของจริง")

# --- เทส 1: Streamlit ทำงาน ---
st.success("**เทส 1 ผ่าน** — Streamlit รันได้")

# --- เทส 2: ภาษาไทย ---
st.success("**เทส 2 ผ่าน** — ภาษาไทยอ่านออก: ศุกร์ เสาร์ อาทิตย์ อังคาร พุธ")

# --- เทส 3: อ่านไฟล์ข้อมูล ---
# ใช้ @st.cache_data เพื่อไม่ให้อ่านไฟล์ใหม่ทุกครั้งที่ผู้ใช้กดอะไร (เร็วขึ้นมาก)
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
# เรียงวันตามลำดับปฏิทิน ไม่ให้ plotly เรียงตามตัวอักษรไทยเอง
ORDER = ["ศุกร์ 13/3", "เสาร์ 14/3", "อาทิตย์ 15/3", "อังคาร 17/3", "พุธ 18/3"]

summary = (df.groupby("day_label")
             .agg(จำนวนกลุ่ม=("service_no", "size"))
             .reindex(ORDER)
             .reset_index())

fig = px.bar(summary, x="day_label", y="จำนวนกลุ่ม",
             title="จำนวนกลุ่มลูกค้าต่อวัน (13–18 มี.ค. 2026)",
             text="จำนวนกลุ่ม")
fig.update_traces(textposition="outside")
fig.update_layout(xaxis_title="", yaxis_title="จำนวนกลุ่ม")

st.success("**เทส 4 ผ่าน** — plotly วาดกราฟได้")
st.plotly_chart(fig, use_container_width=True)

st.divider()
st.subheader("ตัวอย่างข้อมูล 10 แถวแรก")
st.dataframe(df.head(10), use_container_width=True)
