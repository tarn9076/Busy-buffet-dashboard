"""
================================================================================
streamlit_app.py | Busy Buffet Dashboard - Hotel Amber 85
ATMIND Data Analytics Test 2026
================================================================================
โครงสร้าง 5 แท็บ:
    Tab 0 : ภาพรวม + ข้อจำกัดของข้อมูล
    Tab 1 : Task 1 - พิสูจน์คำพูดพนักงาน 3 ข้อ
    Tab 2 : Task 2 - หักล้างมาตรการ 3 ข้อ
    Tab 3 : Task 3 - ข้อเสนอที่ควรทำ (Plan A / Plan B)
    Tab 4 : Assumption & Data Quality

[กฎเหล็กของไฟล์นี้]
ห้ามใช้ภาษาไทยเป็นชื่อคอลัมน์หรือชื่อตัวแปร Python เด็ดขาด
เพราะ Python normalize สระอำ (ำ) แตกเป็นนิคหิต+สระอา (ํา) อัตโนมัติ
ทำให้ชื่อคอลัมน์ไม่ตรงกับ string ที่พิมพ์ ทั้งที่ตาเห็นเหมือนกัน
--> ชื่อในระบบใช้อังกฤษ / ภาษาไทยใช้เฉพาะข้อความแสดงผล (title, labels)
================================================================================
"""

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="Busy Buffet - Amber 85", layout="wide")

# --------------------------------------------------------------------------
# BLOCK 1: ค่าคงที่และการโหลดข้อมูล
# --------------------------------------------------------------------------
# เรียงวันตามปฏิทิน ไม่ให้ plotly เรียงตามตัวอักษรไทยเอง
DAY_ORDER = ["ศุกร์ 13/3", "เสาร์ 14/3", "อาทิตย์ 15/3", "อังคาร 17/3", "พุธ 18/3"]

# สีประจำ guest_type ใช้ให้เหมือนกันทุกกราฟ เพื่อให้คนดูจำได้
COLOR_GUEST = {"In house": "#2E86AB", "Walk in": "#F18F01"}
C_OK, C_WARN, C_BAD = "#2E9E5B", "#E8A33D", "#D64545"


@st.cache_data
def load():
    """โหลดไฟล์ที่ผ่าน cleaning pipeline มาแล้ว (clean_data.py)"""
    g = pd.read_csv("clean_groups.csv")
    u = pd.read_csv("clean_units.csv")
    inv = pd.read_csv("table_inventory.csv")
    return g, u, inv


groups, units, inventory = load()
TOTAL_UNITS = len(inventory)      # 32 หน่วยโต๊ะ = ตัวหารของ occupancy
TOTAL_SEATS = int(inventory["seats"].sum())


# --------------------------------------------------------------------------
# BLOCK 2: ฟังก์ชันคำนวณ occupancy รายนาที
# --------------------------------------------------------------------------
# วิธีคิด: สร้างแกนเวลา 1440 นาที (1 วัน) แล้วไล่ทุกกลุ่มที่นั่งอยู่
# บวก +1 ลงในทุกนาทีที่โต๊ะนั้นถูกครอง
# ทำแบบนี้เพราะการนับ "กี่โต๊ะถูกใช้ตอน 09:00" ตรงกว่าการเฉลี่ยรายชั่วโมง

@st.cache_data
def occupancy_curve(day, cap_minutes=None):
    """คืน array 1440 ช่อง = จำนวนหน่วยโต๊ะที่ถูกครองในแต่ละนาที
    cap_minutes = ถ้าใส่ จะจำลองว่าบังคับให้ลุกภายในกี่นาที (ใช้ตอน simulate Action 1)
    """
    sub = units[units["day_label"] == day].dropna(
        subset=["meal_start_min", "meal_end_min"])
    grid = np.zeros(1440)
    for _, r in sub.iterrows():
        a = int(r["meal_start_min"])
        b = int(r["meal_end_min"])
        if cap_minutes is not None:
            b = int(min(b, a + cap_minutes))
        if b > a:
            grid[a:b] += 1
    return grid


@st.cache_data
def queue_curve(day):
    """คืน array 1440 ช่อง = จำนวนกลุ่มที่ยืนรออยู่ในคิวแต่ละนาที"""
    sub = groups[(groups["day_label"] == day) & (groups["has_queue"])].dropna(
        subset=["queue_start_min", "queue_end_min"])
    grid = np.zeros(1440)
    for _, r in sub.iterrows():
        a, b = int(r["queue_start_min"]), int(r["queue_end_min"])
        if b > a:
            grid[a:b] += 1
    return grid


def hhmm(m):
    return f"{int(m) // 60:02d}:{int(m) % 60:02d}"


# --------------------------------------------------------------------------
# BLOCK 3: หัวเรื่องและแท็บ
# --------------------------------------------------------------------------
st.title("Busy Buffet — Hotel Amber 85")
st.caption("ATMIND Data Analytics Test 2026 | ข้อมูล 13–18 มีนาคม 2026 (5 วัน)")

tab0, tab1, tab2, tab3, tab4 = st.tabs([
    "ภาพรวม", "Task 1 · คำพูดพนักงาน", "Task 2 · หักล้างมาตรการ",
    "Task 3 · ข้อเสนอ", "Assumption & Data Quality"])


# ==========================================================================
# TAB 0 : ภาพรวม
# ==========================================================================
with tab0:
    st.subheader("ตัวเลขหลัก")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("กลุ่มลูกค้ารวม", f"{len(groups):,}")
    c2.metric("จำนวนคนรวม", f"{groups['pax'].sum():,.0f}")
    c3.metric("เวลานั่งเฉลี่ย (median)", f"{groups['duration_min_clean'].median():.0f} นาที")
    c4.metric("หน่วยโต๊ะทั้งหมด", f"{TOTAL_UNITS} โต๊ะ / {TOTAL_SEATS} ที่นั่ง")

    st.divider()

    # --- ข้อจำกัดของข้อมูล ต้องขึ้นก่อนกราฟทุกใบ ---
    # เหตุผล: ถ้าคนดูเห็นกราฟก่อนเห็นข้อจำกัด จะตีความเกินกว่าที่ข้อมูลรองรับ
    st.error(
        "**ข้อจำกัดสำคัญที่ต้องอ่านก่อน**\n\n"
        "1. ข้อมูลมีเพียง **5 วันจาก 7 วันของสัปดาห์** (ขาดวันจันทร์ 16/3 และไม่มีวันพฤหัสบดีเลย) "
        "จึงสรุปว่า *busy ทุกวัน* หรือ *ไม่ busy ทุกวัน* แบบเต็มสัปดาห์ไม่ได้\n\n"
        "2. **ข้อมูลคิวมีเพียง 2 วัน** (เสาร์ 14/3 และอาทิตย์ 15/3) — อีก 3 วันคอลัมน์คิวว่างทั้งคอลัมน์ "
        "ทุกตัวเลขที่เกี่ยวกับการรอและการทิ้งคิว จึงคำนวณจาก 2 วันนี้เท่านั้น\n\n"
        "3. **ไม่มีคอลัมน์ราคา ยอดขาย หรือต้นทุน** จึงวัดความอ่อนไหวต่อราคาโดยตรงไม่ได้"
    )

    st.divider()
    st.subheader("ปริมาณลูกค้ารายวัน")

    day_sum = (groups.groupby("day_label")
               .agg(n_groups=("service_no", "size"), n_pax=("pax", "sum"))
               .reindex(DAY_ORDER).reset_index())
    # เติมข้อมูลว่าวันไหนมีข้อมูลคิว เพื่อสื่อสารข้อจำกัดในกราฟเลย
    day_sum["queue_data"] = day_sum["day_label"].map(
        groups.groupby("day_label")["queue_data_available"].first())
    day_sum["note"] = np.where(day_sum["queue_data"], "มีข้อมูลคิว", "ไม่มีข้อมูลคิว")

    fig = px.bar(day_sum, x="day_label", y="n_pax", text="n_pax", color="note",
                 color_discrete_map={"มีข้อมูลคิว": C_OK, "ไม่มีข้อมูลคิว": "#9AA0A6"},
                 title="จำนวนลูกค้า (คน) ต่อวัน",
                 labels={"day_label": "", "n_pax": "จำนวนคน", "note": ""})
    fig.update_traces(textposition="outside")
    st.plotly_chart(fig, width='stretch')

    st.info(
        "เสาร์–อาทิตย์มีลูกค้าเฉลี่ย **160 คน/วัน** เทียบกับวันธรรมดา **114 คน/วัน** "
        "(มากกว่า 40%) — ความต้องการกระจุกที่วันหยุด ไม่ได้สูงเท่ากันทุกวัน"
    )


# ==========================================================================
# TAB 1 : Task 1 - พิสูจน์คำพูดพนักงาน
# ==========================================================================
with tab1:
    st.header("Task 1 — คำพูดพนักงานจริงหรือไม่")

    # ---------------- COMMENT 1 ----------------
    st.subheader("Comment 1 — ลูกค้าต้องรอโต๊ะ และทิ้งคิวเพราะรอนาน")
    st.warning("**คำตอบ: จริง — แต่พนักงานเข้าใจ *ตัวการ* ผิด**")

    q = groups[(groups["queue_data_available"]) & (groups["has_queue"])]

    t = (q.groupby("guest_type")
         .agg(queued=("service_no", "size"),
              walkaway=("is_walkaway", "sum"),
              med_wait=("wait_min", "median"))
         .reset_index())
    t["walkaway_rate"] = (t["walkaway"] / t["queued"] * 100).round(1)

    c1, c2 = st.columns(2)

    with c1:
        fig = px.bar(t, x="guest_type", y="walkaway_rate", text="walkaway_rate",
                     color="guest_type", color_discrete_map=COLOR_GUEST,
                     title="อัตราการทิ้งคิว (%)",
                     labels={"guest_type": "", "walkaway_rate": "% ที่ทิ้งคิว"})
        fig.update_traces(texttemplate="%{text}%", textposition="outside")
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, width='stretch')

    with c2:
        fig = px.bar(t, x="guest_type", y="med_wait", text="med_wait",
                     color="guest_type", color_discrete_map=COLOR_GUEST,
                     title="เวลารอเฉลี่ย (median, นาที)",
                     labels={"guest_type": "", "med_wait": "นาที"})
        fig.update_traces(textposition="outside")
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, width='stretch')

    st.error(
        "**จุดพลิก:** แขกที่พักโรงแรม (In house) **รอสั้นกว่า** walk-in (28 vs 42.5 นาที) "
        "แต่กลับ **ทิ้งคิวมากกว่าเกือบ 2 เท่า** (28.0% vs 14.6%)\n\n"
        "แปลว่าปัญหาไม่ใช่ *เวลารอนานเกินไป* แต่คือ **ความอดทนของแขกโรงแรมต่ำกว่า** "
        "เพราะเขารู้สึกว่าจ่ายค่าห้องแล้วควรได้รับสิทธิ์ — เป็นปัญหาเรื่องความคาดหวัง "
        "ไม่ใช่ปัญหาจำนวนโต๊ะ"
    )

    st.dataframe(
        t.rename(columns={"guest_type": "ประเภทลูกค้า", "queued": "เข้าคิว (กลุ่ม)",
                          "walkaway": "ทิ้งคิว (กลุ่ม)", "med_wait": "รอเฉลี่ย (นาที)",
                          "walkaway_rate": "อัตราทิ้งคิว (%)"}),
        width='stretch', hide_index=True)

    st.divider()

    # ---------------- COMMENT 2 ----------------
    st.subheader("Comment 2 — แน่นทุกวัน ธุรกิจนี้ไปไม่รอด")
    st.success("**คำตอบ: เท็จ — สำหรับ 5 วันที่มีข้อมูล**")

    rows = []
    for d in DAY_ORDER:
        curve = occupancy_curve(d)
        window = curve[390:750]           # 06:30 - 12:30 ช่วงที่ให้บริการจริง
        rows.append({
            "day_label": d,
            "peak_pct": round(curve.max() / TOTAL_UNITS * 100, 1),
            "avg_pct": round(window.mean() / TOTAL_UNITS * 100, 1),
            "peak_time": hhmm(curve.argmax()),
            "min_over75": int((curve >= 0.75 * TOTAL_UNITS).sum()),
        })
    occ_tbl = pd.DataFrame(rows)

    fig = go.Figure()
    fig.add_bar(x=occ_tbl["day_label"], y=occ_tbl["peak_pct"],
                name="สูงสุดของวัน", marker_color="#B8D8E8",
                text=occ_tbl["peak_pct"], textposition="outside")
    fig.add_bar(x=occ_tbl["day_label"], y=occ_tbl["avg_pct"],
                name="เฉลี่ยตลอดช่วงเปิด", marker_color="#2E86AB",
                text=occ_tbl["avg_pct"], textposition="outside")
    # เส้นอ้างอิง 75% = ระดับที่ถือว่าเริ่มแน่นในธุรกิจร้านอาหาร
    fig.add_hline(y=75, line_dash="dash", line_color=C_BAD,
                  annotation_text="ระดับที่ถือว่าเริ่มแน่น (75%)")
    fig.update_layout(barmode="group", title="อัตราการใช้โต๊ะรายวัน (%)",
                      yaxis_title="% ของโต๊ะทั้งหมด (32 หน่วย)", xaxis_title="")
    st.plotly_chart(fig, width='stretch')

    c1, c2 = st.columns([2, 1])
    with c1:
        st.error(
            "**ศุกร์และอังคาร ไม่แตะระดับ 75% เลยแม้แต่นาทีเดียว**\n\n"
            "- ศุกร์ใช้โต๊ะเฉลี่ยเพียง **26.8%** — โต๊ะว่างเกินครึ่งร้านนานถึง 5.5 ชั่วโมง\n"
            "- อังคารเฉลี่ย **37.9%**\n"
            "- วันเดียวที่แตะ 90% คือ **อาทิตย์ และแตะอยู่เพียง 3 นาที**\n\n"
            "ความแออัดจึงไม่ได้เกิดทุกวัน แต่กระจุกอยู่ที่ **เสาร์–อาทิตย์ ช่วง 09:00–10:30**"
        )
    with c2:
        st.dataframe(
            occ_tbl.rename(columns={"day_label": "วัน", "peak_pct": "สูงสุด %",
                                    "avg_pct": "เฉลี่ย %", "peak_time": "เวลา peak",
                                    "min_over75": "นาทีที่ >75%"}),
            width='stretch', hide_index=True)

    st.caption(
        "ข้อจำกัด: ข้อมูลมี 5 จาก 7 วัน จึงพูดได้เพียงว่า *5 วันที่วัดได้ ไม่ได้แน่นเท่ากัน* "
        "ไม่สามารถยืนยันสถานการณ์ของวันจันทร์และวันพฤหัสบดีได้"
    )

    st.divider()

    # ---------------- COMMENT 3 ----------------
    st.subheader("Comment 3 — ลูกค้า Walk-in นั่งทั้งวัน")
    st.success("**คำตอบ: เท็จ — แต่พนักงานสังเกตทิศทางถูก**")

    dur = groups.dropna(subset=["duration_min_clean"])

    c1, c2 = st.columns([3, 2])
    with c1:
        fig = px.box(dur, x="guest_type", y="duration_min_clean", color="guest_type",
                     color_discrete_map=COLOR_GUEST, points="outliers",
                     title="การกระจายของเวลานั่งกิน (นาที)",
                     labels={"guest_type": "", "duration_min_clean": "นาที"})
        # เส้นอ้างอิง: สิทธิ์ที่โปรโมชั่นให้ = 5 ชั่วโมง = 300 นาที
        fig.add_hline(y=300, line_dash="dash", line_color=C_BAD,
                      annotation_text="สิทธิ์ที่โปรโมชั่นให้ = 5 ชม.")
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, width='stretch')

    with c2:
        st.metric("นั่งเกิน 5 ชั่วโมง", "0 ราย", delta="จาก 347 ราย", delta_color="off")
        st.metric("นานที่สุดที่พบจริง", "225 นาที", delta="3 ชม. 45 นาที", delta_color="off")
        st.metric("median (ทุกคน)", "52 นาที", delta="= 17% ของสิทธิ์ 5 ชม.", delta_color="off")

    st.error(
        "**ร้านเปิดจริงเพียง 7 ชั่วโมง (06:26 – 13:30)**\n\n"
        "- โปรโมชั่น *นั่งได้ 5 ชั่วโมง* กินพื้นที่ถึง **71% ของเวลาเปิดร้านทั้งหมด**\n"
        "- ลูกค้าต้องมาถึงก่อน **08:30** เท่านั้นจึงจะใช้สิทธิ์ครบ 5 ชั่วโมงได้ "
        "— มีเพียง 40.5% ของลูกค้าที่มาทันเวลานั้น\n"
        "- คนที่นั่งนานที่สุดจริงใช้สิทธิ์ไปเพียง **75%** และมีเพียง **8 ราย (2.3%)** ที่ใช้เกินครึ่ง\n\n"
        "การ *นั่งทั้งวัน* จึงเป็นไปไม่ได้เชิงโครงสร้าง และไม่มีใครทำได้จริงแม้แต่คนเดียว"
    )

    st.warning(
        "**ส่วนที่พนักงานสังเกตถูก:** Walk-in นั่งนานกว่าแขกโรงแรมจริง "
        "— median **66 นาที เทียบกับ 38.5 นาที (นานกว่า 1.7 เท่า)** "
        "และครองเวลาโต๊ะรวม **70%** ทั้งที่เป็นเพียง 57% ของจำนวนกลุ่ม\n\n"
        "พนักงานจับ *ทิศทาง* ถูก แต่ประเมิน *ขนาด* เกินจริงไปมาก"
    )

    share = (units.dropna(subset=["duration_min_clean"])
             .groupby("guest_type")["duration_min_clean"].sum().reset_index())
    share["pct"] = (share["duration_min_clean"] / share["duration_min_clean"].sum() * 100).round(1)
    fig = px.pie(share, names="guest_type", values="duration_min_clean", hole=0.45,
                 color="guest_type", color_discrete_map=COLOR_GUEST,
                 title="สัดส่วนการครองเวลาโต๊ะรวม (table-minutes)")
    st.plotly_chart(fig, width='stretch')


# ==========================================================================
# TAB 2 : Task 2 - หักล้างมาตรการ
# ==========================================================================
with tab2:
    st.header("Task 2 — เหตุผลที่มาตรการทั้ง 3 จะไม่ได้ผล")

    # ---------------- ACTION 1 ----------------
    st.subheader("มาตรการ 1 — ลดเวลานั่งจาก 5 ชั่วโมง")
    st.error("**ไม่ได้ผล: เป็นการแก้ปัญหาที่ไม่เคยมีอยู่จริง**")

    d = groups["duration_min_clean"].dropna()
    caps = [300, 240, 180, 120, 90, 60]
    impact = pd.DataFrame({
        "cap_min": caps,
        "cap_label": [f"{c} นาที ({c/60:.1f} ชม.)" for c in caps],
        "n_affected": [int((d > c).sum()) for c in caps],
    })
    impact["pct_affected"] = (impact["n_affected"] / len(d) * 100).round(1)

    c1, c2 = st.columns([3, 2])
    with c1:
        fig = px.bar(impact, x="cap_label", y="n_affected", text="n_affected",
                     title="ถ้าจำกัดเวลานั่ง จะกระทบลูกค้ากี่กลุ่ม (จาก 347 กลุ่ม)",
                     labels={"cap_label": "เพดานเวลาที่กำหนด", "n_affected": "จำนวนกลุ่มที่ถูกกระทบ"})
        fig.update_traces(textposition="outside", marker_color="#2E86AB")
        st.plotly_chart(fig, width='stretch')
    with c2:
        st.dataframe(
            impact[["cap_label", "n_affected", "pct_affected"]].rename(
                columns={"cap_label": "เพดานเวลา", "n_affected": "กลุ่มที่กระทบ",
                         "pct_affected": "%"}),
            width='stretch', hide_index=True)

    st.warning(
        "**ลดจาก 5 ชั่วโมงเหลือ 4 ชั่วโมง กระทบลูกค้า 0 ราย** เพราะไม่มีใครนั่งนานขนาดนั้นอยู่แล้ว\n\n"
        "ต้องบีบลงถึง **90 นาที** จึงจะเริ่มเห็นผล แต่นั่นหมายถึงการไล่ลูกค้า 59 กลุ่ม (17%)"
    )

    # จำลองว่าถ้าบังคับ 90 นาที occupancy จะลดลงแค่ไหน
    sim = []
    for dd in DAY_ORDER:
        base = occupancy_curve(dd).max()
        capped = occupancy_curve(dd, cap_minutes=90).max()
        sim.append({"day_label": dd,
                    "before": round(base / TOTAL_UNITS * 100, 1),
                    "after": round(capped / TOTAL_UNITS * 100, 1)})
    sim = pd.DataFrame(sim)
    sim_long = sim.melt(id_vars="day_label", var_name="scenario", value_name="pct")
    sim_long["scenario"] = sim_long["scenario"].map(
        {"before": "ปัจจุบัน", "after": "หลังบังคับ 90 นาที"})

    fig = px.bar(sim_long, x="day_label", y="pct", color="scenario", barmode="group",
                 text="pct", title="จำลอง: ถ้าบังคับให้ลุกภายใน 90 นาที peak จะลดแค่ไหน",
                 labels={"day_label": "", "pct": "% การใช้โต๊ะสูงสุด", "scenario": ""},
                 color_discrete_map={"ปัจจุบัน": "#B8D8E8", "หลังบังคับ 90 นาที": "#2E86AB"})
    fig.update_traces(textposition="outside")
    st.plotly_chart(fig, width='stretch')

    st.error(
        "แม้บังคับเข้มถึง 90 นาที **วันศุกร์ peak ไม่ขยับเลย (59.4% เท่าเดิม)** "
        "และวันอาทิตย์ลดได้เพียง 3 จุด (90.6% → 87.5%) "
        "— ต้นทุนคือไล่ลูกค้า 17% แลกกับผลที่แทบไม่ต่าง"
    )

    st.divider()

    # ---------------- ACTION 2 ----------------
    st.subheader("มาตรการ 2 — ขึ้นราคาเป็น 259 บาททุกวัน")
    st.error("**ไม่ได้ผล: ความเสี่ยงสูงและยิงผิดเป้า**")

    st.info(
        "**ข้อจำกัดที่ต้องพูดตรง ๆ:** ไฟล์ข้อมูลไม่มีคอลัมน์ราคา ยอดขาย หรือต้นทุน "
        "จึงวัดความอ่อนไหวต่อราคา (price elasticity) โดยตรงไม่ได้ "
        "จึงใช้การวิเคราะห์จุดคุ้มทุน (break-even) แทน"
    )

    walkin = groups[groups["guest_type"] == "Walk in"]
    be = []
    for dd in DAY_ORDER:
        sub = walkin[walkin["day_label"] == dd]
        price = int(groups[groups["day_label"] == dd]["menu_price"].iloc[0])
        pax = sub["pax"].sum()
        be.append({"day_label": dd, "price": price,
                   "increase_pct": round((259 / price - 1) * 100, 1),
                   "breakeven_pct": round((1 - price / 259) * 100, 1),
                   "revenue": int(pax * price)})
    be = pd.DataFrame(be)

    c1, c2 = st.columns(2)
    with c1:
        fig = px.bar(be, x="day_label", y="breakeven_pct", text="breakeven_pct",
                     color="price", color_continuous_scale=["#D64545", "#2E86AB"],
                     title="ลูกค้าหายได้กี่ % ก่อนที่รายได้จะลดลง",
                     labels={"day_label": "", "breakeven_pct": "% ที่หายได้ก่อนขาดทุน",
                             "price": "ราคาเดิม"})
        fig.update_traces(texttemplate="%{text}%", textposition="outside")
        st.plotly_chart(fig, width='stretch')
    with c2:
        st.dataframe(
            be.rename(columns={"day_label": "วัน", "price": "ราคาเดิม",
                               "increase_pct": "ขึ้นราคา (%)",
                               "breakeven_pct": "ลูกค้าหายได้ (%)",
                               "revenue": "รายได้เดิม (บาท)"}),
            width='stretch', hide_index=True)

    st.error(
        "**ปัญหาที่ 1 — จุดคุ้มทุนแคบ:** วันธรรมดาต้องขึ้นราคาถึง **+63%** (159 → 259) "
        "ถ้าลูกค้าหายเกิน **38.6%** รายได้จะลดลงทันที ส่วนวันหยุดทนได้เพียง **23.2%**\n\n"
        "**ปัญหาที่ 2 — ยิงผิดเป้า:** วันที่ต้องขึ้นราคาแรงที่สุดคือวันธรรมดา "
        "ซึ่งใช้โต๊ะเฉลี่ยเพียง **26.8–40.7%** เท่ากับเก็บแพงขึ้นในวันที่โต๊ะว่างครึ่งร้าน "
        "โดยไม่ได้แก้ความแออัดที่กระจุกอยู่แค่เสาร์–อาทิตย์"
    )

    st.caption(
        "หมายเหตุเชิงวิธีการ: อาจดูเหมือนว่าราคาวันหยุด (199) สูงกว่าวันธรรมดา (159) 25% "
        "แต่ลูกค้ากลับมากกว่า — **ห้ามสรุปว่าขึ้นราคาแล้วลูกค้าไม่ลด** "
        "เพราะตัวแปรราคาปนกับปัจจัยวันหยุด (confounded) คนว่างในวันหยุดจึงมามากกว่าโดยไม่เกี่ยวกับราคา"
    )

    st.divider()

    # ---------------- ACTION 3 ----------------
    st.subheader("มาตรการ 3 — ให้แขกโรงแรมตัดคิว")
    st.error("**ไม่ได้ผล ในรูปแบบที่ใช้ทุกวันแบบเหมารวม**")

    # แสดงว่าวันไหนมีคิวจริงบ้าง
    qdays = []
    for dd in DAY_ORDER:
        qc = queue_curve(dd)
        has_data = bool(groups[groups["day_label"] == dd]["queue_data_available"].iloc[0])
        qdays.append({"day_label": dd,
                      "max_queue": int(qc.max()) if has_data else None,
                      "status": "มีข้อมูลคิว" if has_data else "ไม่มีข้อมูลคิว"})
    qdays = pd.DataFrame(qdays)

    c1, c2, c3 = st.columns(3)
    c1.metric("วันที่มีข้อมูลคิว", "2 จาก 5 วัน")
    c2.metric("แขกโรงแรมที่เข้าคิว (2 วัน)", "25 กลุ่ม")
    c3.metric("Walk-in ที่เข้าคิว (2 วัน)", "48 กลุ่ม")

    st.dataframe(
        qdays.rename(columns={"day_label": "วัน", "max_queue": "คิวยาวสุด (กลุ่ม)",
                              "status": "สถานะข้อมูล"}),
        width='stretch', hide_index=True)

    st.error(
        "**เหตุผลที่ 1 — 3 ใน 5 วันไม่มีคิวให้ตัด:** วันศุกร์ อังคาร พุธ "
        "ใช้โต๊ะสูงสุดเพียง 59–78% การให้สิทธิ์ตัดคิวในวันเหล่านี้จึงไม่มีผลใด ๆ\n\n"
        "**เหตุผลที่ 2 — ย้ายปัญหา ไม่ได้แก้ปัญหา (zero-sum):** วันอาทิตย์มีแขกโรงแรมเข้าคิว 19 กลุ่ม "
        "เทียบกับ walk-in 35 กลุ่ม หากแขกโรงแรมตัดคิวทั้งหมด walk-in ทุกกลุ่มจะถูกดันถอยหลังราว 54% "
        "ของคิวเดิม จำนวนโต๊ะไม่ได้เพิ่มขึ้นเลย\n\n"
        "**เหตุผลที่ 3 — บังคับใช้หน้างานไม่ได้:** แขกที่จองห้องแบบไม่รวมอาหารเช้า "
        "แล้วซื้อบุฟเฟ่ต์หน้างาน จะถูกบันทึกเป็น *Walk in* ในระบบ "
        "พนักงานจึงแยกไม่ออกว่าใครพักโรงแรมจริง เสี่ยงที่แขกโรงแรมจะถูกไล่ไปต่อท้ายคิว"
    )

    st.warning(
        "**หลักฐานสนับสนุนเหตุผลที่ 3:** ในช่วง 06:00–06:59 ซึ่งเป็นเวลาที่คนนอกยังไม่เดินทางมา "
        "พบลูกค้าที่ระบุเป็น *Walk in* ถึง **21 กลุ่ม** เทียบกับ *In house* เพียง **2 กลุ่ม** "
        "(walk-in คิดเป็น 91% ของลูกค้าช่วงเวลานั้น) "
        "ชี้ว่าคำว่า Walk in ในข้อมูลชุดนี้น่าจะหมายถึง **วิธีชำระเงิน** มากกว่า **การพักโรงแรม**"
    )


# ==========================================================================
# TAB 3 : Task 3 - ข้อเสนอ
# ==========================================================================
with tab3:
    st.header("Task 3 — ข้อเสนอที่ควรทำ")

    st.success(
        "**เลือกปรับมาตรการที่ 3 (ให้แขกโรงแรมตัดคิว) โดยเพิ่มเงื่อนไขการเปิดใช้**\n\n"
        "เหตุผลที่เลือกมาตรการนี้: เป็นมาตรการเดียวที่ตรงกับปัญหาที่ข้อมูลยืนยันได้ "
        "คือแขกโรงแรมทิ้งคิว 28% ทั้งที่รอสั้นกว่า walk-in "
        "ส่วนอีก 2 มาตรการมุ่งแก้ปัญหาที่ข้อมูลไม่พบว่ามีอยู่จริง"
    )

    st.subheader("ทำไมต้องมีเงื่อนไข — เกณฑ์ที่เลือกและเกณฑ์ที่ตัดทิ้ง")

    # เปรียบเทียบ 2 trigger บนกราฟเดียวกัน (วันอาทิตย์ = วันที่หนักสุด)
    day_pick = st.selectbox("เลือกวันเพื่อดูรายละเอียด",
                            ["อาทิตย์ 15/3", "เสาร์ 14/3"], index=0)

    occ = occupancy_curve(day_pick)
    qc = queue_curve(day_pick)
    x = list(range(6 * 60, 14 * 60))

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=[hhmm(m) for m in x], y=[occ[m] / TOTAL_UNITS * 100 for m in x],
        name="การใช้โต๊ะ (%)", line=dict(color="#2E86AB", width=2)))
    fig.add_trace(go.Scatter(
        x=[hhmm(m) for m in x], y=[qc[m] for m in x],
        name="จำนวนกลุ่มที่รอคิว", yaxis="y2",
        line=dict(color="#F18F01", width=2)))
    fig.add_hline(y=80, line_dash="dot", line_color="#999",
                  annotation_text="เกณฑ์ที่ตัดทิ้ง: การใช้โต๊ะ 80%")
    fig.update_layout(
        title=f"{day_pick} — การใช้โต๊ะ เทียบกับ ความยาวคิว",
        xaxis_title="เวลา",
        yaxis=dict(title="การใช้โต๊ะ (%)", range=[0, 100]),
        yaxis2=dict(title="กลุ่มที่รอคิว", overlaying="y", side="right",
                    range=[0, 25], showgrid=False),
        legend=dict(orientation="h", y=1.12), height=430)
    fig.update_xaxes(tickmode="array",
                     tickvals=[hhmm(m) for m in range(6 * 60, 14 * 60, 60)])
    st.plotly_chart(fig, width='stretch')

    st.error(
        "**เกณฑ์ที่ตัดทิ้ง — ใช้อัตราการใช้โต๊ะ 80%:** จับจังหวะความเดือดร้อนผิด\n\n"
        "- เวลา 09:00 วันอาทิตย์ มีลูกค้ารอคิวถึง **15 กลุ่ม** แต่การใช้โต๊ะอยู่ที่ 71.9% "
        "มาตรการจะยัง **ไม่ทำงาน**\n"
        "- เวลา 11:30 การใช้โต๊ะ 81.2% มาตรการ **ทำงาน** ทั้งที่เหลือคนรอเพียง 1 กลุ่ม\n\n"
        "สาเหตุ: โต๊ะที่ว่างบนกระดาษไม่ได้พร้อมให้นั่งทันที ต้องเก็บ ทำความสะอาด และจัดโต๊ะก่อน"
    )

    st.divider()
    st.subheader("Plan A (ข้อเสนอหลัก) — เปิดสิทธิ์ตัดคิวเมื่อคิวยาวตั้งแต่ 5 กลุ่มขึ้นไป")

    # ที่มาของเลข 5: ดูจากเวลารอ median ตามความยาวคิว
    q2 = groups[(groups["queue_data_available"]) & (groups["has_queue"])].dropna(
        subset=["queue_start_min"]).copy()

    def qlen_at_arrival(row):
        same_day = q2[q2["day_label"] == row["day_label"]]
        t = row["queue_start_min"]
        return int(((same_day["queue_start_min"] <= t) & (same_day["queue_end_min"] > t)).sum())

    q2["qlen"] = q2.apply(qlen_at_arrival, axis=1)
    q2["bucket"] = pd.cut(q2["qlen"], [-1, 2, 4, 6, 9, 99],
                          labels=["0-2", "3-4", "5-6", "7-9", "10+"])
    bk = (q2.groupby("bucket", observed=True)
          .agg(n=("service_no", "size"), med_wait=("wait_min", "median"))
          .reset_index())

    c1, c2 = st.columns([3, 2])
    with c1:
        fig = px.bar(bk, x="bucket", y="med_wait", text="med_wait",
                     title="เวลารอเฉลี่ย (median) ตามความยาวคิวขณะมาถึง",
                     labels={"bucket": "จำนวนกลุ่มที่รออยู่ในคิว", "med_wait": "นาทีที่ต้องรอ"})
        fig.update_traces(textposition="outside", marker_color="#2E86AB")
        fig.add_vrect(x0=1.5, x1=2.5, fillcolor=C_WARN, opacity=0.18, line_width=0,
                      annotation_text="จุดหักที่ 1")
        st.plotly_chart(fig, width='stretch')
    with c2:
        st.dataframe(
            bk.rename(columns={"bucket": "คิว (กลุ่ม)", "n": "จำนวนตัวอย่าง",
                               "med_wait": "รอเฉลี่ย (นาที)"}),
            width='stretch', hide_index=True)
        st.metric("จุดหักที่ 1", "คิว 5 กลุ่ม", delta="เวลารอเพิ่มเท่าตัว 11.5 → 22 นาที",
                  delta_color="off")
        st.metric("จุดหักที่ 2", "คิว 10 กลุ่ม", delta="เวลารอเพิ่ม 4 เท่า → 45 นาที",
                  delta_color="off")

    st.info(
        "**ที่มาของเลข 5:** ไม่ได้เลือกจากอัตราการทิ้งคิว เพราะฐานข้อมูลแขกโรงแรมที่เข้าคิว "
        "มีเพียง 25 กลุ่ม (ทิ้งคิว 7 ราย) เล็กเกินกว่าจะหาจุดตัดที่เชื่อถือได้ "
        "จึงใช้ **เวลารอเฉลี่ย** ซึ่งเป็นค่าที่เสถียรกว่าและเพิ่มขึ้นอย่างต่อเนื่อง "
        "พบว่าเมื่อคิวแตะ 5 กลุ่ม เวลารอกระโดดจาก 11.5 เป็น 22 นาที หรือเพิ่มเท่าตัวพอดี"
    )

    st.markdown(
        "**ข้อดีของเกณฑ์นี้**\n"
        "- พนักงานนับใบคิวได้ด้วยตาเปล่า ไม่ต้องใช้ระบบหรือคำนวณอะไร\n"
        "- เปิดใช้จริงเฉพาะ เสาร์ 33 นาที และ อาทิตย์ 173 นาที ส่วนอีก 3 วันไม่ต้องทำอะไรเลย\n"
        "- ตรงกับความรู้สึกของลูกค้า เพราะคนมองเห็นความยาวคิว ไม่ได้มองเห็นอัตราการใช้โต๊ะ"
    )

    st.divider()
    st.subheader("Plan B (ทางถอย) — กันโต๊ะไว้ 6 หน่วยสำหรับแขกโรงแรมช่วงเร่งด่วน")

    c1, c2, c3 = st.columns(3)
    c1.metric("โต๊ะที่เสนอให้กันไว้", "6 หน่วย", delta="18.8% ของ 32 หน่วย", delta_color="off")
    c2.metric("แขกโรงแรมใช้จริงสูงสุดช่วง peak", "6 หน่วย", delta="ทั้งเสาร์และอาทิตย์",
              delta_color="off")
    c3.metric("เหลือให้ walk-in", "26 หน่วย", delta="เคยใช้จริงสูงสุด 23 หน่วย",
              delta_color="off")

    st.warning(
        "**เมื่อไรจึงควรใช้ Plan B แทน Plan A:** หากตรวจสอบแล้วพบว่าแขกที่จองห้องแบบไม่รวมอาหารเช้า "
        "ถูกบันทึกเป็น *Walk in* จริง Plan A จะบังคับใช้หน้างานไม่ได้ "
        "เพราะพนักงานแยกไม่ออกว่าใครพักโรงแรม และแขกโรงแรมกลุ่มนี้จะถูกไล่ไปต่อท้ายคิว "
        "แล้วไปร้องเรียนที่แผนกต้อนรับ\n\n"
        "Plan B ไม่ต้องตัดสินหน้างานว่าใครเป็นใคร จึงมีความเสี่ยงด้านการบริการต่ำกว่า"
    )

    st.markdown(
        "**ตัวเลข 6 หน่วยมาจากไหน:** ดูจากจำนวนโต๊ะที่แขกโรงแรมครองจริงสูงสุด "
        "ในช่วง 08:30–11:00 ของทั้งเสาร์และอาทิตย์ ซึ่งเท่ากับ 6 หน่วยทั้งสองวัน "
        "โดยยังเหลือ 26 หน่วยให้ walk-in ซึ่งมากกว่าที่ walk-in เคยใช้จริงตอนแน่นที่สุด (23 หน่วย)"
    )

    st.divider()
    st.error(
        "**ข้อควรระวังที่ต้องระบุก่อนนำไปใช้**\n\n"
        "เกณฑ์ทั้งหมดนี้คำนวณจากข้อมูลคิวเพียง 2 วัน (73 กลุ่มที่เข้าคิว) "
        "จึงเป็นจุดตั้งต้นที่ดีที่สุดเท่าที่ข้อมูลปัจจุบันรองรับ ไม่ใช่ค่าตายตัว\n\n"
        "**ข้อเสนอ:** ทดลองใช้ 2 สัปดาห์ พร้อมกับเก็บข้อมูลคิวให้ครบทุกวัน "
        "แล้วนำมาปรับเกณฑ์อีกครั้ง โดยวัดผลจากอัตราการทิ้งคิวของแขกโรงแรม "
        "ซึ่งปัจจุบันอยู่ที่ 28%"
    )


# ==========================================================================
# TAB 4 : Assumption & Data Quality
# ==========================================================================
with tab4:
    st.header("Assumption & Data Quality")

    st.warning(
        "**สถานะการสอบถาม:** ส่งคำถามเพื่อขอความชัดเจนไปยังผู้ให้ข้อมูลเมื่อวันที่ 28 กรกฎาคม 2026 "
        "ยังไม่ได้รับคำตอบจนถึงวันจัดทำรายงาน จึงตัดสินใจดำเนินการต่อด้วยสมมติฐาน "
        "ที่มีหลักฐานจากตัวข้อมูลรองรับ และเปิดเผยสมมติฐานทั้งหมดไว้ในหน้านี้"
    )

    st.subheader("สมมติฐานที่ใช้")
    assumptions = pd.DataFrame([
        ["A-01", "ชื่อชีต = วันที่ + เลขเดือน จึงเป็น 13–18 มีนาคม 2026",
         "ปฏิทินปี 2026 ตรงกับรูปแบบเสาร์–อาทิตย์ที่ยอดสูงสุด และหลักสุดท้ายของชื่อชีตคือเดือน"],
        ["A-02", "เลขโต๊ะแบบย่อ ใช้กฎผสมตามจำนวนคน (3 คนขึ้นไปใช้ทั้งโต๊ะ)",
         "ทดสอบ 3 วิธี วิธีนี้ขัดแย้งน้อยกว่าการตีความว่าใช้ทั้งโต๊ะเสมอ (26 เทียบกับ 37 คู่)"],
        ["A-03", "โต๊ะ 16 เป็นโต๊ะจริงที่เอกสารผังเขียนตกหล่น",
         "พบ 24 ครั้ง กระจายทุกวันสม่ำเสมอ วันละ 4–5 ครั้ง ซึ่งไม่ใช่ลักษณะของการพิมพ์ผิด"],
        ["A-04", "โต๊ะ 15A / 15B ยอมรับเป็นฝั่งละ 2 ที่นั่ง",
         "พบเพียง 5 แถว (1.4%) เลือกแนวทางที่ทำให้จำนวนที่นั่งรวมไม่บวมเกินจริง"],
        ["A-05", "ผังที่นั่งรวม 32 หน่วยโต๊ะ 74 ที่นั่ง",
         "รวมจากผังในเอกสารแนบ บวกโต๊ะ 16 และ 15A/15B ตาม A-03 และ A-04"],
        ["A-06", "3 วันที่ไม่มีข้อมูลคิว คือไม่ได้บันทึก ไม่ใช่ไม่มีคนรอ",
         "3 วันนั้นใช้โต๊ะสูงสุด 59–78% เป็นไปไม่ได้ที่จะไม่มีลูกค้าต้องรอเลยแม้แต่กลุ่มเดียว"],
        ["A-07", "ช่วงเวลาให้บริการ 06:26–13:30 (7.07 ชั่วโมง)",
         "อ้างอิงจากเวลาจริงในข้อมูล ไม่ได้อ้างอิงมาตรฐานอุตสาหกรรม"],
        ["A-08", "คำว่า Walk in อาจหมายถึงวิธีชำระเงิน ไม่ใช่การพักโรงแรม",
         "ช่วง 06:00–06:59 พบ Walk in 21 กลุ่ม เทียบกับ In house 2 กลุ่ม (91%)"],
    ], columns=["code", "assumption", "evidence"])

    st.dataframe(
        assumptions.rename(columns={"code": "รหัส", "assumption": "สมมติฐาน",
                                    "evidence": "หลักฐานรองรับ"}),
        width='stretch', hide_index=True)

    st.subheader("ปัญหาคุณภาพข้อมูลที่ตรวจพบ")

    # นับ flag จากคอลัมน์ dq_flags ที่ pipeline สร้างไว้
    flag_rows = []
    for f in groups["dq_flags"].fillna(""):
        for x in f.split("|"):
            if x:
                flag_rows.append(x)
    flag_count = pd.Series(flag_rows).value_counts().reset_index()
    flag_count.columns = ["flag", "n_rows"]

    FLAG_TH = {
        "DQ01_NO_QUEUE_DATA_THIS_DAY": "วันที่ไม่มีการบันทึกข้อมูลคิวเลย",
        "DQ04_BARE_TABLE_NO": "เลขโต๊ะบันทึกแบบย่อ ไม่ระบุฝั่ง A/B",
        "DQ03_TABLE16_NOT_IN_APPENDIX": "โต๊ะ 16 ไม่ปรากฏในผังที่นั่งแนบท้าย",
        "DQ16_PAX_OVER_CAPACITY": "จำนวนคนเกินความจุที่นั่งของโต๊ะ",
        "DQ06_SEPARATOR": "ใช้ตัวคั่นโต๊ะรวมไม่ตรงรูปแบบที่กำหนด",
        "DQ05_TABLE15_SPLIT": "โต๊ะ 15 ถูกแยกฝั่ง ทั้งที่ผังระบุว่าแยกไม่ได้",
        "DQ14_PAX_ZERO_WALKAWAY": "ไม่มีจำนวนคน เนื่องจากทิ้งคิวก่อนได้นั่ง",
        "DQ13_PAX_ZERO_BUT_SEATED": "ไม่มีจำนวนคน ทั้งที่ได้นั่งแล้ว",
        "DQ11_DURATION_CENSORED": "เวลาออกตรงกับเวลาปิดร้านพอดี",
        "DQ_QUEUE_AREA": "นั่งรับประทานในพื้นที่รอคิว (โต๊ะ 99)",
        "DQ07_CROSS_ZONE_COMBINE": "รวมโต๊ะข้ามโซนในและนอกอาคาร",
        "DQ10_MEALSTART_OUT_OF_HOURS": "เวลาเริ่มรับประทานอยู่นอกเวลาให้บริการ",
        "DQ09_MEALEND_BEFORE_START": "เวลาออกก่อนเวลาเข้า",
    }
    flag_count["description"] = flag_count["flag"].map(FLAG_TH)
    st.dataframe(
        flag_count[["description", "n_rows", "flag"]].rename(
            columns={"description": "ปัญหาที่พบ", "n_rows": "จำนวนแถว", "flag": "รหัส"}),
        width='stretch', hide_index=True)

    st.info(
        "**แนวทางจัดการ:** ตัดออกเพียง 1 แถวที่ไม่มีข้อมูลใช้งานเลย "
        "ส่วนที่เหลือเก็บไว้ทั้งหมดพร้อมติดรหัสกำกับ เพื่อให้เลือกรวมหรือแยกออกได้ตอนวิเคราะห์ "
        "และตรวจสอบย้อนกลับได้"
    )

    st.subheader("คำถามที่ข้อมูลชุดนี้ยังตอบไม่ได้")
    st.markdown(
        "1. เหตุใดจึงไม่มีข้อมูลของวันจันทร์ที่ 16 มีนาคม และไม่มีวันพฤหัสบดีเลย\n"
        "2. เหตุใดวันศุกร์ อังคาร และพุธ จึงไม่มีการบันทึกข้อมูลคิว\n"
        "3. แขกที่พักโรงแรมชำระค่าอาหารเช้ารวมในค่าห้อง หรือชำระแยก "
        "และแขกที่จองห้องแบบไม่รวมอาหารเช้าถูกบันทึกเป็นประเภทใด\n"
        "4. ไม่มีข้อมูลราคา ยอดขาย และต้นทุน จึงประเมินผลกระทบด้านรายได้ได้เพียงโดยประมาณ"
    )

    st.divider()
    with st.expander("ดูข้อมูลที่ผ่านการทำความสะอาดแล้ว"):
        st.dataframe(groups, width='stretch')
